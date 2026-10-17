"""Download the MediaPipe model files into models/.

    python tools/download_models.py
"""

from pathlib import Path
import sys
import urllib.request

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from shared import config  # noqa: E402

BASE = "https://storage.googleapis.com/mediapipe-models"
MODELS = {
    config.POSE_MODEL: f"{BASE}/pose_landmarker/pose_landmarker_lite/float16/latest/pose_landmarker_lite.task",
    config.GESTURE_MODEL: f"{BASE}/gesture_recognizer/gesture_recognizer/float16/latest/gesture_recognizer.task",
}


def main():
    config.MODELS_DIR.mkdir(exist_ok=True)
    for path, url in MODELS.items():
        if path.exists():
            print(f"already have {path.name}")
            continue
        print(f"downloading {path.name} ...")
        urllib.request.urlretrieve(url, path)
        print(f"  saved {path} ({path.stat().st_size // 1024} KB)")


if __name__ == "__main__":
    main()
