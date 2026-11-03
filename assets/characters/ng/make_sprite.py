"""Professor Ren Ng as a retro pixel sprite.

Owner: Person 4.

    python assets/characters/ng/make_sprite.py

Look: short black hair swept up with spiky texture, a friendly smile, navy
blazer over an open-collar white shirt, jeans. Pose: hands clasped in front.
See ../pixel_sprite.py for the shared toolkit and outputs.
"""

from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from poses import Limbs  # noqa: E402
from pixel_sprite import Canvas, save  # noqa: E402

NAME = "Prof. Ren Ng"

PALETTE = {
    "hair": "#24242c", "hair_light": "#454a5c", "hair_dark": "#121218",
    "skin": "#f0c39a", "skin_shade": "#d8a179", "cheek": "#e6a08a",
    "eye": "#1b1414", "mouth": "#9c4f45",
    "blazer": "#2f3549", "blazer_light": "#48526e", "blazer_dark": "#1d2130",
    "shirt": "#f4f4f6", "shirt_shade": "#d0d4dc",
    "jeans": "#40608f", "jeans_light": "#5a7aad", "jeans_dark": "#2b4168",
    "shoe": "#2a1f1a", "shoe_light": "#54433a",
}

# Sleeve and hand colors for the generated action poses (see ../poses.py)
LIMBS = Limbs("blazer", "blazer_light", "skin", "skin_shade")


def front() -> Canvas:
    c = Canvas(PALETTE)

    # Jeans and shoes
    c.rect(10, 32, 15, 40, "jeans")
    c.rect(16, 32, 21, 40, "jeans")
    c.rect(10, 33, 11, 40, "jeans_light")
    c.rect(19, 32, 21, 40, "jeans_dark")
    c.rect(15, 33, 15, 40, "jeans_dark")
    c.rect(8, 41, 15, 42, "shoe")
    c.rect(16, 41, 23, 42, "shoe")
    c.pixels("shoe_light", (9, 41), (10, 41), (21, 41))

    # Blazer, open over a white shirt
    c.rect(9, 20, 22, 31, "blazer")
    c.rect(10, 19, 21, 19, "blazer")
    c.pixels(None, (9, 20), (22, 20))
    c.rect(10, 21, 11, 31, "blazer_light")
    c.rect(20, 21, 22, 31, "blazer_dark")
    c.rect(14, 19, 17, 24, "shirt")
    c.rect(15, 25, 16, 27, "shirt")
    c.pixels("shirt_shade", (17, 21), (17, 22), (16, 26), (16, 27))
    c.pixels("shirt", (13, 19), (18, 19), (13, 20))        # collar points
    c.pixels("skin_shade", (15, 19), (16, 19), (15, 20), (16, 20))  # open collar
    c.pixels("blazer_light", (13, 21), (13, 22), (14, 23), (14, 24), (14, 25))  # lapels
    c.pixels("blazer_dark", (18, 21), (18, 22), (17, 23), (17, 24), (17, 25))

    # Neck
    c.rect(14, 17, 17, 18, "skin_shade")

    # Head
    c.ellipse(16, 10.5, 7.6, 8.2, "skin")
    c.recolor(("skin",), "skin_shade", lambda x, y: x >= 20)
    c.rect(7, 10, 7, 12, "skin_shade")
    c.rect(24, 10, 24, 12, "skin_shade")

    # Hair: thick and short, swept up into spikes
    c.recolor(("skin", "skin_shade"), "hair",
              lambda x, y: 8 <= x <= 23 and (y <= 5 or (y <= 9 and (x <= 9 or x >= 22))))
    c.rect(11, 2, 20, 2, "hair")
    c.pixels("hair", (12, 1), (13, 1), (15, 1), (16, 1), (18, 1), (19, 1), (13, 0), (16, 0), (19, 0),
             (10, 3), (21, 3), (9, 4), (22, 4))
    c.recolor(("hair",), "hair_dark", lambda x, y: x >= 21)
    c.pixels("hair_light", (12, 3), (13, 2), (15, 2), (16, 1), (14, 4), (11, 5), (18, 3), (19, 2))

    # Face
    c.pixels("hair_dark", (10, 8), (11, 8), (12, 8), (19, 8), (20, 8), (21, 8))  # brows
    c.pixels("eye", (11, 10), (12, 10), (19, 10), (20, 10))
    c.pixels("skin_shade", (11, 11), (12, 11), (19, 11), (20, 11))  # smiling lower lids
    c.pixels("cheek", (10, 13), (21, 13))
    c.pixels("skin_shade", (16, 12), (16, 13), (15, 13))             # nose
    c.pixels("mouth", (13, 14), (14, 15), (15, 15), (16, 15), (17, 15), (18, 14))

    # Arms come together, hands clasped in front
    c.rect(6, 20, 8, 26, "blazer_light")
    c.rect(23, 20, 25, 26, "blazer_dark")
    c.rect(7, 27, 12, 27, "blazer")
    c.rect(8, 28, 13, 28, "blazer")
    c.rect(9, 29, 13, 29, "blazer")
    c.rect(19, 27, 24, 27, "blazer_dark")
    c.rect(18, 28, 23, 28, "blazer_dark")
    c.rect(18, 29, 22, 29, "blazer_dark")
    c.rect(13, 27, 13, 29, "shirt")      # cuffs
    c.rect(18, 27, 18, 29, "shirt")
    c.rect(14, 27, 17, 30, "skin")
    c.pixels("skin_shade", (14, 29), (16, 29), (17, 30), (15, 30))   # interlaced fingers

    c.outline()
    c.pixels("outline", *[(9, y) for y in range(21, 27)], *[(22, y) for y in range(21, 27)])
    return c


def side() -> Canvas:
    """Facing left."""
    c = Canvas(PALETTE)

    # Far arm and leg, behind the body
    c.rect(20, 21, 22, 28, "blazer_dark")
    c.rect(16, 32, 20, 40, "jeans_dark")
    c.rect(13, 41, 20, 42, "shoe")

    # Blazer and shirt
    c.rect(11, 20, 20, 31, "blazer")
    c.rect(12, 19, 19, 19, "blazer")
    c.rect(19, 21, 20, 31, "blazer_dark")
    c.rect(11, 19, 12, 24, "shirt")
    c.pixels("shirt_shade", (12, 23), (12, 24))
    c.rect(13, 20, 13, 25, "blazer_light")    # lapel

    # Near leg and shoe
    c.rect(11, 32, 16, 40, "jeans")
    c.rect(11, 33, 12, 40, "jeans_light")
    c.rect(16, 33, 16, 40, "jeans_dark")
    c.rect(8, 41, 16, 42, "shoe")
    c.pixels("shoe_light", (9, 41), (10, 41))

    # Neck
    c.rect(15, 17, 18, 19, "skin_shade")

    # Head in profile
    c.ellipse(16.5, 10.5, 7.2, 8.2, "skin")
    c.pixels("skin", (8, 11), (8, 12), (9, 13))                 # nose
    c.recolor(("skin",), "skin_shade", lambda x, y: x >= 17 and y >= 14)
    c.recolor(("skin", "skin_shade"), "hair",
              lambda x, y: (x >= 18 and y <= 13) or (y <= 5 and x >= 10))
    c.rect(12, 2, 20, 2, "hair")
    c.pixels("hair", (13, 1), (14, 1), (16, 1), (17, 1), (19, 1), (14, 0), (17, 0), (20, 0),
             (10, 4), (11, 3), (9, 5), (21, 3), (22, 4), (24, 6))
    c.recolor(("hair",), "hair_dark", lambda x, y: x >= 21)
    c.pixels("hair_light", (11, 4), (12, 3), (14, 2), (17, 1), (15, 3))
    c.rect(18, 10, 19, 12, "skin_shade")                        # ear

    # Face
    c.pixels("hair_dark", (9, 8), (10, 8), (11, 8))
    c.pixels("eye", (10, 10), (11, 10))
    c.pixels("skin_shade", (10, 11), (11, 11))
    c.pixels("cheek", (12, 13))
    c.pixels("mouth", (9, 15), (10, 15), (11, 14))

    # Near arm bent forward, hands clasped
    c.rect(14, 20, 17, 26, "blazer")
    c.rect(14, 20, 14, 26, "blazer_light")
    c.rect(10, 25, 16, 27, "blazer")
    c.rect(10, 25, 10, 27, "shirt")      # cuff
    c.rect(7, 25, 9, 28, "skin")
    c.pixels("skin_shade", (8, 27), (9, 28), (7, 28))

    c.outline()
    c.pixels("outline", *[(18, y) for y in range(21, 25)], (13, 22), (13, 23), (13, 24))
    return c


if __name__ == "__main__":
    save(Path(__file__).resolve().parent, front(), side(), NAME, LIMBS)
