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

from game.events import KO, Disconnect, GameEvent, GameOver, Hit
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
    rematch: bool = False   # voted to play again after game over
    cpu: bool = False       # the computer opponent in a vs-CPU room


def welcome(player_id: int, room: str, link: str, mode: str) -> dict:
    """First message after joining: who you are, the room, and (with friends) the link to share."""
    return {"type": "welcome", "player_id": player_id, "room": room, "link": link, "mode": mode}


def lobby(room: str, link: str, host: int | None, stage: str, phase: str, capacity: int,
          players: list[LobbyPlayer], mode: str) -> dict:
    """Sent to everyone whenever anyone joins, leaves, readies up or votes for a rematch.

    `stage` is the id of the stage the host picked (see STAGES in game/stage.py).
    `phase` is "lobby", "countdown", "playing" or "finished". `mode` is "cpu" or
    "friends"; `capacity` is how many humans the room holds.
    """
    return {
        "type": "lobby",
        "room": room,
        "link": link,
        "host": host,
        "stage": stage,
        "phase": phase,
        "capacity": capacity,
        "mode": mode,
        "players": [
            {"id": p.id, "name": p.name, "character": p.character, "ready": p.ready,
             "connected": p.connected, "rematch": p.rematch, "cpu": p.cpu}
            for p in players
        ],
    }


def match_start(stage: Stage, players: list[dict], countdown: float = 0.0) -> dict:
    """`players`: [{"id": 0, "name": "Arissa", "character": "golden_bear"}, ...]

    Play begins `countdown` seconds after this message.
    """
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
        "countdown": round(countdown, 3),
    }


def error(message: str) -> dict:
    return {"type": "error", "message": message}


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
                "life_id": f.life_id,                # goes up on respawn: snap, don't slide
                "invulnerable": f.invulnerable > 0,  # just respawned; can't be hit
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
    if isinstance(e, Disconnect):
        return {**base, "kind": "disconnect", "player": e.player}
    raise TypeError(f"unknown event {e!r}")
