"""Things that happened during a tick, for the browser to show (hit sparks, KO
bursts, the "GAME!" screen). The game logic never reads these back.

Owner: Person 3. shared/protocol.py turns them into `event` messages.
"""

from dataclasses import dataclass


@dataclass
class Hit:
    attacker: int
    target: int
    attack: str          # "jab", "smash", ...
    damage: float        # percent added (0 when shielded)
    shielded: bool
    x: float             # where the hit landed, for the spark
    y: float


@dataclass
class KO:
    player: int
    stocks_left: int
    x: float             # where they left the stage, for the burst
    y: float


@dataclass
class GameOver:
    winner: int | None   # None = draw (last fighters KO'd on the same tick)


@dataclass
class Disconnect:
    player: int          # left mid-match and was removed


GameEvent = Hit | KO | GameOver | Disconnect
