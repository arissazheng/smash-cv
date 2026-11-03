// The renderer must be able to read the server's real messages.
//
// shared/protocol_examples/*.json are built from the Python game and checked
// by tests/test_protocol.py on the server side. Here we check that the
// browser expects exactly those fields and can draw every example without a
// NaN or "undefined" reaching the screen. If this fails after a server change,
// update protocol.js and the renderer to match, or ask for the change to be
// undone.

import assert from "node:assert/strict";
import { readFileSync, readdirSync } from "node:fs";
import { test } from "node:test";

import { Effects } from "../effects.js";
import { scriptedEvents, scriptedFighters, MATCH_LENGTH } from "../fake_server.js";
import { EVENT_FIELDS, FIGHTER_FIELDS, LOBBY_PLAYER_FIELDS, STAGE_FIELDS } from "../protocol.js";
import { Renderer } from "../renderer.js";
import { interpolate } from "../interpolation.js";
import { PROTOCOL_VERSION } from "../../net.js";
import { CHARACTERS } from "../../characters.js";

const EXAMPLES_DIR = new URL("../../../shared/protocol_examples/", import.meta.url);
const example = (name) => JSON.parse(readFileSync(new URL(`${name}.json`, EXAMPLES_DIR), "utf8"));
const sorted = (keys) => [...keys].sort();

test("examples exist for every message the renderer handles", () => {
  const names = readdirSync(EXAMPLES_DIR).filter((f) => f.endsWith(".json")).map((f) => f.slice(0, -5));
  for (const name of ["welcome", "lobby", "error", "match_start", "snapshot", "event_hit", "event_ko",
                      "event_game_over", "event_disconnect"]) {
    assert.ok(names.includes(name), `missing shared/protocol_examples/${name}.json`);
  }
});

test("snapshot fighters have exactly the fields in protocol.js", () => {
  for (const f of example("snapshot").fighters) assert.deepEqual(sorted(Object.keys(f)), sorted(FIGHTER_FIELDS));
});

test("match_start stage has exactly the fields in protocol.js", () => {
  assert.deepEqual(sorted(Object.keys(example("match_start").stage)), sorted(STAGE_FIELDS));
});

test("lobby players have exactly the fields in protocol.js", () => {
  for (const p of example("lobby").players) assert.deepEqual(sorted(Object.keys(p)), sorted(LOBBY_PLAYER_FIELDS));
});

test("events have exactly the fields in protocol.js for their kind", () => {
  for (const name of ["event_hit", "event_ko", "event_game_over", "event_disconnect"]) {
    const { type, tick, t, kind, ...rest } = example(name);
    assert.equal(type, "event");
    assert.ok(Number.isFinite(tick) && Number.isFinite(t), `${name}: tick and t must be numbers`);
    assert.deepEqual(sorted(Object.keys(rest)), sorted(EVENT_FIELDS[kind]), name);
  }
});

test("the fake server sends the same fields as the real one", () => {
  for (const f of scriptedFighters(1.3)) assert.deepEqual(sorted(Object.keys(f)), sorted(FIGHTER_FIELDS));
  const events = scriptedEvents(0, MATCH_LENGTH + 0.05).concat(scriptedEvents(2.9, 3.1));
  for (const e of events) {
    const { kind, ...rest } = e;
    assert.deepEqual(sorted(Object.keys(rest)), sorted(EVENT_FIELDS[kind]), `fake ${kind}`);
  }
});

test("the renderer draws every example without NaN or undefined", () => {
  const { canvas, problems, texts } = recordingCanvas();
  const renderer = new Renderer(canvas, { showHitboxes: true });

  renderer.receive(example("lobby"), 0);
  renderer.receive(example("match_start"), 0);
  const snap = example("snapshot");
  renderer.receive(snap, 10);
  renderer.receive({ ...snap, tick: snap.tick + 2, t: snap.t + 1 / 30 }, 10 + 1 / 30);
  for (const name of ["event_hit", "event_ko", "event_game_over"]) renderer.receive(example(name), 10.05);

  for (const time of [10, 10.1, 10.2, 10.5, 11]) renderer.draw(time);

  assert.deepEqual(problems, []);
  assert.ok(texts.some((s) => s.endsWith("%")), "damage % was drawn");
  assert.ok(texts.includes("GAME!"), "game over banner was drawn");
  assert.equal(renderer.lobby.room, example("lobby").room);
});

test("events wait until the smoothed picture reaches their time", () => {
  const effects = new Effects(1280, 720);
  effects.add({ ...example("event_hit"), t: 5 });
  effects.update(4.9, 100);
  assert.equal(effects.active.length, 0);
  effects.update(5.0, 100.1);
  assert.equal(effects.active.length, 1);
});

test("old hits are skipped instead of all playing at once", () => {
  const effects = new Effects(1280, 720);
  effects.add({ ...example("event_hit"), t: 1 });
  effects.add({ ...example("event_game_over"), t: 1 });
  effects.update(5, 100); // picture is 4 s past both events
  assert.equal(effects.active.length, 0);
  assert.ok(effects.banner, "game over still shows");
});

test("a KO burst is drawn on screen even though the fighter left it", () => {
  const effects = new Effects(1280, 720);
  effects.add({ ...example("event_ko"), x: -1000, y: 5000 });
  effects.update(null, 0);
  const [burst] = effects.active;
  assert.ok(burst.x >= 0 && burst.x <= 1280 && burst.y >= 0 && burst.y <= 720);
});

test("game over with no winner shows a draw", () => {
  const { canvas, texts } = recordingCanvas();
  const renderer = new Renderer(canvas);
  renderer.receive(example("match_start"), 0);
  renderer.receive({ ...example("event_game_over"), winner: null }, 0);
  renderer.draw(1);
  assert.ok(texts.includes("Draw"));
});

/** A stand-in canvas that records drawing calls and flags bad values. */
function recordingCanvas() {
  const problems = [];
  const texts = [];
  const props = {};
  const ctx = new Proxy({}, {
    get(_, name) {
      if (name in props) return props[name];
      return (...args) => {
        for (const a of args) {
          if (typeof a === "number" && !Number.isFinite(a)) problems.push(`${String(name)} got ${a}`);
          if (typeof a === "string" && /undefined|NaN/.test(a)) problems.push(`${String(name)} got "${a}"`);
        }
        if (name === "fillText") texts.push(args[0]);
      };
    },
    set(_, name, value) {
      if (typeof value === "string" && /undefined|NaN/.test(value)) problems.push(`${String(name)} set to "${value}"`);
      props[name] = value;
      return true;
    },
  });
  return { canvas: { width: 0, height: 0, getContext: () => ctx }, problems, texts };
}

test("browser and server agree on the protocol version and the character list", () => {
  const python = readFileSync(new URL("../../../network/protocol.py", import.meta.url), "utf8");
  const version = Number(python.match(/^VERSION = (\d+)/m)[1]);
  assert.equal(PROTOCOL_VERSION, version, "update PROTOCOL_VERSION in client/net.js");
  const ids = [...python.match(/^CHARACTERS = \(([^)]*)\)/m)[1].matchAll(/"(\w+)"/g)].map((m) => m[1]);
  assert.deepEqual(CHARACTERS.map((c) => c.id), ids, "client/characters.js and network/protocol.py differ");
});

test("every character has a portrait", () => {
  for (const c of CHARACTERS) {
    const png = new URL(`../../../assets/characters/${c.id}/views/front.png`, import.meta.url);
    assert.ok(readFileSync(png).length > 0, c.id);
  }
});

test("a respawn snaps instead of sliding", () => {
  const a = { type: "snapshot", tick: 1, t: 0, fighters: [{ ...example("snapshot").fighters[0], x: 100, life_id: 0 }] };
  const b = { type: "snapshot", tick: 2, t: 0.1, fighters: [{ ...a.fighters[0], x: 150, life_id: 1 }] };
  assert.equal(interpolate(a, b, 0.5).fighters[0].x, 150);
});
