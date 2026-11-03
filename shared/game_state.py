"""Read-only, JSON-friendly contract for Person 4's renderer and network clients.

No Pygame, camera, or simulation objects cross this boundary. Positions use the
server's fixed world coordinates; fighter y is the feet position.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Optional


@dataclass(frozen=True)
class StageView:
    name: str
    width: int
    height: int
    main: tuple[int, int, int, int]
    platforms: tuple[tuple[int, int, int, int], ...]

    @classmethod
    def from_dict(cls, data: dict) -> StageView:
        return cls(data["name"], data["width"], data["height"], tuple(data["main"]),
                   tuple(tuple(rect) for rect in data["platforms"]))


@dataclass(frozen=True)
class FighterView:
    player_id: int
    character: str
    x: float
    y: float
    vx: float
    vy: float
    facing: int
    width: int
    height: int
    state: str
    state_time: float
    damage: float
    stocks: int
    on_ground: bool
    life_id: int
    invulnerable: bool
    hitbox: Optional[tuple[int, int, int, int]]

    @classmethod
    def from_dict(cls, data: dict) -> FighterView:
        return cls(**{**data, "hitbox": tuple(data["hitbox"]) if data["hitbox"] else None})


@dataclass(frozen=True)
class MatchView:
    match_id: str
    tick: int
    phase: str
    winner: Optional[int]
    result: Optional[str]
    stage: StageView
    fighters: tuple[FighterView, ...]

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> MatchView:
        return cls(**{**data, "stage": StageView.from_dict(data["stage"]),
                      "fighters": tuple(FighterView.from_dict(f) for f in data["fighters"])})
