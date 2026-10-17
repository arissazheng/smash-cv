"""Plain-Python landmark data, independent of MediaPipe.

Everything downstream of the camera (gesture detectors, recorder, replay,
tests) works on these types, so recordings can be replayed and tests can run
without a webcam.

Coordinates are normalized to the (mirrored) camera image: x and y in 0..1,
y grows downward.
"""

from dataclasses import dataclass, field
import json
from typing import Optional

# MediaPipe Pose landmark indices we use.
NOSE = 0
LEFT_SHOULDER, RIGHT_SHOULDER = 11, 12
LEFT_ELBOW, RIGHT_ELBOW = 13, 14
LEFT_WRIST, RIGHT_WRIST = 15, 16
LEFT_HIP, RIGHT_HIP = 23, 24

# MediaPipe Hand landmark indices we use.
HAND_WRIST = 0
INDEX_TIP = 8

# Pose skeleton edges for drawing (upper body only).
POSE_EDGES = [
    (LEFT_SHOULDER, RIGHT_SHOULDER),
    (LEFT_SHOULDER, LEFT_ELBOW), (LEFT_ELBOW, LEFT_WRIST),
    (RIGHT_SHOULDER, RIGHT_ELBOW), (RIGHT_ELBOW, RIGHT_WRIST),
    (LEFT_SHOULDER, LEFT_HIP), (RIGHT_SHOULDER, RIGHT_HIP), (LEFT_HIP, RIGHT_HIP),
]

Point = tuple[float, float, float, float]  # x, y, z, visibility


@dataclass
class Hand:
    handedness: str                        # "Left" or "Right", as MediaPipe reports it
    landmarks: list[tuple[float, float, float]]  # 21 points
    gesture: str = "None"                  # MediaPipe canned gesture, e.g. "Open_Palm"
    gesture_score: float = 0.0


@dataclass
class LandmarkFrame:
    timestamp: float                       # seconds
    pose: Optional[list[Point]] = None     # 33 points, or None if no person found
    hands: list[Hand] = field(default_factory=list)

    def point(self, index: int) -> Optional[Point]:
        if self.pose is None:
            return None
        return self.pose[index]

    def to_json(self) -> str:
        return json.dumps({
            "t": round(self.timestamp, 4),
            "pose": [[round(v, 5) for v in p] for p in self.pose] if self.pose else None,
            "hands": [
                {
                    "side": h.handedness,
                    "lm": [[round(v, 5) for v in p] for p in h.landmarks],
                    "g": h.gesture,
                    "gs": round(h.gesture_score, 3),
                }
                for h in self.hands
            ],
        })

    @classmethod
    def from_json(cls, line: str) -> "LandmarkFrame":
        d = json.loads(line)
        pose = [tuple(p) for p in d["pose"]] if d["pose"] else None
        hands = [Hand(h["side"], [tuple(p) for p in h["lm"]], h["g"], h["gs"]) for h in d["hands"]]
        return cls(d["t"], pose, hands)
