"""Headless authoritative server for one 2–4 player LAN match at a time."""

from __future__ import annotations

import asyncio
from collections import deque
from dataclasses import dataclass, field
from uuid import uuid4

from game.engine import GameWorld
from network.protocol import MAX_MESSAGE_BYTES, VERSION, ProtocolError, encode, read_message, validate_client
from shared import config
from shared.controller_state import ControllerState

STALE_INPUT_SECONDS = 0.25
DISCONNECT_SECONDS = 3.0
MAX_PENDING_ACTIONS = 32


@dataclass
class Session:
    player_id: int
    name: str
    writer: asyncio.StreamWriter
    ready: bool = False
    rematch: bool = False
    held: dict = field(default_factory=lambda: {"move_x": 0.0, "crouch": False})
    actions: deque = field(default_factory=deque)
    last_input: float = 0.0
    last_sample: int = -1
    last_action: int = -1
    processed_action: int = -1
    controls: deque = field(default_factory=deque)
    latest_snapshot: object = None
    wake: asyncio.Event = field(default_factory=asyncio.Event)

    def send(self, message):
        if self.writer.is_closing():
            return
        if message["type"] == "snapshot":
            self.latest_snapshot = message
        elif len(self.controls) < 64:
            self.controls.append(message)
        else:
            self.writer.close()
        self.wake.set()

    async def write_loop(self):
        try:
            while not self.writer.is_closing():
                await self.wake.wait()
                self.wake.clear()
                while self.controls or self.latest_snapshot is not None:
                    if self.controls:
                        packet = self.controls.popleft()
                    else:
                        packet, self.latest_snapshot = self.latest_snapshot, None
                    self.writer.write(encode(packet))
                    await asyncio.wait_for(self.writer.drain(), timeout=1.0)
        except (ConnectionError, OSError, asyncio.TimeoutError):
            self.writer.close()

    def reset_inputs(self, now):
        self.held = {"move_x": 0.0, "crouch": False}
        self.actions.clear()
        self.last_sample = self.last_action = self.processed_action = -1
        self.last_input = now

    def accept_input(self, message, now):
        if message["seq"] <= self.last_sample:
            return
        new = [a for a in message["actions"] if a["id"] > self.last_action]
        if len(self.actions) + len(new) > MAX_PENDING_ACTIONS:
            raise ProtocolError("action queue overflow")
        self.held = message["held"]
        self.last_sample = message["seq"]
        self.last_input = now
        for action in new:
            self.actions.append((now, action))
            self.last_action = action["id"]

    def consume(self, now):
        state = ControllerState(player_id=self.player_id)
        if now - self.last_input <= STALE_INPUT_SECONDS:
            state.move_x = self.held["move_x"]
            state.crouch = self.held["crouch"]
        while self.actions and now - self.actions[0][0] > STALE_INPUT_SECONDS:
            self.processed_action = self.actions.popleft()[1]["id"]
        if self.actions:
            _, action = self.actions.popleft()
            self.processed_action = action["id"]
            state.jump, state.attack = action["jump"], action["attack"]
        return state


class GameServer:
    def __init__(self, host=config.SERVER_HOST, port=config.SERVER_PORT,
                 players=2, stocks=2, countdown=1.5):
        if not 2 <= players <= 4 or stocks < 1 or countdown < 0:
            raise ValueError("expected 2–4 players, positive stocks, nonnegative countdown")
        self.host, self.port = host, port
        self.capacity, self.stocks, self.countdown = players, stocks, countdown
        self.sessions: dict[int, Session] = {}
        self.world = None
        self.tick_overruns = 0
        self._listener = None
        self._ticker = None
        self._handlers = set()
        self._closing = False
        self._starts_at = 0.0
        self._end_sent = False

    @property
    def address(self):
        return self._listener.sockets[0].getsockname()[:2]

    async def start(self):
        self._listener = await asyncio.start_server(self._handle, self.host, self.port,
                                                    limit=MAX_MESSAGE_BYTES)
        self._ticker = asyncio.create_task(self._tick_loop())
        return self

    async def close(self):
        self._closing = True
        if self._listener:
            self._listener.close()
            await self._listener.wait_closed()
        if self._ticker:
            self._ticker.cancel()
            await asyncio.gather(self._ticker, return_exceptions=True)
        for session in list(self.sessions.values()):
            session.writer.close()
        tasks = list(self._handlers)
        for task in tasks:
            task.cancel()
        await asyncio.gather(*tasks, return_exceptions=True)

    def _broadcast(self, message):
        for session in list(self.sessions.values()):
            session.send(message)

    def _lobby(self):
        self._broadcast({"type": "lobby", "capacity": self.capacity,
                         "players": [{"player_id": s.player_id, "name": s.name,
                                      "ready": s.ready, "rematch": s.rematch}
                                     for s in self.sessions.values()]})

    def _snapshot(self):
        if self.world is None:
            return
        self._broadcast({"type": "snapshot", "world": self.world.snapshot().to_dict(),
                         "countdown": max(0.0, self._starts_at - asyncio.get_running_loop().time())
                         if self.world.phase == "countdown" else 0.0,
                         "acks": {str(s.player_id): {"sample": s.last_sample,
                                                    "action": s.processed_action}
                                  for s in self.sessions.values()},
                         "tick_overruns": self.tick_overruns})

    def _start_if_ready(self):
        if (self.world is not None or len(self.sessions) != self.capacity
                or not all(s.ready for s in self.sessions.values())):
            return
        now = asyncio.get_running_loop().time()
        self.world = GameWorld(sorted(self.sessions), stocks=self.stocks, match_id=uuid4().hex)
        self.world.phase = "countdown"
        self._starts_at = now + self.countdown
        self._end_sent = False
        for session in self.sessions.values():
            session.reset_inputs(now)
        self._broadcast({"type": "match_start", "match_id": self.world.match_id})
        self._snapshot()

    def _reset_lobby(self):
        self.world = None
        for session in self.sessions.values():
            session.ready = session.rematch = False
            session.latest_snapshot = None
        self._broadcast({"type": "reset"})
        self._lobby()

    def _publish_events(self):
        if self.world and self.world.events:
            self._broadcast({"type": "events", "match_id": self.world.match_id,
                             "events": self.world.events.copy()})
            self.world.events = []

    async def _handle(self, reader, writer):
        task = asyncio.current_task()
        self._handlers.add(task)
        session = None
        write_task = None
        try:
            hello = validate_client(await asyncio.wait_for(read_message(reader), timeout=5.0))
            if hello["type"] != "hello":
                raise ProtocolError("hello must be the first message")
            if self.world is not None:
                raise ProtocolError("match in progress; join the next lobby")
            free = [i for i in range(self.capacity) if i not in self.sessions]
            if not free:
                raise ProtocolError("lobby is full")
            session = Session(free[0], hello["name"].strip(), writer)
            self.sessions[session.player_id] = session
            write_task = asyncio.create_task(session.write_loop())
            session.send({"type": "welcome", "version": VERSION, "player_id": session.player_id,
                          "simulation_hz": config.SIMULATION_HZ, "input_hz": config.INPUT_HZ})
            self._lobby()
            rate_start, messages = asyncio.get_running_loop().time(), 0
            while not writer.is_closing():
                message = validate_client(await read_message(reader))
                now = asyncio.get_running_loop().time()
                if now - rate_start >= 1:
                    rate_start, messages = now, 0
                messages += 1
                if messages > 120:
                    raise ProtocolError("message rate exceeded")
                kind = message["type"]
                if kind == "leave":
                    break
                if kind == "ready" and self.world is None:
                    session.ready = message["ready"]
                    self._lobby()
                    self._start_if_ready()
                elif kind == "input":
                    if (self.world and self.world.phase == "playing"
                            and message["match_id"] == self.world.match_id):
                        session.accept_input(message, now)
                elif kind == "rematch" and self.world and self.world.phase == "finished":
                    session.rematch = True
                    self._lobby()
                    if all(s.rematch for s in self.sessions.values()):
                        self._reset_lobby()
                elif kind == "hello":
                    raise ProtocolError("already connected")
        except ProtocolError as exc:
            try:
                writer.write(encode({"type": "error", "message": str(exc)}))
                await asyncio.wait_for(writer.drain(), timeout=0.5)
            except (ConnectionError, OSError, asyncio.TimeoutError):
                pass
        except (EOFError, ConnectionError, OSError, asyncio.TimeoutError):
            pass
        finally:
            writer.close()
            if write_task:
                write_task.cancel()
                await asyncio.gather(write_task, return_exceptions=True)
            try:
                await writer.wait_closed()
            except (ConnectionError, OSError):
                pass
            if session and self.sessions.get(session.player_id) is session:
                del self.sessions[session.player_id]
                if not self._closing:
                    if self.world:
                        self.world.eliminate(session.player_id)
                        self._publish_events()
                        self._snapshot()
                    self._lobby()
                    if not self.sessions:
                        self.world = None
                    elif (self.world and self.world.phase == "finished"
                          and all(s.rematch for s in self.sessions.values())):
                        self._reset_lobby()
            self._handlers.discard(task)

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
                    if self.world.phase == "playing":
                        for s in list(self.sessions.values()):
                            if now - s.last_input > DISCONNECT_SECONDS:
                                s.writer.close()
                        lives = {f.player_id: f.life_id for f in self.world.fighters}
                        self.world.step({s.player_id: s.consume(now) for s in self.sessions.values()})
                        for f in self.world.fighters:
                            if f.life_id != lives[f.player_id] and f.player_id in self.sessions:
                                s = self.sessions[f.player_id]
                                s.actions.clear()
                                s.processed_action = s.last_action
                        self._publish_events()
                    if self.world.phase == "finished" and not self._end_sent:
                        self._broadcast({"type": "match_end", "match_id": self.world.match_id,
                                         "winner": self.world.winner, "result": self.world.result})
                        self._end_sent = True
                        self._snapshot()
                next_tick += dt
                steps += 1
            if now >= next_tick:
                self.tick_overruns += 1
                next_tick = now + dt
            if now >= next_snapshot:
                self._snapshot()
                next_snapshot = now + 1 / config.SNAPSHOT_HZ
            await asyncio.sleep(max(0.0, min(next_tick, next_snapshot) - loop.time()))


async def serve(args):
    server = await GameServer(args.host, args.port, args.players, args.stocks).start()
    host, port = server.address
    print(f"Smash CV server on {host}:{port} — waiting for {args.players} ready players", flush=True)
    try:
        await asyncio.Event().wait()
    finally:
        await server.close()
