"""CPU opponent, so one person can test alone.

Owner: Person 3.
"""

from shared.controller_state import ControllerState


class CpuController:
    """Walks toward the target and jabs when close.

    TODO(Person 3): jump back to the stage when off the edge, shield sometimes,
    use smash attacks on high-damage targets.
    """

    def __init__(self, me, target, player_id: int = 1, attack_every: float = 0.8):
        self.me, self.target = me, target
        self.player_id = player_id
        self.attack_every = attack_every
        self._since_attack = 0.0

    def poll(self, dt: float = 1 / 60) -> ControllerState:
        self._since_attack += dt
        dx = self.target.x - self.me.x
        state = ControllerState(player_id=self.player_id)
        if abs(dx) > 70:
            state.move_x = 0.6 if dx > 0 else -0.6
        elif self._since_attack >= self.attack_every:
            state.attack = "jab"
            self._since_attack = 0.0
        return state
