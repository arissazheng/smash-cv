"""Rule-based gesture detectors.

Owner: Person 2.

Each detector reads LandmarkFrames (never the camera directly), so every one of
them can be tested on recordings. Distances are measured in shoulder widths
(see vision/calibration.py) and y grows downward.

Implemented: lean, crouch, hands-up jump, punch, pointer, special, shield,
up special, grab, taunt, pause. Phase 2 thresholds are untuned first guesses.
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


# ---- phase 2 detectors (Person 2) ----------------------------------------------
# Thresholds are first guesses from the team plan; tune them on recorded clips.

def _gesture_hands(frame: LandmarkFrame, gesture: str):
    return [h for h in frame.hands if h.gesture == gesture]


def detect_special(frame: LandmarkFrame, calib: Calibration, max_gap: float = 0.5) -> bool:
    """Hadouken: both hands Open_Palm and wrists within ~0.5 shoulder widths of each other.
    Level check; the recognizer makes it edge-triggered."""
    if len(_gesture_hands(frame, "Open_Palm")) < 2 or not _visible(frame, LEFT_WRIST, RIGHT_WRIST):
        return False
    l, r = frame.pose[LEFT_WRIST], frame.pose[RIGHT_WRIST]
    return math.hypot(l[0] - r[0], l[1] - r[1]) / calib.shoulder_width <= max_gap


def detect_shield(frame: LandmarkFrame, calib: Calibration, face_band: float = 0.6) -> bool:
    """Arms crossed in front of the face: wrists past the body midline, at face height. Held."""
    if not _visible(frame, NOSE, LEFT_SHOULDER, RIGHT_SHOULDER, LEFT_WRIST, RIGHT_WRIST):
        return False
    p = frame.pose
    # Crossed = wrists are in the opposite left/right order from the shoulders.
    crossed = (p[LEFT_WRIST][0] - p[RIGHT_WRIST][0]) * (p[LEFT_SHOULDER][0] - p[RIGHT_SHOULDER][0]) < 0
    at_face = all(abs(p[w][1] - p[NOSE][1]) / calib.shoulder_width <= face_band for w in (LEFT_WRIST, RIGHT_WRIST))
    return crossed and at_face


class UpSpecialDetector:
    """Pointing_Up appearing, or a fast upward wrist (uppercut). Suppressed while both hands are up (jump)."""

    def __init__(self, speed_threshold: float = 6.0):
        self.speed_threshold = speed_threshold
        self._prev: dict[int, tuple[float, float]] = {}  # wrist -> (y, t)
        self._was_pointing = False

    def update(self, frame: LandmarkFrame, calib: Calibration) -> bool:
        pointing = bool(_gesture_hands(frame, "Pointing_Up"))
        fired = pointing and not self._was_pointing
        self._was_pointing = pointing

        t = frame.timestamp
        for w in (LEFT_WRIST, RIGHT_WRIST):
            if not _visible(frame, w, NOSE):
                self._prev.pop(w, None)
                continue
            y = frame.pose[w][1]
            prev = self._prev.get(w)
            self._prev[w] = (y, t)
            if prev is None or t <= prev[1]:
                continue
            speed_up = (prev[0] - y) / calib.shoulder_width / (t - prev[1])
            if speed_up >= self.speed_threshold and y < frame.pose[NOSE][1]:
                fired = True
        return fired and not hands_up(frame, calib)

    def reset(self):
        self._prev.clear()
        self._was_pointing = False


class GrabDetector:
    """A hand goes Open_Palm -> Closed_Fist within `window` seconds."""

    def __init__(self, window: float = 0.2):
        self.window = window
        self._open_t: dict[str, float] = {}  # handedness -> last time seen as Open_Palm
        self._was_fist: set[str] = set()

    def update(self, frame: LandmarkFrame, calib: Calibration) -> bool:
        fired, fists = False, set()
        for h in frame.hands:
            if h.gesture == "Open_Palm":
                self._open_t[h.handedness] = frame.timestamp
            elif h.gesture == "Closed_Fist":
                fists.add(h.handedness)
                opened = self._open_t.get(h.handedness)
                if h.handedness not in self._was_fist and opened is not None and frame.timestamp - opened <= self.window:
                    fired = True
        self._was_fist = fists
        return fired

    def reset(self):
        self._open_t.clear()
        self._was_fist.clear()


class TauntDetector:
    """Thumb_Up held `hold` seconds. Fires once; release the thumb to re-arm."""

    def __init__(self, hold: float = 0.5):
        self.hold = hold
        self._since: Optional[float] = None
        self._fired = False

    def update(self, frame: LandmarkFrame, calib: Calibration) -> bool:
        if not _gesture_hands(frame, "Thumb_Up"):
            self.reset()
            return False
        if self._since is None:
            self._since = frame.timestamp
        if not self._fired and frame.timestamp - self._since >= self.hold:
            self._fired = True
            return True
        return False

    def reset(self):
        self._since, self._fired = None, False


class PauseDetector:
    """One Open_Palm held still for `hold` seconds (two palms is special). Fires once; lower the hand to re-arm."""

    def __init__(self, hold: float = 1.0, still: float = 0.3):
        self.hold, self.still = hold, still  # still: max wrist drift, in shoulder widths
        self._anchor: Optional[tuple[float, float, float]] = None  # x, y, start time
        self._fired = False

    def update(self, frame: LandmarkFrame, calib: Calibration) -> bool:
        palms = _gesture_hands(frame, "Open_Palm")
        if len(palms) != 1 or len(frame.hands) != 1:
            self.reset()
            return False
        x, y, _ = palms[0].landmarks[0]
        if self._anchor is None or math.hypot(x - self._anchor[0], y - self._anchor[1]) / calib.shoulder_width > self.still:
            self._anchor, self._fired = (x, y, frame.timestamp), False
            return False
        if not self._fired and frame.timestamp - self._anchor[2] >= self.hold:
            self._fired = True
            return True
        return False

    def reset(self):
        self._anchor, self._fired = None, False
