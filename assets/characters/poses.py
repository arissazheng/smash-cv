"""Action poses for every game state, built on top of a character's side view.

Owner: Person 4.

Every character's side view (facing left) uses the same template: the near
shoulder is around (15, 21), the legs start at y=33. So one set of pose rules
works for the whole roster; each character only says which palette colors are
its sleeve and hand (Limbs). Poses are drawn over the finished side view and
re-outlined, then pixel_sprite.save() mirrors them to face right.

To give a character a hand-drawn pose instead, add frames for that state in its
make_sprite.py; this file only fills in a generic one.
"""

from __future__ import annotations

import copy
from dataclasses import dataclass

from pixel_sprite import H, W, Canvas

SHOULDER = (15, 21)     # near shoulder in the side view
LEGS_TOP = 33           # first row of the legs
FX = {"fx": "#fff4b0", "fx_glow": "#ffd23f", "fx_blue": "#8fd3ff"}


@dataclass
class Limbs:
    sleeve: str          # palette name of the near sleeve
    sleeve_light: str    # its highlight
    hand: str            # skin or glove
    hand_shade: str
    keep_front: bool = False  # keep what the idle pose holds out front (Lyons' guitar)


def _copy(c: Canvas) -> Canvas:
    out = Canvas({})
    out.palette = {**c.palette, **FX}
    out.px = copy.deepcopy(c.px)
    return out


def _line(x0, y0, x1, y1):
    """Pixels on a straight line (Bresenham)."""
    dx, dy = abs(x1 - x0), -abs(y1 - y0)
    sx, sy = (1 if x0 < x1 else -1), (1 if y0 < y1 else -1)
    err, points = dx + dy, []
    while True:
        points.append((x0, y0))
        if (x0, y0) == (x1, y1):
            return points
        e2 = 2 * err
        if e2 >= dy:
            err += dy
            x0 += sx
        if e2 <= dx:
            err += dx
            y0 += sy


def _arm(c: Canvas, limbs: Limbs, end, *, open_hand=False, big=False, shoulder=SHOULDER):
    """A 3-pixel-thick sleeve from the shoulder to `end`, with a hand there."""
    for x, y in _line(*shoulder, *end):
        c.rect(x - 1, y - 1, x + 1, y + 1, limbs.sleeve)
    for x, y in _line(shoulder[0], shoulder[1] - 1, end[0], end[1] - 1):
        c.put(x, y, limbs.sleeve_light)
    ex, ey = end
    size = 2 if big else 1
    c.rect(ex - size - 1, ey - size, ex + size - 1, ey + size, limbs.hand)
    c.put(ex + size - 1, ey + size, limbs.hand_shade)
    if open_hand:  # fingers spread
        c.pixels(limbs.hand, (ex - size - 2, ey - size), (ex - size - 2, ey), (ex - size - 2, ey + size))


def _shift(c: Canvas, y0, y1, dx):
    """Slide rows y0..y1 sideways by dx pixels (a lean)."""
    for y in range(y0, y1 + 1):
        row = c.px[y]
        c.px[y] = ([None] * dx + row[:W - dx]) if dx > 0 else (row[-dx:] + [None] * -dx)


def _tuck_legs(c: Canvas, rows=3):
    """Shorter legs for a jump: drop `rows` leg rows and pull the feet up."""
    legs = c.px[LEGS_TOP + rows:]
    c.px[LEGS_TOP:] = legs + [[None] * W for _ in range(rows)]
    c.px = c.px[:H]


def _streaks(c: Canvas, x, y):
    """Speed lines behind a punch."""
    for dy in (-2, 0, 2):
        c.rect(x + 2, y + dy, x + 4, y + dy, "fx")


def _clear_front_arm(c: Canvas):
    """Remove the idle pose's forearm and hand in front of the body, so a pose has one near arm."""
    for y in range(22, 31):
        for x in range(0, 11):
            c.px[y][x] = None


def pose_frames(side: Canvas, limbs: Limbs) -> dict[str, list[Canvas]]:
    """Left-facing frames for every state Fighter.state can report."""
    base = _copy(side)

    def make(*steps):
        c = _copy(side)
        if not limbs.keep_front:
            _clear_front_arm(c)
        for step in steps:
            step(c)
        c.outline()
        return c

    sx, sy = SHOULDER
    jab = make(lambda c: _arm(c, limbs, (3, sy + 1)),
               lambda c: _streaks(c, 6, sy + 1))
    smash = make(lambda c: _shift(c, 0, LEGS_TOP - 1, -2),            # lean into it
                 lambda c: _arm(c, limbs, (2, sy + 3), big=True, shoulder=(sx - 2, sy + 1)),
                 lambda c: _arm(c, limbs, (3, sy - 1), big=True, shoulder=(sx - 1, sy - 1)),
                 lambda c: _streaks(c, 6, sy + 1))
    special = make(lambda c: _arm(c, limbs, (5, sy), open_hand=True),
                   lambda c: c.ellipse(2.5, sy + 0.5, 2.6, 3.2, "fx_glow"),
                   lambda c: c.ellipse(2.5, sy + 0.5, 1.4, 1.8, "fx"))
    up_special = make(lambda c: _arm(c, limbs, (9, 6)),
                      lambda c: c.rect(7, 2, 11, 2, "fx"))
    grab = make(lambda c: _arm(c, limbs, (4, sy + 4), open_hand=True),
                lambda c: _arm(c, limbs, (5, sy + 1), open_hand=True, shoulder=(sx - 1, sy - 1)))
    jump = make(_tuck_legs, lambda c: _arm(c, limbs, (10, 12)))
    fall = make(lambda c: _arm(c, limbs, (8, 15)))
    hurt = make(lambda c: _shift(c, 0, 20, 2),                          # knocked back
                lambda c: _shift(c, 21, LEGS_TOP - 1, 1),
                lambda c: _arm(c, limbs, (22, 13), open_hand=True, shoulder=(sx + 1, sy)))
    taunt_a = make(lambda c: _arm(c, limbs, (10, 9), open_hand=True))
    taunt_b = make(lambda c: _arm(c, limbs, (7, 10), open_hand=True))
    run_b = _copy(side)
    run_b.px = run_b.px[1:] + [[None] * W]                              # bob up a pixel

    return {
        "idle": [base], "run": [base, run_b], "jump": [jump], "fall": [fall],
        "crouch": [base], "shield": [base], "hurt": [hurt], "taunt": [taunt_a, taunt_b],
        "jab": [jab], "smash": [smash], "special": [special], "up_special": [up_special], "grab": [grab],
    }
