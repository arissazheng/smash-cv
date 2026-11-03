"""Sather Gate stage background in retro pixel art.

Owner: Person 4.

    python assets/stages/make_sather_gate.py

The patina-green iron arch with its starburst crest and "SATHER GATE"
inscription, granite pillars with globe lamps, the red brick plaza and the
trees beyond under a cloudy sky. Fighters stand on the plaza, the two pillar
tops and the crown of the arch. Platforms come from sather_gate() in
game/stage.py.
"""

import numpy as np

from stage_art import H, W, Picture, platforms, save, stone_wall, text, text_width, tree

rng = np.random.default_rng(23)
MAIN, LEDGES = platforms("sather_gate")
PILLAR_L, PILLAR_R, CROWN = LEDGES
PLATFORM_TOPS = {"#e6e1d5", "#8fd0b4"}  # granite tops and the arch's highlight; tests check these

PATINA_DARK, PATINA, PATINA_LIGHT, PATINA_DEEP = "#2e6b5b", "#5fa38c", "#8fd0b4", "#1f4a3f"
GRANITE, GRANITE_LIGHT, GRANITE_SHADE, GRANITE_TOP = "#d9d4c8", "#ece8de", "#b8b2a6", "#e6e1d5"


def sky(p: Picture):
    p.gradient(0, 259, ["#6d7086", "#85869a", "#a3a1b2", "#bfbbc6"])
    for cx, cy, s in [(120, 40, 1.2), (330, 25, 1.0), (520, 60, 1.3), (250, 95, 0.8)]:
        for dx, dy, r in [(-16, 4, 10), (0, 0, 14), (16, 3, 11), (30, 6, 8)]:
            p.ellipse(cx + dx * s, cy + dy * s, r * s * 1.5, r * s, "#9896a8")
            p.ellipse(cx + dx * s - 2, cy + dy * s - 3, r * s * 1.2, r * s * 0.7, "#b4b1c0")


def background(p: Picture):
    trees = ("#1f3a24", "#2f5232", "#4c7649")
    for cx, cy, r in [(40, 110, 70), (130, 70, 60), (600, 120, 60), (520, 170, 40), (250, 200, 22),
                      (390, 195, 26), (330, 205, 18), (450, 200, 20)]:
        p.ellipse(cx, cy, r * 1.15, r, trees[0])
        p.ellipse(cx - r * 0.2, cy - r * 0.2, r * 0.85, r * 0.7, trees[1])
        for _ in range(int(r * 3)):
            a, d = rng.random() * 6.28, rng.random() * r * 0.75
            p.put(int(cx - r * 0.25 + np.cos(a) * d), int(cy - r * 0.3 + np.sin(a) * d * 0.8), trees[2])
    p.rect(232, 205, 282, 235, "#e9e4d8")                                  # building down the path
    p.rect(228, 200, 286, 204, "#b55a3f")
    for x in range(236, 280, 6):
        p.rect(x, 212, x + 2, 226, "#c8c1b1")
    # Path into campus, narrowing into the distance
    for y in range(222, 262):
        half = 20 + (y - 222) * 4
        p.rect(320 - half, y, 320 + half, y, "#8d8a8e" if y % 5 else "#7c797e")
    # Red brick plaza
    for y in range(256, H):
        for x in range(W):
            mortar = y % 4 == 0 or (x + (3 if (y // 4) % 2 else 0)) % 7 == 0
            p.px[y, x] = (0x7a, 0x3a, 0x2b) if mortar else ((0xa5, 0x52, 0x3c) if (x // 7 + y // 4) % 3 else (0x96, 0x4a, 0x36))
    for x in range(200, 440, 30):                                          # gray paving in the middle
        p.rect(x, 262, x + 24, 300, "#7f7a78")


def ironwork_column(p: Picture, x0, x1, y0, y1):
    p.rect(x0, y0, x1, y1, PATINA)
    p.rect(x0, y0, x0 + 1, y1, PATINA_DARK)
    p.rect(x1 - 1, y0, x1, y1, PATINA_DARK)
    cx = (x0 + x1) / 2
    for y in range(y0 + 4, y1 - 3, 8):                                     # scrollwork
        p.ellipse(cx, y + 3, (x1 - x0) / 2 - 2, 3.2, PATINA_DEEP)
        p.ellipse(cx, y + 3, (x1 - x0) / 2 - 4, 1.8, PATINA_LIGHT)


def arch(p: Picture):
    left, right = PILLAR_L[2] + 1, PILLAR_R[0] - 1                         # inner edges of the pillars
    crown_x0, crown_y, crown_x1 = CROWN
    springing = crown_y + 25
    ironwork_column(p, left, left + 13, springing, 262)
    ironwork_column(p, right - 13, right, springing, 262)

    def top_edge(x):
        if crown_x0 <= x <= crown_x1:
            return crown_y
        run = crown_x0 - left if x < crown_x0 else right - crown_x1
        t = (crown_x0 - x if x < crown_x0 else x - crown_x1) / run
        return round(crown_y + 25 * (1 - (1 - min(t, 1) ** 2) ** 0.5))

    for x in range(left, right + 1):
        y = top_edge(x)
        p.rect(x, y, x, y + 15, PATINA)
        p.put(x, y, PATINA_LIGHT)                                          # lit top edge
        p.rect(x, y + 1, x, y + 1, PATINA_DARK)
        p.rect(x, y + 15, x, y + 16, PATINA_DARK)
        p.rect(x, y + 17, x, y + 23, PATINA_DARK)                          # inscription band
        p.put(x, y + 24, PATINA_DEEP)
        if (x - left) % 8 == 4:                                            # ring pattern along the band
            p.ellipse(x + 0.5, y + 8.5, 3.2, 3.2, PATINA_DEEP)
            p.ellipse(x + 0.5, y + 8.5, 1.6, 1.6, PATINA_LIGHT)
    label = "SATHER GATE"
    text(p, 320 - text_width(label) // 2, crown_y + 18, label, PATINA_LIGHT)
    # Crest above the crown: medallion with a starburst between leaves
    for dx in range(-26, 27):
        h = int(7 * (1 - abs(dx) / 27))
        p.rect(320 + dx, crown_y - h, 320 + dx, crown_y - 1, PATINA if abs(dx) % 4 else PATINA_LIGHT)
    p.ellipse(320.5, crown_y - 13, 9, 12, PATINA_DARK)
    p.ellipse(320.5, crown_y - 13, 7, 10, PATINA)
    for dx, dy in [(0, -6), (0, 6), (-5, 0), (5, 0), (-3, -4), (3, -4), (-3, 4), (3, 4), (0, 0)]:
        p.put(320 + dx, crown_y - 13 + dy, PATINA_LIGHT)


def pillar(p: Picture, x0, top, x1):
    cx = (x0 + x1) // 2
    p.rect(x0 + 3, top + 6, x1 - 3, 268, GRANITE)                          # shaft
    p.rect(x0 + 3, top + 6, x0 + 5, 268, GRANITE_LIGHT)
    p.rect(x1 - 7, top + 6, x1 - 3, 268, GRANITE_SHADE)
    p.rect(x0 + 10, top + 24, x1 - 10, top + 52, "#cfc9bc")               # carved panel
    p.rect(x0 + 10, top + 24, x1 - 10, top + 24, GRANITE_SHADE)
    p.rect(cx - 2, top + 30, cx + 2, top + 46, "#c3bdb0")                  # relief figure
    p.ellipse(cx + 0.5, top + 30, 3, 3, "#c3bdb0")
    for y in (top + 70, top + 74):                                         # inscription lines
        p.rect(cx - 12, y, cx + 12, y, "#a59f93")
    p.rect(x0 - 2, 252, x1 + 2, 268, GRANITE_SHADE)                        # plinth
    p.rect(x0 - 2, 252, x1 + 2, 253, GRANITE_LIGHT)
    p.rect(x0 - 3, top + 1, x1 + 3, top + 5, GRANITE_LIGHT)                # cap
    p.rect(x0 - 3, top + 5, x1 + 3, top + 5, GRANITE_SHADE)
    p.rect(x0, top, x1, top, GRANITE_TOP)
    # Globe lamp above the pillar
    p.rect(cx - 1, top - 9, cx + 1, top - 1, PATINA_DARK)
    p.ellipse(cx + 0.5, top - 16, 7, 7, "#a7b9ae")
    p.ellipse(cx - 1.5, top - 18, 3, 3, "#d6e2da")
    p.rect(cx - 7, top - 16, cx + 7, top - 16, PATINA_DARK)
    p.rect(cx, top - 25, cx, top - 23, PATINA_DARK)


def side_fences(p: Picture):
    for x0, x1 in [(MAIN[0] + 6, PILLAR_L[0] - 5), (PILLAR_R[2] + 5, MAIN[2] - 6)]:
        p.rect(x0, 205, x1, 262, PATINA_DARK)
        for x in range(x0 + 2, x1 - 1, 5):
            p.rect(x, 207, x + 2, 260, PATINA)
            p.put(x + 1, 220, PATINA_LIGHT)


def plaza(p: Picture):
    mask = np.zeros((H, W), bool)
    x0, top, x1 = MAIN
    p.rect(x0, top, x1, top, GRANITE_TOP, mask)                            # granite curb
    p.rect(x0, top + 1, x1, top + 2, GRANITE_SHADE, mask)
    for y in range(top + 3, top + 9):
        for x in range(x0, x1 + 1):
            mortar = (y - top) % 3 == 0 or (x + (3 if ((y - top) // 3) % 2 else 0)) % 7 == 0
            p.put(x, y, "#7a3a2b" if mortar else "#b05a42")
        mask[y, x0:x1 + 1] = True
    stone_wall(p, mask, x0 + 2, x1 - 2, top + 9, top + 34, taper=2.4,
               colors=("#8f8a80", GRANITE_LIGHT, GRANITE_SHADE, GRANITE))
    p.outline(mask)


def build() -> Picture:
    p = Picture()
    sky(p)
    background(p)
    side_fences(p)
    arch(p)
    for x0, top, x1 in (PILLAR_L, PILLAR_R):
        pillar(p, x0, top, x1)
    plaza(p)
    return p


if __name__ == "__main__":
    save("sather_gate", build(), MAIN, LEDGES)
