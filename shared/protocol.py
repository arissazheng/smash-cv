"""Server -> browser messages, built from the running game.

Owners: Person 3 (server) and Person 4 (renderer). The browser side that reads
these is client/render/protocol.js; change both together.

Every message has a matching example in shared/protocol_examples/. Tests on
both sides check against those examples, so a change on one side only fails
loudly instead of silently breaking the other. If you change a message on
purpose, run `python tools/update_protocol_examples.py` and tell the team.

Each function returns a plain dict ready for json.dumps.
"""

from dataclasses import dataclass

from game.events import KO, GameEvent, GameOver, Hit
from game.stage import Stage
from shared import config


def _rect(r) -> list[int]:
    return [r.x, r.y, r.w, r.h]


@dataclass
class LobbyPlayer:
    id: int
    name: str
    character: str          # folder name in assets/characters/
    ready: bool = False
    connected: bool = True


def lobby(room: str, link: str, host: int, stage: str, players: list[LobbyPlayer]) -> dict:
    """Sent to everyone in a room whenever anyone joins, leaves, picks or readies up."""
    return {
        "type": "lobby",
        "room": room,
        "link": link,
        "host": host,
        "stage": stage,
        "players": [
            {"id": p.id, "name": p.name, "character": p.character, "ready": p.ready, "connected": p.connected}
            for p in players
        ],
    }


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


def event(e: GameEvent, tick: int, t: float) -> dict:
    """One thing that happened, stamped with the tick and server time it happened at.

    The browser holds it until its (slightly delayed) picture reaches that time,
    so the spark lines up with the punch.
    """
    base = {"type": "event", "tick": tick, "t": round(t, 4)}
    if isinstance(e, Hit):
        return {**base, "kind": "hit", "attacker": e.attacker, "target": e.target, "attack": e.attack,
                "damage": e.damage, "shielded": e.shielded, "x": round(e.x, 1), "y": round(e.y, 1)}
    if isinstance(e, KO):
        return {**base, "kind": "ko", "player": e.player, "stocks_left": e.stocks_left,
                "x": round(e.x, 1), "y": round(e.y, 1)}
    if isinstance(e, GameOver):
        return {**base, "kind": "game_over", "winner": e.winner}
    raise TypeError(f"unknown event {e!r}")
