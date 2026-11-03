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


def test_simultaneous_final_ko_finishes_as_draw_and_freezes():
    from game.engine import GameWorld
    world = GameWorld(stocks=1)
    for fighter in world.fighters:
        fighter.x = -1000
    world.step({})
    assert world.phase == "finished" and world.result == "draw" and world.winner is None
    before = world.snapshot()
    for _ in range(10):
        world.step({})
    assert world.snapshot() == before
    assert [f.stocks for f in world.fighters] == [0, 0]


def test_respawn_resets_life_state():
    f = Fighter(0, 0, 0, on_ground=True, crouching=True, shielding=True,
                shield_health=-1, taunting=1, attack="jab", attack_time=0.1)
    f.hit_targets.add(1)
    f.respawn((400, 300))
    assert (f.x, f.y) == (400, 300)
    assert not f.on_ground and not f.crouching and not f.shielding
    assert not f.hit_targets and f.attack is None and f.attack_time == 0
    assert f.life_id == 1 and f.invulnerable > 0 and f.taunting == 0


def test_attack_hits_new_target_on_later_active_frame_and_can_trade():
    a = Fighter(0, 600, 520, attack="jab", attack_time=0.06)
    b = Fighter(1, 660, 520)
    c = Fighter(2, 900, 520)
    resolve_hits([a, b, c])
    c.x = 660
    resolve_hits([a, b, c])
    assert b.damage == c.damage == ATTACKS["jab"].damage
    a = Fighter(0, 600, 520, attack="jab", attack_time=0.06)
    b = Fighter(1, 660, 520, facing=-1, attack="jab", attack_time=0.06)
    resolve_hits([a, b])
    assert a.damage == b.damage == ATTACKS["jab"].damage


def test_world_replay_determinism_four_players_and_json_snapshot():
    import json
    from game.engine import GameWorld
    a = GameWorld([0, 2, 4, 6])
    b = GameWorld([0, 2, 4, 6])
    for tick in range(180):
        inputs = {pid: ControllerState(move_x=0.2 if i % 2 else -0.2,
                                       jump=tick == 30, attack="special" if tick == 70 else None)
                  for i, pid in enumerate([0, 2, 4, 6])}
        a.step(inputs)
        b.step(inputs)
    assert a.snapshot() == b.snapshot()
    assert json.loads(json.dumps(a.snapshot())) == a.snapshot()


def test_headless_world_does_not_import_camera_or_ui():
    import subprocess
    import sys
    check = """
import sys
from game.engine import GameWorld
GameWorld().step({})
assert not any(name.split('.')[0] in {'ui', 'cv2', 'mediapipe', 'vision'} for name in sys.modules)
import pygame
assert not pygame.display.get_init()
"""
    subprocess.run([sys.executable, "-c", check], check=True, capture_output=True)


def test_every_attack_works_through_world_inputs():
    from game.engine import GameWorld
    from game.events import Hit
    for attack in ATTACKS:
        world = GameWorld()
        a, b = world.fighters
        a.x, b.x = 600, 660
        a.y = b.y = world.stage.main.top
        a.on_ground = b.on_ground = True
        world.step({0: ControllerState(attack=attack)})
        hits = []
        for _ in range(60):
            world.step({})
            hits.extend(e for e in world.events if isinstance(e, Hit))
        assert b.damage == ATTACKS[attack].damage, attack
        assert len(hits) == 1 and hits[0].attack == attack
