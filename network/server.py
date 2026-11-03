"""Authoritative game server: one 2–4 player match at a time, played in browsers.

Owner: Person 3.

    python main.py server            # then open the printed link

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

from game.engine import GameWorld
from gestures.recognizer import GestureRecognizer
from network.protocol import MAX_MESSAGE_BYTES, ProtocolError, decode, encode, validate_client
from shared import config, protocol
from shared.controller_state import ControllerState
from shared.landmarks import LandmarkFrame
from vision.calibration import Calibration

STALE_INPUT_SECONDS = 0.25   # no landmarks for this long: stand still
DISCONNECT_SECONDS = 5.0     # no landmarks for this long mid-match: removed from the match
MAX_PENDING_ACTIONS = 32
MAX_MESSAGES_PER_SECOND = 120
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


class GameServer:
    def __init__(self, host=config.SERVER_HOST, port=config.SERVER_PORT,
                 players=2, stocks=2, countdown=3.0, public_url: str | None = None):
        if not 2 <= players <= 4 or stocks < 1 or countdown < 0:
            raise ValueError("expected 2–4 players, positive stocks, nonnegative countdown")
        self.host, self.port = host, port
        self.capacity, self.stocks, self.countdown = players, stocks, countdown
        self.room = "".join(random.choices(string.ascii_uppercase, k=4))
        self.public_url = public_url
        self.sessions: dict[int, Session] = {}
        self.world: GameWorld | None = None
        self.tick_overruns = 0
        self._server = None
        self._ticker = None
        self._closing = False
        self._starts_at = 0.0
        self._link = public_url

    @property
    def address(self):
        return self._server.sockets[0].getsockname()[:2]

    @property
    def link(self) -> str:
        """The shareable link: --public-url, or the address the first browser used."""
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

    # ---- messages to everyone --------------------------------------------

    def _broadcast(self, message):
        for session in list(self.sessions.values()):
            session.send(message)

    def _phase(self) -> str:
        return "lobby" if self.world is None else self.world.phase

    def _lobby(self):
        players = [protocol.LobbyPlayer(s.player_id, s.name, s.character, s.ready, not s.closed, s.rematch)
                   for s in sorted(self.sessions.values(), key=lambda s: s.player_id)]
        self._broadcast(protocol.lobby(self.room, self.link, min(self.sessions, default=None),
                                       self.world.stage.name if self.world else "Memorial Glade",
                                       self._phase(), self.capacity, players))

    def _snapshot(self):
        if self.world is not None:
            self._broadcast(self.world.snapshot())

    def _publish_events(self):
        if self.world and self.world.events:
            for e in self.world.events:
                self._broadcast(protocol.event(e, self.world.tick_number, self.world.time))
            self.world.events = []

    def _start_if_ready(self):
        if (self.world is not None or len(self.sessions) != self.capacity
                or not all(s.ready for s in self.sessions.values())):
            return
        now = asyncio.get_running_loop().time()
        self.world = GameWorld(sorted(self.sessions), stocks=self.stocks, match_id=uuid4().hex)
        for fighter in self.world.fighters:
            fighter.character = self.sessions[fighter.player_id].character
        self.world.phase = "countdown"
        self._starts_at = now + self.countdown
        for session in self.sessions.values():
            session.reset_inputs(now)
        players = [{"id": s.player_id, "name": s.name, "character": s.character}
                   for s in sorted(self.sessions.values(), key=lambda s: s.player_id)]
        self._broadcast(protocol.match_start(self.world.stage, players, self.countdown))
        self._lobby()
        self._snapshot()

    def _reset_lobby(self):
        self.world = None
        for session in self.sessions.values():
            session.ready = session.rematch = False
            session.latest_snapshot = None
        self._lobby()

    # ---- one connection ----------------------------------------------------

    async def _handle(self, ws: ServerConnection):
        session = None
        write_task = None
        try:
            hello = validate_client(decode(await asyncio.wait_for(ws.recv(), timeout=5.0)))
            if hello["type"] != "hello":
                raise ProtocolError("hello must be the first message")
            if self.world is not None:
                raise ProtocolError("match in progress; join after it ends")
            free = [i for i in range(self.capacity) if i not in self.sessions]
            if not free:
                raise ProtocolError("lobby is full")
            session = Session(free[0], hello["name"].strip(), hello["character"], ws)
            self.sessions[session.player_id] = session
            write_task = asyncio.create_task(session.write_loop())
            session.send(protocol.welcome(session.player_id, self.room, self.link))
            self._lobby()

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
                kind = message["type"]
                if kind == "leave":
                    break
                if kind == "landmarks":
                    if self.world and self.world.phase == "playing":
                        session.accept_frame(message["frame"], now)
                elif kind == "calibrate":
                    session.set_calibration(message["calibration"])
                elif kind == "ready" and self.world is None:
                    session.ready = message["ready"]
                    self._lobby()
                    self._start_if_ready()
                elif kind == "rematch" and self.world and self.world.phase == "finished":
                    session.rematch = True
                    self._lobby()
                    if all(s.rematch for s in self.sessions.values()):
                        self._reset_lobby()
                elif kind == "hello":
                    raise ProtocolError("already joined")
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
            if session and self.sessions.get(session.player_id) is session:
                del self.sessions[session.player_id]
                if not self._closing:
                    if self.world:
                        self.world.eliminate(session.player_id)
                        self._publish_events()
                        self._snapshot()
                    if not self.sessions:
                        self.world = None
                    elif (self.world and self.world.phase == "finished"
                          and all(s.rematch for s in self.sessions.values())):
                        self._reset_lobby()
                    self._lobby()

    # ---- the clock -----------------------------------------------------------

    async def _tick_loop(self):
        loop = asyncio.get_running_loop()
        dt = 1 / config.SIMULATION_HZ
        next_tick = next_snapshot = loop.time()
        while True:
            now = loop.time()
            steps = 0
            while now >= next_tick and steps < 5:
                if self.world:
                    if self.world.phase == "countdown" and now >= self._starts_at:
                        self.world.phase = "playing"
                        for s in self.sessions.values():
                            s.last_input = now
                        self._lobby()
                    if self.world.phase == "playing":
                        for s in list(self.sessions.values()):
                            if now - s.last_input > DISCONNECT_SECONDS:
                                s.close()  # camera stopped sending; the handler removes them
                        lives = {f.player_id: f.life_id for f in self.world.fighters}
                        self.world.step({s.player_id: s.consume(now) for s in self.sessions.values()})
                        for f in self.world.fighters:
                            if f.life_id != lives[f.player_id] and f.player_id in self.sessions:
                                self.sessions[f.player_id].actions.clear()  # no attacks queued across a KO
                        finished = self.world.phase == "finished"
                        self._publish_events()
                        if finished:
                            self._snapshot()
                            self._lobby()  # phase "finished": browsers show rematch
                next_tick += dt
                steps += 1
            if now >= next_tick:
                self.tick_overruns += 1
                next_tick = now + dt
            if now >= next_snapshot:
                if self.world and self.world.phase != "finished":
                    self._snapshot()
                next_snapshot = now + 1 / config.SNAPSHOT_HZ
            await asyncio.sleep(max(0.0, min(next_tick, next_snapshot) - loop.time()))


def _response(status: int, reason: str, body: bytes, content_type: str) -> Response:
    headers = Headers([("Content-Type", content_type), ("Content-Length", str(len(body))),
                       ("Cache-Control", "no-cache")])
    return Response(status, reason, headers, body)


async def serve(args):
    server = await GameServer(args.host, args.port, args.players, args.stocks,
                              public_url=args.public_url).start()
    host, port = server.address
    print(f"Smash CV server for {args.players} players, room {server.room}", flush=True)
    print(f"  On this computer:  http://127.0.0.1:{port}/", flush=True)
    if not args.public_url:
        print("  For friends on other computers, the link must be https (browsers only allow the",
              flush=True)
        print(f"  camera on https). For example: cloudflared tunnel --url http://localhost:{port}",
              flush=True)
        print("  then share the https link it prints.", flush=True)
    try:
        await asyncio.Event().wait()
    finally:
        await server.close()
