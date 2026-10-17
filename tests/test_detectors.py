from gestures import detectors
from shared.landmarks import LandmarkFrame
from tests.helpers import CALIB, hand, person


def test_lean_deadzone_and_direction():
    assert detectors.lean_move_x(person(lean=0.01), CALIB) == 0.0
    assert detectors.lean_move_x(person(lean=0.06), CALIB) > 0
    assert detectors.lean_move_x(person(lean=-0.06), CALIB) < 0
    assert detectors.lean_move_x(person(lean=0.5), CALIB) == 1.0


def test_lean_is_zero_without_a_person():
    assert detectors.lean_move_x(LandmarkFrame(0.0), CALIB) == 0.0


def test_crouch():
    assert not detectors.is_crouching(person(), CALIB)
    assert detectors.is_crouching(person(nose_drop=0.1), CALIB)


def test_hands_up_needs_both_hands():
    assert detectors.hands_up(person(left_wrist=(0.4, 0.2), right_wrist=(0.6, 0.2)), CALIB)
    assert not detectors.hands_up(person(left_wrist=(0.4, 0.2)), CALIB)


def test_pointer_prefers_pointing_hand():
    frame = person(hands=[hand("Open_Palm", tip=(0.1, 0.1)), hand("Pointing_Up", tip=(0.7, 0.2))])
    assert detectors.pointer(frame) == (0.7, 0.2)
    assert detectors.pointer(person()) is None


def test_one_fast_wrist_is_a_jab_after_the_pair_window():
    punch = detectors.PunchDetector()
    assert punch.update(person(t=0.00), CALIB) is None
    assert punch.update(person(t=0.033, right_wrist=(0.55, 0.6)), CALIB) is None  # spike, waiting for pair
    assert punch.update(person(t=0.066, right_wrist=(0.55, 0.6)), CALIB) is None
    assert punch.update(person(t=0.12, right_wrist=(0.55, 0.6)), CALIB) == "jab"


def test_two_fast_wrists_are_a_smash():
    punch = detectors.PunchDetector()
    punch.update(person(t=0.0), CALIB)
    moved = person(t=0.033, left_wrist=(0.45, 0.6), right_wrist=(0.55, 0.6))
    assert punch.update(moved, CALIB) == "smash"


def test_slow_movement_is_not_a_punch():
    punch = detectors.PunchDetector()
    for i in range(20):
        result = punch.update(person(t=i * 0.033, right_wrist=(0.65 - 0.002 * i, 0.8)), CALIB)
        assert result is None


def test_raising_hands_is_not_a_punch():
    punch = detectors.PunchDetector()
    punch.update(person(t=0.0), CALIB)
    up = person(t=0.033, left_wrist=(0.35, 0.2), right_wrist=(0.65, 0.2))
    assert punch.update(up, CALIB) is None
    assert punch.update(person(t=0.2, left_wrist=(0.35, 0.2), right_wrist=(0.65, 0.2)), CALIB) is None
