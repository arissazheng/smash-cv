// A pretend server that sends scripted messages, so the renderer can be built
// and tested before the real server exists.
//
// Owner: Person 4.
//
// It sends the same message shapes as the real server (see protocol.js): one
// match_start, then snapshots about 30 times a second, optionally with
// network-like jitter so you can see what snapshot smoothing does.

import { SNAPSHOT_RATE } from "./protocol.js";

// Same layout as battlefield() in game/stage.py.
export const MEMORIAL_GLADE = {
  name: "Memorial Glade",
  width: 1280,
  height: 720,
  main: [240, 520, 800, 40],
  platforms: [[340, 380, 180, 12], [760, 380, 180, 12], [550, 250, 180, 12]],
  background: null,
};

const GROUND_Y = 520;
const BODY = { w: 60, h: 90 };

/** Where each scripted fighter is at time t (seconds). Pure, so tests can call it. */
export function scriptedFighters(t) {
  return [bear(t), squirrel(t)];
}

// Player 1 runs back and forth, jumps every 2.4 s and jabs every 1.5 s.
function bear(t) {
  const x = 640 + 280 * Math.sin(t * 0.9);
  const facing = Math.cos(t * 0.9) >= 0 ? 1 : -1;
  const jumpPhase = t % 2.4;
  const airborne = jumpPhase < 0.6;
  const p = jumpPhase / 0.6;
  const y = airborne ? GROUND_Y - 4 * 150 * p * (1 - p) : GROUND_Y;
  const jabbing = !airborne && t % 1.5 < 0.25;

  let state = "run";
  if (airborne) state = p < 0.5 ? "jump" : "fall";
  else if (jabbing) state = "jab";

  return {
    id: 0,
    character: "golden_bear",
    x, y, ...BODY, facing, state,
    damage: (Math.floor(t / 5) * 4) % 160,
    stocks: 3 - (Math.floor(t / 40) % 3),
    shield: false,
    hitbox: jabbing ? [x + facing * 50 - 25, y - 70, 50, 30] : null,
  };
}

// Player 2 wanders slowly, gets hit every 3 s and shields now and then.
function squirrel(t) {
  const x = 640 - 200 * Math.sin(t * 0.5);
  const hurt = t % 3 < 0.4;
  const shield = !hurt && t % 7 > 6;
  return {
    id: 1,
    character: "campus_squirrel",
    x, y: GROUND_Y, ...BODY,
    facing: Math.cos(t * 0.5) >= 0 ? -1 : 1,
    state: hurt ? "hurt" : shield ? "shield" : "run",
    damage: (Math.floor(t / 3) * 7) % 160,
    stocks: 3,
    shield,
    hitbox: null,
  };
}

export class FakeServer {
  /** @param {(message: object) => void} onMessage */
  constructor(onMessage, { jitter = 0.03 } = {}) {
    this.onMessage = onMessage;
    this.jitter = jitter; // max random extra delay per snapshot, seconds
    this._timer = null;
  }

  start() {
    this.onMessage({
      type: "match_start",
      stage: MEMORIAL_GLADE,
      players: [
        { id: 0, name: "Arissa", character: "golden_bear" },
        { id: 1, name: "CPU", character: "campus_squirrel" },
      ],
    });
    const start = performance.now() / 1000;
    let tick = 0;
    this._timer = setInterval(() => {
      tick += 1;
      const t = performance.now() / 1000 - start;
      const snapshot = { type: "snapshot", tick, t, fighters: scriptedFighters(t) };
      // Real networks deliver unevenly; this makes snapshots arrive late by a random amount.
      const delay = Math.random() * this.jitter * 1000;
      setTimeout(() => this.onMessage(snapshot), delay);
    }, 1000 / SNAPSHOT_RATE);
  }

  stop() {
    clearInterval(this._timer);
  }
}
