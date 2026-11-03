"""Professor Alyosha Efros as a retro pixel sprite.

Owner: Person 4.

    python assets/characters/efros/make_sprite.py

Look: tousled strawberry-blond hair thinning on top, wire glasses, a squinting
smile, blue button-up with a black belt. Front view: one hand raised
mid-lecture, the other holding a slide clicker. Side view: clicker pointed
forward. See ../pixel_sprite.py for the shared toolkit and outputs.
"""

from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from pixel_sprite import H, W, Canvas, save  # noqa: E402

NAME = "Prof. Alyosha Efros"

PALETTE = {
    "hair": "#e2ac6a", "hair_light": "#f4d095", "hair_dark": "#b97b3e",
    "skin": "#f7caa8", "skin_shade": "#e3a07f", "cheek": "#ee9282",
    "eye": "#2a1e1c", "mouth": "#a85a4c",
    "glasses": "#6b5d50",
    "shirt": "#5f7dc8", "shirt_light": "#88a4e2", "shirt_dark": "#3e5498",
    "button": "#eef1f8",
    "belt": "#1b1b21", "buckle": "#c9ccd4",
    "pants": "#4b505f", "pants_dark": "#30333d",
    "shoe": "#1c1716", "shoe_light": "#4a403b",
    "clicker": "#26262c", "clicker_light": "#e5484d",
}


def front() -> Canvas:
    c = Canvas(PALETTE)

    # Legs and shoes
    c.rect(10, 33, 15, 40, "pants")
    c.rect(16, 33, 21, 40, "pants")
    c.rect(19, 33, 21, 40, "pants_dark")
    c.rect(15, 34, 15, 40, "pants_dark")
    c.rect(8, 41, 15, 42, "shoe")
    c.rect(16, 41, 23, 42, "shoe")
    c.pixels("shoe_light", (9, 41), (10, 41), (21, 41))

    # Shirt
    c.rect(9, 20, 22, 30, "shirt")
    c.rect(10, 19, 21, 19, "shirt")
    c.pixels(None, (9, 20), (22, 20))
    c.rect(9, 21, 10, 30, "shirt_light")
    c.rect(20, 21, 22, 30, "shirt_dark")
    c.rect(15, 21, 15, 30, "shirt_dark")                  # placket
    c.pixels("button", (16, 22), (16, 25), (16, 28))
    c.pixels("shirt_dark", (11, 22), (12, 22), (13, 22))  # chest pocket
    c.pixels("shirt_light", (12, 19), (13, 19), (13, 20), (18, 19), (19, 19), (18, 20))  # collar
    c.rect(9, 31, 22, 32, "belt")
    c.rect(15, 31, 16, 32, "buckle")

    # Neck
    c.rect(14, 17, 17, 19, "skin_shade")
    c.pixels("skin_shade", (15, 20), (16, 20))

    # Head
    c.ellipse(16, 10.5, 7.6, 8.2, "skin")
    c.recolor(("skin",), "skin_shade", lambda x, y: x >= 20)
    c.rect(7, 10, 7, 12, "skin_shade")   # ears
    c.rect(24, 10, 24, 12, "skin_shade")

    # Hair: high hairline, thinning on top, fuller at the sides, tousled tufts
    c.recolor(("skin", "skin_shade"), "hair",
              lambda x, y: 8 <= x <= 23 and (y <= 4 or (y <= 9 and (x <= 9 or x >= 22))))
    c.recolor(("hair",), "hair_dark", lambda x, y: x >= 20)
    c.pixels("hair_light", (12, 3), (13, 3), (14, 4), (11, 4), (10, 5), (9, 6))
    c.pixels("hair", (13, 2), (12, 1), (17, 2), (17, 1), (18, 0), (19, 3), (20, 2), (10, 4), (9, 3))
    c.pixels("hair_dark", (21, 4), (22, 3))
    c.pixels("hair_light", (14, 2), (16, 1))

    # Face
    c.pixels("hair_dark", (10, 7), (11, 7), (12, 7), (19, 7), (20, 7), (21, 7))  # brows
    for x0 in (9, 17):  # glasses: two lenses and a bridge
        c.rect(x0, 8, x0 + 5, 8, "glasses")
        c.rect(x0, 11, x0 + 5, 11, "glasses")
        c.rect(x0, 9, x0, 10, "glasses")
        c.rect(x0 + 5, 9, x0 + 5, 10, "glasses")
    c.pixels("glasses", (15, 9), (16, 9), (8, 9), (23, 9))
    c.pixels("eye", (10, 10), (11, 9), (12, 9), (13, 10))      # smiling squint
    c.pixels("eye", (18, 10), (19, 9), (20, 9), (21, 10))
    c.pixels("cheek", (9, 13), (10, 13), (21, 13), (22, 13))
    c.pixels("skin_shade", (16, 12), (16, 13), (15, 13))        # nose
    c.pixels("mouth", (14, 15), (15, 15), (16, 15), (17, 15), (13, 14), (18, 14))

    # Raised open hand (viewer's left), mid-lecture
    c.rect(6, 20, 8, 22, "shirt_light")
    c.rect(4, 15, 6, 23, "shirt")
    c.rect(4, 15, 4, 23, "shirt_light")
    c.rect(4, 15, 6, 15, "shirt_dark")   # cuff
    c.rect(3, 11, 7, 14, "skin")
    c.pixels("skin", (3, 9), (3, 10), (5, 8), (5, 9), (5, 10), (7, 9), (7, 10), (2, 13), (1, 12))
    c.pixels("skin_shade", (7, 13), (7, 14), (6, 14))

    # Other arm hangs at the side, holding the slide clicker
    c.rect(23, 20, 25, 27, "shirt_dark")
    c.rect(24, 21, 24, 26, "shirt")
    c.rect(22, 28, 24, 29, "skin")
    c.pixels("skin_shade", (24, 29))
    c.pixels("clicker", (20, 28), (21, 28), (21, 29))
    c.pixels("clicker_light", (20, 28))

    c.outline()
    # Inner lines so arms read as separate from the body
    c.pixels("outline", *[(23, y) for y in range(21, 28)])
    c.pixels("outline", (8, 23), (8, 24), (7, 23))
    return c


def side() -> Canvas:
    """Facing left."""
    c = Canvas(PALETTE)

    # Far arm and leg, darker, behind the body
    c.rect(20, 21, 22, 28, "shirt_dark")
    c.rect(21, 29, 22, 29, "skin_shade")
    c.rect(16, 33, 20, 40, "pants_dark")
    c.rect(13, 41, 20, 42, "shoe")

    # Shirt
    c.rect(11, 20, 20, 30, "shirt")
    c.rect(12, 19, 19, 19, "shirt")
    c.rect(11, 21, 12, 30, "shirt_light")
    c.rect(19, 21, 20, 30, "shirt_dark")
    c.rect(13, 21, 13, 30, "shirt_dark")
    c.pixels("button", (12, 22), (12, 25), (12, 28))
    c.pixels("shirt_light", (12, 19), (13, 19), (13, 20))
    c.rect(11, 31, 20, 32, "belt")
    c.rect(11, 31, 11, 32, "buckle")

    # Near leg and shoe, toe pointing left
    c.rect(11, 33, 16, 40, "pants")
    c.rect(16, 34, 16, 40, "pants_dark")
    c.rect(8, 41, 16, 42, "shoe")
    c.pixels("shoe_light", (9, 41), (10, 41))

    # Neck
    c.rect(15, 17, 18, 19, "skin_shade")

    # Head in profile
    c.ellipse(16.5, 10.5, 7.2, 8.2, "skin")
    c.pixels("skin", (8, 11), (8, 12), (9, 13))                 # nose
    c.recolor(("skin",), "skin_shade", lambda x, y: x >= 17 and y >= 14)
    c.recolor(("skin", "skin_shade"), "hair",
              lambda x, y: y <= 17 and ((x >= 18 and y <= 15) or (y <= 4 and x >= 11)))
    c.recolor(("hair",), "hair_dark", lambda x, y: x >= 21)
    c.pixels("hair_light", (13, 3), (14, 3), (15, 2), (18, 4), (19, 5))
    c.pixels("hair", (14, 2), (13, 1), (18, 2), (18, 1), (19, 0), (20, 3), (21, 2))
    c.pixels("hair_dark", (22, 5), (23, 4), (23, 8), (24, 7))
    c.pixels("hair_light", (16, 1))
    c.rect(18, 10, 19, 12, "skin_shade")                        # ear

    # Face
    c.pixels("hair_dark", (9, 7), (10, 7), (11, 7))
    c.rect(9, 8, 12, 8, "glasses")
    c.rect(9, 11, 12, 11, "glasses")
    c.rect(9, 9, 9, 10, "glasses")
    c.rect(12, 9, 12, 10, "glasses")
    c.rect(13, 9, 17, 9, "glasses")                             # arm to the ear
    c.pixels("eye", (10, 10), (11, 9))
    c.pixels("cheek", (12, 13), (13, 13))
    c.pixels("mouth", (9, 15), (10, 15), (11, 14))

    # Near arm: forearm forward, clicker pointed at the screen
    c.rect(14, 20, 17, 26, "shirt")
    c.rect(14, 20, 14, 26, "shirt_light")
    c.rect(10, 25, 16, 27, "shirt")
    c.rect(10, 25, 10, 27, "shirt_dark")   # cuff
    c.rect(7, 25, 9, 27, "skin")
    c.pixels("skin_shade", (9, 27))
    c.pixels("clicker", (5, 26), (6, 26))
    c.pixels("clicker_light", (5, 26))

    c.outline()
    c.pixels("outline", *[(18, y) for y in range(21, 25)], (13, 22), (13, 23), (13, 24))
    return c


if __name__ == "__main__":
    save(Path(__file__).resolve().parent, front(), side(), NAME)
