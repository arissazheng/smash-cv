import asyncio

import pytest

from network.protocol import MAX_MESSAGE_BYTES, ProtocolError, encode, read_message, validate_client


def packet(**changes):
    return {"type": "input", "match_id": "test", "seq": 0,
            "held": {"move_x": 0.5, "crouch": False},
            "actions": [{"id": 0, "jump": True, "attack": "jab"}], **changes}


@pytest.mark.parametrize("changes", [
    {"player_id": 1}, {"seq": True}, {"seq": -1},
    {"held": {"move_x": float("nan"), "crouch": False}},
    {"held": {"move_x": float("inf"), "crouch": False}},
    {"held": {"move_x": 10**1000, "crouch": False}},
    {"held": {"move_x": 2, "crouch": False}},
    {"held": {"move_x": True, "crouch": False}},
    {"held": {"move_x": 0, "crouch": "false"}},
    {"actions": [{"id": 0, "jump": False, "attack": "grab"}]},
    {"actions": [{"id": 0, "jump": "false", "attack": None}]},
    {"actions": [{"id": 0, "jump": True, "attack": None}] * 2},
])
def test_reject_invalid_or_spoofed_inputs(changes):
    with pytest.raises(ProtocolError):
        validate_client(packet(**changes))


def test_split_and_combined_stream_messages():
    async def scenario():
        reader = asyncio.StreamReader(limit=MAX_MESSAGE_BYTES)
        data = encode(packet())
        reader.feed_data(data[:12])
        pending = asyncio.create_task(read_message(reader))
        await asyncio.sleep(0)
        assert not pending.done()
        reader.feed_data(data[12:] + encode({"type": "ready", "ready": True}))
        assert validate_client(await pending) == packet()
        assert validate_client(await read_message(reader))["ready"]
    asyncio.run(scenario())


@pytest.mark.parametrize("data", [b'{"type":"input","seq":NaN}\n', b'not json\n',
                                  b'{"type":"ready"}', b'x' * (MAX_MESSAGE_BYTES + 1)])
def test_bad_framing_and_json(data):
    async def scenario():
        reader = asyncio.StreamReader(limit=MAX_MESSAGE_BYTES)
        reader.feed_data(data)
        reader.feed_eof()
        with pytest.raises(ProtocolError):
            await read_message(reader)
    asyncio.run(scenario())
