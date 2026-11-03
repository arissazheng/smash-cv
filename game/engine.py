"""The game loop.

Owner: Person 3.

Fixed 60 fps timestep. Each tick: poll every controller, apply inputs, step
physics, resolve hits, check blast zones, draw.
"""

import pygame

from game.combat import resolve_hits
from game.events import KO, GameEvent, GameOver
from game.fighter import Fighter
from game.stage import Stage, battlefield
from shared import config
from ui import hud, render


class Game:
    def __init__(self, stage: Stage | None = None, stocks: int = 2, camera=None):
        self.stage = stage or battlefield()
        self.fighters = [
            Fighter(player_id=i, x=sx, y=sy, stocks=stocks, facing=1 if i == 0 else -1)
            for i, (sx, sy) in enumerate(self.stage.spawns)
        ]
        self.controllers = []
        self.camera = camera  # optional CameraSource, for the picture-in-picture view
        self.paused = False
        self.over = False
        self.winner: int | None = None  # None after a draw
        self.tick_count = 0
        self.events: list[GameEvent] = []  # what happened during the latest tick

    def set_controllers(self, controllers: list) -> None:
        """One controller per fighter, each with poll() -> ControllerState."""
        assert len(controllers) == len(self.fighters)
        self.controllers = controllers

    def tick(self, dt: float) -> None:
        self.events = []
        states = [c.poll() for c in self.controllers]
        if any(s.pause for s in states):
            self.paused = not self.paused
        if self.paused or self.over:
            return

        self.tick_count += 1
        for fighter, state in zip(self.fighters, states):
            if fighter.stocks > 0:
                fighter.apply_input(state)
        for fighter in self.fighters:
            if fighter.stocks > 0:
                fighter.step(dt, self.stage)
        self.events += resolve_hits([f for f in self.fighters if f.stocks > 0])
        self._check_blast_zones()

    def _check_blast_zones(self) -> None:
        for i, fighter in enumerate(self.fighters):
            if fighter.stocks <= 0 or self.stage.blast_zone.collidepoint(fighter.x, fighter.y):
                continue
            fighter.stocks -= 1
            self.events.append(KO(fighter.player_id, fighter.stocks, fighter.x, fighter.y))
            if fighter.stocks > 0:
                fighter.respawn(self.stage.spawns[i])
        alive = [f for f in self.fighters if f.stocks > 0]
        if len(alive) <= 1:
            self.over = True
            self.winner = alive[0].player_id if alive else None
            self.events.append(GameOver(self.winner))

    def run(self) -> None:
        pygame.init()
        screen = pygame.display.set_mode((config.SCREEN_WIDTH, config.SCREEN_HEIGHT))
        pygame.display.set_caption("Smash CV")
        clock = pygame.time.Clock()
        dt = 1.0 / config.GAME_FPS

        running = True
        while running:
            for event in pygame.event.get():
                # Closing the window is the only non-camera input.
                if event.type == pygame.QUIT:
                    running = False
            self.tick(dt)

            render.draw_stage(screen, self.stage)
            for fighter in self.fighters:
                render.draw_fighter(screen, fighter)
            hud.draw_hud(screen, self.fighters)
            if self.camera is not None:
                hud.draw_camera_preview(screen, self.camera)
            if self.paused:
                hud.draw_banner(screen, "PAUSED")
            if self.over:
                hud.draw_banner(screen, "GAME!", f"P{self.winner + 1} wins" if self.winner is not None else "Draw")
            pygame.display.flip()
            clock.tick(config.GAME_FPS)
        pygame.quit()
