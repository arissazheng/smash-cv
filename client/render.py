"""Replaceable Pygame shape renderer. No simulation or asset dependencies.

Person 4 can replace draw() while keeping MatchView and the client runtime.
"""

from __future__ import annotations

import pygame

from shared import config

COLORS = [(240, 105, 87), (91, 169, 245), (242, 203, 88), (116, 214, 157)]
BG, PANEL, TEXT, MUTED = (19, 25, 39), (30, 39, 57), (235, 240, 248), (146, 162, 184)


class PrototypeRenderer:
    def __init__(self):
        pygame.font.init()
        self.canvas = pygame.Surface((config.SCREEN_WIDTH, config.SCREEN_HEIGHT))
        self.fonts = {size: pygame.font.Font(None, size) for size in (20, 24, 30, 42, 64)}
        self.show_hitboxes = True

    def text(self, label, position, size=24, color=TEXT, center=False):
        surface = self.fonts[size].render(str(label), True, color)
        rect = surface.get_rect(center=position) if center else surface.get_rect(topleft=position)
        self.canvas.blit(surface, rect)

    def draw(self, screen, view, lobby, player_id, countdown=0.0, status="", input_name="keyboard"):
        c = self.canvas
        c.fill(BG)
        self.text("SMASH / CV", (32, 25), 42)
        self.text("MULTIPLAYER ENGINE PROTOTYPE", (34, 65), 20, MUTED)
        self.text(status, (820, 32), 20, MUTED)
        self.text(f"YOU: P{player_id + 1}  |  INPUT: {input_name.upper()}", (820, 60), 20)
        pygame.draw.line(c, PANEL, (32, 102), (1248, 102), 2)

        if view is None:
            self.text("WAITING FOR PLAYERS", (640, 215), 42, center=True)
            self.text(f"{len(lobby['players'])} / {lobby['capacity']} connected", (640, 260), 30, MUTED, True)
            for i, player in enumerate(lobby["players"]):
                color = COLORS[player["player_id"] % len(COLORS)]
                marker = "READY" if player["ready"] else "press ENTER to ready"
                self.text(f"P{player['player_id'] + 1}  {player['name']}  /  {marker}",
                          (640, 325 + i * 45), 30, color, True)
        else:
            for x in range(40, 1280, 80):
                pygame.draw.line(c, PANEL, (x, 125), (x, 565))
            main = pygame.Rect(view.stage.main)
            pygame.draw.rect(c, (74, 91, 116), main, border_radius=5)
            pygame.draw.line(c, (164, 184, 208), main.topleft, main.topright, 4)
            for rect in view.stage.platforms:
                pygame.draw.rect(c, (100, 122, 151), rect, border_radius=4)
            for f in view.fighters:
                if f.stocks <= 0:
                    continue
                color = COLORS[f.player_id % len(COLORS)]
                rect = pygame.Rect(int(f.x - f.width / 2), int(f.y - f.height), f.width, f.height)
                if f.invulnerable:
                    pygame.draw.rect(c, TEXT, rect.inflate(8, 8), 2, border_radius=9)
                pygame.draw.rect(c, color, rect, border_radius=7)
                pygame.draw.rect(c, BG, (rect.centerx + f.facing * 13 - 4, rect.y + 18, 8, 8))
                self.text(f"P{f.player_id + 1}", (rect.centerx, rect.top - 18), 24, color, True)
                if f.hitbox and self.show_hitboxes:
                    attack_color = {"jab": TEXT, "smash": (255, 187, 80),
                                    "special": (100, 237, 231)}.get(f.state, TEXT)
                    pygame.draw.rect(c, attack_color, f.hitbox, 3, border_radius=5)
            if view.phase == "countdown":
                self.banner("GET READY", f"{countdown:.1f}s")
            elif view.phase == "finished":
                title = f"P{view.winner + 1} WINS" if view.winner is not None else "DRAW"
                self.banner(title, "Press R for the next lobby")
            names = {p["player_id"]: p["name"] for p in lobby["players"]}
            slot = 1216 / len(view.fighters)
            for i, f in enumerate(view.fighters):
                x = int(32 + i * slot)
                pygame.draw.rect(c, PANEL, (x, 591, int(slot) - 12, 85), border_radius=8)
                color = COLORS[f.player_id % len(COLORS)] if f.stocks > 0 else MUTED
                label = f"P{f.player_id + 1} {names.get(f.player_id, '')}"
                self.text(label, (x + 16, 602), 24, color)
                self.text(f"{int(f.damage)}%", (x + 16, 628), 42, color)
                self.text(f"{f.stocks} stocks  /  {f.state}", (x + 116, 640), 20, MUTED)

        footer = "A/D or arrows: move   SPACE: jump   J: jab   K: heavy   L: special   TAB: hitboxes   ESC: quit"
        self.text(footer if input_name == "keyboard" else "ENTER: ready   R: rematch   TAB: hitboxes   ESC: quit",
                  (32, 695), 20, MUTED)
        if screen.get_size() == c.get_size():
            screen.blit(c, (0, 0))
        else:
            # Fixed world coordinates are scaled uniformly to a letterboxed window.
            scale = min(screen.get_width() / c.get_width(), screen.get_height() / c.get_height())
            size = (max(1, int(c.get_width() * scale)), max(1, int(c.get_height() * scale)))
            image = pygame.transform.smoothscale(c, size)
            screen.fill(BG)
            screen.blit(image, image.get_rect(center=screen.get_rect().center))

    def banner(self, title, subtitle):
        pygame.draw.rect(self.canvas, PANEL, (350, 270, 580, 130), border_radius=12)
        self.text(title, (640, 315), 64, center=True)
        self.text(subtitle, (640, 368), 24, MUTED, True)
