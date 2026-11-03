"""A headless player that speaks the browser protocol, for tests and solo testing.

Owner: Person 3.

    python main.py bot --replay recordings/jump/arissa_20261103.jsonl

It joins like a browser would, readies up, and sends landmark frames from a
recording (looping) through the same gesture recognizer real players use, so
one person can test a full online match.
"""

from __future__ import annotations

import asyncio
import json
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from websockets.asyncio.client import connect

from gestures.recording import read_recording
from network.protocol import VERSION
from shared.landmarks import LandmarkFrame


def ws_url(link: str) -> str:
    """http://host:port/?room=ABCD -> ws://host:port/ws (https -> wss)."""
    base = link.split("?", 1)[0].rstrip("/")
    if base.startswith("https://"):
        base = "wss://" + base[len("https://"):]
    elif base.startswith("http://"):
        base = "ws://" + base[len("http://"):]
    return base + "/ws"


class Bot:
    def __init__(self, link: str, name: str = "Bot", character: str = "oski", mode: str = "friends"):
        """A link with ?room=ABCD joins that room; without one the bot creates a room in `mode`."""
        self.url = ws_url(link)
        self.room = parse_qs(urlparse(link).query).get("room", [None])[0]
        self.mode = mode
        self.name, self.character = name, character
        self.player_id = None
        self.messages: list[dict] = []
        self.ws = None
        self._reader = None
        self._arrived = asyncio.Event()

    async def connect(self, hello: bool = True):
        self.ws = await connect(self.url, max_size=None)
        self._reader = asyncio.create_task(self._read())
        if hello:
            await self.send({"type": "hello", "version": VERSION, "name": self.name,
                             "character": self.character, "mode": self.mode, "room": self.room})
            welcome = await self.wait_for("welcome")
            self.player_id = welcome["player_id"]
            self.room, self.link = welcome["room"], welcome["link"]
        return self

    async def _read(self):
        try:
            async for raw in self.ws:
                self.messages.append(json.loads(raw))
                self._arrived.set()
        except Exception:  # connection closed; wait_for() reports what arrived
            pass
        finally:
            self._arrived.set()

    async def send(self, message: dict):
        await self.ws.send(json.dumps(message))

    async def ready(self, ready: bool = True):
        await self.send({"type": "ready", "ready": ready})

    async def calibrate(self, center_x, shoulder_y, nose_y, shoulder_width):
        await self.send({"type": "calibrate", "calibration": {
            "center_x": center_x, "shoulder_y": shoulder_y, "nose_y": nose_y, "shoulder_width": shoulder_width}})

    async def send_frame(self, frame: LandmarkFrame):
        await self.send({"type": "landmarks", "frame": json.loads(frame.to_json())})

    def mark(self) -> int:
        """A point in the message history; pass it as wait_for(since=...) to skip older messages."""
        return len(self.messages)

    def of_type(self, message_type: str, since: int = 0, **match) -> list[dict]:
        return [m for m in self.messages[since:] if m["type"] == message_type
                and all(m.get(k) == v for k, v in match.items())]

    async def wait_for(self, message_type: str, timeout: float = 5.0, where=lambda m: True,
                       since: int = 0, **match) -> dict:
        """The first message of this type, at or after `since`, whose fields match (e.g. kind="hit")."""
        async def find():
            while True:
                for m in self.of_type(message_type, since, **match):
                    if where(m):
                        return m
                if self._reader.done():
                    raise ConnectionError(f"closed before a {message_type!r} message arrived")
                self._arrived.clear()
                await self._arrived.wait()
        return await asyncio.wait_for(find(), timeout)

    async def close(self):
        if self.ws is not None:
            await self.ws.close()
        if self._reader is not None:
            await asyncio.gather(self._reader, return_exceptions=True)


async def replay(link: str, path: Path, name: str = "Replay", character: str = "oski"):
    """Join the room in `link` (?room=ABCD), ready up, and play a recording on loop."""
    _, frames = read_recording(path)
    if not frames:
        raise SystemExit(f"{path} has no frames")
    bot = await Bot(link, name, character).connect()
    await bot.ready()
    print(f"joined as player {bot.player_id + 1}; replaying {path.name} on loop", flush=True)
    loop = asyncio.get_running_loop()
    start, offset = loop.time(), 0.0
    duration = frames[-1].timestamp - frames[0].timestamp + 0.1
    try:
        while not bot._reader.done():
            for frame in frames:
                due = start + offset + frame.timestamp - frames[0].timestamp
                await asyncio.sleep(max(0.0, due - loop.time()))
                await bot.send_frame(LandmarkFrame(offset + frame.timestamp, frame.pose, frame.hands))
            offset += duration
    finally:
        await bot.close()
