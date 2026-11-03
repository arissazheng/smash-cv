"""Stage layout: platforms, blast zones, spawn points.

Owner: Person 3 (layout) + Person 4 (background art).
"""

from __future__ import annotations

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


def battlefield(players: int = 2) -> Stage:
    if not 2 <= players <= 4:
        raise ValueError("the prototype supports 2–4 players")
    w, h = config.SCREEN_WIDTH, config.SCREEN_HEIGHT
    offsets = {2: [-200, 200], 3: [-240, 0, 240], 4: [-300, -100, 100, 300]}
    return Stage(
        name="Memorial Glade",
        main=pygame.Rect(w // 2 - 400, h - 200, 800, 40),
        platforms=[
            pygame.Rect(w // 2 - 300, h - 340, 180, 12),
            pygame.Rect(w // 2 + 120, h - 340, 180, 12),
            pygame.Rect(w // 2 - 90, h - 470, 180, 12),
        ],
        spawns=[(w // 2 + x, h - 400) for x in offsets[players]],
        background="memorial_glade.png",  # drawn to match these platforms; see assets/stages/
    )
