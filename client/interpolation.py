"""Interpolate authoritative positions; never run client-side combat/physics."""

from __future__ import annotations

from collections import deque
from dataclasses import replace

from shared import config


class SnapshotBuffer:
    def __init__(self, delay=2 / config.SNAPSHOT_HZ):
        self.delay = delay
        self.frames = deque(maxlen=32)

    def push(self, view, received_at):
        if self.frames and self.frames[-1][0].match_id != view.match_id:
            self.frames.clear()
        if self.frames and view.tick < self.frames[-1][0].tick:
            return
        self.frames.append((view, received_at))

    def sample(self, now):
        if not self.frames:
            return None
        latest, received_at = self.frames[-1]
        if latest.phase != "playing":
            return latest
        target = min(latest.tick, latest.tick + (now - received_at - self.delay) * config.SIMULATION_HZ)
        earlier = self.frames[0][0]
        later = latest
        for frame, _ in self.frames:
            if frame.tick <= target:
                earlier = frame
            if frame.tick >= target:
                later = frame
                break
        span = later.tick - earlier.tick
        alpha = max(0.0, min(1.0, (target - earlier.tick) / span)) if span > 0 else 1.0
        old = {f.player_id: f for f in earlier.fighters}
        new = {f.player_id: f for f in later.fighters}
        fighters = []
        for current in latest.fighters:
            a, b = old.get(current.player_id), new.get(current.player_id)
            if (a is None or b is None or a.life_id != b.life_id
                    or b.life_id != current.life_id or current.stocks <= 0):
                fighters.append(current)
            else:
                fighters.append(replace(current, x=a.x + (b.x - a.x) * alpha,
                                         y=a.y + (b.y - a.y) * alpha))
        return replace(latest, fighters=tuple(fighters))
