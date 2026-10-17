"""Reading and writing recorded sessions (JSON lines).

Owner: Person 2.

File format, one JSON object per line:
  line 1: header  {"label": "jab", "player": "arissa", "created": "..."}
  line 2+: one LandmarkFrame each (see shared/landmarks.py)
"""

from datetime import datetime
import json
from pathlib import Path

from shared.landmarks import LandmarkFrame


def write_recording(path: Path, frames: list[LandmarkFrame], label: str = "", player: str = "") -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    header = {"label": label, "player": player, "created": datetime.now().isoformat(timespec="seconds")}
    with path.open("w") as f:
        f.write(json.dumps(header) + "\n")
        for frame in frames:
            f.write(frame.to_json() + "\n")


def read_recording(path: Path) -> tuple[dict, list[LandmarkFrame]]:
    with Path(path).open() as f:
        header = json.loads(f.readline())
        frames = [LandmarkFrame.from_json(line) for line in f if line.strip()]
    return header, frames
