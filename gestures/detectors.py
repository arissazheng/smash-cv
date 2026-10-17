"""Rule-based gesture detectors.

Owner: Person 2.

Each detector reads LandmarkFrames (never the camera directly), so every one of
them can be tested on recordings. Distances are measured in shoulder widths
(see vision/calibration.py) and y grows downward.

v0 (phase 1) detectors are implemented: lean, crouch, hands-up jump, punch,
pointer. The rest are stubs with the rule from the team plan written out.
"""

from collections import deque
import math
from typing import Optional

from shared.landmarks import (
    INDEX_TIP, LEFT_SHOULDER, LEFT_WRIST, NOSE, RIGHT_SHOULDER, RIGHT_WRIST, LandmarkFrame,
)
from vision.calibration import Calibration

MIN_VISIBILITY = 0.5


def _visible(frame: LandmarkFrame, *indices: int) -> bool:
    return frame.pose is not None and all(frame.pose[i][3] >= MIN_VISIBILITY for i in indices)


def shoulder_mid(frame: LandmarkFrame) -> tuple[float, float]:
    l, r = frame.pose[LEFT_SHOULDER], frame.pose[RIGHT_SHOULDER]
    return (l[0] + r[0]) / 2, (l[1] + r[1]) / 2


# ---- continuous / held -------------------------------------------------------

def lean_move_x(frame: LandmarkFrame, calib: Calibration, deadzone: float = 0.15, full: float = 0.6) -> float:
    """Torso lean -> move_x in -1..1. Inside `deadzone` shoulder widths = 0, past `full` = +-1."""
    if not _visible(frame, LEFT_SHOULDER, RIGHT_SHOULDER):
        return 0.0
    offset = (shoulder_mid(frame)[0] - calib.center_x) / calib.shoulder_width
    if abs(offset) <= deadzone:
        return 0.0
    magnitude = min(1.0, (abs(offset) - deadzone) / (full - deadzone))
    return math.copysign(magnitude, offset)


def is_crouching(frame: LandmarkFrame, calib: Calibration, threshold: float = 0.35) -> bool:
    """Head ducked: nose has dropped `threshold` shoulder widths below its neutral height."""
    if not _visible(frame, NOSE):
        return False
    return (frame.pose[NOSE][1] - calib.nose_y) / calib.shoulder_width > threshold


def hands_up(frame: LandmarkFrame, calib: Calibration, margin: float = 0.2) -> bool:
    """Both wrists at least `margin` shoulder widths above the nose. Jump = rising edge of this."""
    if not _visible(frame, NOSE, LEFT_WRIST, RIGHT_WRIST):
        return False
    limit = frame.pose[NOSE][1] - margin * calib.shoulder_width
    return frame.pose[LEFT_WRIST][1] < limit and frame.pose[RIGHT_WRIST][1] < limit


def pointer(frame: LandmarkFrame) -> Optional[tuple[float, float]]:
    """Index fingertip for the menu cursor. Prefers a hand doing Pointing_Up."""
    if not frame.hands:
        return None
    hand = next((h for h in frame.hands if h.gesture == "Pointing_Up"), frame.hands[0])
    x, y, _ = hand.landmarks[INDEX_TIP]
    return (x, y)


# ---- punches -----------------------------------------------------------------

class PunchDetector:
    """Wrist speed spikes -> "jab" (one hand) or "smash" (both hands together).

    A spike waits `pair_window` seconds for the other hand before it is
    reported, so a two-fist punch reads as one smash instead of a jab.

    TODO(Person 2): a punch toward the camera moves little in x/y. Add the
    hand's apparent size growing (hand landmarks spreading apart) as a second
    signal, and tune `speed_threshold` on recorded clips.
    """

    def __init__(self, speed_threshold: float = 6.0, pair_window: float = 0.08):
        self.speed_threshold = speed_threshold  # shoulder widths per second
        self.pair_window = pair_window
        self._prev: dict[int, tuple[float, float, float]] = {}  # wrist index -> (x, y, t)
        self._pending: Optional[tuple[int, float]] = None        # (wrist, time of first spike)

    def _spiked(self, frame: LandmarkFrame, calib: Calibration, wrist: int) -> bool:
        if not _visible(frame, wrist, NOSE):
            self._prev.pop(wrist, None)
            return False
        x, y = frame.pose[wrist][:2]
        t = frame.timestamp
        prev = self._prev.get(wrist)
        self._prev[wrist] = (x, y, t)
        if prev is None or t <= prev[2]:
            return False
        dx, dy = x - prev[0], y - prev[1]
        speed = math.hypot(dx, dy) / calib.shoulder_width / (t - prev[2])
        if speed < self.speed_threshold:
            return False
        # Mostly-upward motion ending above the nose is a jump or uppercut, not a punch.
        if dy < 0 and abs(dy) > 0.7 * math.hypot(dx, dy) and y < frame.pose[NOSE][1]:
            return False
        return True

    def update(self, frame: LandmarkFrame, calib: Calibration) -> Optional[str]:
        spikes = [w for w in (LEFT_WRIST, RIGHT_WRIST) if self._spiked(frame, calib, w)]
        t = frame.timestamp

        if self._pending is not None:
            first_wrist, first_t = self._pending
            if any(w != first_wrist for w in spikes):
                self._pending = None
                return "smash"
            if t - first_t >= self.pair_window:
                self._pending = None
                return "jab"
            return None

        if len(spikes) == 2:
            return "smash"
        if len(spikes) == 1:
            self._pending = (spikes[0], t)
        return None

    def reset(self):
        self._prev.clear()
        self._pending = None


# ---- stubs for phase 2 (Person 2) ---------------------------------------------

def detect_special(frame: LandmarkFrame, calib: Calibration) -> bool:
    """"Hadouken": both hands Open_Palm and wrists within ~0.5 shoulder widths of each other."""
    return False  # TODO(Person 2)


def detect_up_special(frame: LandmarkFrame, calib: Calibration) -> bool:
    """Uppercut (fast upward wrist) or one hand Pointing_Up. Must not collide with hands_up."""
    return False  # TODO(Person 2)


def detect_shield(frame: LandmarkFrame, calib: Calibration) -> bool:
    """Arms crossed in front of the face: wrists past the body midline, at face height. Held."""
    return False  # TODO(Person 2)


def detect_grab(frame: LandmarkFrame, calib: Calibration) -> bool:
    """A hand goes Open_Palm -> Closed_Fist within ~200 ms. Needs history: make it a class."""
    return False  # TODO(Person 2)


def detect_taunt(frame: LandmarkFrame, calib: Calibration) -> bool:
    """Thumb_Up held 0.5 s. Needs history: make it a class like PunchDetector."""
    return False  # TODO(Person 2)


def detect_pause(frame: LandmarkFrame, calib: Calibration) -> bool:
    """One Open_Palm held still for 1 s (and not two palms, which is special)."""
    return False  # TODO(Person 2)
