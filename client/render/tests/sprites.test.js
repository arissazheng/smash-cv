// Run with: cd client && npm test
import assert from "node:assert/strict";
import { test } from "node:test";

import { drawFighter } from "../draw.js";
import { SPRITE_SCALE, SpriteSet } from "../sprites.js";

const fighter = (extra = {}) => ({
  id: 0, character: "lyons", x: 400, y: 520, w: 60, h: 90, facing: 1, state: "idle",
  damage: 0, stocks: 2, shield: false, life_id: 0, invulnerable: false, hitbox: null, ...extra,
});
const sprite = { width: 32, height: 44 };

/** Records drawImage and fillRect calls on a stand-in canvas context. */
function recorder() {
  const calls = [];
  const props = {};
  const ctx = new Proxy({}, {
    get: (_, name) => (name in props ? props[name] : (...args) => calls.push({ name, args, alpha: props.globalAlpha })),
    set: (_, name, value) => { props[name] = value; return true; },
  });
  return { ctx, calls };
}

test("a fighter with a sprite is drawn as the sprite at 2x, feet on the ground", () => {
  const { ctx, calls } = recorder();
  drawFighter(ctx, fighter(), { stateTime: 0, showHitboxes: false, sprite });
  const draw = calls.find((c) => c.name === "drawImage");
  const [, x, y, w, h] = draw.args;
  assert.deepEqual([w, h], [32 * SPRITE_SCALE, 44 * SPRITE_SCALE]);
  assert.equal(x, 400 - 32);   // centered on x
  assert.equal(y + h, 520);    // feet on y
  assert.ok(!calls.some((c) => c.name === "fill"), "no box drawn");
});

test("without a sprite the colored box is drawn instead", () => {
  const { ctx, calls } = recorder();
  drawFighter(ctx, fighter(), { stateTime: 0, showHitboxes: false, sprite: null });
  assert.ok(!calls.some((c) => c.name === "drawImage"));
  assert.ok(calls.some((c) => c.name === "fill"));
});

test("crouching is shorter and facing left mirrors the sprite", () => {
  const draw = (extra) => {
    const { ctx, calls } = recorder();
    drawFighter(ctx, fighter(extra), { stateTime: 0, showHitboxes: false, sprite });
    return calls;
  };
  const [, , y, , h] = draw({ h: 55 }).find((c) => c.name === "drawImage").args;
  assert.ok(h < 44 * SPRITE_SCALE && y + h === 520);
  assert.ok(draw({ facing: -1 }).some((c) => c.name === "scale" && c.args[0] === -1));
});

test("getting hit makes the sprite flicker", () => {
  const { ctx, calls } = recorder();
  drawFighter(ctx, fighter({ state: "hurt" }), { stateTime: 0, showHitboxes: false, sprite });
  assert.ok(calls.find((c) => c.name === "drawImage").alpha < 1);
});

test("sprite set picks the frame for the state and time, with fallbacks", () => {
  const set = new SpriteSet("/assets");
  const img = (name) => ({ name, naturalWidth: 32, complete: true });
  set.characters.set("oski", { frameTime: 0.1, states: new Map([
    ["idle", [img("idle0")]], ["run", [img("run0"), img("run1")]], ["jump", [img("jump0")]],
  ]) });
  assert.equal(set.frame("oski", "run", 0.05).name, "run0");
  assert.equal(set.frame("oski", "run", 0.15).name, "run1");
  assert.equal(set.frame("oski", "fall", 0).name, "jump0");   // fall falls back to jump
  assert.equal(set.frame("oski", "smash", 0).name, "idle0");  // unknown state falls back to idle
  assert.equal(set.frame("efros", "idle", 0), null);          // not loaded yet: draw a box
});
