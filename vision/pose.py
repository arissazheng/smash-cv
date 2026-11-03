"""MediaPipe wrapper: one BGR camera frame in, one LandmarkFrame out.

Owner: Person 1.

Uses the MediaPipe Tasks API (Pose Landmarker + Gesture Recognizer). The
Gesture Recognizer also returns the 21 hand landmarks, so we don't run a
separate Hand Landmarker. Run `python tools/download_models.py` first.
"""

import cv2
import mediapipe as mp
from mediapipe.tasks.python import BaseOptions, vision

from shared import config
from shared.landmarks import Hand, LandmarkFrame


class PoseTracker:
    def __init__(self, num_poses: int = 1, num_hands: int = 2):
        for path in (config.POSE_MODEL, config.GESTURE_MODEL):
            if not path.exists():
                raise FileNotFoundError(f"{path} missing. Run: python tools/download_models.py")

        self._pose = vision.PoseLandmarker.create_from_options(vision.PoseLandmarkerOptions(
            base_options=BaseOptions(model_asset_path=str(config.POSE_MODEL)),
            running_mode=vision.RunningMode.VIDEO,
            num_poses=num_poses,
        ))
        self._gestures = vision.GestureRecognizer.create_from_options(vision.GestureRecognizerOptions(
            base_options=BaseOptions(model_asset_path=str(config.GESTURE_MODEL)),
            running_mode=vision.RunningMode.VIDEO,
            num_hands=num_hands,
        ))
        self._last_ms = -1

    def process(self, bgr_image, timestamp: float) -> LandmarkFrame:
        """`timestamp` is in seconds and must increase between calls."""
        ms = max(int(timestamp * 1000), self._last_ms + 1)  # VIDEO mode needs strictly increasing ms
        self._last_ms = ms

        rgb = cv2.cvtColor(bgr_image, cv2.COLOR_BGR2RGB)
        image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)

        pose_result = self._pose.detect_for_video(image, ms)
        gesture_result = self._gestures.recognize_for_video(image, ms)

        pose = None
        if pose_result.pose_landmarks:
            pose = [(p.x, p.y, p.z, p.visibility or 0.0) for p in pose_result.pose_landmarks[0]]

        hands = []
        for i, landmarks in enumerate(gesture_result.hand_landmarks):
            side = gesture_result.handedness[i][0].category_name if gesture_result.handedness else "Unknown"
            gesture, score = "None", 0.0
            if i < len(gesture_result.gestures) and gesture_result.gestures[i]:
                top = gesture_result.gestures[i][0]
                gesture, score = top.category_name, top.score
            hands.append(Hand(side, [(p.x, p.y, p.z) for p in landmarks], gesture, score))

        return LandmarkFrame(timestamp, pose, hands)

    def close(self):
        self._pose.close()
        self._gestures.close()
