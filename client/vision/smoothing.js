// One Euro filter, port of vision/smoothing.py. Owner: Person 1.
class OneEuro {
  constructor(minCutoff = 1.0, beta = 0.05, dCutoff = 1.0) {
    Object.assign(this, { minCutoff, beta, dCutoff, x: null, dx: 0, t: null });
  }
  static alpha(cutoff, dt) { return 1 / (1 + 1 / (2 * Math.PI * cutoff) / dt); }
  filter(x, t) {
    if (this.x === null || t <= this.t) { this.x = x; this.t = t; return x; }
    const dt = t - this.t;
    const aD = OneEuro.alpha(this.dCutoff, dt);
    this.dx = aD * ((x - this.x) / dt) + (1 - aD) * this.dx;
    const a = OneEuro.alpha(this.minCutoff + this.beta * Math.abs(this.dx), dt);
    this.x = a * x + (1 - a) * this.x;
    this.t = t;
    return this.x;
  }
}

// Smooths pose x/y and hand x/y (hands keyed by handedness, so order swaps don't matter).
export class LandmarkSmoother {
  constructor(opts = {}) { this.opts = opts; this.f = new Map(); }
  _f(key) {
    if (!this.f.has(key)) this.f.set(key, new OneEuro(this.opts.minCutoff, this.opts.beta, this.opts.dCutoff));
    return this.f.get(key);
  }
  smooth(frame) {
    const t = frame.t;
    if (!frame.pose) { this.f.clear(); return frame; }
    const pose = frame.pose.map(([x, y, z, v], i) => [this._f(`p${i}x`).filter(x, t), this._f(`p${i}y`).filter(y, t), z, v]);
    const seen = new Set();
    const hands = frame.hands.map((h) => {
      seen.add(h.side);
      return { ...h, lm: h.lm.map(([x, y, z], i) => [this._f(`${h.side}${i}x`).filter(x, t), this._f(`${h.side}${i}y`).filter(y, t), z]) };
    });
    for (const k of [...this.f.keys()]) if (/^(Left|Right|Unknown)/.test(k) && !seen.has(k.match(/^(Left|Right|Unknown)/)[1])) this.f.delete(k);
    return { t, pose, hands };
  }
}
