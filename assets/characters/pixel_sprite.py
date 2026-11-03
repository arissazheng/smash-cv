"""Shared toolkit for the retro pixel character sprites.

Owner: Person 4.

Each character has a make_sprite.py in its own folder that paints flat color
regions on a 32x44 grid with this Canvas, adds a 1-pixel dark outline with
outline(), then calls save(). save() mirrors the left view into the right view
and writes:

    <character>/views/front.png, left.png, right.png   32x44, transparent
    <character>/idle/frame_00.png                       facing right, what the game loads
    <character>/preview.png                             all three views at 8x on a shelf
"""

from pathlib import Path

import cv2
import numpy as np

W, H = 32, 44
OUTLINE = "#2a1e1c"


class Canvas:
    def __init__(self, palette: dict[str, str]):
        self.palette = {"outline": OUTLINE, **palette}
        self.px: list[list[str | None]] = [[None] * W for _ in range(H)]

    def put(self, x, y, color):
        if 0 <= x < W and 0 <= y < H:
            self.px[y][x] = color

    def get(self, x, y):
        return self.px[y][x] if 0 <= x < W and 0 <= y < H else None

    def rect(self, x0, y0, x1, y1, color):
        for y in range(y0, y1 + 1):
            for x in range(x0, x1 + 1):
                self.put(x, y, color)

    def ellipse(self, cx, cy, rx, ry, color):
        for y in range(H):
            for x in range(W):
                if ((x + 0.5 - cx) / rx) ** 2 + ((y + 0.5 - cy) / ry) ** 2 <= 1:
                    self.put(x, y, color)

    def pixels(self, color, *points):
        for x, y in points:
            self.put(x, y, color)

    def recolor(self, old: tuple[str, ...], new: str, where):
        """Repaint pixels of the `old` colors for which where(x, y) is true."""
        for y in range(H):
            for x in range(W):
                if self.px[y][x] in old and where(x, y):
                    self.px[y][x] = new

    def outline(self):
        """Dark 1-pixel border around everything that's drawn."""
        border = [
            (x, y)
            for y in range(H)
            for x in range(W)
            if self.px[y][x] is None
            and any(self.get(x + dx, y + dy) not in (None, "outline") for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)))
        ]
        for x, y in border:
            self.px[y][x] = "outline"

    def to_bgra(self) -> np.ndarray:
        img = np.zeros((H, W, 4), np.uint8)
        for y in range(H):
            for x in range(W):
                name = self.px[y][x]
                if name:
                    hex_color = self.palette[name]
                    r, g, b = (int(hex_color[i:i + 2], 16) for i in (1, 3, 5))
                    img[y, x] = (b, g, r, 255)
        return img


def preview(views: dict[str, np.ndarray], scale: int = 8) -> np.ndarray:
    """Views side by side on a dark shelf, like a roster sheet."""
    pad, gap, shelf_h = 24, 40, 10
    width = pad * 2 + len(views) * W * scale + (len(views) - 1) * gap
    height = pad * 2 + H * scale + shelf_h + 30
    sheet = np.zeros((height, width, 4), np.uint8)
    sheet[:] = (0x2e, 0x1f, 0x2b, 255)  # BGRA dark plum
    floor_y = pad + H * scale
    sheet[floor_y:floor_y + shelf_h] = (0x55, 0x3d, 0x52, 255)
    sheet[floor_y + shelf_h:floor_y + shelf_h + 6] = (0x24, 0x18, 0x22, 255)

    for i, (name, img) in enumerate(views.items()):
        big = cv2.resize(img, (W * scale, H * scale), interpolation=cv2.INTER_NEAREST)
        x0 = pad + i * (W * scale + gap)
        region = sheet[pad:pad + H * scale, x0:x0 + W * scale]
        alpha = big[:, :, 3:4] / 255.0
        region[:] = (big * alpha + region * (1 - alpha)).astype(np.uint8)
        label = name.upper()
        (tw, _), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_DUPLEX, 0.7, 1)
        cv2.putText(sheet, label, (x0 + (W * scale - tw) // 2, height - 12),
                    cv2.FONT_HERSHEY_DUPLEX, 0.7, (0xd8, 0xcf, 0xe0, 255), 1, cv2.LINE_AA)
    return sheet


def save(folder: Path, front: Canvas, left: Canvas) -> None:
    """Mirror left into right and write every output file.

    Call outline() on each canvas first, then add any inner lines.
    """
    left_img = left.to_bgra()
    views = {"left": left_img, "front": front.to_bgra(), "right": cv2.flip(left_img, 1)}

    (folder / "views").mkdir(exist_ok=True)
    for name, img in views.items():
        cv2.imwrite(str(folder / "views" / f"{name}.png"), img)
    (folder / "idle").mkdir(exist_ok=True)
    cv2.imwrite(str(folder / "idle" / "frame_00.png"), views["right"])  # game sprites face right
    cv2.imwrite(str(folder / "preview.png"), preview(views))
    print(f"wrote views/, idle/frame_00.png and preview.png in {folder}")
