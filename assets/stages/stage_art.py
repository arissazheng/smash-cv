"""Shared toolkit for the retro pixel stage backgrounds.

Owner: Person 4.

Every stage is drawn at 640x360 (half the game's 1280x720) and shown at 2x,
so its pixels match the character sprites. Each make_<stage>.py builds a
Picture and calls save(), which writes <stage>.png and a mock screenshot with
the roster standing on the stage, <stage>_preview.png.

Platform positions come from game/stage.py (platforms()), so the art is drawn
exactly where fighters can stand. tests/test_stage_art.py checks every stage.
"""

from pathlib import Path
import sys

import cv2
import numpy as np

W, H = 640, 360
HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
CHARACTERS = HERE.parent / "characters"

BAYER4 = np.array([[0, 8, 2, 10], [12, 4, 14, 6], [3, 11, 1, 9], [15, 7, 13, 5]]) / 16


def rgb(hex_color: str) -> np.ndarray:
    return np.array([int(hex_color[i:i + 2], 16) for i in (1, 3, 5)], np.uint8)


OUTLINE = rgb("#1d1a24")


class Picture:
    def __init__(self):
        self.px = np.zeros((H, W, 3), np.uint8)

    def rect(self, x0, y0, x1, y1, color, mask=None):
        x0, y0, x1, y1 = max(x0, 0), max(y0, 0), min(x1, W - 1), min(y1, H - 1)
        if x0 > x1 or y0 > y1:
            return
        c = rgb(color) if isinstance(color, str) else color
        self.px[y0:y1 + 1, x0:x1 + 1] = c
        if mask is not None:
            mask[y0:y1 + 1, x0:x1 + 1] = True

    def put(self, x, y, color):
        if 0 <= x < W and 0 <= y < H:
            self.px[y, x] = rgb(color)

    def ellipse(self, cx, cy, rx, ry, color, mask=None):
        ys, xs = np.ogrid[:H, :W]
        inside = ((xs + 0.5 - cx) / rx) ** 2 + ((ys + 0.5 - cy) / ry) ** 2 <= 1
        self.px[inside] = rgb(color)
        if mask is not None:
            mask |= inside
        return inside

    def gradient(self, y0, y1, colors, x0=0, x1=W - 1):
        """Vertical gradient through `colors`, ordered-dithered like old consoles."""
        cols = [rgb(c).astype(float) for c in colors]
        steps = len(cols) - 1
        for y in range(y0, y1 + 1):
            t = (y - y0) / max(1, y1 - y0) * steps
            i = min(int(t), steps - 1)
            frac = t - i
            for x in range(x0, x1 + 1):
                self.px[y, x] = cols[i + 1] if frac > BAYER4[y % 4, x % 4] else cols[i]

    def outline(self, mask):
        """Dark 1-pixel border around a shape."""
        grown = mask.copy()
        grown[1:] |= mask[:-1]
        grown[:-1] |= mask[1:]
        grown[:, 1:] |= mask[:, :-1]
        grown[:, :-1] |= mask[:, 1:]
        self.px[grown & ~mask] = OUTLINE



def stone_wall(p: Picture, mask, x0, x1, y0, y1, taper=0.0,
               colors=("#8f8775", "#ddd6c4", "#a59d8a", "#c8c0ad")):
    """Stone blocks with mortar lines, optionally narrowing toward the bottom.

    colors: mortar, light edge, shadow, face.
    """
    mortar, light, shadow, face = colors
    for y in range(y0, y1 + 1):
        inset = int((y - y0) * taper)
        a, b = x0 + inset, x1 - inset
        if a > b:
            break
        row = (y - y0) // 6
        for x in range(a, b + 1):
            joint = (x + (8 if row % 2 else 0)) % 16 == 0
            if (y - y0) % 6 == 5 or joint:
                c = mortar
            elif x - a < 3:
                c = light
            elif b - x < 4 or y > y1 - 4:
                c = shadow
            else:
                c = face
            p.put(x, y, c)
        mask[y, a:b + 1] = True



def platforms(stage_id: str):
    """(main, ledges) from game/stage.py at half scale: each is (x0, top, x1)."""
    sys.path.insert(0, str(ROOT))
    from game.stage import STAGES  # noqa: E402

    stage = STAGES[stage_id]()
    half = lambda r: (r.x // 2, r.top // 2, (r.right - 1) // 2)  # noqa: E731
    return half(stage.main), [half(p) for p in stage.platforms]


def tree(p: Picture, cx, cy, r, rng, colors=("#2d6a37", "#3f8a47", "#62ad5c")):
    dark, mid, light = colors
    p.rect(cx - 1, cy + r - 3, cx + 1, cy + r + 6, "#5b3a26")
    p.ellipse(cx, cy, r * 1.15, r, dark)
    p.ellipse(cx - r * 0.25, cy - r * 0.25, r * 0.8, r * 0.7, mid)
    for _ in range(int(r * 2)):
        a, d = rng.random() * 6.28, rng.random() * r * 0.7
        p.put(int(cx - r * 0.3 + np.cos(a) * d), int(cy - r * 0.35 + np.sin(a) * d * 0.8), light)


def preview(bg: np.ndarray, main, ledges) -> np.ndarray:
    """The stage at game size with the roster standing on it."""
    scene = cv2.cvtColor(bg, cv2.COLOR_BGR2BGRA)
    mid = lambda x0, x1: (x0 + x1) // 2  # noqa: E731
    cast = [  # (character, view, feet x, feet y) in stage pixels
        ("efros", "right", mid(ledges[0][0], ledges[0][2]), ledges[0][1]),
        ("ng", "right", main[0] + 80, main[1]),
        ("liu", "front", mid(ledges[2][0], ledges[2][2]), ledges[2][1]),
        ("lyons", "left", main[2] - 80, main[1]),
        ("oski", "left", mid(ledges[1][0], ledges[1][2]), ledges[1][1]),
    ]
    for name, view, fx, fy in cast:
        sprite = cv2.imread(str(CHARACTERS / name / "views" / f"{view}.png"), cv2.IMREAD_UNCHANGED)
        if sprite is None:
            continue
        h, w = sprite.shape[:2]
        x, y = fx - w // 2, fy - h
        region = scene[y:y + h, x:x + w]
        alpha = sprite[:, :, 3:4] / 255.0
        region[:] = (sprite * alpha + region * (1 - alpha)).astype(np.uint8)
    big = cv2.resize(scene, (W * 2, H * 2), interpolation=cv2.INTER_NEAREST)
    return big



def save(name: str, p: Picture, main, ledges) -> None:
    bg = cv2.cvtColor(p.px, cv2.COLOR_RGB2BGR)
    cv2.imwrite(str(HERE / f"{name}.png"), bg)
    cv2.imwrite(str(HERE / f"{name}_preview.png"), preview(bg, main, ledges))
    print(f"wrote {name}.png and {name}_preview.png in {HERE}")


def line(p: Picture, x0, y0, x1, y1, color, width=1):
    """A straight line `width` pixels thick."""
    steps = max(abs(x1 - x0), abs(y1 - y0), 1)
    for i in range(steps + 1):
        x = round(x0 + (x1 - x0) * i / steps)
        y = round(y0 + (y1 - y0) * i / steps)
        p.rect(x - width // 2, y - width // 2, x + (width - 1) // 2, y + (width - 1) // 2, color)


# 3x5 pixel font for signs and inscriptions ("#" = ink).
GLYPHS = {
    "A": ["###", "#.#", "###", "#.#", "#.#"], "E": ["###", "#..", "##.", "#..", "###"],
    "G": ["###", "#..", "#.#", "#.#", "###"], "H": ["#.#", "#.#", "###", "#.#", "#.#"],
    "L": ["#..", "#..", "#..", "#..", "###"], "O": ["###", "#.#", "#.#", "#.#", "###"],
    "R": ["##.", "#.#", "##.", "#.#", "#.#"], "S": ["###", "#..", "###", "..#", "###"],
    "T": ["###", ".#.", ".#.", ".#.", ".#."], "V": ["#.#", "#.#", "#.#", "#.#", ".#."],
    "Y": ["#.#", "#.#", ".#.", ".#.", ".#."], " ": ["...", "...", "...", "...", "..."],
}


def text(p: Picture, x, y, message: str, color):
    """Pixel text, 4 pixels per letter, top-left at (x, y)."""
    for i, ch in enumerate(message.upper()):
        for dy, row in enumerate(GLYPHS[ch]):
            for dx, cell in enumerate(row):
                if cell == "#":
                    p.put(x + i * 4 + dx, y + dy, color)


def text_width(message: str) -> int:
    return len(message) * 4 - 1
