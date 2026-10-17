"""Debug drawing on top of the camera image.

Owner: Person 1.
"""

import cv2

from shared.controller_state import ControllerState
from shared.landmarks import INDEX_TIP, POSE_EDGES, LandmarkFrame

GREEN, YELLOW, WHITE, RED = (80, 220, 80), (0, 220, 255), (255, 255, 255), (60, 60, 255)


def draw_landmarks(image, frame: LandmarkFrame | None):
    if frame is None:
        return
    h, w = image.shape[:2]
    if frame.pose:
        pts = [(int(x * w), int(y * h)) for x, y, _, _ in frame.pose]
        for a, b in POSE_EDGES:
            cv2.line(image, pts[a], pts[b], GREEN, 2)
        for i in range(25):  # upper body points only
            cv2.circle(image, pts[i], 3, GREEN, -1)
    for hand in frame.hands:
        for x, y, _ in hand.landmarks:
            cv2.circle(image, (int(x * w), int(y * h)), 2, YELLOW, -1)
        x, y, _ = hand.landmarks[INDEX_TIP]
        cv2.putText(image, hand.gesture, (int(x * w) + 8, int(y * h)), cv2.FONT_HERSHEY_SIMPLEX, 0.5, YELLOW, 1)


def draw_state(image, state: ControllerState, fps: float = 0.0, latency_ms: float = 0.0):
    lines = [
        f"fps {fps:4.1f}   latency {latency_ms:4.0f} ms",
        f"move_x {state.move_x:+.2f}   crouch {state.crouch}   shield {state.shield}",
    ]
    for i, text in enumerate(lines):
        cv2.putText(image, text, (10, 22 + 22 * i), cv2.FONT_HERSHEY_SIMPLEX, 0.55, WHITE, 1)

    # Flash edge-triggered events in big letters.
    events = [name for name, on in (("JUMP", state.jump), ("TAUNT", state.taunt), ("PAUSE", state.pause)) if on]
    if state.attack:
        events.append(state.attack.upper())
    if events:
        cv2.putText(image, " ".join(events), (10, image.shape[0] - 20), cv2.FONT_HERSHEY_SIMPLEX, 1.2, RED, 3)

    # Lean meter.
    h, w = image.shape[:2]
    cx, y = w // 2, 70
    cv2.line(image, (cx - 100, y), (cx + 100, y), WHITE, 1)
    cv2.circle(image, (cx + int(state.move_x * 100), y), 6, YELLOW, -1)
