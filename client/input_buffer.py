"""Preserve one-shot controller events when polling faster than network sends."""

from __future__ import annotations

from collections import deque
from network.protocol import ATTACKS, MAX_ACTIONS


class InputBuffer:
    def __init__(self):
        self.reset()

    def reset(self):
        self.held = {"move_x": 0.0, "crouch": False}
        self.actions = deque()
        self.sample_seq = 0
        self.event_seq = 0

    def capture(self, state, allow_actions=True):
        self.held = {"move_x": state.move_x, "crouch": bool(state.crouch)}
        attack = state.attack if state.attack in ATTACKS else None
        if allow_actions and (state.jump or attack):
            if len(self.actions) >= 32:
                raise ConnectionError("input connection is stalled")
            self.actions.append({"id": self.event_seq, "jump": bool(state.jump), "attack": attack})
            self.event_seq += 1

    def message(self, match_id):
        actions = [self.actions.popleft() for _ in range(min(MAX_ACTIONS, len(self.actions)))]
        packet = {"type": "input", "match_id": match_id, "seq": self.sample_seq,
                  "held": self.held.copy(), "actions": actions}
        self.sample_seq += 1
        return packet
