"""Validation of browser -> server messages (network/protocol.py)."""

import json

import pytest

from network.protocol import MAX_MESSAGE_BYTES, VERSION, ProtocolError, decode, encode, validate_client
from tests.helpers import hand, person


def landmarks(**frame_changes):
    frame = json.loads(person(t=1.5, hands=[hand("Open_Palm")]).to_json())
    return {"type": "landmarks", "frame": {**frame, **frame_changes}}


def hello(**changes):
    return {"type": "hello", "version": VERSION, "name": "Arissa", "character": "efros", **changes}


def calibrate(**changes):
    return {"type": "calibrate", "calibration": {"center_x": 0.5, "shoulder_y": 0.6, "nose_y": 0.4,
                                                 "shoulder_width": 0.2, **changes}}


def test_valid_messages_pass():
    for message in (hello(), {"type": "ready", "ready": True}, {"type": "rematch"}, {"type": "leave"},
                    {"type": "stage", "stage": "gateway"}, {"type": "character", "character": "oski"},
                    calibrate(), landmarks(), landmarks(pose=None, hands=[])):
        assert validate_client(decode(encode(message))) == message


@pytest.mark.parametrize("message", [
    hello(version=1), hello(name=""), hello(name="x" * 25), hello(name="bad\nname"),
    hello(character="mario"), hello(player_id=3),
    {"type": "ready", "ready": "yes"}, {"type": "rematch", "now": True},
    {"type": "stage", "stage": "moon"}, {"type": "stage"}, {"type": "character", "character": "mario"},
    calibrate(shoulder_width=0), calibrate(center_x=2), calibrate(nose_y="0.4"),
    landmarks(pose=[[0.5, 0.5, 0, 1]] * 5),                 # wrong number of body points
    landmarks(pose=[[0.5, 0.5, 0]] * 33),                    # points missing visibility
    landmarks(pose=[[1e9, 0.5, 0, 1]] * 33),                 # impossible coordinates
    landmarks(hands=[json.loads(person().to_json())["hands"]] * 3),
    landmarks(hands=[{"side": "Middle", "lm": [[0, 0, 0]] * 21, "g": "None", "gs": 0}]),
    landmarks(hands=[{"side": "Left", "lm": [[0, 0, 0]] * 20, "g": "None", "gs": 0}]),
    landmarks(t=-1), landmarks(extra=1),
    {"type": "input", "held": {"move_x": 1}},                # browsers never send inputs
    {"type": "snapshot"},
])
def test_invalid_or_spoofed_messages_are_rejected(message):
    with pytest.raises(ProtocolError):
        validate_client(message)


@pytest.mark.parametrize("data", ['{"type":"ready","ready":NaN}', "not json", "[1,2]", '{"no":"type"}',
                                  "x" * (MAX_MESSAGE_BYTES + 1), b'{"type":"leave"}'])
def test_bad_frames_are_rejected_before_validation(data):
    with pytest.raises(ProtocolError):
        decode(data)


def test_a_full_landmark_frame_fits_the_size_limit():
    frame = json.loads(person(t=123.456, hands=[hand("Open_Palm"), hand("Thumb_Up")]).to_json())
    assert len(encode({"type": "landmarks", "frame": frame}).encode()) < MAX_MESSAGE_BYTES
