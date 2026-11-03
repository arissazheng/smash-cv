"""Build roster.png: every character's front view side by side on one shelf.

Owner: Person 4.

    python assets/characters/make_roster.py

Run each character's make_sprite.py first. Add new characters to ROSTER.
"""

from pathlib import Path

import cv2

from pixel_sprite import preview

HERE = Path(__file__).resolve().parent
# folder -> label under the sprite ("\n" starts a second line)
ROSTER = {
    "efros": "Prof.\nAlyosha Efros",
    "ng": "Prof.\nRen Ng",
    "liu": "Dean\nTsu-Jae King Liu",
    "lyons": "Chancellor\nRich Lyons",
    "oski": "Cal mascot\nOski the Bear",
}


def main():
    views = {
        label: cv2.imread(str(HERE / folder / "views" / "front.png"), cv2.IMREAD_UNCHANGED)
        for folder, label in ROSTER.items()
    }
    missing = [label for label, img in views.items() if img is None]
    if missing:
        raise SystemExit(f"no front view for {missing}; run their make_sprite.py first")
    cv2.imwrite(str(HERE / "roster.png"), preview(views, title="Smash CV roster"))
    print(f"wrote {HERE / 'roster.png'}")


if __name__ == "__main__":
    main()
