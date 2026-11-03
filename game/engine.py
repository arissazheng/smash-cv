"""Authoritative, headless simulation; Game preserves the local-play adapter."""

from __future__ import annotations

from typing import Mapping, Optional

from game.combat import resolve_hits
from game.events import KO, Disconnect, GameEvent, GameOver
from game.fighter import Fighter
from game.stage import Stage, battlefield
from shared import config
from shared.controller_state import ControllerState
from shared import protocol

DT = 1.0 / config.SIMULATION_HZ


class GameWorld:
    """The server supplies inputs; the world never polls devices or reads time."""

    def __init__(self, player_ids=None, stage: Optional[Stage] = None,
                 stocks: int = 2, match_id: str = "local"):
        ids = list([0, 1] if player_ids is None else player_ids)
        if not 2 <= len(ids) <= 4 or len(set(ids)) != len(ids):
            raise ValueError("a match requires 2–4 distinct player IDs")
        if stocks < 1:
            raise ValueError("stocks must be positive")
        self.stage = stage or battlefield(len(ids))
        if len(self.stage.spawns) < len(ids):
            raise ValueError("not enough stage spawn points")
        self.fighters = [Fighter(pid, *self.stage.spawns[i], stocks=stocks,
                                 facing=1 if i < len(ids) / 2 else -1)
                         for i, pid in enumerate(ids)]
        self.match_id = match_id
        self.tick_number = 0
        self.phase = "playing"
        self.winner: int | None = None  # None after a draw
        self.result = None              # "win" or "draw" once finished
        self.events: list[GameEvent] = []  # what happened during the latest tick

    @property
    def time(self) -> float:
        """Seconds of match time; snapshots and events are stamped with it."""
        return self.tick_number * DT

    def step(self, inputs: Mapping[int, ControllerState]) -> None:
        self._advance(inputs, DT)

    def _advance(self, inputs, dt):
        self.events = []
        if self.phase != "playing":
            return
        self.tick_number += 1
        for f in self.fighters:
            if f.stocks > 0:
                f.apply_input(inputs.get(f.player_id, ControllerState(player_id=f.player_id)))
                f.step(dt, self.stage)
        self.events += resolve_hits(self.fighters)
        self._check_blast_zones()

    def _check_blast_zones(self) -> None:
        for i, f in enumerate(self.fighters):
            if f.stocks <= 0 or self.stage.blast_zone.collidepoint(f.x, f.y):
                continue
            f.stocks -= 1
            self.events.append(KO(f.player_id, f.stocks, f.x, f.y))
            if f.stocks > 0:
                f.respawn(self.stage.spawns[i])
        self._check_result()

    def eliminate(self, player_id: int) -> None:
        """Server disconnect policy: remove the player from the current match."""
        if self.phase == "finished":
            return
        for f in self.fighters:
            if f.player_id == player_id and f.stocks > 0:
                f.stocks = 0
                f.attack = None
                self.events.append(Disconnect(player_id))
        self._check_result()

    def _check_result(self):
        if self.phase == "finished":
            return
        alive = [f for f in self.fighters if f.stocks > 0]
        if len(alive) <= 1:
            self.phase = "finished"
            self.winner = alive[0].player_id if alive else None
            self.result = "win" if alive else "draw"
            self.events.append(GameOver(self.winner))

    def snapshot(self) -> dict:
        """The `snapshot` message for browsers (see shared/protocol.py)."""
        return protocol.snapshot(self.fighters, self.tick_number, self.time)


class Game(GameWorld):
    """Compatibility wrapper for the original local camera/replay vs CPU mode."""

    def __init__(self, stage: Optional[Stage] = None, stocks: int = 2, camera=None):
        super().__init__(stage=stage, stocks=stocks)
        self.controllers = []
        self.camera = camera
        self.paused = False

    def set_controllers(self, controllers: list) -> None:
        if len(controllers) != len(self.fighters):
            raise ValueError("one controller is required per fighter")
        self.controllers = controllers

    def tick(self, dt: float) -> None:
        states = [c.poll() for c in self.controllers]
        if any(s.pause for s in states):
            self.paused = not self.paused
        if self.paused:
            self.events = []  # nothing happens while paused
        else:
            self._advance({f.player_id: s for f, s in zip(self.fighters, states)}, dt)

    def run(self) -> None:
        # Presentation is imported only by this legacy local entry point.
        import pygame
        from ui import hud, render

        pygame.init()
        screen = pygame.display.set_mode((config.SCREEN_WIDTH, config.SCREEN_HEIGHT))
        clock = pygame.time.Clock()
        accumulator = 0.0
        running = True
        try:
            while running:
                elapsed = min(clock.tick(config.GAME_FPS) / 1000.0, 0.1)
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        running = False
                accumulator += elapsed
                while accumulator >= DT:
                    self.tick(DT)
                    accumulator -= DT
                render.draw_stage(screen, self.stage)
                for f in self.fighters:
                    if f.stocks > 0:
                        render.draw_fighter(screen, f)
                hud.draw_hud(screen, self.fighters)
                if self.camera is not None:
                    hud.draw_camera_preview(screen, self.camera)
                if self.paused:
                    hud.draw_banner(screen, "PAUSED")
                elif self.phase == "finished":
                    subtitle = f"P{self.winner + 1} wins" if self.winner is not None else "Draw"
                    hud.draw_banner(screen, "GAME!", subtitle)
                pygame.display.flip()
        finally:
            pygame.quit()
