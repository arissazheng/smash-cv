"""Nonblocking client connection. Usable by Pygame or headless test clients."""

from __future__ import annotations

import asyncio
from collections import deque

from client.input_buffer import InputBuffer
from client.interpolation import SnapshotBuffer
from network.protocol import MAX_MESSAGE_BYTES, VERSION, ProtocolError, encode, read_message
from shared import config
from shared.game_state import MatchView


class NetworkClient:
    def __init__(self, host=config.SERVER_HOST, port=config.SERVER_PORT, name="Player"):
        self.host, self.port, self.name = host, port, name
        self.player_id = None
        self.lobby = {"capacity": 2, "players": []}
        self.latest = None
        self.match_id = None
        self.countdown = 0.0
        self.acks = {}
        self.tick_overruns = 0
        self.last_snapshot_at = None
        self.events = deque(maxlen=128)
        self.buffer = SnapshotBuffer()
        self.inputs = InputBuffer()
        self.error = None
        self.closed = False
        self._writer = None
        self._tasks = []
        self._commands = asyncio.Queue(maxsize=16)
        self._last_event = -1

    async def connect(self):
        reader, self._writer = await asyncio.wait_for(
            asyncio.open_connection(self.host, self.port, limit=MAX_MESSAGE_BYTES), timeout=5.0)
        self._writer.write(encode({"type": "hello", "version": VERSION, "name": self.name}))
        await asyncio.wait_for(self._writer.drain(), timeout=1.0)
        welcome = await asyncio.wait_for(read_message(reader), timeout=5.0)
        if welcome["type"] == "error":
            raise ConnectionError(welcome["message"])
        if welcome["type"] != "welcome" or welcome["version"] != VERSION:
            raise ProtocolError("incompatible server")
        self.player_id = welcome["player_id"]
        self._tasks = [asyncio.create_task(self._read_loop(reader)),
                       asyncio.create_task(self._send_loop())]
        return self

    def ready(self, value=True):
        self._command({"type": "ready", "ready": value})

    def rematch(self):
        self._command({"type": "rematch"})

    def _command(self, message):
        try:
            self._commands.put_nowait(message)
        except asyncio.QueueFull:
            self.error = "too many pending commands"
            self.closed = True

    def _activate_match(self, match_id):
        if match_id != self.match_id:
            self.match_id = match_id
            self.inputs.reset()
            self.buffer.frames.clear()
            self.events.clear()
            self._last_event = -1

    async def _read_loop(self, reader):
        try:
            while not self.closed:
                message = await read_message(reader)
                kind = message["type"]
                if kind == "error":
                    raise ConnectionError(message["message"])
                if kind == "lobby":
                    self.lobby = message
                elif kind == "match_start":
                    self._activate_match(message["match_id"])
                elif kind == "reset":
                    self.match_id = self.latest = None
                    self.inputs.reset()
                    self.buffer.frames.clear()
                    self.events.clear()
                elif kind == "snapshot":
                    view = MatchView.from_dict(message["world"])
                    self._activate_match(view.match_id)
                    self.latest = view
                    self.countdown = message["countdown"]
                    self.acks = message["acks"]
                    self.tick_overruns = message["tick_overruns"]
                    self.last_snapshot_at = asyncio.get_running_loop().time()
                    self.buffer.push(view, self.last_snapshot_at)
                elif kind == "events" and message["match_id"] == self.match_id:
                    for event in message["events"]:
                        if event["id"] > self._last_event:
                            self.events.append(event)
                            self._last_event = event["id"]
        except (EOFError, ConnectionError, OSError, ValueError, KeyError, TypeError) as exc:
            self.error = str(exc)
            self.closed = True

    async def _send_loop(self):
        try:
            while not self.closed:
                while not self._commands.empty():
                    self._writer.write(encode(self._commands.get_nowait()))
                if self.latest and self.latest.phase == "playing":
                    self._writer.write(encode(self.inputs.message(self.match_id)))
                await asyncio.wait_for(self._writer.drain(), timeout=1.0)
                await asyncio.sleep(1 / config.INPUT_HZ)
        except (ConnectionError, OSError, asyncio.TimeoutError, ValueError) as exc:
            self.error = str(exc) or "send timed out"
            self.closed = True

    async def close(self):
        self.closed = True
        for task in self._tasks:
            task.cancel()
        await asyncio.gather(*self._tasks, return_exceptions=True)
        if self._writer:
            self._writer.close()
            try:
                await asyncio.wait_for(self._writer.wait_closed(), timeout=1.0)
            except (ConnectionError, OSError, asyncio.TimeoutError):
                pass
