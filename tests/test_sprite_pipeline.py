import cv2
import numpy as np

from ui.sprite_pipeline import slice_sheet


def test_slices_sprites_in_reading_order(tmp_path):
    sheet = np.full((100, 200, 3), (255, 0, 255), np.uint8)  # magenta background
    cv2.rectangle(sheet, (10, 10), (40, 60), (0, 0, 255), -1)    # top-left sprite
    cv2.rectangle(sheet, (120, 15), (160, 55), (0, 255, 0), -1)  # top-right sprite
    path = tmp_path / "sheet.png"
    cv2.imwrite(str(path), sheet)

    count = slice_sheet(path, tmp_path / "out")
    assert count == 2
    first = cv2.imread(str(tmp_path / "out" / "frame_00.png"), cv2.IMREAD_UNCHANGED)
    assert first.shape[2] == 4                      # has alpha
    assert tuple(first[first.shape[0] // 2, first.shape[1] // 2][:3]) == (0, 0, 255)  # the red one
