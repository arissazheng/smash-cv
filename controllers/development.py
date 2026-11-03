"""Optional camera-free prototype inputs. Production controllers stay unchanged."""

from __future__ import annotations

import time

from shared.controller_state import ControllerState


class KeyboardController:
    def __init__(self, player_id=0):
        self.player_id = player_id
        self._keys = set()
        self._actions = []

    def handle(self, events):
        import pygame

        for event in events:
            if event.type == pygame.WINDOWFOCUSLOST:
                self._keys.clear()
                self._actions.clear()
            elif event.type == pygame.KEYUP:
                self._keys.discard(event.key)
            elif event.type == pygame.KEYDOWN:
                if event.key in self._keys:
                    continue
                self._keys.add(event.key)
                if event.key in (pygame.K_SPACE, pygame.K_w, pygame.K_UP):
                    self._actions.append((True, None))
                elif event.key in (pygame.K_j, pygame.K_k, pygame.K_l):
                    self._actions.append((False, {pygame.K_j: "jab", pygame.K_k: "smash",
                                                   pygame.K_l: "special"}[event.key]))

    def poll(self):
        import pygame

        right = bool(self._keys & {pygame.K_d, pygame.K_RIGHT})
        left = bool(self._keys & {pygame.K_a, pygame.K_LEFT})
        jump, attack = self._actions.pop(0) if self._actions else (False, None)
        return ControllerState(player_id=self.player_id, move_x=float(right - left),
                               crouch=bool(self._keys & {pygame.K_s, pygame.K_DOWN}),
                               jump=jump, attack=attack)


class DemoController:
    """Small snapshot-driven bot for exercising the full network path."""

    def __init__(self, player_id, get_view, clock=time.monotonic):
        self.player_id, self.get_view, self.clock = player_id, get_view, clock
        self.next_attack = self.next_jump = 0.0
        self.attack_index = 0

    def poll(self):
        state = ControllerState(player_id=self.player_id)
        view = self.get_view()
        if not view or view.phase != "playing":
            return state
        me = next((f for f in view.fighters if f.player_id == self.player_id), None)
        opponents = [f for f in view.fighters if f.player_id != self.player_id and f.stocks > 0]
        if me is None or me.stocks <= 0 or not opponents:
            return state
        target = min(opponents, key=lambda f: abs(f.x - me.x))
        dx = target.x - me.x
        if abs(dx) > 65:
            state.move_x = 0.8 if dx > 0 else -0.8
        now = self.clock()
        if now >= self.next_attack and abs(dx) < 130:
            state.attack = ("jab", "smash", "special")[self.attack_index % 3]
            self.attack_index += 1
            self.next_attack = now + 0.85
        main_x, main_y, main_w, _ = view.stage.main
        offstage = me.x < main_x + 15 or me.x > main_x + main_w - 15
        if offstage:
            state.move_x = 1.0 if me.x < main_x + main_w / 2 else -1.0
        if now >= self.next_jump and (offstage or target.y < me.y - 60):
            state.jump = True
            self.next_jump = now + 0.5
        return state
