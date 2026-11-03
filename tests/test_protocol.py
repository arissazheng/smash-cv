"""The server's messages must keep the shape of shared/protocol_examples/*.json,
which is what the browser's tests draw. If one of these fails, either change
the code back or, if the change is on purpose, run
`python tools/update_protocol_examples.py` and update client/render to match.
"""

import json
import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")

import pytest  # noqa: E402

from game.engine import Game  # noqa: E402
from game.events import KO, GameOver, Hit  # noqa: E402
from shared import config  # noqa: E402
from shared.controller_state import ControllerState  # noqa: E402
from shared.protocol_samples import EXAMPLES_DIR_NAME, build_examples  # noqa: E402

EXAMPLES_DIR = config.ROOT / "shared" / EXAMPLES_DIR_NAME
CURRENT = build_examples()


def assert_same_shape(actual, example, path="message"):
    """Same keys at every level and the same kind of value. Values themselves may differ.

    null in either matches anything, since fields like hitbox are sometimes null.
    """
    if actual is None or example is None:
        return
    if isinstance(example, dict):
        assert isinstance(actual, dict), f"{path}: expected an object, got {actual!r}"
        missing, extra = example.keys() - actual.keys(), actual.keys() - example.keys()
        assert not missing and not extra, f"{path}: missing {sorted(missing)}, unexpected {sorted(extra)}"
        for key in example:
            assert_same_shape(actual[key], example[key], f"{path}.{key}")
    elif isinstance(example, list):
        assert isinstance(actual, list), f"{path}: expected a list, got {actual!r}"
        if example:
            for i, item in enumerate(actual):
                assert_same_shape(item, example[0], f"{path}[{i}]")
    elif isinstance(example, bool):
        assert isinstance(actual, bool), f"{path}: expected true/false, got {actual!r}"
    elif isinstance(example, (int, float)):
        assert isinstance(actual, (int, float)) and not isinstance(actual, bool), f"{path}: expected a number, got {actual!r}"
    else:
        assert type(actual) is type(example), f"{path}: expected {type(example).__name__}, got {actual!r}"


@pytest.mark.parametrize("name", sorted(CURRENT))
def test_message_matches_committed_example(name):
    path = EXAMPLES_DIR / f"{name}.json"
    assert path.exists(), f"{path} missing; run python tools/update_protocol_examples.py"
    example = json.loads(path.read_text())
    actual = json.loads(json.dumps(CURRENT[name]))  # exactly what goes over the wire
    assert actual["type"] == example["type"]
    if "kind" in example:
        assert actual["kind"] == example["kind"]
    assert_same_shape(actual, example, name)


def test_every_example_file_is_still_produced():
    on_disk = {p.stem for p in EXAMPLES_DIR.glob("*.json")}
    assert on_disk == set(CURRENT), "examples on disk and build_examples() disagree"


def test_shape_check_catches_a_renamed_field():
    example = CURRENT["snapshot"]
    renamed = json.loads(json.dumps(example))
    renamed["fighters"][0]["percent"] = renamed["fighters"][0].pop("damage")
    with pytest.raises(AssertionError, match="damage"):
        assert_same_shape(renamed, example)


# ---- game events --------------------------------------------------------------

class _Idle:
    def poll(self):
        return ControllerState()


def _game(stocks=2):
    game = Game(stocks=stocks)
    game.set_controllers([_Idle(), _Idle()])
    return game


def test_jab_reports_one_hit():
    game = _game()
    a, b = game.fighters
    ground = float(game.stage.main.top)
    a.x, a.y, a.facing, b.x, b.y = 600.0, ground, 1, 660.0, ground
    a.apply_input(ControllerState(attack="jab"))
    hits = []
    for _ in range(40):
        game.tick(1 / 60)
        hits += [e for e in game.events if isinstance(e, Hit)]
    assert len(hits) == 1
    assert (hits[0].attacker, hits[0].target, hits[0].attack) == (0, 1, "jab")
    assert hits[0].damage == b.damage


def test_ko_is_reported_once_and_stocks_never_go_negative():
    game = _game(stocks=1)
    game.fighters[1].x = -1000.0
    events = []
    for _ in range(10):
        game.tick(1 / 60)
        events += game.events
    assert [type(e) for e in events] == [KO, GameOver]
    assert game.fighters[1].stocks == 0
    assert events[1].winner == 0


def test_double_ko_is_a_draw():
    game = _game(stocks=1)
    game.fighters[0].x = game.fighters[1].x = -1000.0
    game.tick(1 / 60)
    over = [e for e in game.events if isinstance(e, GameOver)]
    assert len(over) == 1 and over[0].winner is None
    assert game.over
