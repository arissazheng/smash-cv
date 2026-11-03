"""Browser -> server messages: decoding and strict validation.

Owner: Person 3.

Every browser message is one JSON text frame over the WebSocket. Never trust a
client's identity or the game state it claims; the server assigns player IDs
and decides every input by running the gesture recognizer on the landmarks
the browser sends. Server -> browser messages are built by shared/protocol.py.

    hello       {"version", "name", "character", "mode", "room"}   first message;
                mode "cpu" or "friends"; room is a code from a shared link, or null to create one
    character   {"character"}                       change fighter, in the lobby
    stage       {"stage"}                           pick the map, in the lobby (host only)
    ready       {"ready": bool}                     in the lobby
    calibrate   {"calibration": {"center_x", "shoulder_y", "nose_y", "shoulder_width"}}
    landmarks   {"frame": {"t", "pose", "hands"}}  every camera frame (shared/landmarks.py format)
    rematch     {}                                  after game over
    leave       {}
"""

from __future__ import annotations

import json
import math

VERSION = 4
MAX_MESSAGE_BYTES = 16384
CHARACTERS = ("efros", "ng", "liu", "lyons", "oski")  # folders in assets/characters/
STAGES = ("memorial_glade", "gateway", "sather_gate", "soda_hall")  # STAGES in game/stage.py
HAND_SIDES = ("Left", "Right", "Unknown")
POSE_POINTS, HAND_POINTS, MAX_HANDS = 33, 21, 2
MODES = ("cpu", "friends")


class ProtocolError(ValueError):
    pass


def encode(message: dict) -> str:
    text = json.dumps(message, separators=(",", ":"), allow_nan=False)
    if len(text.encode()) > MAX_MESSAGE_BYTES * 4:  # snapshots for 4 players stay far below this
        raise ProtocolError("message too large")
    return text


def _invalid_number(value):
    raise ProtocolError("non-finite JSON number")


def decode(data: str | bytes) -> dict:
    if isinstance(data, bytes):
        raise ProtocolError("expected a text message")
    if len(data.encode()) > MAX_MESSAGE_BYTES:
        raise ProtocolError("message too large")
    try:
        message = json.loads(data, parse_constant=_invalid_number)
    except (ValueError, RecursionError) as exc:
        raise ProtocolError("invalid JSON") from exc
    if not isinstance(message, dict) or not isinstance(message.get("type"), str):
        raise ProtocolError("expected an object with a message type")
    return message


def _keys(data, required):
    if not isinstance(data, dict) or set(data) != set(required):
        raise ProtocolError("invalid message fields")


def _number(value, low=-math.inf, high=math.inf) -> float:
    if type(value) not in (int, float) or not math.isfinite(value) or not low <= value <= high:
        raise ProtocolError("invalid number")
    return float(value)


def _points(points, count, width):
    if not isinstance(points, list) or len(points) != count:
        raise ProtocolError("wrong number of landmarks")
    for point in points:
        if not isinstance(point, list) or len(point) != width:
            raise ProtocolError("invalid landmark")
        for v in point:
            _number(v, -10, 10)  # normalized coordinates; MediaPipe can stray a little outside 0..1


def _frame(frame):
    _keys(frame, ("t", "pose", "hands"))
    _number(frame["t"], 0)
    if frame["pose"] is not None:
        _points(frame["pose"], POSE_POINTS, 4)
    hands = frame["hands"]
    if not isinstance(hands, list) or len(hands) > MAX_HANDS:
        raise ProtocolError("too many hands")
    for hand in hands:
        _keys(hand, ("side", "lm", "g", "gs"))
        if hand["side"] not in HAND_SIDES:
            raise ProtocolError("invalid handedness")
        _points(hand["lm"], HAND_POINTS, 3)
        if not isinstance(hand["g"], str) or len(hand["g"]) > 32:
            raise ProtocolError("invalid gesture name")
        _number(hand["gs"], 0, 1)


def validate_client(message: dict) -> dict:
    kind = message["type"]
    if kind == "hello":
        _keys(message, ("type", "version", "name", "character", "mode", "room"))
        if type(message["version"]) is not int or message["version"] != VERSION:
            raise ProtocolError(f"protocol version {VERSION} required; refresh the page")
        name = message["name"]
        if not isinstance(name, str) or not name.strip() or len(name) > 24 or not name.isprintable():
            raise ProtocolError("name must contain 1–24 printable characters")
        if message["character"] not in CHARACTERS:
            raise ProtocolError(f"character must be one of {', '.join(CHARACTERS)}")
        if message["mode"] not in MODES:
            raise ProtocolError("mode must be cpu or friends")
        room = message["room"]
        if room is not None and (not isinstance(room, str) or len(room) != 4 or not room.isalpha()
                                 or not room.isupper() or not room.isascii()):
            raise ProtocolError("room must be a 4-letter code")
        if room is not None and message["mode"] != "friends":
            raise ProtocolError("only friends rooms can be joined by code")
    elif kind == "character":
        _keys(message, ("type", "character"))
        if message["character"] not in CHARACTERS:
            raise ProtocolError(f"character must be one of {', '.join(CHARACTERS)}")
    elif kind == "stage":
        _keys(message, ("type", "stage"))
        if message["stage"] not in STAGES:
            raise ProtocolError(f"stage must be one of {', '.join(STAGES)}")
    elif kind == "ready":
        _keys(message, ("type", "ready"))
        if type(message["ready"]) is not bool:
            raise ProtocolError("ready must be a boolean")
    elif kind in ("rematch", "leave"):
        _keys(message, ("type",))
    elif kind == "calibrate":
        _keys(message, ("type", "calibration"))
        c = message["calibration"]
        _keys(c, ("center_x", "shoulder_y", "nose_y", "shoulder_width"))
        for key in ("center_x", "shoulder_y", "nose_y"):
            _number(c[key], 0, 1)
        _number(c["shoulder_width"], 0.02, 1)
    elif kind == "landmarks":
        _keys(message, ("type", "frame"))
        _frame(message["frame"])
    else:
        raise ProtocolError("unknown message type")
    return message
