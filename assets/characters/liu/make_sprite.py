"""Dean Tsu-Jae King Liu as a retro pixel sprite.

Owner: Person 4.

    python assets/characters/liu/make_sprite.py

Look: short silver-gray hair swept to one side, darker underneath, a warm
smile, navy blazer over a bright blue crew-neck with a lapel pin, silver
watch. Pose: arms crossed. See ../pixel_sprite.py for the shared toolkit and
outputs.
"""

from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from pixel_sprite import Canvas, save  # noqa: E402

NAME = "Dean Tsu-Jae King Liu"

PALETTE = {
    "hair": "#a9abb0", "hair_light": "#d8dade", "hair_dark": "#62656d",
    "skin": "#f1c8a2", "skin_shade": "#d9a580", "cheek": "#e9a08c",
    "eye": "#1b1414", "mouth": "#9c4f45", "teeth": "#f6f3ee",
    "blazer": "#232c48", "blazer_light": "#3a456d", "blazer_dark": "#151a2e",
    "top": "#3f78d6", "top_light": "#6896e6", "top_dark": "#2c5aa8",
    "pin": "#eef2f8", "pin_blue": "#2c4fb3", "watch": "#c9ccd4",
    "pants": "#262d46", "pants_dark": "#171c2e",
    "shoe": "#141416", "shoe_light": "#3c3c44",
}


def front() -> Canvas:
    c = Canvas(PALETTE)

    # Trousers and shoes
    c.rect(10, 33, 15, 40, "pants")
    c.rect(16, 33, 21, 40, "pants")
    c.rect(19, 33, 21, 40, "pants_dark")
    c.rect(15, 34, 15, 40, "pants_dark")
    c.rect(8, 41, 15, 42, "shoe")
    c.rect(16, 41, 23, 42, "shoe")
    c.pixels("shoe_light", (9, 41), (10, 41), (21, 41))

    # Blazer over a blue crew-neck
    c.rect(9, 20, 22, 32, "blazer")
    c.rect(10, 19, 21, 19, "blazer")
    c.pixels(None, (9, 20), (22, 20))
    c.rect(10, 21, 11, 32, "blazer_light")
    c.rect(20, 21, 22, 32, "blazer_dark")
    c.rect(13, 19, 18, 22, "top")
    c.rect(14, 23, 17, 24, "top")
    c.rect(15, 25, 16, 25, "top")
    c.pixels("top_light", (13, 20), (14, 21), (14, 22))
    c.pixels("top_dark", (18, 21), (18, 22), (17, 24))
    c.pixels("top_dark", (14, 19), (15, 19), (16, 19), (17, 19))   # crew neck rib
    c.pixels("blazer_light", (12, 20), (12, 21), (13, 23), (13, 24), (14, 25))   # lapels
    c.pixels("blazer_dark", (19, 20), (19, 21), (18, 23), (18, 24), (17, 25))
    c.pixels("pin", (20, 23))
    c.pixels("pin_blue", (20, 24))

    # Neck
    c.rect(14, 17, 17, 18, "skin_shade")

    # Head
    c.ellipse(16, 10.5, 7.6, 8.2, "skin")
    c.recolor(("skin",), "skin_shade", lambda x, y: x >= 20)

    # Short hair with volume on top, swept toward the viewer's left
    c.recolor(("skin", "skin_shade"), "hair",
              lambda x, y: 8 <= x <= 23 and (y <= 5 or (y <= 12 and (x <= 9 or x >= 22))))
    c.rect(11, 2, 21, 2, "hair")
    c.rect(12, 1, 19, 1, "hair")
    c.pixels("hair", (9, 6), (10, 6), (11, 6), (12, 6), (13, 6), (9, 7), (10, 7), (11, 7),
             (10, 3), (22, 3))
    c.recolor(("hair",), "hair_dark", lambda x, y: y >= 11 or (x >= 22 and y >= 7))
    c.pixels("hair_light", (13, 1), (14, 2), (16, 1), (17, 2), (12, 3), (15, 3), (19, 2), (11, 5), (12, 5), (14, 4))

    # Face: warm open smile
    c.pixels("hair_dark", (12, 8), (13, 8), (19, 8), (20, 8))      # brows
    c.pixels("eye", (11, 10), (12, 10), (19, 10), (20, 10))
    c.pixels("skin_shade", (11, 11), (12, 11), (19, 11), (20, 11))
    c.pixels("cheek", (10, 13), (21, 13))
    c.pixels("skin_shade", (16, 12), (16, 13), (15, 13))             # nose
    c.pixels("teeth", (14, 14), (15, 14), (16, 14), (17, 14))
    c.pixels("mouth", (13, 14), (18, 14), (14, 15), (15, 15), (16, 15), (17, 15))

    # Arms crossed
    c.rect(6, 20, 8, 27, "blazer_light")
    c.rect(23, 20, 25, 27, "blazer_dark")
    c.rect(8, 25, 21, 27, "blazer_light")    # top forearm
    c.rect(10, 28, 23, 30, "blazer")         # lower forearm
    c.rect(22, 25, 23, 26, "skin")           # hand peeking out on the right
    c.rect(8, 29, 9, 30, "skin")             # hand peeking out on the left
    c.pixels("watch", (10, 29), (10, 30))

    c.outline()
    c.pixels("outline", *[(9, y) for y in range(21, 25)], *[(22, y) for y in range(21, 25)])
    c.pixels("outline", *[(x, 28) for x in range(11, 22)])   # edge between the two forearms
    return c


def side() -> Canvas:
    """Facing left."""
    c = Canvas(PALETTE)

    # Far arm and leg
    c.rect(20, 21, 22, 28, "blazer_dark")
    c.rect(16, 33, 20, 40, "pants_dark")
    c.rect(13, 41, 20, 42, "shoe")

    # Blazer and top
    c.rect(11, 20, 20, 32, "blazer")
    c.rect(12, 19, 19, 19, "blazer")
    c.rect(19, 21, 20, 32, "blazer_dark")
    c.rect(11, 19, 12, 24, "top")
    c.pixels("top_dark", (12, 19), (12, 23), (12, 24))
    c.rect(13, 20, 13, 25, "blazer_light")
    c.pixels("pin", (14, 22))

    # Near leg and shoe
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
              lambda x, y: (x >= 17 and y <= 14) or (y <= 5 and x >= 10))
    c.rect(12, 2, 21, 2, "hair")
    c.rect(13, 1, 20, 1, "hair")
    c.pixels("hair", (9, 5), (10, 5), (9, 6), (11, 3), (10, 4), (22, 3), (23, 4), (24, 12), (24, 13))
    c.recolor(("hair",), "hair_dark", lambda x, y: y >= 12 or (x >= 23 and y >= 4))
    c.pixels("hair_light", (13, 2), (15, 1), (16, 2), (18, 1), (12, 3), (14, 4), (17, 4), (10, 5),
             (19, 6), (20, 8), (21, 6), (19, 10))

    # Face
    c.pixels("hair_dark", (10, 8), (11, 8))
    c.pixels("eye", (10, 10), (11, 10))
    c.pixels("skin_shade", (10, 11), (11, 11))
    c.pixels("cheek", (12, 13))
    c.pixels("teeth", (9, 14), (10, 14))
    c.pixels("mouth", (9, 15), (10, 15), (11, 14))

    # Near arm folded across the chest
    c.rect(14, 20, 17, 25, "blazer")
    c.rect(14, 20, 14, 25, "blazer_light")
    c.rect(9, 25, 17, 28, "blazer")
    c.rect(9, 25, 16, 25, "blazer_light")
    c.rect(8, 26, 8, 27, "skin")
    c.pixels("watch", (10, 28))

    c.outline()
    c.pixels("outline", *[(18, y) for y in range(21, 25)])
    return c


if __name__ == "__main__":
    save(Path(__file__).resolve().parent, front(), side(), NAME)
