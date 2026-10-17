"""Paths and tunable numbers shared across the project."""

from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MODELS_DIR = ROOT / "models"
RECORDINGS_DIR = ROOT / "recordings"
CALIBRATION_DIR = ROOT / "calibration"
ASSETS_DIR = ROOT / "assets"

POSE_MODEL = MODELS_DIR / "pose_landmarker_lite.task"
GESTURE_MODEL = MODELS_DIR / "gesture_recognizer.task"

CAMERA_INDEX = 0
CAMERA_WIDTH = 640
CAMERA_HEIGHT = 480

SCREEN_WIDTH = 1280
SCREEN_HEIGHT = 720
GAME_FPS = 60
