"""One Euro filter for jittery landmarks.

Owner: Person 1.

Smooths heavily when a point is still and lightly when it moves fast, so
punches stay sharp but idle jitter disappears.
Paper: https://gery.casiez.net/1euro/
"""

import math

from shared.landmarks import Hand, LandmarkFrame


class OneEuroFilter:
    def __init__(self, min_cutoff: float = 1.0, beta: float = 0.05, d_cutoff: float = 1.0):
        self.min_cutoff, self.beta, self.d_cutoff = min_cutoff, beta, d_cutoff
        self._x = None
        self._dx = 0.0
        self._t = None

    @staticmethod
    def _alpha(cutoff: float, dt: float) -> float:
        tau = 1.0 / (2 * math.pi * cutoff)
        return 1.0 / (1.0 + tau / dt)

    def __call__(self, x: float, t: float) -> float:
        if self._x is None or t <= self._t:
            self._x, self._t = x, t
            return x
        dt = t - self._t
        dx = (x - self._x) / dt
        a_d = self._alpha(self.d_cutoff, dt)
        self._dx = a_d * dx + (1 - a_d) * self._dx
        cutoff = self.min_cutoff + self.beta * abs(self._dx)
        a = self._alpha(cutoff, dt)
        self._x = a * x + (1 - a) * self._x
        self._t = t
        return self._x


class LandmarkSmoother:
    """Applies a OneEuroFilter to every pose x/y coordinate.

    TODO(Person 1): hands are passed through unsmoothed because hand order can
    swap between frames. Match hands by handedness, then smooth them too.
    """

    def __init__(self, **filter_kwargs):
        self._kwargs = filter_kwargs
        self._filters: dict[tuple[int, int], OneEuroFilter] = {}

    def __call__(self, frame: LandmarkFrame) -> LandmarkFrame:
        if frame.pose is None:
            self._filters.clear()  # person left the frame; don't smooth across the gap
            return frame
        t = frame.timestamp
        pose = []
        for i, (x, y, z, vis) in enumerate(frame.pose):
            fx = self._filters.setdefault((i, 0), OneEuroFilter(**self._kwargs))
            fy = self._filters.setdefault((i, 1), OneEuroFilter(**self._kwargs))
            pose.append((fx(x, t), fy(y, t), z, vis))
        hands = [Hand(h.handedness, list(h.landmarks), h.gesture, h.gesture_score) for h in frame.hands]
        return LandmarkFrame(t, pose, hands)
