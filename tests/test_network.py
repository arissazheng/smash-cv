import asyncio

import pytest

from network.client import NetworkClient
from network.protocol import ProtocolError, encode, read_message
from network.server import GameServer, Session, STALE_INPUT_SECONDS
from shared.controller_state import ControllerState


async def until(predicate, timeout=3.0):
    deadline = asyncio.get_running_loop().time() + timeout
    while not predicate():
        if asyncio.get_running_loop().time() >= deadline:
            raise AssertionError("timed out waiting for network state")
        await asyncio.sleep(0.01)


def test_two_clients_move_finish_rematch_and_forfeit():
    async def scenario():
        server = await GameServer(port=0, stocks=1, countdown=0).start()
        a = NetworkClient(*server.address, name="Alice")
        b = NetworkClient(*server.address, name="Bob")
        try:
            await a.connect()
            await b.connect()
            assert (a.player_id, b.player_id) == (0, 1)
            a.ready()
            b.ready()
            await until(lambda: a.latest and b.latest and a.latest.phase == b.latest.phase == "playing")
            first_match = a.match_id
            x = server.world.fighters[0].x
            a.inputs.capture(ControllerState(move_x=1, jump=True))
            a.inputs.capture(ControllerState(move_x=1, attack="special"))
            await until(lambda: server.sessions[0].processed_action == 1)
            await until(lambda: server.world.fighters[0].x > x + 40)
            assert server.sessions[0].last_action == 1
            assert a.error is None and b.error is None
            server.world.fighters[0].x = -1000
            await until(lambda: a.latest.phase == b.latest.phase == "finished")
            assert a.latest.result == b.latest.result == "win"
            assert a.latest.winner == b.latest.winner == 1
            assert a.latest.tick == b.latest.tick
            a.rematch()
            b.rematch()
            await until(lambda: a.latest is None and b.latest is None)
            a.ready()
            b.ready()
            await until(lambda: a.latest and b.latest and a.latest.phase == b.latest.phase == "playing")
            assert a.match_id == b.match_id != first_match
            assert server.world.fighters[0].damage == 0
            # A delayed packet from the prior match cannot poison the new
            # session's sequence numbers or trigger an old action.
            a._writer.write(encode(input_packet(999999, [{"id": 999999, "jump": True,
                                                        "attack": "smash"}], first_match)))
            await a._writer.drain()
            await until(lambda: server.sessions[0].last_sample >= 0)
            assert server.sessions[0].last_sample < 999999
            assert server.sessions[0].last_action == -1
            await a.close()
            await until(lambda: b.latest.phase == "finished")
            assert b.latest.winner == 1
        finally:
            await a.close()
            await b.close()
            await server.close()
    asyncio.run(scenario())


def test_four_clients_and_bad_connection_do_not_interrupt_match():
    async def scenario():
        server = await GameServer(port=0, players=4, countdown=0).start()
        clients = [NetworkClient(*server.address, name=f"Player{i}") for i in range(4)]
        try:
            for client in clients:
                await client.connect()
                client.ready()
            await until(lambda: all(c.latest and c.latest.phase == "playing" for c in clients))
            assert len(server.world.fighters) == 4
            reader, writer = await asyncio.open_connection(*server.address)
            writer.write(encode({"type": "hello", "version": 999, "name": "bad"}))
            await writer.drain()
            assert (await read_message(reader))["type"] == "error"
            writer.close()
            await writer.wait_closed()
            before = server.world.tick_number
            await until(lambda: server.world.tick_number >= before + 5)
            assert all(c.error is None for c in clients)
        finally:
            for client in clients:
                await client.close()
            await server.close()
    asyncio.run(scenario())


def test_blocked_client_writer_does_not_stop_other_client_or_simulation():
    async def scenario():
        server = await GameServer(port=0, countdown=0).start()
        a = NetworkClient(*server.address, name="Slow")
        b = NetworkClient(*server.address, name="Fast")
        blocked = asyncio.Event()
        async def stall():
            await blocked.wait()
        try:
            await a.connect()
            await b.connect()
            a.ready()
            b.ready()
            await until(lambda: b.latest and b.latest.phase == "playing")
            server.sessions[a.player_id].writer.drain = stall
            before = server.world.tick_number
            await until(lambda: b.latest.tick >= before + 12)
            assert b.error is None and server.world.tick_number >= before + 12
        finally:
            blocked.set()
            await a.close()
            await b.close()
            await server.close()
    asyncio.run(scenario())


def input_packet(seq, actions=None, match_id="match"):
    return {"type": "input", "match_id": match_id, "seq": seq,
            "held": {"move_x": 1.0, "crouch": False}, "actions": actions or []}


def test_duplicate_actions_stale_controls_and_bounded_queue():
    async def scenario():
        session = Session(7, "test", None)
        action = {"id": 0, "jump": True, "attack": "jab"}
        session.accept_input(input_packet(0, [action]), 10)
        session.accept_input(input_packet(1, [action]), 10)
        first = session.consume(10)
        second = session.consume(10)
        assert first.player_id == 7 and first.jump and first.attack == "jab"
        assert not second.jump and second.attack is None
        assert session.consume(10 + STALE_INPUT_SECONDS + 0.01).move_x == 0
        for i in range(1, 33):
            session.accept_input(input_packet(i + 1, [{**action, "id": i}]), 11)
        with pytest.raises(ProtocolError):
            session.accept_input(input_packet(34, [{**action, "id": 33}]), 11)
    asyncio.run(scenario())


def test_slow_writer_coalesces_snapshots_and_keeps_events_bounded():
    class Writer:
        closed = False
        def is_closing(self):
            return self.closed
        def close(self):
            self.closed = True

    async def scenario():
        writer = Writer()
        session = Session(0, "slow", writer)
        for tick in range(100):
            session.send({"type": "snapshot", "tick": tick})
        assert session.latest_snapshot["tick"] == 99
        assert len(session.controls) == 0
        for _ in range(65):
            session.send({"type": "events", "events": []})
        assert writer.closed and len(session.controls) == 64
    asyncio.run(scenario())
