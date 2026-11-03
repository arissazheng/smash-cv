import json
import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")

from game.engine import Game  # noqa: E402
from shared import protocol  # noqa: E402
from shared.controller_state import ControllerState  # noqa: E402

# Every field client/render/protocol.js reads.
FIGHTER_KEYS = {"id", "character", "x", "y", "w", "h", "facing", "state", "damage", "stocks", "shield", "hitbox"}


def test_match_start_matches_renderer_format():
    game = Game()
    msg = protocol.match_start(game.stage, [{"id": 0, "name": "A", "character": "box"}])
    json.dumps(msg)
    assert msg["stage"]["width"] == 1280 and msg["stage"]["height"] == 720
    assert len(msg["stage"]["main"]) == 4
    assert all(len(p) == 4 for p in msg["stage"]["platforms"])


def test_snapshot_matches_renderer_format():
    game = Game()
    game.fighters[0].apply_input(ControllerState(attack="jab"))
    for _ in range(5):  # into the jab's active frames
        game.fighters[0].step(1 / 60, game.stage)
    msg = protocol.snapshot(game.fighters, tick=5, t=0.083)
    json.dumps(msg)
    assert msg["type"] == "snapshot"
    for f in msg["fighters"]:
        assert set(f) == FIGHTER_KEYS
    assert msg["fighters"][0]["state"] == "jab"
    assert msg["fighters"][0]["hitbox"] is not None
