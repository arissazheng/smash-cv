from shared.landmarks import Hand, LandmarkFrame
from vision.smoothing import LandmarkSmoother


def _frame(t, hands):
    return LandmarkFrame(t, [(0.5, 0.5, 0.0, 1.0)] * 33, hands)


def _hand(side, x):
    return Hand(side, [(x, 0.5, 0.0)] * 21)


def test_hands_matched_by_handedness_not_order():
    s = LandmarkSmoother()
    s(_frame(0.0, [_hand("Left", 0.2), _hand("Right", 0.8)]))
    out = s(_frame(0.033, [_hand("Right", 0.8), _hand("Left", 0.2)]))  # order swapped
    by_side = {h.handedness: h.landmarks[0][0] for h in out.hands}
    assert abs(by_side["Left"] - 0.2) < 0.01 and abs(by_side["Right"] - 0.8) < 0.01
