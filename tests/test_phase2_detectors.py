from gestures import detectors
from tests.helpers import CALIB, hand, person


def test_special_needs_two_palms_close_together():
    near = dict(left_wrist=(0.46, 0.6), right_wrist=(0.54, 0.6))
    two = [hand("Open_Palm"), hand("Open_Palm")]
    assert detectors.detect_special(person(hands=two, **near), CALIB)
    assert not detectors.detect_special(person(hands=two), CALIB)  # wrists far apart
    assert not detectors.detect_special(person(hands=[hand("Open_Palm")], **near), CALIB)


def test_shield_is_crossed_wrists_at_face_height():
    assert detectors.detect_shield(person(left_wrist=(0.55, 0.4), right_wrist=(0.45, 0.4)), CALIB)
    assert not detectors.detect_shield(person(left_wrist=(0.35, 0.4), right_wrist=(0.65, 0.4)), CALIB)  # not crossed
    assert not detectors.detect_shield(person(left_wrist=(0.55, 0.8), right_wrist=(0.45, 0.8)), CALIB)  # too low


def test_up_special_on_pointing_up_edge_not_while_hands_up():
    d = detectors.UpSpecialDetector()
    assert not d.update(person(t=0.0), CALIB)
    assert d.update(person(t=0.1, hands=[hand("Pointing_Up")]), CALIB)
    assert not d.update(person(t=0.2, hands=[hand("Pointing_Up")]), CALIB)  # held, no repeat
    d = detectors.UpSpecialDetector()
    both_up = dict(left_wrist=(0.4, 0.2), right_wrist=(0.6, 0.2), hands=[hand("Pointing_Up")])
    assert not d.update(person(t=0.1, **both_up), CALIB)


def test_up_special_on_fast_upward_wrist():
    d = detectors.UpSpecialDetector()
    d.update(person(t=0.0, right_wrist=(0.65, 0.6)), CALIB)
    assert d.update(person(t=0.05, right_wrist=(0.65, 0.3)), CALIB)  # 1.5 sw in 0.05 s, ends above the nose


def test_grab_open_then_fist_quickly():
    d = detectors.GrabDetector()
    assert not d.update(person(t=0.0, hands=[hand("Open_Palm")]), CALIB)
    assert d.update(person(t=0.1, hands=[hand("Closed_Fist")]), CALIB)
    d = detectors.GrabDetector()
    d.update(person(t=0.0, hands=[hand("Open_Palm")]), CALIB)
    assert not d.update(person(t=0.5, hands=[hand("Closed_Fist")]), CALIB)  # too slow


def test_taunt_after_half_second_once():
    d = detectors.TauntDetector()
    assert not d.update(person(t=0.0, hands=[hand("Thumb_Up")]), CALIB)
    assert d.update(person(t=0.6, hands=[hand("Thumb_Up")]), CALIB)
    assert not d.update(person(t=0.7, hands=[hand("Thumb_Up")]), CALIB)


def test_pause_one_still_palm_for_a_second():
    d = detectors.PauseDetector()
    assert not d.update(person(t=0.0, hands=[hand("Open_Palm")]), CALIB)
    assert d.update(person(t=1.1, hands=[hand("Open_Palm")]), CALIB)
    d = detectors.PauseDetector()
    two = [hand("Open_Palm"), hand("Open_Palm")]
    d.update(person(t=0.0, hands=two), CALIB)
    assert not d.update(person(t=1.1, hands=two), CALIB)  # two palms is special, not pause
