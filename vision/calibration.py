"""Per-player calibration: where "neutral" is for this person and this camera.

Owner: Person 1.

Detectors measure distances in shoulder widths from these baselines, so the
same thresholds work whether you sit close to the camera or far away.
"""

from dataclasses import asdict, dataclass
import json
from pathlib import Path
from statistics import mean

from shared import config
from shared.landmarks import LEFT_SHOULDER, NOSE, RIGHT_SHOULDER, LandmarkFrame


@dataclass
class Calibration:
    center_x: float = 0.5        # shoulder midpoint x when sitting neutral
    shoulder_y: float = 0.6      # shoulder midpoint y when sitting neutral
    nose_y: float = 0.4          # nose y when sitting neutral
    shoulder_width: float = 0.25  # distance between shoulders, the unit for all thresholds

    @classmethod
    def from_frames(cls, frames: list[LandmarkFrame]) -> "Calibration":
        """Average a few seconds of the player sitting still, facing the camera."""
        usable = [f for f in frames if f.pose is not None]
        if len(usable) < 10:
            raise ValueError(f"only {len(usable)} frames with a person in them; need at least 10")
        ls = [f.pose[LEFT_SHOULDER] for f in usable]
        rs = [f.pose[RIGHT_SHOULDER] for f in usable]
        return cls(
            center_x=mean((l[0] + r[0]) / 2 for l, r in zip(ls, rs)),
            shoulder_y=mean((l[1] + r[1]) / 2 for l, r in zip(ls, rs)),
            nose_y=mean(f.pose[NOSE][1] for f in usable),
            shoulder_width=mean(abs(l[0] - r[0]) for l, r in zip(ls, rs)),
        )

    def save(self, name: str = "default") -> Path:
        config.CALIBRATION_DIR.mkdir(exist_ok=True)
        path = config.CALIBRATION_DIR / f"{name}.json"
        path.write_text(json.dumps(asdict(self), indent=2))
        return path

    @classmethod
    def load(cls, name: str = "default") -> "Calibration":
        path = config.CALIBRATION_DIR / f"{name}.json"
        if not path.exists():
            print(f"[calibration] {path} not found, using defaults. Run: python main.py calibrate")
            return cls()
        return cls(**json.loads(path.read_text()))
