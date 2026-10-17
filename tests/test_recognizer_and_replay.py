from controllers.replay_controller import ReplayController
from gestures.recognizer import GestureRecognizer
from gestures.recording import read_recording, write_recording
from shared.landmarks import LandmarkFrame
from tests.helpers import CALIB, hand, person

HANDS_UP = dict(left_wrist=(0.4, 0.2), right_wrist=(0.6, 0.2))


def test_jump_fires_once_while_hands_stay_up():
    rec = GestureRecognizer(CALIB)
    assert not rec.update(person(t=0.0)).jump
    assert rec.update(person(t=0.1, **HANDS_UP)).jump
    assert not rec.update(person(t=0.2, **HANDS_UP)).jump
    assert not rec.update(person(t=0.3)).jump
    assert rec.update(person(t=0.4, **HANDS_UP)).jump


def test_nobody_in_frame_is_neutral():
    state = GestureRecognizer(CALIB).update(LandmarkFrame(0.0))
    assert state.move_x == 0 and not state.jump and state.attack is None


def test_attack_cooldown():
    rec = GestureRecognizer(CALIB, attack_cooldown=0.3)
    both = dict(left_wrist=(0.45, 0.6), right_wrist=(0.55, 0.6))
    rec.update(person(t=0.0))
    assert rec.update(person(t=0.033, **both)).attack == "smash"
    rec.update(person(t=0.066))
    assert rec.update(person(t=0.1, **both)).attack is None  # still cooling down


def test_landmark_json_round_trip():
    frame = person(t=1.5, lean=0.05, hands=[hand("Thumb_Up")])
    back = LandmarkFrame.from_json(frame.to_json())
    assert back.timestamp == 1.5
    assert back.pose[0][:2] == (0.55, 0.4)
    assert back.hands[0].gesture == "Thumb_Up"


def test_replay_feeds_frames_in_real_time(tmp_path):
    frames = [person(t=10.0), person(t=10.1, **HANDS_UP), person(t=10.2, **HANDS_UP)]
    path = tmp_path / "jump.jsonl"
    write_recording(path, frames, label="jump", player="test")
    assert read_recording(path)[0]["label"] == "jump"

    now = [0.0]
    replay = ReplayController(path, CALIB, loop=False, clock=lambda: now[0])
    assert not replay.poll().jump      # only the first frame is due
    now[0] = 0.15
    assert replay.poll().jump          # second frame raises hands
    assert not replay.poll().jump      # edge already reported
    now[0] = 1.0
    replay.poll()
    assert replay.finished


def test_replay_loops_with_increasing_timestamps(tmp_path):
    path = tmp_path / "idle.jsonl"
    write_recording(path, [person(t=0.0), person(t=0.1)])
    now = [0.0]
    replay = ReplayController(path, CALIB, loop=True, clock=lambda: now[0])
    stamps = []
    for step in range(10):
        now[0] = step * 0.1
        state = replay.poll()
        stamps.append(state.timestamp)
    assert stamps == sorted(stamps)
    assert not replay.finished
