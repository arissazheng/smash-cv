// Smooth movement between server snapshots.
//
// Owner: Person 4.
//
// Snapshots arrive about 30 times a second, unevenly. We draw at 60 fps a
// little in the past (RENDER_DELAY) so there are almost always two snapshots
// to slide between. Times are in seconds.

export const RENDER_DELAY = 0.1; // about 3 snapshots of cushion for network jitter
const TELEPORT_DISTANCE = 300;    // farther than this in one step = respawn, don't slide

export class SnapshotBuffer {
  constructor({ delay = RENDER_DELAY, maxSize = 60 } = {}) {
    this.delay = delay;
    this.maxSize = maxSize;
    this.snapshots = [];
    this.offset = null; // estimated (client clock - server clock) for the fastest-arriving snapshots
  }

  /** Add a snapshot that arrived at client time `arrival`. */
  push(snapshot, arrival) {
    const last = this.snapshots[this.snapshots.length - 1];
    if (last && snapshot.tick <= last.tick) return; // late or duplicate

    const offset = arrival - snapshot.t;
    if (this.offset === null || offset < this.offset) {
      this.offset = offset;
    } else {
      // Drift up slowly so one unusually fast packet doesn't set the clock forever.
      this.offset += (offset - this.offset) * 0.01;
    }

    this.snapshots.push(snapshot);
    if (this.snapshots.length > this.maxSize) this.snapshots.shift();
  }

  get latest() {
    return this.snapshots[this.snapshots.length - 1] ?? null;
  }

  /** The match as it should look at client time `now`, or null before any snapshot. */
  sample(now) {
    const s = this.snapshots;
    if (s.length === 0) return null;

    const target = now - this.offset - this.delay; // in server time
    if (target <= s[0].t) return s[0];
    if (target >= s[s.length - 1].t) return s[s.length - 1]; // never guess ahead

    let i = s.length - 2;
    while (i > 0 && s[i].t > target) i--;
    const a = s[i];
    const b = s[i + 1];
    return interpolate(a, b, (target - a.t) / (b.t - a.t));
  }
}

/** Positions slide from a to b; everything else (state, damage, ...) comes from b. */
export function interpolate(a, b, alpha) {
  const before = new Map(a.fighters.map((f) => [f.id, f]));
  const fighters = b.fighters.map((fb) => {
    const fa = before.get(fb.id);
    if (!fa || Math.hypot(fb.x - fa.x, fb.y - fa.y) > TELEPORT_DISTANCE) return fb;
    return { ...fb, x: lerp(fa.x, fb.x, alpha), y: lerp(fa.y, fb.y, alpha) };
  });
  return { ...b, t: lerp(a.t, b.t, alpha), fighters };
}

function lerp(from, to, alpha) {
  return from + (to - from) * alpha;
}
