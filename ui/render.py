"""Drawing the stage and fighters.

Owner: Person 4.

Fighters are colored boxes until sprites exist. Once
assets/characters/<name>/<state>/frame_XX.png is filled in, draw_fighter
switches to the sprite automatically.
"""

import pygame

from shared import config
from ui.animation import SpriteLibrary

PLAYER_COLORS = [(230, 70, 70), (70, 130, 230), (240, 200, 60), (80, 200, 110)]  # Smash P1-P4
SKY, GROUND, PLATFORM = (24, 26, 48), (90, 90, 110), (150, 150, 175)

_sprites = SpriteLibrary(config.ASSETS_DIR / "characters")
_backgrounds: dict[str, pygame.Surface] = {}


def draw_stage(screen: pygame.Surface, stage) -> None:
    if stage.background:
        if stage.background not in _backgrounds:
            image = pygame.image.load(str(config.ASSETS_DIR / "stages" / stage.background)).convert()
            _backgrounds[stage.background] = pygame.transform.smoothscale(image, screen.get_size())
        screen.blit(_backgrounds[stage.background], (0, 0))
    else:
        screen.fill(SKY)
    pygame.draw.rect(screen, GROUND, stage.main)
    for platform in stage.platforms:
        pygame.draw.rect(screen, PLATFORM, platform)


def draw_fighter(screen: pygame.Surface, fighter) -> None:
    color = PLAYER_COLORS[fighter.player_id % len(PLAYER_COLORS)]
    frame = _sprites.frame(fighter.character, fighter.state, fighter.attack_time, fighter.facing)
    if frame is not None:
        screen.blit(frame, frame.get_rect(midbottom=(int(fighter.x), int(fighter.y))))
    else:
        rect = fighter.rect
        pygame.draw.rect(screen, color, rect, border_radius=8)
        eye_x = rect.centerx + fighter.facing * 14
        pygame.draw.circle(screen, (255, 255, 255), (eye_x, rect.top + 20), 6)
        if fighter.shielding:
            pygame.draw.circle(screen, (120, 200, 255), rect.center, 55, 4)

    box = fighter.hitbox()
    if box is not None:
        pygame.draw.rect(screen, (255, 240, 120), box, 2)  # debug: show active hitboxes
