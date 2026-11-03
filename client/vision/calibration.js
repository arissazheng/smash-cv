// Calibration screen logic. Owner: Person 1.
// Per README, the server computes the Calibration from the `calibrate` message (~2 s of frames).
// collectFrames() gathers those frames; fromFrames() is a port of vision/calibration.py for local preview only.
const mean = (a) => a.reduce((s, v) => s + v, 0) / a.length;

/** Collects frames for `seconds`. getFrame() returns a LandmarkFrame or null; onTick(secondsLeft, hasPerson) updates the UI. */
export function collectFrames(getFrame, { seconds = 2, onTick = () => {} } = {}) {
  return new Promise((resolve) => {
    const frames = [], start = performance.now();
    (function step() {
      const left = seconds - (performance.now() - start) / 1000;
      const f = getFrame();
      if (f) frames.push(f);
      onTick(Math.max(left, 0), !!f?.pose);
      left > 0 ? requestAnimationFrame(step) : resolve(frames);
    })();
  });
}

export function fromFrames(frames) {
  const u = frames.filter((f) => f.pose);
  if (u.length < 10) throw new Error(`only ${u.length} frames with a person in them; need at least 10`);
  const L = u.map((f) => f.pose[11]), R = u.map((f) => f.pose[12]);
  return {
    center_x: mean(L.map((l, i) => (l[0] + R[i][0]) / 2)),
    shoulder_y: mean(L.map((l, i) => (l[1] + R[i][1]) / 2)),
    nose_y: mean(u.map((f) => f.pose[0][1])),
    shoulder_width: mean(L.map((l, i) => Math.abs(l[0] - R[i][0]))),
  };
}
