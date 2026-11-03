"""Oski the bear as a retro pixel sprite.

Owner: Person 4.

    python assets/characters/oski/make_sprite.py

Look: oversized tan mascot head framed by a dark shaggy fringe, big cartoon
eyes, a big black nose and wide grin, yellow cardigan with a blue "C" and
sleeve stripes, white gloves, navy pants. Front pose: one arm thrown up and
pointing, the other on the hip. See ../pixel_sprite.py for the shared toolkit
and outputs.
"""

from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from pixel_sprite import Canvas, save  # noqa: E402

PALETTE = {
    "fur": "#d9b27c", "fur_light": "#efcd9a", "fur_shade": "#b98e57",
    "mane": "#4b301f", "mane_light": "#72503a", "mane_dark": "#2c1c12",
    "eye_white": "#f4f4ef", "eye": "#1a1414",
    "nose": "#141414", "nose_light": "#555558", "smile": "#1a1414",
    "sweater": "#f5c518", "sweater_light": "#ffdc55", "sweater_dark": "#d6a20b",
    "button": "#c8930a", "blue": "#2c4fb3",
    "glove": "#f6f6f2", "glove_shade": "#d0d0cb",
    "pants": "#24335f", "pants_dark": "#182240",
    "shoe": "#1c1716",
}


def front() -> Canvas:
    c = Canvas(PALETTE)

    # Pants and shoes
    c.rect(10, 34, 15, 40, "pants")
    c.rect(16, 34, 21, 40, "pants")
    c.rect(19, 34, 21, 40, "pants_dark")
    c.rect(15, 35, 15, 40, "pants_dark")
    c.rect(8, 41, 15, 42, "shoe")
    c.rect(16, 41, 23, 42, "shoe")

    # Cardigan with the blue C
    c.rect(8, 21, 23, 33, "sweater")
    c.pixels(None, (8, 21), (23, 21))
    c.rect(8, 22, 9, 33, "sweater_light")
    c.rect(21, 22, 23, 33, "sweater_dark")
    c.rect(15, 21, 15, 33, "sweater_dark")             # placket
    c.pixels("button", (14, 24), (14, 27), (14, 30))
    c.rect(18, 24, 21, 24, "blue")
    c.rect(18, 25, 18, 27, "blue")
    c.rect(18, 28, 21, 28, "blue")
    c.rect(8, 33, 23, 33, "sweater_dark")              # ribbed hem

    # Head: dark shaggy fringe behind an oversized tan face
    c.ellipse(16, 10, 10.4, 9.6, "mane")
    c.pixels("mane", (7, 1), (8, 0), (11, 0), (15, 0), (19, 0), (23, 0), (25, 1), (5, 6), (26, 6), (4, 10), (27, 10))
    c.rect(5, 1, 7, 3, "mane")                         # ears in the fur
    c.rect(24, 1, 26, 3, "mane")
    c.recolor(("mane",), "mane_dark", lambda x, y: x >= 22 or y >= 15)
    c.pixels("mane_light", (10, 2), (12, 1), (14, 2), (9, 4), (18, 1), (16, 2))
    c.ellipse(16, 12.5, 8.4, 7.8, "fur")
    c.recolor(("fur",), "fur_shade", lambda x, y: x >= 21 or y >= 19)
    c.pixels("fur_light", (11, 6), (12, 6), (10, 7), (14, 16), (15, 16), (16, 16))

    # Big cartoon eyes
    for x0 in (9, 17):  # rounded white oval, dark rim, big pupil looking slightly down
        c.rect(x0 + 1, 7, x0 + 4, 7, "eye")
        c.rect(x0, 8, x0, 11, "eye")
        c.rect(x0 + 5, 8, x0 + 5, 11, "eye")
        c.rect(x0 + 1, 12, x0 + 4, 12, "eye")
        c.rect(x0 + 1, 8, x0 + 4, 11, "eye_white")
        c.rect(x0 + 2, 9, x0 + 4, 11, "eye")
        c.put(x0 + 2, 9, "eye_white")                  # shine

    # Nose and grin
    c.rect(13, 13, 18, 15, "nose")
    c.rect(14, 16, 17, 16, "nose")
    c.pixels("nose_light", (14, 13), (15, 13), (14, 14))
    c.pixels("smile", (8, 15), (9, 16), (10, 17), (11, 18), (12, 18), (13, 18), (14, 18), (15, 18),
             (16, 18), (17, 18), (18, 18), (19, 18), (20, 18), (21, 17), (22, 16), (23, 15))

    # Arm thrown up and pointing (viewer's left)
    c.rect(5, 15, 7, 23, "sweater")
    c.rect(5, 15, 5, 23, "sweater_light")
    c.rect(5, 18, 7, 18, "blue")                        # sleeve stripes
    c.rect(5, 20, 7, 20, "blue")
    c.rect(4, 12, 7, 14, "glove")
    c.pixels("glove", (4, 11), (4, 10), (4, 9))         # pointing finger
    c.pixels("glove_shade", (7, 14), (6, 14))

    # Other hand on the hip
    c.rect(24, 22, 26, 29, "sweater_dark")
    c.rect(24, 25, 26, 25, "blue")
    c.rect(24, 27, 26, 27, "blue")
    c.rect(22, 29, 24, 31, "glove")
    c.pixels("glove_shade", (24, 31))

    c.outline()
    c.pixels("outline", *[(23, y) for y in range(22, 29)], (8, 22), (8, 23))
    return c


def side() -> Canvas:
    """Facing left."""
    c = Canvas(PALETTE)

    # Far arm and leg
    c.rect(20, 22, 22, 29, "sweater_dark")
    c.rect(21, 30, 22, 31, "glove_shade")
    c.rect(16, 34, 20, 40, "pants_dark")
    c.rect(13, 41, 20, 42, "shoe")

    # Cardigan
    c.rect(11, 21, 21, 33, "sweater")
    c.rect(11, 22, 12, 33, "sweater_light")
    c.rect(19, 22, 21, 33, "sweater_dark")
    c.rect(13, 22, 13, 33, "sweater_dark")
    c.pixels("button", (12, 24), (12, 27), (12, 30))
    c.rect(11, 33, 21, 33, "sweater_dark")

    # Near leg and shoe
    c.rect(11, 34, 16, 40, "pants")
    c.rect(16, 35, 16, 40, "pants_dark")
    c.rect(8, 41, 16, 42, "shoe")

    # Head: fringe at the back and top, snout and nose forward
    c.ellipse(18, 10, 9.6, 9.4, "mane")
    c.pixels("mane", (10, 1), (13, 0), (17, 0), (21, 0), (25, 1), (27, 5), (28, 9), (27, 14))
    c.rect(22, 0, 24, 2, "mane")                        # ear
    c.recolor(("mane",), "mane_dark", lambda x, y: x >= 23 or y >= 15)
    c.pixels("mane_light", (13, 2), (15, 1), (17, 2), (19, 1), (12, 4))
    c.ellipse(14.5, 12.5, 7.4, 7.6, "fur")
    c.rect(6, 12, 9, 17, "fur")                          # snout
    c.recolor(("fur",), "fur_shade", lambda x, y: y >= 19 or x >= 20)
    c.pixels("fur_light", (10, 6), (11, 6), (9, 8), (7, 16), (8, 16))
    c.rect(3, 11, 7, 14, "nose")
    c.pixels("nose", (4, 15), (5, 15), (6, 15))
    c.pixels("nose_light", (4, 11), (5, 11), (4, 12))
    c.rect(10, 7, 14, 11, "eye")
    c.rect(11, 8, 13, 10, "eye_white")
    c.rect(11, 8, 11, 10, "eye")
    c.put(12, 8, "eye_white")
    c.pixels("fur", (10, 7), (14, 7), (10, 11), (14, 11))
    c.pixels("smile", (6, 17), (7, 18), (8, 18), (9, 18), (10, 18), (11, 18), (12, 17), (13, 16))

    # Near arm punching forward
    c.rect(14, 22, 17, 26, "sweater")
    c.rect(14, 22, 14, 26, "sweater_light")
    c.rect(8, 25, 16, 27, "sweater")
    c.rect(11, 25, 11, 27, "blue")
    c.rect(13, 25, 13, 27, "blue")
    c.rect(5, 24, 8, 28, "glove")
    c.pixels("glove_shade", (8, 28), (7, 28))

    c.outline()
    c.pixels("outline", *[(18, y) for y in range(22, 26)])
    return c


if __name__ == "__main__":
    save(Path(__file__).resolve().parent, front(), side())
