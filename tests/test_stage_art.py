"""Every stage's art must line up with the platforms the game actually uses.

The art scripts in assets/stages/ draw at half the game's resolution. If
someone moves a platform in game/stage.py without redrawing the art (or the
other way round), players would stand on thin air; these tests catch that.
"""

import importlib.util
import os
import sys

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")

import cv2  # noqa: E402
import pytest  # noqa: E402

from game.stage import STAGES  # noqa: E402
from shared import config  # noqa: E402

STAGE_DIR = config.ASSETS_DIR / "stages"
MEMORIAL_GRASS_TOP = "#7ad35a"  # light top row of the grass on Memorial Glade


def _art_script(stage_id):
    sys.path.insert(0, str(STAGE_DIR))
    path = STAGE_DIR / f"make_{stage_id}.py"
    spec = importlib.util.spec_from_file_location(f"make_{stage_id}", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _half(rect):
    return (rect.x // 2, rect.top // 2, (rect.right - 1) // 2)


@pytest.mark.parametrize("stage_id", sorted(STAGES))
def test_art_script_uses_the_game_platforms(stage_id):
    stage, art = STAGES[stage_id](), _art_script(stage_id)
    assert art.MAIN == _half(stage.main)
    assert list(art.LEDGES) == [_half(p) for p in stage.platforms]


@pytest.mark.parametrize("stage_id", sorted(STAGES))
def test_stage_image_has_a_surface_where_fighters_stand(stage_id):
    stage, art = STAGES[stage_id](), _art_script(stage_id)
    tops = getattr(art, "PLATFORM_TOPS", {MEMORIAL_GRASS_TOP})
    image = cv2.imread(str(STAGE_DIR / stage.background))
    assert image is not None, f"{stage.background} missing; run python assets/stages/make_{stage_id}.py"
    assert image.shape[:2] == (config.SCREEN_HEIGHT // 2, config.SCREEN_WIDTH // 2)
    for rect in [stage.main, *stage.platforms]:
        x0, top, x1 = _half(rect)
        for x in (x0, (x0 + x1) // 2, x1):
            b, g, r = image[top, x]
            assert f"#{r:02x}{g:02x}{b:02x}" in tops, f"{stage_id}: no platform surface at ({x}, {top}) for {rect}"
