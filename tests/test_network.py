"""The real server over real localhost WebSockets, with bots standing in for browsers.

Bots send landmark frames exactly like the browser page, so these tests run
the whole path: WebSocket -> validation -> gesture recognizer -> game world ->
snapshots and events in the shared/protocol.py format.
"""

import asyncio
import json
import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")

import pytest  # noqa: E402

from network.client import Bot, ws_url  # noqa: E402
from network.protocol import VERSION  # noqa: E402
from network.server import STALE_INPUT_SECONDS, GameServer, Session  # noqa: E402
from shared.controller_state import ControllerState  # noqa: E402
from tests.helpers import CALIB, person  # noqa: E402

HANDS_UP = dict(left_wrist=(0.4, 0.2), right_wrist=(0.6, 0.2))


def run(scenario):
    asyncio.run(asyncio.wait_for(scenario(), timeout=20))


async def started_server(**kwargs):
    server = await GameServer("127.0.0.1", 0, countdown=0.05, **kwargs).start()
    host, port = server.address
    return server, f"http://{host}:{port}/"


async def joined(link, n=2, characters=("efros", "oski", "ng", "liu")):
    bots = [await Bot(link, f"P{i + 1}", characters[i]).connect() for i in range(n)]
    for bot in bots:
        await bot.calibrate(CALIB.center_x, CALIB.shoulder_y, CALIB.nose_y, CALIB.shoulder_width)
    return bots


async def stream(bot, make_frame, seconds, start_t):
    """Send frames at ~30/s for `seconds`; returns the next timestamp."""
    t = start_t
    for _ in range(int(seconds * 30)):
        await bot.send_frame(make_frame(t))
        t += 1 / 30
        await asyncio.sleep(1 / 30)
    return t


def fighter(snapshot, player_id):
    return next(f for f in snapshot["fighters"] if f["id"] == player_id)


def test_join_play_lean_jump_and_snapshot_format():
    async def scenario():
        server, link = await started_server()
        a, b = await joined(link)
        assert (a.player_id, b.player_id) == (0, 1)
        welcome = await a.wait_for("welcome")
        assert welcome["room"] == server.room and welcome["link"] == link

        await a.ready()
        await b.ready()
        start = await a.wait_for("match_start")
        assert start["stage"]["background"] == "memorial_glade.png"
        assert [p["character"] for p in start["players"]] == ["efros", "oski"]
        await a.wait_for("lobby", phase="playing")

        first = await a.wait_for("snapshot", where=lambda m: m["tick"] > 0)
        x0 = fighter(first, 0)["x"]
        t = await stream(a, lambda t: person(t=t, lean=0.12), 0.8, 1.0)       # lean right: walk right
        moved = a.of_type("snapshot")[-1]
        assert fighter(moved, 0)["x"] > x0 + 40
        assert fighter(moved, 1)["x"] == pytest.approx(fighter(first, 1)["x"], abs=1)  # P2 sent nothing

        await stream(a, lambda t: person(t=t), 0.3, t)                          # stand, then hands up
        await stream(a, lambda t: person(t=t, **HANDS_UP), 0.15, t + 0.3)
        await a.wait_for("snapshot", timeout=2, where=lambda m: fighter(m, 0)["state"] == "jump")
        assert set(fighter(moved, 0)) >= {"life_id", "invulnerable", "hitbox"}
        for bot in (a, b):
            await bot.close()
        await server.close()
    run(scenario)


def test_disconnect_ends_match_then_rematch_returns_to_lobby():
    async def scenario():
        server, link = await started_server(players=3)
        a, b, c = await joined(link, n=3)
        for bot in (a, b, c):
            await bot.ready()
        await a.wait_for("lobby", phase="playing")

        mark = a.mark()
        await c.close()                                          # P3 leaves mid-match
        gone = await a.wait_for("event", kind="disconnect")
        assert gone["player"] == 2
        assert (await a.wait_for("lobby", since=mark))["phase"] == "playing"

        await b.close()                                          # P2 leaves: P1 wins
        over = await a.wait_for("event", kind="game_over")
        assert over["winner"] == 0
        await a.wait_for("lobby", phase="finished")

        d = await Bot(link).connect(hello=False)                 # can't join a finished match
        await d.send({"type": "hello", "version": VERSION, "name": "Late", "character": "ng"})
        assert (await d.wait_for("error"))["message"].startswith("match in progress")
        mark = a.mark()
        await a.send({"type": "rematch"})
        await a.wait_for("lobby", phase="lobby", since=mark)     # everyone left voted: back to lobby
        await a.close()
        await server.close()
    run(scenario)


def test_rematch_needs_everyone():
    async def scenario():
        server, link = await started_server(stocks=1)
        a, b = await joined(link)
        await a.ready()
        await b.ready()
        await a.wait_for("lobby", phase="playing")
        server.world.fighters[1].x = -5000                       # P2 falls off: game over
        await a.wait_for("event", kind="game_over")
        await a.send({"type": "rematch"})
        lobby = await b.wait_for("lobby", where=lambda m: any(p["rematch"] for p in m["players"]))
        assert lobby["phase"] == "finished"
        mark = a.mark()
        await b.send({"type": "rematch"})
        await a.wait_for("lobby", phase="lobby", since=mark)
        assert server.world is None
        for bot in (a, b):
            await bot.close()
        await server.close()
    run(scenario)


@pytest.mark.parametrize("first_message, error", [
    ({"type": "ready", "ready": True}, "hello must be the first"),
    ({"type": "hello", "version": VERSION, "name": "A", "character": "mario"}, "character must be"),
    ({"type": "hello", "version": 1, "name": "A", "character": "oski"}, "protocol version"),
    ({"type": "hello", "version": VERSION, "name": "", "character": "oski"}, "name must"),
])
def test_bad_first_message_gets_an_error_and_is_closed(first_message, error):
    async def scenario():
        server, link = await started_server()
        bot = await Bot(link).connect(hello=False)
        await bot.send(first_message)
        assert error in (await bot.wait_for("error"))["message"]
        await bot._reader          # the server closed the connection
        assert server.sessions == {}
        await server.close()
    run(scenario)


def test_clients_cannot_send_inputs_or_bad_frames_and_full_lobby_is_refused():
    async def scenario():
        server, link = await started_server()
        a, b = await joined(link)
        await a.send({"type": "input", "held": {"move_x": 1}})    # inputs come only from the recognizer
        assert (await a.wait_for("error"))["message"] == "unknown message type"
        frame = json.loads(person(t=1).to_json())
        frame["pose"] = frame["pose"][:5]
        await b.send({"type": "landmarks", "frame": frame})
        assert "landmarks" in (await b.wait_for("error"))["message"]
        await asyncio.gather(a._reader, b._reader)                # the server closed both
        while server.sessions:                                     # and finished removing them
            await asyncio.sleep(0.01)
        c = await Bot(link).connect(hello=False)
        await c.send({"type": "hello", "version": VERSION, "name": "Late", "character": "ng"})
        await c.wait_for("welcome")                                # both earlier players were removed
        d = await Bot(link).connect(hello=False)
        await d.send({"type": "hello", "version": VERSION, "name": "Later", "character": "ng"})
        await d.wait_for("welcome")
        e = await Bot(link).connect(hello=False)
        await e.send({"type": "hello", "version": VERSION, "name": "Full", "character": "ng"})
        assert (await e.wait_for("error"))["message"] == "lobby is full"
        for bot in (a, b, c, d, e):
            await bot.close()
        await server.close()
    run(scenario)


async def http_get(link, path):
    host, port = link.split("//")[1].rstrip("/").split(":")
    reader, writer = await asyncio.open_connection(host, int(port))
    writer.write(f"GET {path} HTTP/1.1\r\nHost: {host}:{port}\r\nConnection: close\r\n\r\n".encode())
    data = await reader.read()
    writer.close()
    head, _, body = data.partition(b"\r\n\r\n")
    return int(head.split()[1]), head.decode(), body


def test_server_serves_the_play_page_and_assets_but_nothing_else():
    async def scenario():
        server, link = await started_server()
        status, head, body = await http_get(link, "/")
        assert status == 200 and b"<canvas" in body and "text/html" in head
        status, head, _ = await http_get(link, "/client/render/renderer.js")
        assert status == 200 and "text/javascript" in head
        status, head, body = await http_get(link, "/assets/stages/memorial_glade.png")
        assert status == 200 and body.startswith(b"\x89PNG")
        for path in ("/client/../shared/config.py", "/assets/../README.md", "/main.py", "/client/nope.js"):
            assert (await http_get(link, path))[0] == 404, path
        await server.close()
    run(scenario)


def test_ws_url():
    assert ws_url("http://127.0.0.1:8765/") == "ws://127.0.0.1:8765/ws"
    assert ws_url("https://abc.trycloudflare.com/") == "wss://abc.trycloudflare.com/ws"


# ---- session logic without sockets ---------------------------------------------

class _NoSocket:
    async def close(self):
        pass


def _session():
    return Session(0, "A", "oski", _NoSocket())


def test_actions_survive_until_consumed_and_stale_inputs_go_neutral():
    s = _session()
    s.set_calibration(dict(center_x=CALIB.center_x, shoulder_y=CALIB.shoulder_y,
                           nose_y=CALIB.nose_y, shoulder_width=CALIB.shoulder_width))
    s.accept_frame(json.loads(person(t=1.0, lean=0.12).to_json()), now=10.0)
    s.accept_frame(json.loads(person(t=1.1, lean=0.12, **HANDS_UP).to_json()), now=10.05)
    first = s.consume(10.06)
    assert first.move_x > 0 and first.jump                       # the jump edge is delivered once
    assert not s.consume(10.07).jump
    assert s.consume(10.05 + STALE_INPUT_SECONDS + 0.01).move_x == 0   # camera went quiet: stand still


def test_out_of_order_frames_are_ignored():
    s = _session()
    s.accept_frame(json.loads(person(t=2.0, **HANDS_UP).to_json()), now=1.0)
    s.accept_frame(json.loads(person(t=1.0).to_json()), now=1.01)     # older frame: dropped
    assert s.last_frame_t == 2.0


def test_slow_link_gets_only_the_newest_snapshot():
    async def scenario():
        s = _session()
        for tick in range(5):
            s.send({"type": "snapshot", "tick": tick})
        s.send({"type": "event", "kind": "hit"})
        assert s.latest_snapshot["tick"] == 4 and len(s.controls) == 1
    run(scenario)


def test_neutral_state_has_no_pause():
    assert ControllerState().pause is False  # pause is ignored online (see Session.consume)


def test_host_picks_the_stage_and_players_can_change_fighter():
    async def scenario():
        server, link = await started_server()
        a, b = await joined(link)                                  # a joined first: a is the host
        await b.send({"type": "stage", "stage": "soda_hall"})      # not the host: ignored
        await a.send({"type": "stage", "stage": "sather_gate"})
        await b.wait_for("lobby", stage="sather_gate")
        assert not b.of_type("lobby", stage="soda_hall")
        await b.send({"type": "character", "character": "liu"})
        await a.wait_for("lobby", where=lambda m: any(p["id"] == 1 and p["character"] == "liu" for p in m["players"]))
        await a.ready()
        await b.ready()
        start = await a.wait_for("match_start")
        assert start["stage"]["name"] == "Sather Gate"
        assert start["stage"]["background"] == "sather_gate.png"
        assert [p["character"] for p in start["players"]] == ["efros", "liu"]
        snap = await a.wait_for("snapshot")
        assert fighter(snap, 1)["character"] == "liu"
        await b.send({"type": "stage", "stage": "gateway"})        # can't change mid-match
        await asyncio.sleep(0.1)
        assert server.stage_id == "sather_gate"
        for bot in (a, b):
            await bot.close()
        await server.close()
    run(scenario)


def test_stage_lists_agree():
    from game.stage import STAGES
    from network.protocol import STAGES as WIRE_STAGES
    assert tuple(STAGES) == WIRE_STAGES
