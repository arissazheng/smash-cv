"""A fighter: physics, state machine, and reacting to ControllerState.

Owner: Person 3.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

import pygame

from game.combat import ATTACKS, PLAYABLE_ATTACKS, hitbox_rect
from game.stage import Stage
from shared.controller_state import ControllerState

WIDTH, HEIGHT, CROUCH_HEIGHT = 60, 90, 55
RUN_SPEED = 420.0       # px/s at move_x = 1
AIR_SPEED = 320.0
GRAVITY = 2200.0        # px/s^2
FAST_FALL_SPEED = 1100.0
MAX_FALL_SPEED = 800.0
JUMP_SPEED = 900.0
MAX_JUMPS = 2           # ground jump + one air jump
GROUND_FRICTION = 10.0  # how fast you stop when not leaning
HITSTUN_PER_SPEED = 0.0006  # seconds of hitstun per px/s of knockback


@dataclass
class Fighter:
    player_id: int
    x: float               # center x
    y: float               # feet y
    character: str = "box"
    facing: int = 1
    vx: float = 0.0
    vy: float = 0.0
    damage: float = 0.0
    stocks: int = 3
    on_ground: bool = False
    jumps_left: int = MAX_JUMPS
    crouching: bool = False
    shielding: bool = False
    shield_health: float = 50.0
    hitstun: float = 0.0
    attack: Optional[str] = None
    attack_time: float = 0.0
    attack_connected: bool = False
    taunting: float = 0.0
    hit_targets: set[int] = field(default_factory=set, repr=False)
    life_id: int = 0
    invulnerable: float = 0.0
    state_time: float = 0.0
    _last_state: str = field(default="fall", repr=False)

    @property
    def rect(self) -> pygame.Rect:
        h = CROUCH_HEIGHT if self.crouching else HEIGHT
        return pygame.Rect(int(self.x - WIDTH / 2), int(self.y - h), WIDTH, h)

    @property
    def state(self) -> str:
        """Animation name for the renderer: matches assets/characters/<name>/<state>/."""
        if self.stocks <= 0:
            return "eliminated"
        if self.hitstun > 0:
            return "hurt"
        if self.attack:
            return self.attack
        if self.shielding:
            return "shield"
        if not self.on_ground:
            return "jump" if self.vy < 0 else "fall"
        if self.crouching:
            return "crouch"
        if self.taunting > 0:
            return "taunt"
        return "run" if abs(self.vx) > 20 else "idle"

    def apply_input(self, s: ControllerState) -> None:
        if self.stocks <= 0 or self.hitstun > 0:
            return
        busy = self.attack is not None

        self.shielding = s.shield and self.on_ground and not busy
        self.crouching = s.crouch and self.on_ground and not busy
        can_move = not (busy and self.on_ground) and not self.shielding and not self.crouching

        target = s.move_x * (RUN_SPEED if self.on_ground else AIR_SPEED) if can_move else 0.0
        if self.on_ground:
            self.vx += (target - self.vx) * min(1.0, GROUND_FRICTION / 60)
        elif s.move_x:
            self.vx = target
        if s.move_x and not busy:
            self.facing = 1 if s.move_x > 0 else -1

        if s.jump and self.jumps_left > 0 and not self.shielding:
            self.vy = -JUMP_SPEED
            self.jumps_left -= 1
            self.on_ground = False
        if s.crouch and not self.on_ground and self.vy > 0:
            self.vy = FAST_FALL_SPEED

        if s.attack in PLAYABLE_ATTACKS and not busy and not self.shielding:
            self.attack, self.attack_time, self.attack_connected = s.attack, 0.0, False
            self.hit_targets.clear()
        if s.taunt and self.on_ground and not busy:
            self.taunting = 1.0

    def step(self, dt: float, stage: Stage) -> None:
        if self.stocks <= 0:
            return
        self.hitstun = max(0.0, self.hitstun - dt)
        self.invulnerable = max(0.0, self.invulnerable - dt)
        self.taunting = max(0.0, self.taunting - dt)
        if self.attack:
            self.attack_time += dt
            if self.attack_time >= ATTACKS[self.attack].total:
                self.attack = None

        if self.vy < FAST_FALL_SPEED:
            self.vy = min(self.vy + GRAVITY * dt, max(MAX_FALL_SPEED, self.vy))
        prev_y = self.y
        self.x += self.vx * dt
        self.y += self.vy * dt
        if not self.on_ground or self.hitstun > 0:
            self.vx *= 0.995  # a little air drag so launched fighters slow down
        self._land(prev_y, stage)
        current = self.state
        self.state_time = self.state_time + dt if current == self._last_state else 0.0
        self._last_state = current

    def _land(self, prev_y: float, stage: Stage) -> None:
        self.on_ground = False
        if self.vy < 0:
            return
        for surface in sorted([stage.main, *stage.platforms], key=lambda r: r.top):
            within_x = surface.left <= self.x <= surface.right
            if within_x and prev_y <= surface.top <= self.y:
                if surface is not stage.main and self.crouching:
                    continue  # crouching on a platform drops through it
                self.y, self.vy = surface.top, 0.0
                self.on_ground, self.jumps_left = True, MAX_JUMPS
                return
            if within_x and self.y == surface.top:
                self.on_ground = True
                return

    def hitbox(self) -> Optional[pygame.Rect]:
        if self.stocks <= 0 or not self.attack:
            return None
        data = ATTACKS[self.attack]
        if not data.startup <= self.attack_time < data.startup + data.active:
            return None
        return hitbox_rect(self.rect.center, self.facing, data)

    def take_hit(self, vx: float, vy: float) -> None:
        self.vx, self.vy = vx, vy
        self.hitstun = HITSTUN_PER_SPEED * (vx * vx + vy * vy) ** 0.5
        self.attack, self.shielding, self.crouching = None, False, False
        self.on_ground = False

    def respawn(self, spawn: tuple[int, int]) -> None:
        self.x, self.y = spawn
        self.vx = self.vy = 0.0
        self.damage = 0.0
        self.hitstun = 0.0
        self.attack = None
        self.attack_time = 0.0
        self.attack_connected = False
        self.hit_targets.clear()
        self.on_ground = self.crouching = self.shielding = False
        self.shield_health = 50.0
        self.taunting = self.state_time = 0.0
        self._last_state = "fall"
        self.jumps_left = MAX_JUMPS
        self.life_id += 1
        self.invulnerable = 0.8
