// Run with: node --test client/
import assert from "node:assert/strict";
import { test } from "node:test";

import { SnapshotBuffer, interpolate } from "../interpolation.js";
import { scriptedFighters } from "../fake_server.js";
import { damageColor } from "../hud.js";

const fighter = (x, extra = {}) => ({ id: 0, x, y: 500, state: "run", ...extra });
const snap = (tick, t, fighters) => ({ type: "snapshot", tick, t, fighters });

test("interpolate slides position and takes other fields from the newer snapshot", () => {
  const a = snap(1, 0.0, [fighter(100, { damage: 0 })]);
  const b = snap(2, 0.1, [fighter(200, { damage: 12, state: "jab" })]);
  const mid = interpolate(a, b, 0.25);
  assert.equal(mid.fighters[0].x, 125);
  assert.equal(mid.fighters[0].damage, 12);
  assert.equal(mid.fighters[0].state, "jab");
});

test("interpolate jumps instead of sliding on respawn", () => {
  const a = snap(1, 0.0, [fighter(-500)]);
  const b = snap(2, 0.1, [fighter(640)]);
  assert.equal(interpolate(a, b, 0.5).fighters[0].x, 640);
});

test("buffer draws RENDER_DELAY behind and slides between snapshots", () => {
  const buffer = new SnapshotBuffer({ delay: 0.1 });
  // Server time t, arriving at client time t + 5 (clocks differ by 5 s).
  for (let i = 0; i <= 10; i++) buffer.push(snap(i, i * 0.1, [fighter(i * 10)]), i * 0.1 + 5);
  const now = 0.85 + 5; // render target = 0.85 - 0.1 = 0.75 server time
  assert.ok(Math.abs(buffer.sample(now).fighters[0].x - 75) < 1e-9);
});

test("buffer never guesses ahead of the newest snapshot", () => {
  const buffer = new SnapshotBuffer({ delay: 0.1 });
  buffer.push(snap(1, 0.0, [fighter(0)]), 0);
  buffer.push(snap(2, 0.1, [fighter(10)]), 0.1);
  assert.equal(buffer.sample(99).fighters[0].x, 10);
});

test("buffer ignores late and duplicate snapshots", () => {
  const buffer = new SnapshotBuffer();
  buffer.push(snap(2, 0.1, [fighter(10)]), 0.1);
  buffer.push(snap(1, 0.0, [fighter(0)]), 0.12);
  buffer.push(snap(2, 0.1, [fighter(99)]), 0.13);
  assert.equal(buffer.snapshots.length, 1);
  assert.equal(buffer.latest.fighters[0].x, 10);
});

test("buffer returns null before any snapshot", () => {
  assert.equal(new SnapshotBuffer().sample(1), null);
});

test("fake server fighters have every field the renderer reads", () => {
  for (const t of [0, 0.3, 1.3, 6.5]) {
    for (const f of scriptedFighters(t)) {
      for (const key of ["id", "character", "x", "y", "w", "h", "facing", "state", "damage", "stocks", "shield", "hitbox"]) {
        assert.ok(key in f, `missing ${key}`);
      }
    }
  }
});

test("damage color goes from white toward red", () => {
  assert.equal(damageColor(0), "rgb(255, 255, 255)");
  assert.equal(damageColor(150), "rgb(255, 0, 0)");
});
