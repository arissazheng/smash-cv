// A pretend server that sends scripted messages, so the renderer can be built
// and tested before the real server exists.
//
// Owner: Person 4.
//
// It sends the same message shapes as the real server (see protocol.js):
// match_start, then snapshots about 30 times a second, with hit, KO and
// game-over events along the way. Snapshots can arrive with network-like
// jitter so you can see what snapshot smoothing does. The match restarts a
// few seconds after "GAME!".

import { SNAPSHOT_RATE } from "./protocol.js";

// Same layout as battlefield() in game/stage.py.
export const MEMORIAL_GLADE = {
  name: "Memorial Glade",
  width: 1280,
  height: 720,
  main: [240, 520, 800, 40],
  platforms: [[340, 380, 180, 12], [760, 380, 180, 12], [550, 250, 180, 12]],
  background: "memorial_glade.png",
};

const GROUND_Y = 520;
const BODY = { w: 60, h: 90 };
const KO_EVERY = 15;     // seconds between Oski's KOs
export const MATCH_LENGTH = 3 * KO_EVERY; // Oski has 3 stocks
const RESTART_AFTER = 4; // seconds of "GAME!" before a new match

/** Where each scripted fighter is at time t (seconds). Pure, so tests can call it. */
export function scriptedFighters(t) {
  return [lyons(t), oski(t)];
}

// Player 1 (Lyons) runs back and forth, jumps every 2.4 s and jabs every 1.5 s.
function lyons(t) {
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
    character: "lyons",
    x, y, ...BODY, facing, state,
    damage: (Math.floor(t / 5) * 4) % 160,
    stocks: 3,
    shield: false,
    life_id: 0,
    invulnerable: false,
    hitbox: jabbing ? [x + facing * 50 - 25, y - 70, 50, 30] : null,
  };
}

// Player 2 (Oski) wanders slowly, gets hit every 3 s, shields now and then, and is
// KO'd every 15 s.
function oski(t) {
  const x = 640 - 200 * Math.sin(t * 0.5);
  const hurt = t % 3 < 0.4;
  const shield = !hurt && t % 7 > 6;
  return {
    id: 1,
    character: "oski",
    x, y: GROUND_Y, ...BODY,
    facing: Math.cos(t * 0.5) >= 0 ? -1 : 1,
    state: hurt ? "hurt" : shield ? "shield" : "run",
    damage: (Math.floor(t / 3) * 7) % 160,
    stocks: Math.max(0, 3 - Math.floor(t / KO_EVERY)),
    shield,
    life_id: Math.floor(t / KO_EVERY),
    invulnerable: t > KO_EVERY && t % KO_EVERY < 1.5,   // blinks after each respawn
    hitbox: null,
  };
}

/** Events between script times `prev` and `t`. Pure, so tests can call it. */
export function scriptedEvents(prev, t) {
  const events = [];
  const crossed = (period) => Math.floor(t / period) > Math.floor(prev / period);
  const [b, s] = scriptedFighters(t);

  if (crossed(3) && t < MATCH_LENGTH) {
    events.push({ kind: "hit", attacker: 0, target: 1, attack: crossed(9) ? "smash" : "jab",
      damage: crossed(9) ? 15 : 7, shielded: false, x: s.x - b.facing * 20, y: s.y - 55 });
  }
  if (crossed(KO_EVERY) && t <= MATCH_LENGTH + 0.1) {
    events.push({ kind: "ko", player: 1, stocks_left: s.stocks, x: -60, y: 300 });
    if (s.stocks === 0) events.push({ kind: "game_over", winner: 0 });
  }
  return events;
}

export class FakeServer {
  /** @param {(message: object) => void} onMessage */
  constructor(onMessage, { jitter = 0.03 } = {}) {
    this.onMessage = onMessage;
    this.jitter = jitter; // max random extra delay per message, seconds
    this._timer = null;
  }

  start() {
    this._newMatch();
    this._timer = setInterval(() => this._step(), 1000 / SNAPSHOT_RATE);
  }

  stop() {
    clearInterval(this._timer);
  }

  _newMatch() {
    this.onMessage({
      type: "match_start",
      stage: MEMORIAL_GLADE,
      players: [
        { id: 0, name: "Arissa", character: "lyons" },
        { id: 1, name: "CPU", character: "oski" },
      ],
    });
    this._start = performance.now() / 1000;
    this._tick = 0;
    this._prevT = 0;
  }

  _step() {
    const t = performance.now() / 1000 - this._start;
    if (t > MATCH_LENGTH + RESTART_AFTER) {
      this._newMatch();
      return;
    }
    this._tick += 1;
    const scriptT = Math.min(t, MATCH_LENGTH); // freeze the picture after GAME!
    this._send({ type: "snapshot", tick: this._tick, t, fighters: scriptedFighters(scriptT) });
    for (const e of scriptedEvents(this._prevT, t)) {
      this._send({ type: "event", tick: this._tick, t, ...e });
    }
    this._prevT = t;
  }

  // Real networks deliver unevenly; this makes messages arrive late by a random amount.
  _send(message) {
    setTimeout(() => this.onMessage(message), Math.random() * this.jitter * 1000);
  }
}
