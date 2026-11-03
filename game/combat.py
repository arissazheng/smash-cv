"""Attack data, hit detection and knockback.

Owner: Person 3.

Times are in seconds, distances in pixels. Hitbox offsets are relative to the
fighter's center and mirrored by facing direction.
"""

from dataclasses import dataclass
import math

import pygame

from game.events import Hit


@dataclass(frozen=True)
class AttackData:
    startup: float       # wind-up before the hitbox appears
    active: float        # how long the hitbox is out
    recovery: float      # cooldown after the hitbox disappears
    damage: float        # percent added to the target
    base_knockback: float
    knockback_growth: float  # extra knockback per percent of damage the target has
    angle: float         # launch angle in degrees, 0 = straight forward, 90 = straight up
    box: tuple[int, int, int, int]  # width, height, offset_x, offset_y

    @property
    def total(self) -> float:
        return self.startup + self.active + self.recovery


ATTACKS = {
    "jab": AttackData(0.05, 0.10, 0.15, 3, 150, 4, 30, (50, 30, 50, -10)),
    "smash": AttackData(0.20, 0.12, 0.35, 15, 300, 12, 40, (70, 50, 55, -10)),
    # TODO(Person 3): tune these once Person 2's detectors fire them.
    "special": AttackData(0.15, 0.20, 0.30, 10, 250, 8, 20, (90, 40, 80, -10)),
    "up_special": AttackData(0.08, 0.20, 0.40, 8, 250, 8, 85, (50, 80, 10, -60)),
    "grab": AttackData(0.06, 0.08, 0.30, 6, 200, 6, 45, (40, 40, 40, 0)),
}


def knockback_speed(attack: AttackData, target_damage: float) -> float:
    """Smash-style: the more damage a fighter has, the farther they fly."""
    return attack.base_knockback + attack.knockback_growth * target_damage


def launch_velocity(attack: AttackData, target_damage: float, facing: int) -> tuple[float, float]:
    speed = knockback_speed(attack, target_damage)
    rad = math.radians(attack.angle)
    return facing * speed * math.cos(rad), -speed * math.sin(rad)  # y up is negative


def resolve_hits(fighters) -> list[Hit]:
    """Apply each active hitbox to every other fighter, at most once per attack.

    Returns what landed, for hit sparks in the browser.
    """
    hits = []
    for attacker in fighters:
        box = attacker.hitbox()
        if box is None or attacker.attack_connected:
            continue
        for target in fighters:
            if target is attacker or not box.colliderect(target.rect):
                continue
            data = ATTACKS[attacker.attack]
            contact = box.clip(target.rect).center
            if target.shielding:
                target.shield_health -= data.damage  # TODO(Person 3): shield breaks
                hits.append(Hit(attacker.player_id, target.player_id, attacker.attack, 0.0, True, *contact))
            else:
                target.damage += data.damage
                target.take_hit(*launch_velocity(data, target.damage, attacker.facing))
                hits.append(Hit(attacker.player_id, target.player_id, attacker.attack, data.damage, False, *contact))
            attacker.attack_connected = True
    return hits


def hitbox_rect(center: tuple[float, float], facing: int, attack: AttackData) -> pygame.Rect:
    w, h, ox, oy = attack.box
    cx, cy = center[0] + facing * ox, center[1] + oy
    return pygame.Rect(int(cx - w / 2), int(cy - h / 2), w, h)
