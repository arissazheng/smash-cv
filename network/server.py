"""Authoritative game server: many rooms, each one match, played in browsers.

Owner: Person 3.

    python main.py server            # then open the printed link

Players choose on the start page: "vs CPU" makes a private room with a CPU
opponent; "with friends" makes a room with a shareable link (?room=ABCD) for
up to 4 players. Opening that link joins the same room.

Browsers load the play page from this same server and connect back over a
WebSocket at /ws. Each browser runs MediaPipe locally and sends landmarks, never
video and never controller inputs. The server runs Person 2's gesture
recognizer for each player, steps the world 60 times a second, and sends
snapshots (30/s) and events in the formats of shared/protocol.py.
"""

from __future__ import annotations

import asyncio
from collections import deque
from dataclasses import dataclass, field
import mimetypes
from pathlib import Path
import random
import string
from uuid import uuid4

from websockets.asyncio.server import ServerConnection, serve as ws_serve
from websockets.datastructures import Headers
from websockets.exceptions import ConnectionClosed
from websockets.http11 import Request, Response

from game.cpu import CpuController
from game.engine import GameWorld
from game.stage import DEFAULT_STAGE, STAGES
from gestures.recognizer import GestureRecognizer
from network.protocol import CHARACTERS, MAX_MESSAGE_BYTES, ProtocolError, decode, encode, validate_client
from shared import config, protocol
from shared.controller_state import ControllerState
from shared.landmarks import LandmarkFrame
from vision.calibration import Calibration

STALE_INPUT_SECONDS = 0.25   # no landmarks for this long: stand still
DISCONNECT_SECONDS = 5.0     # no landmarks for this long mid-match: removed from the match
MAX_PENDING_ACTIONS = 32
MAX_MESSAGES_PER_SECOND = 120
MAX_ROOMS = 100
MAX_FRIENDS = 4              # players in a friends room
CPU_ID = 1                   # in a CPU room the human is player 0
WS_PATH = "/ws"

# Files the server may hand to browsers: URL prefix -> folder in the repo.
STATIC_ROOTS = {"/client/": config.ROOT / "client", "/assets/": config.ROOT / "assets"}
INDEX_PAGE = config.ROOT / "client" / "index.html"


@dataclass
class Session:
    player_id: int
    name: str
    character: str
    ws: ServerConnection
    ready: bool = False
    rematch: bool = False
    calibration: Calibration = field(default_factory=Calibration)
    recognizer: GestureRecognizer | None = None
    held: ControllerState = field(default_factory=ControllerState)
    actions: deque = field(default_factory=deque)  # (time, ControllerState) with jump/attack/taunt
    last_input: float = 0.0
    last_frame_t: float = -1.0
    controls: deque = field(default_factory=deque)
    latest_snapshot: dict | None = None
    wake: asyncio.Event = field(default_factory=asyncio.Event)
    closed: bool = False

    def __post_init__(self):
        self.recognizer = GestureRecognizer(self.calibration, self.player_id)

    # ---- outgoing ---------------------------------------------------------

    def send(self, message: dict):
        """Queue a message. Snapshots replace each other, so a slow link gets the newest one."""
        if self.closed:
            return
        if message["type"] == "snapshot":
            self.latest_snapshot = message
        elif len(self.controls) < 256:
            self.controls.append(message)
        else:
            self.close()
        self.wake.set()

    async def write_loop(self):
        try:
            while not self.closed:
                await self.wake.wait()
                self.wake.clear()
                while self.controls or self.latest_snapshot is not None:
                    if self.controls:
                        packet = self.controls.popleft()
                    else:
                        packet, self.latest_snapshot = self.latest_snapshot, None
                    await asyncio.wait_for(self.ws.send(encode(packet)), timeout=1.0)
        except (ConnectionClosed, OSError, asyncio.TimeoutError):
            self.close()

    def close(self):
        if not self.closed:
            self.closed = True
            self.wake.set()
            asyncio.get_running_loop().create_task(self.ws.close())

    # ---- incoming ---------------------------------------------------------

    def set_calibration(self, values: dict):
        self.calibration = Calibration(**values)
        self.recognizer = GestureRecognizer(self.calibration, self.player_id)
        self.last_frame_t = -1.0

    def reset_inputs(self, now):
        self.held = ControllerState(player_id=self.player_id)
        self.actions.clear()
        self.last_input = now

    def accept_frame(self, frame_data: dict, now: float):
        """Run the gesture recognizer on one camera frame from the browser."""
        frame = LandmarkFrame.from_dict(frame_data)
        if frame.timestamp <= self.last_frame_t:
            return  # out of order or repeated; the recognizer needs increasing time
        self.last_frame_t = frame.timestamp
        state = self.recognizer.update(frame)
        self.held = state
        self.last_input = now
        if state.jump or state.attack or state.taunt:
            if len(self.actions) >= MAX_PENDING_ACTIONS:
                self.actions.popleft()
            self.actions.append((now, state))

    def consume(self, now) -> ControllerState:
        """This tick's input: held controls plus at most one queued action."""
        state = ControllerState(player_id=self.player_id)
        if now - self.last_input <= STALE_INPUT_SECONDS:
            state.move_x, state.crouch, state.shield = self.held.move_x, self.held.crouch, self.held.shield
        while self.actions and now - self.actions[0][0] > STALE_INPUT_SECONDS:
            self.actions.popleft()
        if self.actions:
            _, action = self.actions.popleft()
            state.jump, state.attack, state.taunt = action.jump, action.attack, action.taunt
        return state  # pause is ignored online: one player can't freeze everyone's match


class Room:
    """One lobby and its match. mode is "cpu" (one human vs the CPU) or "friends" (2–4 humans)."""

    def __init__(self, server: "GameServer", code: str, mode: str):
        self.server, self.code, self.mode = server, code, mode
        self.capacity = 1 if mode == "cpu" else MAX_FRIENDS  # humans
        self.sessions: dict[int, Session] = {}
        self.stage_id = DEFAULT_STAGE  # the host picks in the lobby
        self.world: GameWorld | None = None
        self.cpu: CpuController | None = None
        self.starts_at = 0.0

    @property
    def link(self) -> str:
        return f"{self.server.link}?room={self.code}"

    @property
    def phase(self) -> str:
        return "lobby" if self.world is None else self.world.phase

    @property
    def host(self) -> int | None:
        """The first player to join (lowest id still connected) picks the stage."""
        return min(self.sessions, default=None)

    def cpu_character(self) -> str:
        """A different fighter from the human's."""
        human = next(iter(self.sessions.values()), None)
        return next(c for c in CHARACTERS if human is None or c != human.character)

    # ---- joining and leaving ------------------------------------------------

    def join(self, name: str, character: str, ws) -> Session:
        if self.world is not None:
            raise ProtocolError("match in progress; join after it ends")
        free = [i for i in range(self.capacity) if i not in self.sessions]
        if not free:
            raise ProtocolError("room is full")
        session = Session(free[0], name, character, ws)
        self.sessions[session.player_id] = session
        session.send(protocol.welcome(session.player_id, self.code, self.link, self.mode))
        self.lobby()
        return session

    def leave(self, session: Session):
        if self.sessions.get(session.player_id) is not session:
            return
        del self.sessions[session.player_id]
        if self.world:
            self.world.eliminate(session.player_id)
            self.publish_events()
            self.snapshot()
        if not self.sessions:
            self.world = None
        elif self.world and self.world.phase == "finished" and all(s.rematch for s in self.sessions.values()):
            self.reset()
        self.lobby()

    # ---- messages to everyone in the room ------------------------------------

    def broadcast(self, message):
        for session in list(self.sessions.values()):
            session.send(message)

    def lobby(self):
        players = [protocol.LobbyPlayer(s.player_id, s.name, s.character, s.ready, not s.closed, s.rematch)
                   for s in sorted(self.sessions.values(), key=lambda s: s.player_id)]
        if self.mode == "cpu":
            players.append(protocol.LobbyPlayer(CPU_ID, "CPU", self.cpu_character(), True, True, True, cpu=True))
        self.broadcast(protocol.lobby(self.code, self.link, self.host, self.stage_id, self.phase,
                                      self.capacity, players, self.mode))

    def snapshot(self):
        if self.world is not None:
            self.broadcast(self.world.snapshot())

    def publish_events(self):
        if self.world and self.world.events:
            for e in self.world.events:
                self.broadcast(protocol.event(e, self.world.tick_number, self.world.time))
            self.world.events = []

    # ---- match lifecycle ------------------------------------------------------

    def start_if_ready(self):
        humans = len(self.sessions)
        enough = humans == 1 if self.mode == "cpu" else humans >= 2
        if self.world is not None or not enough or not all(s.ready for s in self.sessions.values()):
            return
        now = asyncio.get_running_loop().time()
        players = [{"id": s.player_id, "name": s.name, "character": s.character}
                   for s in sorted(self.sessions.values(), key=lambda s: s.player_id)]
        if self.mode == "cpu":
            players.append({"id": CPU_ID, "name": "CPU", "character": self.cpu_character()})
        stage = STAGES[self.stage_id](len(players))
        self.world = GameWorld([p["id"] for p in players], stage=stage, stocks=self.server.stocks,
                               match_id=uuid4().hex)
        by_id = {f.player_id: f for f in self.world.fighters}
        for p in players:
            by_id[p["id"]].character = p["character"]
        self.cpu = CpuController(by_id[CPU_ID], by_id[0], CPU_ID) if self.mode == "cpu" else None
        self.world.phase = "countdown"
        self.starts_at = now + self.server.countdown
        for session in self.sessions.values():
            session.reset_inputs(now)
        self.broadcast(protocol.match_start(self.world.stage, players, self.server.countdown))
        self.lobby()
        self.snapshot()

    def reset(self):
        self.world = None
        self.cpu = None
        for session in self.sessions.values():
            session.ready = session.rematch = False
            session.latest_snapshot = None
        self.lobby()

    def handle(self, session: Session, message: dict, now: float):
        kind = message["type"]
        if kind == "landmarks":
            if self.world and self.world.phase == "playing":
                session.accept_frame(message["frame"], now)
        elif kind == "character" and self.world is None:
            session.character = message["character"]
            self.lobby()
        elif kind == "stage" and self.world is None and session.player_id == self.host:
            self.stage_id = message["stage"]
            self.lobby()
        elif kind == "calibrate":
            session.set_calibration(message["calibration"])
        elif kind == "ready" and self.world is None:
            session.ready = message["ready"]
            self.lobby()
            self.start_if_ready()
        elif kind == "rematch" and self.world and self.world.phase == "finished":
            session.rematch = True
            self.lobby()
            if all(s.rematch for s in self.sessions.values()):
                self.reset()
        elif kind == "hello":
            raise ProtocolError("already joined")

    def tick(self, now: float, dt: float):
        world = self.world
        if world is None:
            return
        if world.phase == "countdown" and now >= self.starts_at:
            world.phase = "playing"
            for s in self.sessions.values():
                s.last_input = now
            self.lobby()
        if world.phase != "playing":
            return
        for s in list(self.sessions.values()):
            if now - s.last_input > DISCONNECT_SECONDS:
                s.close()  # camera stopped sending; the handler removes them
        lives = {f.player_id: f.life_id for f in world.fighters}
        inputs = {s.player_id: s.consume(now) for s in self.sessions.values()}
        if self.cpu is not None:
            inputs[CPU_ID] = self.cpu.poll(dt)
        world.step(inputs)
        for f in world.fighters:
            if f.life_id != lives[f.player_id] and f.player_id in self.sessions:
                self.sessions[f.player_id].actions.clear()  # no attacks queued across a KO
        finished = world.phase == "finished"
        self.publish_events()
        if finished:
            self.snapshot()
            self.lobby()  # phase "finished": browsers show rematch


class GameServer:
    def __init__(self, host=config.SERVER_HOST, port=config.SERVER_PORT,
                 stocks=2, countdown=3.0, public_url: str | None = None):
        if stocks < 1 or countdown < 0:
            raise ValueError("expected positive stocks and a nonnegative countdown")
        self.host, self.port = host, port
        self.stocks, self.countdown = stocks, countdown
        self.rooms: dict[str, Room] = {}
        self.tick_overruns = 0
        self._server = None
        self._ticker = None
        self._closing = False
        self._link = public_url

    @property
    def address(self):
        return self._server.sockets[0].getsockname()[:2]

    @property
    def link(self) -> str:
        """The server's base link: --public-url, or the address the first browser used."""
        if self._link:
            return self._link
        host, port = self.address
        return f"http://{'127.0.0.1' if host in ('0.0.0.0', '::') else host}:{port}/"

    async def start(self):
        self._server = await ws_serve(self._handle, self.host, self.port,
                                      process_request=self._http, max_size=MAX_MESSAGE_BYTES)
        self._ticker = asyncio.create_task(self._tick_loop())
        return self

    async def close(self):
        self._closing = True
        if self._ticker:
            self._ticker.cancel()
            await asyncio.gather(self._ticker, return_exceptions=True)
        if self._server:
            self._server.close()
            await self._server.wait_closed()

    def _new_room(self, mode: str) -> Room:
        if len(self.rooms) >= MAX_ROOMS:
            raise ProtocolError("the server is full; try again later")
        while (code := "".join(random.choices(string.ascii_uppercase, k=4))) in self.rooms:
            pass
        room = self.rooms[code] = Room(self, code, mode)
        return room

    # ---- web page ---------------------------------------------------------

    def _http(self, connection: ServerConnection, request: Request) -> Response | None:
        path = request.path.split("?", 1)[0]
        if path == WS_PATH:
            if not self._link:  # remember how players reach us, for the shareable link
                proto = request.headers.get("X-Forwarded-Proto", "http")
                if host := request.headers.get("Host"):
                    self._link = f"{proto}://{host}/"
            return None  # continue with the WebSocket handshake
        file = INDEX_PAGE if path in ("/", "/index.html") else None
        for prefix, root in STATIC_ROOTS.items():
            if path.startswith(prefix):
                candidate = (root / path[len(prefix):]).resolve()
                if candidate.is_relative_to(root.resolve()) and candidate.is_file():
                    file = candidate
        if file is None or not file.is_file():
            return _response(404, "Not Found", b"not found\n", "text/plain")
        kind = mimetypes.guess_type(file.name)[0] or "application/octet-stream"
        if file.suffix == ".js":
            kind = "text/javascript"
        return _response(200, "OK", file.read_bytes(), kind)

    # ---- one connection ----------------------------------------------------

    async def _handle(self, ws: ServerConnection):
        session = room = None
        write_task = None
        try:
            hello = validate_client(decode(await asyncio.wait_for(ws.recv(), timeout=5.0)))
            if hello["type"] != "hello":
                raise ProtocolError("hello must be the first message")
            if hello["room"] is not None:
                room = self.rooms.get(hello["room"])
                if room is None or room.mode != "friends":
                    raise ProtocolError(f"room {hello['room']} doesn't exist; ask for a new link")
            else:
                room = self._new_room(hello["mode"])
            session = room.join(hello["name"].strip(), hello["character"], ws)
            write_task = asyncio.create_task(session.write_loop())

            loop = asyncio.get_running_loop()
            rate_start, messages = loop.time(), 0
            while not session.closed:
                message = validate_client(decode(await ws.recv()))
                now = loop.time()
                if now - rate_start >= 1:
                    rate_start, messages = now, 0
                messages += 1
                if messages > MAX_MESSAGES_PER_SECOND:
                    raise ProtocolError("message rate exceeded")
                if message["type"] == "leave":
                    break
                room.handle(session, message, now)
        except ProtocolError as exc:
            try:
                await asyncio.wait_for(ws.send(encode(protocol.error(str(exc)))), timeout=0.5)
                await ws.close(1008, "protocol error")
            except (ConnectionClosed, OSError, asyncio.TimeoutError):
                pass
        except (ConnectionClosed, OSError, asyncio.TimeoutError):
            pass
        finally:
            if session:
                session.close()
            if write_task:
                write_task.cancel()
                await asyncio.gather(write_task, return_exceptions=True)
            if session and room and not self._closing:
                room.leave(session)
            if room and not room.sessions and self.rooms.get(room.code) is room:
                del self.rooms[room.code]

    # ---- the clock -----------------------------------------------------------

    async def _tick_loop(self):
        loop = asyncio.get_running_loop()
        dt = 1 / config.SIMULATION_HZ
        next_tick = next_snapshot = loop.time()
        while True:
            now = loop.time()
            steps = 0
            while now >= next_tick and steps < 5:
                for room in list(self.rooms.values()):
                    room.tick(now, dt)
                next_tick += dt
                steps += 1
            if now >= next_tick:
                self.tick_overruns += 1
                next_tick = now + dt
            if now >= next_snapshot:
                for room in list(self.rooms.values()):
                    if room.world and room.world.phase != "finished":
                        room.snapshot()
                next_snapshot = now + 1 / config.SNAPSHOT_HZ
            await asyncio.sleep(max(0.0, min(next_tick, next_snapshot) - loop.time()))


def _response(status: int, reason: str, body: bytes, content_type: str) -> Response:
    headers = Headers([("Content-Type", content_type), ("Content-Length", str(len(body))),
                       ("Cache-Control", "no-cache")])
    return Response(status, reason, headers, body)


async def serve(args):
    server = await GameServer(args.host, args.port, args.stocks, public_url=args.public_url).start()
    host, port = server.address
    print("Smash CV server running. Players choose vs CPU or with friends on the start page.", flush=True)
    print(f"  On this computer:  http://127.0.0.1:{port}/", flush=True)
    if not args.public_url:
        print("  For friends on other computers, the link must be https (browsers only allow the",
              flush=True)
        print(f"  camera on https). For example: cloudflared tunnel --url http://localhost:{port}",
              flush=True)
        print("  then restart with --public-url <the https link> so room links use it.", flush=True)
    try:
        await asyncio.Event().wait()
    finally:
        await server.close()
