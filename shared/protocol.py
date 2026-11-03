"""Server -> browser messages, built from the running game.

Owners: Person 3 (server) and Person 4 (renderer). The browser side that reads
these is client/render/protocol.js; change both together.

Each function returns a plain dict ready for json.dumps.
"""

from game.stage import Stage
from shared import config


def _rect(r) -> list[int]:
    return [r.x, r.y, r.w, r.h]


def match_start(stage: Stage, players: list[dict]) -> dict:
    """`players`: [{"id": 0, "name": "Arissa", "character": "golden_bear"}, ...]"""
    return {
        "type": "match_start",
        "stage": {
            "name": stage.name,
            "width": config.SCREEN_WIDTH,
            "height": config.SCREEN_HEIGHT,
            "main": _rect(stage.main),
            "platforms": [_rect(p) for p in stage.platforms],
            "background": stage.background,
        },
        "players": players,
    }


def snapshot(fighters, tick: int, t: float) -> dict:
    return {
        "type": "snapshot",
        "tick": tick,
        "t": round(t, 4),
        "fighters": [
            {
                "id": f.player_id,
                "character": f.character,
                "x": round(f.x, 1),
                "y": round(f.y, 1),
                "w": f.rect.w,
                "h": f.rect.h,
                "facing": f.facing,
                "state": f.state,
                "damage": round(f.damage, 1),
                "stocks": f.stocks,
                "shield": f.shielding,
                "hitbox": _rect(box) if (box := f.hitbox()) is not None else None,
            }
            for f in fighters
        ],
    }
