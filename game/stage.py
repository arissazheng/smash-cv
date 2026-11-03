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


SPAWN_OFFSETS = {2: [-200, 200], 3: [-240, 0, 240], 4: [-300, -100, 100, 300]}


def _spawns(players: int, y: int, center: int | None = None) -> list[tuple[int, int]]:
    if not 2 <= players <= 4:
        raise ValueError("matches support 2–4 players")
    cx = config.SCREEN_WIDTH // 2 if center is None else center
    return [(cx + x, y) for x in SPAWN_OFFSETS[players]]


def memorial_glade(players: int = 2) -> Stage:
    """Battlefield layout: a floating island and three ledges, the Campanile behind."""
    w, h = config.SCREEN_WIDTH, config.SCREEN_HEIGHT
    return Stage(
        name="Memorial Glade",
        main=pygame.Rect(w // 2 - 400, h - 200, 800, 40),
        platforms=[
            pygame.Rect(w // 2 - 300, h - 340, 180, 12),
            pygame.Rect(w // 2 + 120, h - 340, 180, 12),
            pygame.Rect(w // 2 - 90, h - 470, 180, 12),
        ],
        spawns=_spawns(players, h - 400),
        background="memorial_glade.png",  # drawn to match these platforms; see assets/stages/
    )


def gateway(players: int = 2) -> Stage:
    """Gateway's atrium: a wide carpet floor and balconies at three different heights."""
    return Stage(
        name="Gateway",
        main=pygame.Rect(160, 540, 960, 40),
        platforms=[
            pygame.Rect(200, 400, 240, 12),
            pygame.Rect(840, 360, 240, 12),
            pygame.Rect(500, 230, 280, 12),
        ],
        spawns=_spawns(players, 420),
        background="gateway.png",
    )


def sather_gate(players: int = 2) -> Stage:
    """The brick plaza; stand on the two pillar tops and the crown of the arch."""
    return Stage(
        name="Sather Gate",
        main=pygame.Rect(140, 540, 1000, 40),
        platforms=[
            pygame.Rect(250, 330, 110, 12),
            pygame.Rect(920, 330, 110, 12),
            pygame.Rect(470, 230, 340, 12),
        ],
        spawns=_spawns(players, 420),
        background="sather_gate.png",
    )


def soda_hall(players: int = 2) -> Stage:
    """Le Roy Ave: the street, the traffic-light arm and Soda Hall's arch sills."""
    return Stage(
        name="Soda Hall",
        main=pygame.Rect(120, 540, 1040, 40),
        platforms=[
            pygame.Rect(150, 290, 300, 12),
            pygame.Rect(700, 400, 200, 12),
            pygame.Rect(940, 300, 200, 12),
        ],
        spawns=_spawns(players, 420),
        background="soda_hall.png",
    )


# id -> builder, in the order the stage picker shows them. The ids are what the
# lobby sends; keep them in sync with STAGES in network/protocol.py and
# client/stages.js (a test checks).
STAGES = {
    "memorial_glade": memorial_glade,
    "gateway": gateway,
    "sather_gate": sather_gate,
    "soda_hall": soda_hall,
}
DEFAULT_STAGE = "memorial_glade"

battlefield = memorial_glade  # the original name, still used by older code and tests
