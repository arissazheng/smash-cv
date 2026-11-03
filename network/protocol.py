"""Versioned newline-framed JSON. Never trust client identity or world state."""

from __future__ import annotations

import asyncio
import json
import math

VERSION = 1
MAX_MESSAGE_BYTES = 16384
MAX_ACTIONS = 8
ATTACKS = ("jab", "smash", "special")


class ProtocolError(ValueError):
    pass


def encode(message: dict) -> bytes:
    payload = json.dumps(message, separators=(",", ":"), allow_nan=False).encode() + b"\n"
    if len(payload) > MAX_MESSAGE_BYTES:
        raise ProtocolError("message too large")
    return payload


def _invalid_number(value):
    raise ProtocolError("non-finite JSON number")


async def read_message(reader: asyncio.StreamReader) -> dict:
    try:
        line = await reader.readline()
    except ValueError as exc:
        raise ProtocolError("message too large") from exc
    if not line:
        raise EOFError("connection closed")
    if len(line) > MAX_MESSAGE_BYTES or not line.endswith(b"\n"):
        raise ProtocolError("oversized or incomplete message")
    try:
        message = json.loads(line, parse_constant=_invalid_number)
    except (ValueError, UnicodeError, RecursionError) as exc:
        raise ProtocolError("invalid JSON") from exc
    if not isinstance(message, dict) or not isinstance(message.get("type"), str):
        raise ProtocolError("expected an object with a message type")
    return message


def _keys(data, required):
    if not isinstance(data, dict) or set(data) != set(required):
        raise ProtocolError("invalid message fields")


def _sequence(value):
    if type(value) is not int or not 0 <= value < 2**53:
        raise ProtocolError("invalid sequence number")


def validate_client(message: dict) -> dict:
    kind = message["type"]
    if kind == "hello":
        _keys(message, ("type", "version", "name"))
        if type(message["version"]) is not int or message["version"] != VERSION:
            raise ProtocolError(f"protocol version {VERSION} required")
        name = message["name"]
        if not isinstance(name, str) or not name.strip() or len(name) > 24 or not name.isprintable():
            raise ProtocolError("name must contain 1–24 printable characters")
    elif kind == "ready":
        _keys(message, ("type", "ready"))
        if type(message["ready"]) is not bool:
            raise ProtocolError("ready must be a boolean")
    elif kind in ("rematch", "leave"):
        _keys(message, ("type",))
    elif kind == "input":
        _keys(message, ("type", "match_id", "seq", "held", "actions"))
        if not isinstance(message["match_id"], str) or len(message["match_id"]) > 64:
            raise ProtocolError("invalid match ID")
        _sequence(message["seq"])
        held = message["held"]
        _keys(held, ("move_x", "crouch"))
        movement = held["move_x"]
        if (type(movement) not in (float, int) or not -1 <= movement <= 1
                or not math.isfinite(movement) or type(held["crouch"]) is not bool):
            raise ProtocolError("invalid held controls")
        actions = message["actions"]
        if not isinstance(actions, list) or len(actions) > MAX_ACTIONS:
            raise ProtocolError("too many actions")
        previous = -1
        for action in actions:
            _keys(action, ("id", "jump", "attack"))
            _sequence(action["id"])
            if action["id"] <= previous or type(action["jump"]) is not bool:
                raise ProtocolError("actions must have increasing IDs and boolean jump values")
            if action["attack"] is not None and action["attack"] not in ATTACKS:
                raise ProtocolError("unsupported prototype attack")
            previous = action["id"]
    else:
        raise ProtocolError("unknown message type")
    return message
