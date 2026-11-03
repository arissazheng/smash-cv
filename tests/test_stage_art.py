"""The stage art must line up with the platforms the game actually uses.

assets/stages/make_memorial_glade.py draws at half the game's resolution. If
someone moves a platform in game/stage.py without redrawing the art (or the
other way round), players would stand on thin air; these tests catch that.
"""

import importlib.util
import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")

import cv2  # noqa: E402

from game.stage import battlefield  # noqa: E402
from shared import config  # noqa: E402

STAGES = config.ASSETS_DIR / "stages"
GRASS_TOP = (0x7a, 0xd3, 0x5a)  # RGB of the light top row of grass


def _art_script():
    spec = importlib.util.spec_from_file_location("make_memorial_glade", STAGES / "make_memorial_glade.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _half(rect):
    return (rect.x // 2, rect.top // 2, (rect.right - 1) // 2)


def test_art_script_uses_the_game_platforms():
    stage, art = battlefield(), _art_script()
    assert art.MAIN == _half(stage.main)
    assert art.LEDGES == [_half(p) for p in stage.platforms]


def test_stage_image_has_grass_where_fighters_stand():
    stage = battlefield()
    image = cv2.imread(str(STAGES / stage.background))
    assert image is not None, f"{stage.background} missing; run python assets/stages/make_memorial_glade.py"
    assert image.shape[:2] == (config.SCREEN_HEIGHT // 2, config.SCREEN_WIDTH // 2)
    for rect in [stage.main, *stage.platforms]:
        x0, top, x1 = _half(rect)
        for x in (x0, (x0 + x1) // 2, x1):
            b, g, r = image[top, x]
            assert (r, g, b) == GRASS_TOP, f"no grass at ({x}, {top}) for platform {rect}"
