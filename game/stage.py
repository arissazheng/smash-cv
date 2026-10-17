"""Stage layout: platforms, blast zones, spawn points.

Owner: Person 3 (layout) + Person 4 (background art).
"""

from dataclasses import dataclass, field

import pygame

from shared import config


@dataclass
class Stage:
    name: str
    main: pygame.Rect                                        # solid ground
    platforms: list[pygame.Rect] = field(default_factory=list)  # pass-through from below
    blast_zone: pygame.Rect = field(default_factory=lambda: pygame.Rect(-300, -400, config.SCREEN_WIDTH + 600, config.SCREEN_HEIGHT + 700))
    spawns: list[tuple[int, int]] = field(default_factory=list)
    background: str | None = None                            # file in assets/stages/


def battlefield() -> Stage:
    w, h = config.SCREEN_WIDTH, config.SCREEN_HEIGHT
    return Stage(
        name="Battlefield",
        main=pygame.Rect(w // 2 - 400, h - 200, 800, 40),
        platforms=[
            pygame.Rect(w // 2 - 300, h - 340, 180, 12),
            pygame.Rect(w // 2 + 120, h - 340, 180, 12),
            pygame.Rect(w // 2 - 90, h - 470, 180, 12),
        ],
        spawns=[(w // 2 - 200, h - 400), (w // 2 + 200, h - 400)],
        background=None,  # TODO(Person 4): e.g. "battlefield.png"
    )
