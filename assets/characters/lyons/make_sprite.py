"""Chancellor Rich Lyons as a retro pixel sprite.

Owner: Person 4.

    python assets/characters/lyons/make_sprite.py

Look: silver hair swept back, trimmed white beard and mustache, navy suit,
gold-and-navy striped tie. Pose: playing an acoustic guitar held across the
body, neck up and away. See ../pixel_sprite.py for the shared toolkit and
outputs.
"""

from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from poses import Limbs  # noqa: E402
from pixel_sprite import Canvas, save  # noqa: E402

NAME = "Chancellor Rich Lyons"

PALETTE = {
    "hair": "#c9ccd2", "hair_light": "#eff1f4", "hair_dark": "#8f949e",
    "beard": "#dfe2e7", "beard_shade": "#aab0ba",
    "skin": "#eebd9a", "skin_shade": "#d29a76", "cheek": "#e19682",
    "eye": "#2a1e1c", "mouth": "#8c4a40",
    "suit": "#27355a", "suit_light": "#3d4f7e", "suit_dark": "#18213b",
    "shirt": "#e6eef9", "shirt_shade": "#bfcbe0",
    "tie": "#e6b52e", "tie_stripe": "#27355a",
    "shoe": "#141416", "shoe_light": "#3c3c44",
    "wood": "#e3a548", "wood_light": "#f3c46f", "wood_dark": "#b4782a",
    "hole": "#3a2416", "neck": "#6b3f22", "neck_light": "#94643c",
    "headstock": "#3f2414", "peg": "#ece6d6",
}


def guitar_front(c: Canvas):
    """Body low on the viewer's left, neck rising to the upper right."""
    c.ellipse(11, 29.5, 5.6, 4.6, "wood")      # lower bout
    c.ellipse(15, 26.5, 4.2, 3.6, "wood")      # upper bout
    c.recolor(("wood",), "wood_dark", lambda x, y: y >= 32 or x >= 18)
    c.pixels("wood_light", (8, 27), (9, 26), (7, 28), (12, 24))
    c.rect(13, 27, 14, 28, "hole")              # sound hole
    c.pixels("neck", (8, 31), (9, 31))          # bridge
    for i in range(9):                          # neck, 2 px thick, climbing right
        c.pixels("neck", (17 + i, 25 - i), (17 + i, 24 - i))
        if i % 2 == 0:
            c.put(17 + i, 24 - i, "neck_light")
    c.pixels("headstock", (26, 15), (27, 15), (26, 14), (27, 14), (27, 13))
    c.pixels("peg", (25, 13), (28, 14), (26, 12))

# Sleeve and hand colors for the generated action poses (see ../poses.py)
LIMBS = Limbs("suit", "suit_light", "skin", "skin_shade", keep_front=True)  # keeps the guitar


def front() -> Canvas:
    c = Canvas(PALETTE)

    # Trousers and shoes
    c.rect(10, 33, 15, 40, "suit")
    c.rect(16, 33, 21, 40, "suit")
    c.rect(19, 33, 21, 40, "suit_dark")
    c.rect(15, 34, 15, 40, "suit_dark")
    c.rect(8, 41, 15, 42, "shoe")
    c.rect(16, 41, 23, 42, "shoe")
    c.pixels("shoe_light", (9, 41), (10, 41), (21, 41))

    # Suit jacket, shirt and striped tie
    c.rect(9, 20, 22, 32, "suit")
    c.rect(10, 19, 21, 19, "suit")
    c.pixels(None, (9, 20), (22, 20))
    c.rect(10, 21, 11, 32, "suit_light")
    c.rect(20, 21, 22, 32, "suit_dark")
    c.rect(14, 19, 17, 23, "shirt")
    c.pixels("shirt", (13, 19), (18, 19))
    c.pixels("shirt_shade", (17, 21), (17, 22))
    c.rect(15, 20, 16, 29, "tie")
    c.pixels("tie_stripe", (15, 22), (16, 23), (15, 25), (16, 26), (15, 28))
    c.pixels("suit_light", (13, 21), (13, 22), (14, 24), (14, 25))   # lapels
    c.pixels("suit_dark", (18, 21), (18, 22), (17, 24), (17, 25))

    # Neck
    c.rect(14, 17, 17, 18, "skin_shade")

    # Head
    c.ellipse(16, 10.5, 7.6, 8.2, "skin")
    c.recolor(("skin",), "skin_shade", lambda x, y: x >= 20)
    c.rect(7, 10, 7, 12, "skin_shade")
    c.rect(24, 10, 24, 12, "skin_shade")

    # Silver hair, swept back with a wave
    c.recolor(("skin", "skin_shade"), "hair",
              lambda x, y: 8 <= x <= 23 and (y <= 5 or (y <= 10 and (x <= 9 or x >= 22))))
    c.rect(12, 2, 19, 2, "hair")
    c.pixels("hair", (13, 1), (14, 1), (17, 1), (18, 1), (10, 3), (21, 3), (9, 4), (22, 4))
    c.recolor(("hair",), "hair_dark", lambda x, y: x >= 21)
    c.pixels("hair_light", (12, 3), (13, 2), (14, 3), (15, 4), (17, 2), (18, 3), (11, 5), (10, 6))

    # Beard, mustache and face
    c.recolor(("skin", "skin_shade"), "beard",
              lambda x, y: (y >= 14 and 8 <= x <= 23) or (y >= 11 and (x <= 9 or x >= 22)))
    c.recolor(("beard",), "beard_shade", lambda x, y: x >= 20 or y >= 18)
    c.rect(13, 13, 18, 13, "beard")              # mustache
    c.pixels("mouth", (14, 14), (15, 14), (16, 14), (17, 14))
    c.pixels("hair_dark", (10, 8), (11, 8), (12, 8), (19, 8), (20, 8), (21, 8))  # brows
    c.pixels("eye", (11, 10), (12, 10), (19, 10), (20, 10))
    c.pixels("skin_shade", (11, 11), (20, 11))
    c.pixels("cheek", (10, 12), (21, 12))
    c.pixels("skin_shade", (16, 11), (16, 12), (15, 12))   # nose

    guitar_front(c)

    # Strumming arm (viewer's left): over the guitar body to the sound hole
    c.rect(6, 20, 8, 25, "suit_light")
    c.rect(7, 25, 11, 26, "suit")
    c.rect(11, 26, 12, 27, "shirt")             # cuff
    c.rect(12, 28, 13, 29, "skin")
    c.pixels("skin_shade", (13, 29))

    # Fretting arm (viewer's right): up to the neck
    c.rect(23, 20, 25, 26, "suit_dark")
    c.rect(23, 21, 24, 22, "suit")
    c.rect(22, 22, 23, 23, "shirt")             # cuff
    c.pixels("skin", (21, 20), (22, 20), (21, 21), (20, 21))
    c.pixels("skin_shade", (22, 21))

    c.outline()
    c.pixels("outline", *[(9, y) for y in range(21, 25)], *[(22, y) for y in range(24, 27)])
    return c


def side() -> Canvas:
    """Facing left, guitar held out in front with the neck pointing forward."""
    c = Canvas(PALETTE)

    # Far arm reaches forward to the guitar neck, behind everything
    c.rect(19, 21, 21, 25, "suit_dark")
    c.rect(8, 22, 19, 23, "suit_dark")

    # Far leg and shoe
    c.rect(16, 33, 20, 40, "suit_dark")
    c.rect(13, 41, 20, 42, "shoe")

    # Jacket, shirt and tie
    c.rect(11, 20, 20, 32, "suit")
    c.rect(12, 19, 19, 19, "suit")
    c.rect(19, 21, 20, 32, "suit_dark")
    c.rect(11, 19, 12, 22, "shirt")
    c.rect(11, 21, 11, 27, "tie")
    c.pixels("tie_stripe", (11, 23), (11, 26))
    c.rect(13, 20, 13, 24, "suit_light")

    # Near leg and shoe
    c.rect(11, 33, 16, 40, "suit")
    c.rect(16, 34, 16, 40, "suit_dark")
    c.rect(8, 41, 16, 42, "shoe")
    c.pixels("shoe_light", (9, 41), (10, 41))

    # Neck
    c.rect(15, 17, 18, 19, "skin_shade")

    # Head in profile
    c.ellipse(16.5, 10.5, 7.2, 8.2, "skin")
    c.pixels("skin", (8, 11), (8, 12))                          # nose
    c.recolor(("skin",), "skin_shade", lambda x, y: x >= 17 and y >= 13)
    c.recolor(("skin", "skin_shade"), "hair",
              lambda x, y: (x >= 18 and y <= 14) or (y <= 5 and x >= 10))
    c.rect(12, 2, 20, 2, "hair")
    c.pixels("hair", (13, 1), (14, 1), (17, 1), (18, 1), (11, 3), (10, 4), (21, 3), (22, 4), (24, 7))
    c.recolor(("hair",), "hair_dark", lambda x, y: x >= 21)
    c.pixels("hair_light", (12, 3), (13, 2), (15, 3), (16, 2), (19, 4), (20, 6))
    c.rect(18, 10, 19, 12, "skin_shade")                        # ear
    c.recolor(("skin", "skin_shade"), "beard", lambda x, y: y >= 14 or (x >= 15 and y >= 12))
    c.pixels("beard", (9, 14), (9, 15), (9, 16), (10, 17))
    c.recolor(("beard",), "beard_shade", lambda x, y: x >= 17 or y >= 18)
    c.pixels("beard", (9, 13), (10, 13), (11, 13))              # mustache
    c.pixels("mouth", (10, 14), (11, 14))
    c.pixels("hair_dark", (9, 8), (10, 8), (11, 8))
    c.pixels("eye", (10, 10), (11, 10))
    c.pixels("cheek", (12, 12))

    # Guitar in front of the body, neck pointing forward and up
    c.ellipse(10, 28.5, 4.8, 4.6, "wood")
    c.ellipse(12, 25.5, 3.4, 3.0, "wood")
    c.recolor(("wood",), "wood_dark", lambda x, y: y >= 31 or x >= 14)
    c.pixels("wood_light", (7, 26), (8, 25), (6, 28))
    c.rect(10, 26, 11, 27, "hole")
    c.pixels("neck", (8, 30), (9, 30))
    for i in range(7):
        c.pixels("neck", (7 - i, 23 - i // 2), (7 - i, 22 - i // 2))
        if i % 2 == 0:
            c.put(7 - i, 22 - i // 2, "neck_light")
    c.pixels("headstock", (0, 19), (1, 19), (0, 18))
    c.pixels("peg", (1, 18))
    c.pixels("skin", (4, 21), (5, 21), (4, 22))                 # far hand on the neck

    # Near arm: down to strum over the sound hole
    c.rect(14, 20, 17, 26, "suit")
    c.rect(14, 20, 14, 26, "suit_light")
    c.rect(12, 26, 15, 27, "suit")
    c.rect(12, 28, 13, 28, "shirt")
    c.rect(10, 28, 11, 29, "skin")

    c.outline()
    c.pixels("outline", *[(18, y) for y in range(21, 25)])
    return c


if __name__ == "__main__":
    save(Path(__file__).resolve().parent, front(), side(), NAME, LIMBS)
