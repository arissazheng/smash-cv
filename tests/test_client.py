from dataclasses import replace

import pytest

from client.input_buffer import InputBuffer
from client.interpolation import SnapshotBuffer
from game.engine import GameWorld
from shared.controller_state import ControllerState


def test_polled_edges_survive_later_neutral_polls_and_send_once():
    inputs = InputBuffer()
    inputs.capture(ControllerState(jump=True))
    inputs.capture(ControllerState(attack="smash"))
    inputs.capture(ControllerState(move_x=-1))
    packet = inputs.message("match")
    assert packet["held"]["move_x"] == -1
    assert packet["actions"] == [{"id": 0, "jump": True, "attack": None},
                                 {"id": 1, "jump": False, "attack": "smash"}]
    assert inputs.message("match")["actions"] == []


def test_input_buffer_filters_deferred_moves_and_clears_for_new_match():
    inputs = InputBuffer()
    inputs.capture(ControllerState(attack="grab", shield=True, pause=True))
    inputs.capture(ControllerState(jump=True), allow_actions=False)
    assert inputs.message("match")["actions"] == []
    inputs.capture(ControllerState(attack="special"))
    inputs.reset()
    assert inputs.message("next")["actions"] == []


def test_snapshot_interpolation_and_respawn_snap():
    initial = GameWorld().snapshot()
    a = replace(initial, tick=0)
    b = replace(initial, tick=6, fighters=(replace(initial.fighters[0], x=initial.fighters[0].x + 120),
                                         initial.fighters[1]))
    buffer = SnapshotBuffer(delay=0.05)
    buffer.push(a, 0)
    buffer.push(b, 0.1)
    halfway = buffer.sample(0.1)
    assert halfway.fighters[0].x == pytest.approx(a.fighters[0].x + 60)
    respawned = replace(b, tick=12, fighters=(replace(b.fighters[0], x=250, life_id=1), b.fighters[1]))
    buffer.push(respawned, 0.2)
    assert buffer.sample(0.2).fighters[0].x == 250
    buffer.push(replace(respawned, match_id="new", tick=0), 0.3)
    assert len(buffer.frames) == 1


def test_keyboard_edges_releases_and_focus_loss():
    import pygame
    from controllers.development import KeyboardController
    controller = KeyboardController()
    controller.handle([pygame.event.Event(pygame.KEYDOWN, key=pygame.K_d),
                       pygame.event.Event(pygame.KEYDOWN, key=pygame.K_SPACE),
                       pygame.event.Event(pygame.KEYDOWN, key=pygame.K_j)])
    assert controller.poll().jump
    jab = controller.poll()
    assert jab.move_x == 1 and jab.attack == "jab"
    controller.handle([pygame.event.Event(pygame.KEYDOWN, key=pygame.K_j)])
    assert controller.poll().attack is None
    controller.handle([pygame.event.Event(pygame.KEYUP, key=pygame.K_d)])
    assert controller.poll().move_x == 0
    controller.handle([pygame.event.Event(pygame.KEYDOWN, key=pygame.K_d),
                       pygame.event.Event(pygame.WINDOWFOCUSLOST)])
    assert controller.poll().move_x == 0
