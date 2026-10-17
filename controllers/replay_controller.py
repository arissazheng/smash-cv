"""Recorded session -> ControllerState, played back in real time.

Owner: Person 2.

This replaces a keyboard for testing: the game pair can play back recorded
gestures at a desk, and the frames still go through the real gesture
recognizer.
"""

from dataclasses import replace
from pathlib import Path
import time

from gestures.recognizer import GestureRecognizer
from gestures.recording import read_recording
from shared.controller_state import ControllerState
from vision.calibration import Calibration

LOOP_GAP = 0.1  # seconds of nothing between loops


class ReplayController:
    def __init__(self, path: Path, calibration: Calibration, player_id: int = 0, loop: bool = True,
                 clock=time.monotonic):
        self.header, self.frames = read_recording(path)
        if not self.frames:
            raise ValueError(f"{path} has no frames")
        self.recognizer = GestureRecognizer(calibration, player_id)
        self.loop = loop
        self._clock = clock
        self._start = clock()
        self._t0 = self.frames[0].timestamp
        self._duration = self.frames[-1].timestamp - self._t0
        self._index = 0
        self._loop_base = 0.0  # playback time at which the current loop started
        self._held = ControllerState(player_id=player_id)

    @property
    def finished(self) -> bool:
        return not self.loop and self._index >= len(self.frames)

    def poll(self) -> ControllerState:
        elapsed = self._clock() - self._start
        result = None

        # Feed every frame whose time has come; keep events from any of them.
        while True:
            if self._index >= len(self.frames):
                if not self.loop:
                    break
                self._index = 0
                self._loop_base += self._duration + LOOP_GAP
            frame = self.frames[self._index]
            playback_t = self._loop_base + frame.timestamp - self._t0
            if playback_t > elapsed:
                break
            # Timestamps keep increasing across loops, as the recognizer expects.
            state = self.recognizer.update(replace(frame, timestamp=self._t0 + playback_t))
            result = state if result is None else _merge(result, state)
            self._index += 1

        if result is None:
            return self._held
        self._held = replace(result, jump=False, attack=None, taunt=False, pause=False)
        return result


def _merge(earlier: ControllerState, later: ControllerState) -> ControllerState:
    """Latest held values, but keep any event that fired in an earlier frame."""
    return replace(
        later,
        jump=earlier.jump or later.jump,
        attack=later.attack or earlier.attack,
        taunt=earlier.taunt or later.taunt,
        pause=earlier.pause or later.pause,
    )
