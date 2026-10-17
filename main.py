"""Smash CV entry point.

    python main.py overlay                    # camera + skeleton + live ControllerState (debug)
    python main.py calibrate --name arissa    # sit neutral for 3 s, saves calibration/arissa.json
    python main.py play --calibration arissa  # you (camera) vs CPU
    python main.py play --replay recordings/jab/arissa_20261017_120000.jsonl   # recording vs CPU
"""

import argparse
from pathlib import Path
import time


def overlay(args):
    import cv2
    from controllers.camera_controller import CameraController
    from vision.calibration import Calibration
    from vision.camera import CameraSource
    from vision.overlay import draw_landmarks, draw_state

    camera = CameraSource().start()
    controller = CameraController(camera, Calibration.load(args.calibration))
    shown_state, shown_until = None, 0.0
    try:
        while True:
            state = controller.poll()
            # Keep events on screen for half a second so they're readable.
            if state.jump or state.attack or state.taunt or state.pause:
                shown_state, shown_until = state, time.monotonic() + 0.5
            image, frame = camera.latest()
            if image is not None:
                image = image.copy()
                draw_landmarks(image, frame)
                display = shown_state if time.monotonic() < shown_until else state
                draw_state(image, display, camera.fps, camera.latency_ms)
                cv2.imshow("smash-cv overlay (q to quit)", image)
            if cv2.waitKey(1) & 0xFF == ord("q"):
                break
    finally:
        camera.stop()
        cv2.destroyAllWindows()


def calibrate(args):
    import cv2
    from vision.calibration import Calibration
    from vision.camera import CameraSource
    from vision.overlay import draw_landmarks

    camera = CameraSource(smooth=False).start()
    frames, last_t = [], None
    start = time.monotonic()
    try:
        while time.monotonic() - start < 5.0:
            image, frame = camera.latest()
            if image is None:
                time.sleep(0.01)
                continue
            elapsed = time.monotonic() - start
            if elapsed >= 2.0 and frame is not None and frame.timestamp != last_t:
                frames.append(frame)
                last_t = frame.timestamp
            image = image.copy()
            draw_landmarks(image, frame)
            text = "sit neutral, face the camera" if elapsed < 2.0 else "hold still..."
            cv2.putText(image, text, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (255, 255, 255), 2)
            cv2.imshow("calibrate", image)
            cv2.waitKey(1)
    finally:
        camera.stop()
        cv2.destroyAllWindows()

    calibration = Calibration.from_frames(frames)
    print(f"saved {calibration.save(args.name)}: {calibration}")


def play(args):
    from controllers.camera_controller import CameraController
    from controllers.replay_controller import ReplayController
    from game.cpu import CpuController
    from game.engine import Game
    from vision.calibration import Calibration

    calibration = Calibration.load(args.calibration)
    camera = None
    if args.replay:
        p1 = ReplayController(Path(args.replay), calibration, player_id=0)
    else:
        from vision.camera import CameraSource
        camera = CameraSource().start()
        p1 = CameraController(camera, calibration, player_id=0)

    game = Game(stocks=args.stocks, camera=camera)
    # TODO(Person 1 + Person 3): second camera player instead of the CPU.
    p2 = CpuController(game.fighters[1], game.fighters[0], player_id=1)
    game.set_controllers([p1, p2])
    try:
        game.run()
    finally:
        if camera is not None:
            camera.stop()


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("overlay", help="camera debug view")
    p.add_argument("--calibration", default="default")
    p.set_defaults(func=overlay)

    p = sub.add_parser("calibrate", help="record your neutral pose")
    p.add_argument("--name", default="default")
    p.set_defaults(func=calibrate)

    p = sub.add_parser("play", help="play a match")
    p.add_argument("--calibration", default="default")
    p.add_argument("--replay", help="drive player 1 from a recording instead of the camera")
    p.add_argument("--stocks", type=int, default=2)
    p.set_defaults(func=play)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
