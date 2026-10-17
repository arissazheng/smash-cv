"""Record a labeled gesture clip from the webcam.

Owner: Person 2.

    python -m gestures.recorder --label jab --player arissa --seconds 5

Shows the overlay, counts down 3 seconds, records, then saves to
recordings/<label>/<player>_<timestamp>.jsonl. Record "idle" and
"talking_with_hands" clips too: they catch false positives.
"""

import argparse
from datetime import datetime
import time

import cv2

from gestures.recording import write_recording
from shared import config
from vision.camera import CameraSource
from vision.overlay import draw_landmarks


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--label", required=True, help="gesture name, e.g. jab, jump, idle")
    parser.add_argument("--player", required=True, help="who is recording")
    parser.add_argument("--seconds", type=float, default=5.0)
    parser.add_argument("--countdown", type=float, default=3.0)
    args = parser.parse_args()

    camera = CameraSource().start()
    frames, last_t = [], None
    start = time.monotonic()
    try:
        while True:
            elapsed = time.monotonic() - start
            if elapsed > args.countdown + args.seconds:
                break
            image, frame = camera.latest()
            if image is None:
                time.sleep(0.01)
                continue
            image = image.copy()
            draw_landmarks(image, frame)

            recording = elapsed >= args.countdown
            if recording and frame is not None and frame.timestamp != last_t:
                frames.append(frame)
                last_t = frame.timestamp
            text = f"REC {args.label}" if recording else f"get ready: {args.countdown - elapsed:.1f}"
            cv2.putText(image, text, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (60, 60, 255), 2)
            cv2.imshow("recorder", image)
            if cv2.waitKey(1) & 0xFF == ord("q"):
                break
    finally:
        camera.stop()
        cv2.destroyAllWindows()

    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    path = config.RECORDINGS_DIR / args.label / f"{args.player}_{stamp}.jsonl"
    write_recording(path, frames, label=args.label, player=args.player)
    print(f"saved {len(frames)} frames to {path}")


if __name__ == "__main__":
    main()
