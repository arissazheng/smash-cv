"""Turns a stream of LandmarkFrames into ControllerStates.

Owner: Person 2.

This is where edge-triggering and cooldowns live, so detectors can stay simple
"is it happening right now?" checks.
"""

from typing import Optional

from gestures import detectors
from shared.controller_state import ControllerState
from shared.landmarks import LandmarkFrame
from vision.calibration import Calibration


class GestureRecognizer:
    def __init__(self, calibration: Calibration, player_id: int = 0, attack_cooldown: float = 0.3):
        self.calib = calibration
        self.player_id = player_id
        self.attack_cooldown = attack_cooldown
        self._punch = detectors.PunchDetector()
        self._up_special = detectors.UpSpecialDetector()
        self._grab = detectors.GrabDetector()
        self._taunt = detectors.TauntDetector()
        self._pause = detectors.PauseDetector()
        self._was_hands_up = False
        self._was_special = False
        self._last_attack_t = -1e9

    def update(self, frame: LandmarkFrame) -> ControllerState:
        state = ControllerState(player_id=self.player_id, timestamp=frame.timestamp,
                                pointer=detectors.pointer(frame))
        if frame.pose is None:
            # Nobody in frame: neutral, and forget motion history so we don't fire on return.
            for d in (self._punch, self._up_special, self._grab, self._taunt, self._pause):
                d.reset()
            self._was_hands_up = self._was_special = False
            return state

        c = self.calib
        state.move_x = detectors.lean_move_x(frame, c)
        state.crouch = detectors.is_crouching(frame, c)
        state.shield = detectors.detect_shield(frame, c)

        up = detectors.hands_up(frame, c)
        state.jump = up and not self._was_hands_up
        self._was_hands_up = up

        state.attack = self._attack(frame)
        state.taunt = self._taunt.update(frame, c)
        state.pause = self._pause.update(frame, c)
        return state

    def _attack(self, frame: LandmarkFrame) -> Optional[str]:
        c = self.calib
        punch = self._punch.update(frame, c)  # always update so history stays current
        special_now = detectors.detect_special(frame, c)
        special = special_now and not self._was_special  # edge-triggered
        self._was_special = special_now
        up_special = self._up_special.update(frame, c)
        grab = self._grab.update(frame, c)
        if frame.timestamp - self._last_attack_t < self.attack_cooldown:
            return None

        if special:
            attack = "special"
        elif up_special:
            attack = "up_special"
        elif grab:
            attack = "grab"
        else:
            attack = punch

        if attack:
            self._last_attack_t = frame.timestamp
        return attack
