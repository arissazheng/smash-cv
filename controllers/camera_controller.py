"""Live webcam -> ControllerState.

Owners: Person 1 + Person 2.

The camera runs at ~30 fps and the game polls at 60 fps. The recognizer runs
once per new camera frame; between frames, poll() repeats the held values
(move_x, crouch, shield) but never repeats an edge-triggered event.
"""

from dataclasses import replace

from gestures.recognizer import GestureRecognizer
from shared.controller_state import ControllerState
from vision.calibration import Calibration
from vision.camera import CameraSource


class CameraController:
    def __init__(self, camera: CameraSource, calibration: Calibration, player_id: int = 0):
        self.camera = camera
        self.recognizer = GestureRecognizer(calibration, player_id)
        self._last_t = None
        self._held = ControllerState(player_id=player_id)

    def poll(self) -> ControllerState:
        _, frame = self.camera.latest()
        if frame is None or frame.timestamp == self._last_t:
            return self._held
        self._last_t = frame.timestamp
        state = self.recognizer.update(frame)
        self._held = replace(state, jump=False, attack=None, taunt=False, pause=False)
        return state
