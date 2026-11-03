"""Builds one real example of every server message, from actual game moments.

The committed copies live in shared/protocol_examples/*.json. Python tests
check that today's code still produces messages shaped like them; the
JavaScript tests check the renderer can draw them. Regenerate with
`python tools/update_protocol_examples.py` only when you change the format on
purpose.
"""

from shared import protocol
from shared.controller_state import ControllerState

DT = 1 / 60
EXAMPLES_DIR_NAME = "protocol_examples"


class _Idle:
    def poll(self):
        return ControllerState()


def _new_game(stocks: int = 2):
    from game.engine import Game  # imported here so importing this module stays cheap

    game = Game(stocks=stocks)
    game.set_controllers([_Idle(), _Idle()])
    for _ in range(60):  # let both fighters land
        game.tick(DT)
    return game


def _game_with_jab_landing():
    """Player 1 jabs player 2 at close range. Returns (game, events from the hit tick)."""
    game = _new_game()
    a, b = game.fighters
    ground = float(game.stage.main.top)
    a.x, a.y, a.vy, a.facing = 600.0, ground, 0.0, 1
    b.x, b.y, b.vy = 660.0, ground, 0.0
    a.apply_input(ControllerState(attack="jab"))
    for _ in range(30):
        game.tick(DT)
        if game.events:
            return game, game.events
    raise AssertionError("jab never landed; check ATTACKS['jab'] or the spacing above")


def build_examples() -> dict[str, dict]:
    examples = {}

    examples["welcome"] = protocol.welcome(0, "ABCD", "https://example.com/?room=ABCD", "friends")
    examples["lobby"] = protocol.lobby(
        room="ABCD",
        link="https://example.com/?room=ABCD",
        host=0,
        stage="gateway",
        phase="lobby",
        capacity=2,
        players=[
            protocol.LobbyPlayer(0, "Arissa", "efros", ready=True),
            protocol.LobbyPlayer(1, "Sam", "oski"),
        ],
        mode="friends",
    )
    examples["error"] = protocol.error("room is full")

    game = _new_game()
    examples["match_start"] = protocol.match_start(game.stage, [
        {"id": 0, "name": "Arissa", "character": "efros"},
        {"id": 1, "name": "Sam", "character": "oski"},
    ], countdown=1.5)

    game, hit_events = _game_with_jab_landing()
    # Snapshot taken mid-jab: one fighter has a hitbox, the other has null.
    game.fighters[0].attack, game.fighters[0].attack_time = "jab", 0.06
    examples["snapshot"] = protocol.snapshot(game.fighters, game.tick_number, game.time)
    examples["event_hit"] = protocol.event(hit_events[0], game.tick_number, game.time)

    game = _new_game(stocks=1)
    game.fighters[1].x = -1000.0  # off the left side: KO, and with 1 stock, game over
    game.tick(DT)
    ko, over = game.events
    examples["event_ko"] = protocol.event(ko, game.tick_number, game.time)
    examples["event_game_over"] = protocol.event(over, game.tick_number, game.time)

    game = _new_game()
    game.eliminate(1)  # player 2 disconnects
    examples["event_disconnect"] = protocol.event(game.events[0], game.tick_number, game.time)

    return examples
