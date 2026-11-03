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
    """Applies a OneEuroFilter to every pose and hand x/y coordinate.

    Hands are matched across frames by handedness, so MediaPipe swapping the
    order of the hands doesn't mix up their filters.
    """

    def __init__(self, **filter_kwargs):
        self._kwargs = filter_kwargs
        self._filters: dict[tuple, OneEuroFilter] = {}

    def _f(self, key) -> OneEuroFilter:
        return self._filters.setdefault(key, OneEuroFilter(**self._kwargs))

    def __call__(self, frame: LandmarkFrame) -> LandmarkFrame:
        if frame.pose is None:
            self._filters.clear()  # person left the frame; don't smooth across the gap
            return frame
        t = frame.timestamp
        pose = [(self._f(("p", i, 0))(x, t), self._f(("p", i, 1))(y, t), z, vis)
                for i, (x, y, z, vis) in enumerate(frame.pose)]
        hands = []
        for h in frame.hands:
            lm = [(self._f((h.handedness, i, 0))(x, t), self._f((h.handedness, i, 1))(y, t), z)
                  for i, (x, y, z) in enumerate(h.landmarks)]
            hands.append(Hand(h.handedness, lm, h.gesture, h.gesture_score))
        present = {h.handedness for h in frame.hands}
        for k in [k for k in self._filters if k[0] != "p" and k[0] not in present]:
            del self._filters[k]  # hand left view; restart its filter
        return LandmarkFrame(t, pose, hands)
