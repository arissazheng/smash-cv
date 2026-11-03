"""Gateway stage background in retro pixel art.

Owner: Person 4.

    python assets/stages/make_gateway.py

Gateway's atrium: white balconies curving around a skylight, railings, warm
wood walls, round tables, and the orange striped carpet as the main floor.
Platforms come from gateway() in game/stage.py.
"""

import numpy as np

from stage_art import H, W, Picture, platforms, save, stone_wall

rng = np.random.default_rng(11)
MAIN, LEDGES = platforms("gateway")
PLATFORM_TOPS = {"#fbfaf5"}  # top row of every platform; tests check the art against game/stage.py

CEILING = ["#f5f2ec", "#ebe6dd", "#dfd7ca"]
BAND, BAND_SHADE, RECESS = "#fbfaf6", "#d5cec2", "#e6e0d6"
RAIL = "#aaa59c"


def _arc_y(cx, cy, rx, ry, x):
    """Lower edge of an ellipse at column x (None outside it)."""
    t = (x - cx) / rx
    return None if abs(t) >= 1 else cy + ry * (1 - t * t) ** 0.5


def ceiling(p: Picture):
    p.gradient(0, 230, CEILING)
    # Concentric balconies around the skylight, outermost first
    for cy, rx, ry, thick in [(40, 430, 125, 16), (22, 280, 82, 12), (6, 180, 46, 9)]:
        p.ellipse(320, cy, rx, ry, BAND)
        p.ellipse(320, cy - thick, rx - thick, ry - thick, RECESS)
        for x in range(W):
            lower = _arc_y(320, cy, rx, ry, x)
            if lower is not None and 0 <= lower < H:
                p.rect(x, int(lower) - 2, x, int(lower), BAND_SHADE)       # shadow under the balcony
            inner = _arc_y(320, cy - thick, rx - thick, ry - thick, x)
            if inner is not None and 0 <= inner < H:
                if x % 4 == 0:                                             # railing posts
                    p.rect(x, int(inner) - 6, x, int(inner) - 1, RAIL)
                p.put(x, int(inner) - 7, RAIL)                             # handrail
        for _ in range(int(rx / 6)):                                       # recessed lights
            x = int(rng.integers(320 - rx + 20, 320 + rx - 20))
            inner = _arc_y(320, cy - thick, rx - thick, ry - thick, x)
            if inner is not None:
                y = int(rng.integers(max(0, int(inner) - 40), max(1, int(inner) - 10)))
                p.put(x, y, "#fff3cc")
    p.ellipse(320, -8, 120, 26, "#fffdf5")                                 # skylight
    p.ellipse(320, -12, 80, 18, "#ffffff")


def walls(p: Picture):
    for x in range(W):
        top = _arc_y(320, 40, 430, 125, x)
        y0 = int(top) + 1 if top is not None else 0
        for y in range(max(y0, 150), 300):
            seam = x % 12 == 0
            p.px[y, x] = np.array([0xa8, 0x72, 0x3f] if seam else ([0xc8, 0x8e, 0x58] if (x // 6) % 2 else [0xbf, 0x86, 0x51]), np.uint8)
    p.gradient(262, 359, ["#e2a061", "#c98446", "#9a6236"])                # carpet beyond the main floor
    for y in range(264, 360, 7):
        p.rect(0, y, W - 1, y + 2, "#d48f50")


def table(p: Picture, cx, y):
    p.rect(cx - 1, y, cx + 1, y + 10, "#c9b08a")
    p.ellipse(cx + 0.5, y, 12, 3, "#ecdcc0")
    for side in (-1, 1):                                                   # chairs and students
        p.rect(cx + side * 14 - 2, y - 4, cx + side * 14 + 2, y + 8, "#d9c19b")
        p.rect(cx + side * 12 - 1, y - 9, cx + side * 12 + 1, y - 3, ["#3b5a8c", "#b84a4a", "#4c7a50"][int(rng.integers(0, 3))])
        p.rect(cx + side * 12 - 1, y - 12, cx + side * 12 + 1, y - 10, "#f0c39a")


def carpet_floor(p: Picture, mask, x0, x1, y):
    p.rect(x0, y, x1, y, "#fbfaf5", mask)                                  # white trim along the edge
    for row in range(1, 7):
        color = ["#f2ad62", "#e8954a", "#f6bb76", "#d8803a", "#efa356", "#e08a42"][row - 1]
        p.rect(x0, y + row, x1, y + row, color, mask)
    for x in range(x0, x1 + 1, 23):                                        # stripes across the carpet
        p.rect(x, y + 1, x + 9, y + 6, "#e07f38", mask)
    p.rect(x0, y + 7, x1, y + 12, "#f4f1eb", mask)                         # white fascia
    p.rect(x0, y + 12, x1, y + 13, "#cfc8bc", mask)
    stone_wall(p, mask, x0 + 2, x1 - 2, y + 14, y + 34, taper=2.2,
               colors=("#b9b1a3", "#f7f4ee", "#d3ccbf", "#ebe6dd"))


def balcony(p: Picture, mask, x0, x1, y):
    for x in range(x0, x1 + 1, 4):                                         # railing behind
        p.rect(x, y - 7, x, y - 1, RAIL)
    p.rect(x0, y - 8, x1, y - 8, RAIL)
    p.rect(x0, y, x1, y, "#fbfaf5", mask)
    p.rect(x0, y + 1, x1, y + 4, "#f1eee8", mask)
    p.rect(x0, y + 5, x1, y + 6, "#cfc8bc", mask)
    p.rect(x0 + 6, y + 7, x1 - 6, y + 8, "#ddd6ca", mask)                  # curved underside


def build() -> Picture:
    p = Picture()
    ceiling(p)
    walls(p)
    for cx, y in [(28, 252), (612, 252), (150, 258), (480, 258), (300, 256)]:
        table(p, cx, y)
    mask = np.zeros((H, W), bool)
    x0, top, x1 = MAIN
    carpet_floor(p, mask, x0, x1, top)
    for lx0, ly, lx1 in LEDGES:
        balcony(p, mask, lx0, lx1, ly)
    p.outline(mask)
    return p


if __name__ == "__main__":
    save("gateway", build(), MAIN, LEDGES)
