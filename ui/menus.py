"""Menus driven by the finger-pointing cursor.

Owner: Person 4.

Point at a button and hold still for DWELL_SECONDS to select it. Uses
ControllerState.pointer (index fingertip, 0..1), which Person 1 keeps stable.

TODO(Person 4): title screen, character select grid, stage select, results
screen. Wire them into main.py before Game.run().
"""

from dataclasses import dataclass

import pygame

DWELL_SECONDS = 0.8


@dataclass
class DwellButton:
    label: str
    rect: pygame.Rect
    hover_time: float = 0.0

    def update(self, cursor: tuple[int, int] | None, dt: float) -> bool:
        """Returns True on the frame the button is selected."""
        if cursor is not None and self.rect.collidepoint(cursor):
            self.hover_time += dt
            if self.hover_time >= DWELL_SECONDS:
                self.hover_time = 0.0
                return True
        else:
            self.hover_time = 0.0
        return False

    @property
    def progress(self) -> float:
        return min(self.hover_time / DWELL_SECONDS, 1.0)


def pointer_to_screen(pointer: tuple[float, float] | None, size: tuple[int, int]) -> tuple[int, int] | None:
    """Map a normalized fingertip to screen pixels.

    TODO(Person 4): use only the middle of the camera image (e.g. 0.2..0.8) so
    players can reach the screen edges without leaving the frame.
    """
    if pointer is None:
        return None
    return int(pointer[0] * size[0]), int(pointer[1] * size[1])
