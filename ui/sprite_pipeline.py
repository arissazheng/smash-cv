"""OpenCV sprite pipeline: sprite sheet -> one transparent PNG per frame.

Owner: Person 4.

    python -m ui.sprite_pipeline sheet.png assets/characters/mario/run

1. Remove the background: the color in the top-left corner (most ripped
   sheets use a flat background) becomes transparent.
2. Find each sprite with contour detection on the alpha mask.
3. Crop each sprite and save them in reading order (top to bottom, left to
   right) as frame_00.png, frame_01.png, ...

TODO(Person 4): align frames by their bottom-center so the feet don't jitter,
and handle sheets with labels or grid lines.
"""

import argparse
from pathlib import Path

import cv2
import numpy as np


def remove_background(bgr: np.ndarray, tolerance: int = 12) -> np.ndarray:
    """Returns BGRA with every pixel close to the corner color made transparent."""
    background = bgr[0, 0].astype(int)
    distance = np.abs(bgr.astype(int) - background).max(axis=2)
    alpha = np.where(distance > tolerance, 255, 0).astype(np.uint8)
    return np.dstack([bgr, alpha])


def find_sprites(bgra: np.ndarray, min_area: int = 64, merge_px: int = 3) -> list[tuple[int, int, int, int]]:
    """Bounding boxes (x, y, w, h) of each sprite, in reading order."""
    mask = bgra[:, :, 3]
    # Dilate a little so detached bits of one sprite (a hand, a sword) join the body.
    mask = cv2.dilate(mask, np.ones((merge_px * 2 + 1, merge_px * 2 + 1), np.uint8))
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    boxes = [cv2.boundingRect(c) for c in contours if cv2.contourArea(c) >= min_area]
    if not boxes:
        return []
    row_height = np.median([h for _, _, _, h in boxes])
    return sorted(boxes, key=lambda b: (round(b[1] / row_height), b[0]))


def slice_sheet(sheet_path: Path, out_dir: Path, tolerance: int = 12) -> int:
    bgr = cv2.imread(str(sheet_path), cv2.IMREAD_COLOR)
    if bgr is None:
        raise FileNotFoundError(sheet_path)
    bgra = remove_background(bgr, tolerance)
    out_dir.mkdir(parents=True, exist_ok=True)
    boxes = find_sprites(bgra)
    for i, (x, y, w, h) in enumerate(boxes):
        cv2.imwrite(str(out_dir / f"frame_{i:02d}.png"), bgra[y:y + h, x:x + w])
    return len(boxes)


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("sheet", type=Path)
    parser.add_argument("out_dir", type=Path)
    parser.add_argument("--tolerance", type=int, default=12)
    args = parser.parse_args()
    count = slice_sheet(args.sheet, args.out_dir, args.tolerance)
    print(f"wrote {count} frames to {args.out_dir}")


if __name__ == "__main__":
    main()
