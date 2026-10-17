"""Background thread: webcam -> PoseTracker -> latest LandmarkFrame.

Owner: Person 1.

The game loop never waits on the camera. It asks for the latest result, which
the thread keeps overwriting.
"""

import threading
import time

import cv2

from shared import config
from shared.landmarks import LandmarkFrame
from vision.pose import PoseTracker
from vision.smoothing import LandmarkSmoother


class CameraSource:
    def __init__(self, camera_index: int = config.CAMERA_INDEX, smooth: bool = True):
        self._cap = cv2.VideoCapture(camera_index)
        if not self._cap.isOpened():
            raise RuntimeError(f"could not open camera {camera_index}")
        self._cap.set(cv2.CAP_PROP_FRAME_WIDTH, config.CAMERA_WIDTH)
        self._cap.set(cv2.CAP_PROP_FRAME_HEIGHT, config.CAMERA_HEIGHT)

        self._tracker = PoseTracker()
        self._smoother = LandmarkSmoother() if smooth else None
        self._lock = threading.Lock()
        self._image = None
        self._frame: LandmarkFrame | None = None
        self.fps = 0.0
        self.latency_ms = 0.0  # capture -> landmarks ready
        self._running = False
        self._thread = threading.Thread(target=self._run, daemon=True)

    def start(self) -> "CameraSource":
        self._running = True
        self._thread.start()
        return self

    def _run(self):
        last = time.monotonic()
        while self._running:
            ok, image = self._cap.read()
            if not ok:
                time.sleep(0.01)
                continue
            captured = time.monotonic()
            image = cv2.flip(image, 1)  # mirror, so leaning right moves you right on screen
            frame = self._tracker.process(image, captured)
            if self._smoother:
                frame = self._smoother(frame)

            now = time.monotonic()
            with self._lock:
                self._image, self._frame = image, frame
                self.latency_ms = (now - captured) * 1000
                self.fps = 0.9 * self.fps + 0.1 * (1.0 / max(now - last, 1e-6))
            last = now

    def latest(self) -> tuple:
        """Returns (bgr_image, LandmarkFrame); both None until the first frame is processed."""
        with self._lock:
            return self._image, self._frame

    def stop(self):
        self._running = False
        if self._thread.is_alive():
            self._thread.join(timeout=1.0)
        self._cap.release()
        self._tracker.close()
