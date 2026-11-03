"""Memorial Glade stage background in retro pixel art.

Owner: Person 4.

    python assets/stages/make_memorial_glade.py

Writes, next to this file:
    memorial_glade.png           640x360, drawn at 2x in the game (1280x720)
    memorial_glade_preview.png   1280x720 mock screenshot with the roster on the stage

The play area matches battlefield() in game/stage.py at half scale: the main
island top is y=260 from x=120 to 519, and the three ledges sit at y=190
(x 170-259 and 380-469) and y=125 (x 275-364). If you move platforms there,
move them here too.
"""

from pathlib import Path

import cv2
import numpy as np

W, H = 640, 360
HERE = Path(__file__).resolve().parent
CHARACTERS = HERE.parent / "characters"
rng = np.random.default_rng(7)  # fixed seed: same picture every run

# Play-area geometry (half of game/stage.py battlefield()).
MAIN = (120, 260, 519)                                  # x0, top, x1
LEDGES = [(170, 190, 259), (380, 190, 469), (275, 125, 364)]

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


def sky(p: Picture):
    p.gradient(0, 235, ["#3d7fd6", "#5596e2", "#72ade9", "#93c4f0", "#b7dbf6"])
    for cx, cy, s in [(90, 58, 1.0), (250, 34, 0.8), (585, 66, 1.1), (360, 92, 0.6)]:
        for dx, dy, r in [(-14, 3, 9), (0, 0, 12), (14, 2, 10), (26, 5, 7), (-24, 6, 6)]:
            p.ellipse(cx + dx * s, cy + dy * s, r * s * 1.4, r * s, "#f4f8fc")
        p.rect(int(cx - 30 * s), int(cy + 6 * s), int(cx + 32 * s), int(cy + 8 * s), "#d7e7f4")


def hills(p: Picture):
    xs = np.arange(W)
    ridge = (192 + 9 * np.sin(xs / 64) + 5 * np.sin(xs / 23 + 1.3) + 3 * np.sin(xs / 9)).astype(int)
    for x in range(W):
        p.rect(x, ridge[x], x, 240, "#7da593")
        p.put(x, ridge[x], "#94b9a7")
        for y in range(ridge[x] + 3, 240, 3):  # distant trees speckled on the slope
            if rng.random() < 0.18:
                p.put(x, y, "#668f7c")


def tile_roof(p: Picture, x0, x1, y_top, y_bottom, slope=6):
    for y in range(y_top, y_bottom + 1):
        inset = (y_bottom - y) * slope // max(1, y_bottom - y_top)
        p.rect(x0 + inset, y, x1 - inset, y, "#c6603d" if (y - y_top) % 3 else "#a8492d")
    p.rect(x0, y_bottom, x1, y_bottom, "#8e3c25")


def windows(p: Picture, x0, x1, rows, step=8):
    for y in rows:
        for x in range(x0 + 4, x1 - 4, step):
            p.rect(x, y, x + 2, y + 4, "#7f96ad")
            p.rect(x, y, x + 2, y, "#5a6d84")


def buildings(p: Picture):
    # Left: long halls with red tile roofs
    p.rect(8, 197, 152, 238, "#ede4d1")
    p.rect(8, 233, 152, 238, "#d6cbb3")
    tile_roof(p, 4, 156, 186, 196)
    windows(p, 8, 152, [203, 214, 225])
    p.rect(150, 203, 296, 238, "#e8dfcb")
    p.rect(150, 233, 296, 238, "#d1c6ae")
    tile_roof(p, 146, 300, 193, 202)
    windows(p, 150, 296, [208, 219])

    # Right: big classical library with columns and a red roof
    p.rect(472, 190, 639, 238, "#efe8d6")
    tile_roof(p, 466, 645, 177, 189, slope=8)
    p.rect(472, 190, 639, 193, "#fbf6ea")                  # cornice
    for x in range(478, 640, 8):
        p.rect(x, 196, x + 3, 230, "#f7f2e6")              # columns
        p.rect(x + 4, 196, x + 7, 230, "#b9ae98")          # shadow between them
    p.rect(472, 230, 639, 238, "#d6cbb3")                  # steps
    p.rect(472, 233, 639, 233, "#c2b79f")


def campanile(p: Picture, cx=445):
    left, right = cx - 11, cx + 11
    # Shaft
    p.rect(left, 104, right, 238, "#e2ddd1")
    p.rect(left, 104, left + 3, 238, "#f1ede4")
    p.rect(right - 4, 104, right, 238, "#c3bdb0")
    p.rect(left + 5, 108, left + 5, 236, "#cfc9bb")        # pilasters
    p.rect(right - 6, 108, right - 6, 236, "#cfc9bb")
    # Clock
    p.ellipse(cx + 0.5, 128.5, 6.2, 6.2, "#9a9488")
    p.ellipse(cx + 0.5, 128.5, 5.0, 5.0, "#f8f6f0")
    p.rect(cx, 124, cx, 128, "#2d2d35")
    p.rect(cx, 128, cx + 3, 128, "#2d2d35")
    # Belfry with three arched openings
    p.rect(left - 1, 74, right + 1, 104, "#e8e3d8")
    p.rect(right - 3, 74, right + 1, 104, "#c8c2b5")
    p.rect(left - 2, 102, right + 2, 104, "#f6f2ea")       # ledge under the belfry
    for ax in (left + 2, cx - 2, right - 6):
        p.rect(ax, 81, ax + 4, 98, "#3e4150")
        p.put(ax, 81, "#e8e3d8")
        p.put(ax + 4, 81, "#e8e3d8")
    p.rect(left - 3, 70, right + 3, 73, "#f6f2ea")         # cornice
    p.rect(left - 3, 73, right + 3, 73, "#cfc9bb")
    for px in (left - 3, right + 2):                       # corner pinnacles
        p.rect(px, 63, px + 1, 69, "#e8ece6")
    # Spire
    for y in range(22, 70):
        half = (y - 22) * 12 // 48
        p.rect(cx - half, y, cx, y, "#eef1ec")
        p.rect(cx + 1, y, cx + half, y, "#c5ccc5")
    p.rect(cx, 12, cx, 21, "#7d8079")                      # finial
    p.put(cx, 13, "#d9b54a")


def tree(p: Picture, cx, cy, r):
    p.rect(cx - 1, cy + r - 3, cx + 1, cy + r + 6, "#5b3a26")
    p.ellipse(cx, cy, r * 1.15, r, "#2d6a37")
    p.ellipse(cx - r * 0.25, cy - r * 0.25, r * 0.8, r * 0.7, "#3f8a47")
    for _ in range(int(r * 2)):
        a, d = rng.random() * 6.28, rng.random() * r * 0.7
        p.put(int(cx - r * 0.3 + np.cos(a) * d), int(cy - r * 0.35 + np.sin(a) * d * 0.8), "#62ad5c")


def trees(p: Picture):
    for cx, cy, r in [(36, 224, 13), (118, 226, 11), (176, 219, 15), (222, 225, 11), (300, 214, 19),
                      (344, 221, 16), (392, 212, 21), (420, 226, 10), (512, 224, 14), (598, 227, 12)]:
        tree(p, cx, cy, r)


def lawn(p: Picture):
    # Muted compared with the play area, so the island stands out
    p.gradient(234, 359, ["#9bbd84", "#86ad6e", "#73995d", "#62874f"])
    for y in range(242, 360, 12):                          # faint mowing stripes
        p.rect(0, y, W - 1, y + 4, (p.px[y, :1].astype(int) * 1.03).clip(0, 255).astype(np.uint8)[0])
    for _ in range(500):                                   # grass texture
        x, y = rng.integers(0, W), rng.integers(238, H)
        p.put(int(x), int(y), "#5a7f47" if rng.random() < 0.6 else "#a8c792")
    # Students on picnic blankets
    blankets = ["#e86a6a", "#6a9ee8", "#f2d16b", "#f4f4f4", "#b48ee0"]
    for x, y in [(28, 244), (82, 251), (585, 246), (610, 256), (548, 252), (50, 300), (600, 312), (16, 338)]:
        color = blankets[int(rng.integers(0, len(blankets)))]
        p.rect(x, y, x + 9, y + 3, color)
        p.rect(x + 2, y + 1, x + 6, y + 1, "#2a1f1a")      # someone lying on it
        p.rect(x + 7, y, x + 8, y + 1, "#f0c39a")


def stone_wall(p: Picture, mask, x0, x1, y0, y1, taper=0.0):
    """Granite blocks with mortar lines, optionally narrowing toward the bottom."""
    for y in range(y0, y1 + 1):
        inset = int((y - y0) * taper)
        a, b = x0 + inset, x1 - inset
        if a > b:
            break
        row = (y - y0) // 6
        for x in range(a, b + 1):
            joint = (x + (8 if row % 2 else 0)) % 16 == 0
            if (y - y0) % 6 == 5 or joint:
                c = "#8f8775"
            elif x - a < 3:
                c = "#ddd6c4"
            elif b - x < 4 or y > y1 - 4:
                c = "#a59d8a"
            else:
                c = "#c8c0ad"
            p.put(x, y, c)
        mask[y, a:b + 1] = True


def grass_top(p: Picture, mask, x0, x1, y, depth=5):
    p.rect(x0, y, x1, y + depth - 2, "#4fb33e", mask)
    p.rect(x0, y, x1, y, "#7ad35a")
    p.rect(x0, y + depth - 1, x1, y + depth - 1, "#2f7d2b", mask)
    for x in range(x0 + 1, x1, 3):                        # grass hanging over the edge
        if rng.random() < 0.45:
            p.put(x, y + depth, "#2f7d2b")
            mask[y + depth, x] = True


def play_area(p: Picture):
    mask = np.zeros((H, W), bool)
    x0, top, x1 = MAIN
    grass_top(p, mask, x0, x1, top, depth=6)
    p.rect(x0, top + 7, x1, top + 8, "#23325e", mask)     # Cal blue and gold trim
    p.rect(x0, top + 9, x1, top + 10, "#fdb515", mask)
    stone_wall(p, mask, x0, x1, top + 11, top + 46, taper=1.6)
    for lx0, ly, lx1 in LEDGES:
        grass_top(p, mask, lx0, lx1, ly, depth=3)
        stone_wall(p, mask, lx0, lx1, ly + 3, ly + 6)
        for cx in (lx0 + 8, lx1 - 10):                     # little stone brackets underneath
            stone_wall(p, mask, cx, cx + 3, ly + 7, ly + 10, taper=0.5)
    p.outline(mask)
    # Tufts poking up from the grass (drawn after the outline so they sit on top)
    for x0_, y_, x1_ in [MAIN] + LEDGES:
        for x in range(x0_ + 2, x1_ - 1, 5):
            if rng.random() < 0.5:
                p.put(x, y_ - 1, "#7ad35a")


def build() -> np.ndarray:
    p = Picture()
    sky(p)
    hills(p)
    buildings(p)
    campanile(p)
    trees(p)
    lawn(p)
    play_area(p)
    return cv2.cvtColor(p.px, cv2.COLOR_RGB2BGR)


def preview(bg: np.ndarray) -> np.ndarray:
    """The stage at game size with the roster standing on it."""
    scene = cv2.cvtColor(bg, cv2.COLOR_BGR2BGRA)
    cast = [  # (character, view, feet x, feet y) in stage pixels
        ("efros", "right", 214, LEDGES[0][1]), ("ng", "right", 200, MAIN[1]),
        ("liu", "front", 320, LEDGES[2][1]), ("lyons", "left", 440, MAIN[1]),
        ("oski", "left", 425, LEDGES[1][1]),
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


def main():
    bg = build()
    cv2.imwrite(str(HERE / "memorial_glade.png"), bg)
    cv2.imwrite(str(HERE / "memorial_glade_preview.png"), preview(bg))
    print(f"wrote memorial_glade.png and memorial_glade_preview.png in {HERE}")


if __name__ == "__main__":
    main()
