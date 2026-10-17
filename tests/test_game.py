import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")

from game.combat import ATTACKS, knockback_speed, resolve_hits  # noqa: E402
from game.engine import Game  # noqa: E402
from game.fighter import Fighter  # noqa: E402
from game.stage import battlefield  # noqa: E402
from shared.controller_state import ControllerState  # noqa: E402

DT = 1 / 60


def settle(fighter, stage, seconds=1.0):
    for _ in range(int(seconds / DT)):
        fighter.apply_input(ControllerState())
        fighter.step(DT, stage)


def test_fighter_lands_on_stage():
    stage = battlefield()
    f = Fighter(0, x=stage.main.centerx, y=stage.main.top - 200)
    settle(f, stage)
    assert f.on_ground and f.y == stage.main.top


def test_jump_and_double_jump():
    stage = battlefield()
    f = Fighter(0, x=stage.main.centerx, y=stage.main.top)
    settle(f, stage)
    f.apply_input(ControllerState(jump=True))
    assert f.vy < 0 and f.jumps_left == 1
    f.step(DT, stage)
    f.apply_input(ControllerState(jump=True))
    assert f.jumps_left == 0


def test_knockback_grows_with_damage():
    jab = ATTACKS["jab"]
    assert knockback_speed(jab, 100) > knockback_speed(jab, 0)


def test_jab_hits_once():
    stage = battlefield()
    a = Fighter(0, x=stage.main.centerx, y=stage.main.top, facing=1)
    b = Fighter(1, x=stage.main.centerx + 60, y=stage.main.top)
    settle(a, stage, 0.2)
    settle(b, stage, 0.2)
    a.apply_input(ControllerState(attack="jab"))
    for _ in range(int(ATTACKS["jab"].total / DT) + 1):
        a.step(DT, stage)
        resolve_hits([a, b])
    assert b.damage == ATTACKS["jab"].damage


def test_falling_off_costs_a_stock():
    game = Game(stocks=2)
    game.set_controllers([_Idle(), _Idle()])
    game.fighters[0].x = -1000
    game.tick(DT)
    assert game.fighters[0].stocks == 1


class _Idle:
    def poll(self):
        return ControllerState()
