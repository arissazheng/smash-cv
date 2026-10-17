"""Damage %, stocks, banners and the camera preview.

Owner: Person 4.
"""

import cv2
import pygame

from ui.render import PLAYER_COLORS

_fonts: dict[int, pygame.font.Font] = {}


def _font(size: int) -> pygame.font.Font:
    # TODO(Person 4): swap in a Smash-style font from assets/ui/.
    if size not in _fonts:
        _fonts[size] = pygame.font.Font(None, size)
    return _fonts[size]


def _damage_color(damage: float) -> tuple[int, int, int]:
    """White at 0%, through yellow and red, toward dark red, like Smash."""
    t = min(damage / 150, 1.0)
    return (255, int(255 * (1 - t)), int(255 * max(0.0, 1 - 2 * t)))


def draw_hud(screen: pygame.Surface, fighters) -> None:
    w, h = screen.get_size()
    slot = w // (len(fighters) + 1)
    for i, f in enumerate(fighters):
        cx = slot * (i + 1)
        label = _font(28).render(f"P{f.player_id + 1}", True, PLAYER_COLORS[f.player_id % 4])
        screen.blit(label, label.get_rect(center=(cx, h - 95)))
        pct = _font(64).render(f"{int(f.damage)}%", True, _damage_color(f.damage))
        screen.blit(pct, pct.get_rect(center=(cx, h - 55)))
        for s in range(f.stocks):
            pygame.draw.circle(screen, PLAYER_COLORS[f.player_id % 4], (cx - 20 * (f.stocks - 1) // 2 + 20 * s, h - 18), 7)


def draw_banner(screen: pygame.Surface, title: str, subtitle: str = "") -> None:
    w, h = screen.get_size()
    text = _font(140).render(title, True, (255, 255, 255))
    screen.blit(text, text.get_rect(center=(w // 2, h // 2 - 40)))
    if subtitle:
        sub = _font(48).render(subtitle, True, (230, 230, 230))
        screen.blit(sub, sub.get_rect(center=(w // 2, h // 2 + 40)))


def draw_camera_preview(screen: pygame.Surface, camera, width: int = 240) -> None:
    """Small live camera view in the corner so players can see what's being tracked."""
    image, _ = camera.latest()
    if image is None:
        return
    h = int(image.shape[0] * width / image.shape[1])
    small = cv2.cvtColor(cv2.resize(image, (width, h)), cv2.COLOR_BGR2RGB)
    surface = pygame.image.frombuffer(small.tobytes(), (width, h), "RGB")
    screen.blit(surface, (screen.get_width() - width - 10, 10))
