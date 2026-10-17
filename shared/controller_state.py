"""The contract between the vision side and the game side.

The game reads one ControllerState per player per frame. Only the gesture
recognizer fills it in. Change this file only with all four people agreeing.
"""

from dataclasses import dataclass
from typing import Optional

ATTACKS = ("jab", "smash", "special", "up_special", "grab")


@dataclass
class ControllerState:
    player_id: int = 0
    move_x: float = 0.0                  # -1.0 (left) .. 1.0 (right), continuous
    crouch: bool = False
    shield: bool = False
    jump: bool = False                   # edge-triggered: true for one poll
    attack: Optional[str] = None         # one of ATTACKS, edge-triggered
    taunt: bool = False                  # edge-triggered
    pause: bool = False                  # edge-triggered
    pointer: Optional[tuple[float, float]] = None  # index fingertip, 0..1, for menus
    timestamp: float = 0.0

    def __post_init__(self):
        if self.attack is not None and self.attack not in ATTACKS:
            raise ValueError(f"unknown attack {self.attack!r}, expected one of {ATTACKS}")
        self.move_x = max(-1.0, min(1.0, float(self.move_x)))
