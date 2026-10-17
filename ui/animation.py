"""Loads sprite frames and picks the right one for a fighter's state.

Owner: Person 4.

Expected layout (produced by ui/sprite_pipeline.py):
    assets/characters/<character>/<state>/frame_00.png, frame_01.png, ...
States: idle, run, jump, fall, crouch, shield, hurt, taunt, jab, smash,
special, up_special, grab (see Fighter.state).
"""

from pathlib import Path

import pygame

FRAME_TIME = 1 / 12  # seconds per animation frame
SCALE = 2.0          # TODO(Person 4): per-character scale so everyone is about 90 px tall


class SpriteLibrary:
    def __init__(self, root: Path):
        self.root = root
        self._cache: dict[tuple[str, str], list[pygame.Surface]] = {}

    def _load(self, character: str, state: str) -> list[pygame.Surface]:
        key = (character, state)
        if key not in self._cache:
            folder = self.root / character / state
            frames = []
            for path in sorted(folder.glob("*.png")) if folder.is_dir() else []:
                image = pygame.image.load(str(path))
                if pygame.display.get_init() and pygame.display.get_surface() is not None:
                    image = image.convert_alpha()
                size = (int(image.get_width() * SCALE), int(image.get_height() * SCALE))
                frames.append(pygame.transform.scale(image, size))
            self._cache[key] = frames
        return self._cache[key]

    def frame(self, character: str, state: str, t: float, facing: int) -> pygame.Surface | None:
        """The frame to show `t` seconds into `state`, or None if there are no sprites."""
        frames = self._load(character, state) or self._load(character, "idle")
        if not frames:
            return None
        image = frames[int(t / FRAME_TIME) % len(frames)]
        # TODO(Person 4): sprites are assumed to face right; flip for left.
        return pygame.transform.flip(image, True, False) if facing < 0 else image
