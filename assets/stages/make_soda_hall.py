"""Soda Hall stage background in retro pixel art.

Owner: Person 4.

    python assets/stages/make_soda_hall.py

Le Roy Ave outside Soda Hall: the checkered gray-green tile facade with its
big arched openings, the palm tree, red street trees, power lines, and the
traffic-light arm with its street sign. Fighters stand on the sidewalk, the
traffic-light arm and the building's arch sills. Platforms come from
soda_hall() in game/stage.py.
"""

import numpy as np

from stage_art import H, W, Picture, line, platforms, save, stone_wall, text, text_width

rng = np.random.default_rng(31)
MAIN, LEDGES = platforms("soda_hall")
ARM, SILL_LOW, SILL_HIGH = LEDGES
PLATFORM_TOPS = {"#d9d7d2", "#6d6a72"}  # concrete sills and sidewalk, the signal arm; tests check these

TILES = ["#6f7a76", "#7d8985", "#5f6965", "#8e9995", "#56605c", "#68736f"]
CONCRETE, CONCRETE_SHADE, CONCRETE_TOP = "#bdbab4", "#9a978f", "#d9d7d2"


def sky(p: Picture):
    p.gradient(0, 262, ["#3f86e0", "#5a9ae7", "#7cb2ee", "#a3cbf3"])
    for y0, sag in [(52, 18), (70, 22), (205, 14)]:                         # power lines
        for x in range(W):
            t = x / (W - 1)
            p.put(x, int(y0 + sag * 4 * t * (1 - t) + x * 0.04), "#2b2f38")


def neighbors(p: Picture):
    p.rect(150, 120, 262, 262, "#d6c4a4")                                  # beige building down the street
    for y in range(128, 255, 14):
        p.rect(150, y, 262, y + 2, "#bba887")                              # balconies
        for x in range(158, 256, 16):
            p.rect(x, y + 5, x + 8, y + 11, "#7c8a92")


def soda_hall(p: Picture):
    x0, x1, y0, y1 = 300, W - 1, 64, 262
    for y in range(y0, y1 + 1, 4):                                         # checkered tiles
        for x in range(x0, x1 + 1, 4):
            p.rect(x, y, x + 3, y + 3, TILES[int(rng.integers(0, len(TILES)))])
    p.rect(x0, y0 - 4, x1, y0 - 1, "#5a6460")                               # roof edge
    for x in range(x0, x1 + 1, 6):                                         # rooftop railing
        p.rect(x, y0 - 9, x, y0 - 5, "#c9cfd2")
    p.rect(x0, y0 - 10, x1, y0 - 10, "#c9cfd2")
    for y in (SILL_HIGH[1] + 7, SILL_LOW[1] + 7, 245):                     # floor lines with the maroon trim
        p.rect(x0, y, x1, y + 1, "#3f4744")
        p.rect(x0, y + 3, x1, y + 3, "#6a3a3d")
    # Big arched openings on the upper floors, sitting on the sills
    for sx0, sy, sx1 in (SILL_LOW, SILL_HIGH):
        for ax in range(sx0 + 6, sx1 - 22, 36):
            p.rect(ax, sy - 34, ax + 26, sy - 1, "#d3dad6")                # lit interior
            p.ellipse(ax + 13.5, sy - 34, 13.5, 12, "#d3dad6")
            p.rect(ax, sy - 34, ax + 3, sy - 1, "#2c3436")                 # shadowed jamb
            p.ellipse(ax + 13.5, sy - 34, 13.5, 12, "#d3dad6")
            p.rect(ax + 16, sy - 26, ax + 22, sy - 10, "#8fb6b8")         # window inside
    for wy in (178, 222):                                                  # window rows
        for wx in range(306, 636, 30):
            if not (SILL_LOW[0] - 4 <= wx <= SILL_LOW[2] and wy < SILL_LOW[1] + 4):
                p.rect(wx, wy, wx + 20, wy + 12, "#3c4a4a")
                p.rect(wx + 1, wy + 1, wx + 19, wy + 11, "#8fb6b8")
                p.rect(wx + 1, wy + 1, wx + 6, wy + 11, "#a9cccd")


def palm(p: Picture, cx=286, top=70, base=262):
    for y in range(top, base + 1):                                         # trunk, curving slightly
        x = int(cx + (base - y) * 0.05)
        p.rect(x - 2, y, x + 2, y, "#8a6a45" if (y // 4) % 2 else "#a07c52")
    crown_x = int(cx + (base - top) * 0.05)
    for angle, length, color in [(-170, 46, "#4f7a3a"), (-150, 52, "#6b9a4a"), (-125, 44, "#4f7a3a"),
                                 (-95, 30, "#6b9a4a"), (-60, 44, "#4f7a3a"), (-30, 52, "#6b9a4a"),
                                 (-10, 46, "#4f7a3a"), (20, 38, "#b8a052"), (160, 38, "#b8a052")]:
        a = np.radians(angle)
        for i in range(length):                                            # drooping frond
            x = crown_x + np.cos(a) * i
            y = top + np.sin(a) * i + (i / length) ** 2 * 22
            p.rect(int(x), int(y), int(x) + 1, int(y) + 1, color)
            if i % 3 == 0:
                p.put(int(x), int(y) + 2, color)
    p.ellipse(crown_x, top + 2, 5, 4, "#7a5a36")


def red_tree(p: Picture, cx, cy, r):
    p.rect(cx - 1, cy, cx + 1, 262, "#4d3426")
    p.ellipse(cx, cy, r * 1.1, r, "#8a2a38")
    p.ellipse(cx - r * 0.2, cy - r * 0.2, r * 0.8, r * 0.7, "#b03a48")
    for _ in range(int(r * 3)):
        a, d = rng.random() * 6.28, rng.random() * r * 0.75
        p.put(int(cx - r * 0.25 + np.cos(a) * d), int(cy - r * 0.3 + np.sin(a) * d * 0.8), "#d8656b")


def street(p: Picture):
    p.rect(0, 252, W - 1, 259, "#a9a7a2")                                  # far sidewalk
    for cx, color in [(330, "#c9ccd2"), (420, "#9aa3ad"), (520, "#c9ccd2"), (600, "#6d7f99")]:
        p.rect(cx - 18, 246, cx + 18, 256, color)                          # parked cars
        p.rect(cx - 12, 241, cx + 10, 246, color)
        p.rect(cx - 10, 242, cx + 8, 245, "#3c4a55")
        for wx in (cx - 11, cx + 11):
            p.ellipse(wx, 257, 3, 3, "#1e1f22")
    p.gradient(260, H - 1, ["#4a4c53", "#3e4046", "#34363b"])                # asphalt
    for x in range(0, W, 26):                                              # crosswalk
        p.rect(x, 330, x + 14, 336, "#d9d9d6")
    p.rect(0, 300, W - 1, 300, "#c9a43a")


def signal(p: Picture):
    pole_x = ARM[0] - 28
    p.rect(pole_x, ARM[1] - 30, pole_x + 6, 262, "#2b2a2e")
    p.rect(pole_x + 1, ARM[1] - 30, pole_x + 2, 262, "#4a4950")
    p.rect(pole_x - 4, 108, pole_x + 10, 110, "#3a3a40")                   # crossbars of the old utility pole
    # Mast arm: the top row is the platform
    p.rect(pole_x, ARM[1], ARM[2], ARM[1], "#6d6a72")
    p.rect(pole_x, ARM[1] + 1, ARM[2], ARM[1] + 4, "#2b2a2e")
    line(p, pole_x + 6, ARM[1] + 14, pole_x + 30, ARM[1] + 4, "#2b2a2e", 2)  # brace
    # Hanging street sign
    sign = "LE ROY AVE"
    sx0 = ARM[0] + 30
    p.rect(sx0 + 6, ARM[1] + 5, sx0 + 6, ARM[1] + 8, "#2b2a2e")
    p.rect(sx0, ARM[1] + 9, sx0 + text_width(sign) + 7, ARM[1] + 19, "#6b2a3a")
    p.rect(sx0 + 1, ARM[1] + 10, sx0 + text_width(sign) + 6, ARM[1] + 10, "#d9c9cf")
    text(p, sx0 + 4, ARM[1] + 12, sign, "#f4eef0")
    # Traffic light hanging from the end of the arm, red lit
    tx = ARM[2] - 14
    p.rect(tx, ARM[1] + 5, tx + 8, ARM[1] + 30, "#1f1f23")
    for i, color in enumerate(["#ff4a3d", "#3a2a1a", "#1d3a24"]):
        p.ellipse(tx + 4.5, ARM[1] + 10 + i * 7, 2.6, 2.6, color)


def sidewalk(p: Picture):
    mask = np.zeros((H, W), bool)
    x0, top, x1 = MAIN
    p.rect(x0, top, x1, top, CONCRETE_TOP, mask)
    p.rect(x0, top + 1, x1, top + 6, CONCRETE, mask)
    for x in range(x0, x1 + 1, 18):                                        # sidewalk seams
        p.rect(x, top + 1, x, top + 6, CONCRETE_SHADE)
    p.rect(x0, top + 7, x1, top + 9, "#8a3a2e", mask)                      # red curb
    stone_wall(p, mask, x0 + 2, x1 - 2, top + 10, top + 34, taper=2.4,
               colors=("#4a4c53", "#6e7078", "#3a3c42", "#5a5c64"))
    for sx0, sy, sx1 in (SILL_LOW, SILL_HIGH):                             # concrete sills
        p.rect(sx0, sy, sx1, sy, CONCRETE_TOP, mask)
        p.rect(sx0, sy + 1, sx1, sy + 4, CONCRETE, mask)
        p.rect(sx0, sy + 5, sx1, sy + 6, CONCRETE_SHADE, mask)
    arm_mask = np.zeros((H, W), bool)
    arm_mask[ARM[1]:ARM[1] + 5, ARM[0] - 28:ARM[2] + 1] = True
    p.outline(mask | arm_mask)


def build() -> Picture:
    p = Picture()
    sky(p)
    neighbors(p)
    soda_hall(p)
    for cx, cy, r in [(176, 214, 26), (232, 224, 20), (268, 232, 14), (560, 214, 18)]:
        red_tree(p, cx, cy, r)
    palm(p)
    street(p)
    signal(p)
    sidewalk(p)
    return p


if __name__ == "__main__":
    save("soda_hall", build(), MAIN, LEDGES)
