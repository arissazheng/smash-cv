"""Build fake LandmarkFrames for tests: a person sitting at a laptop."""

from shared.landmarks import (
    LEFT_SHOULDER, LEFT_WRIST, NOSE, RIGHT_SHOULDER, RIGHT_WRIST, Hand, LandmarkFrame,
)
from vision.calibration import Calibration

CALIB = Calibration(center_x=0.5, shoulder_y=0.6, nose_y=0.4, shoulder_width=0.2)


def person(t: float = 0.0, lean: float = 0.0, nose_drop: float = 0.0,
           left_wrist=(0.35, 0.8), right_wrist=(0.65, 0.8), hands=()) -> LandmarkFrame:
    """Neutral pose shifted by `lean` (in image x) with wrists where you put them."""
    pose = [(0.5, 0.5, 0.0, 1.0)] * 33
    pose[NOSE] = (0.5 + lean, 0.4 + nose_drop, 0.0, 1.0)
    pose[LEFT_SHOULDER] = (0.4 + lean, 0.6, 0.0, 1.0)
    pose[RIGHT_SHOULDER] = (0.6 + lean, 0.6, 0.0, 1.0)
    pose[LEFT_WRIST] = (*left_wrist, 0.0, 1.0)
    pose[RIGHT_WRIST] = (*right_wrist, 0.0, 1.0)
    return LandmarkFrame(t, pose, list(hands))


def hand(gesture: str, tip=(0.5, 0.3)) -> Hand:
    landmarks = [(0.5, 0.5, 0.0)] * 21
    landmarks[8] = (*tip, 0.0)
    return Hand("Right", landmarks, gesture, 0.9)
