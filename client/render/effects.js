// Hit sparks, KO bursts, screen shake and the "GAME!" banner, driven by the
// server's `event` messages.
//
// Owner: Person 4.
//
// Events carry the server time they happened at. The renderer draws slightly
// in the past, so each event waits here until the picture reaches its time;
// that way the spark appears exactly when the punch lands on screen.

import { playerColor } from "./draw.js";

const EDGE_MARGIN = 40; // KO bursts happen off-screen; draw them just inside the edge
const STALE_AFTER = 0.5; // seconds; older hits are skipped (e.g. after the tab was in the background)

export class Effects {
  constructor(width, height) {
    this.width = width;
    this.height = height;
    this.pending = [];  // events waiting for their time
    this.active = [];   // effects being drawn
    this.shakeUntil = 0;
    this.banner = null; // {winner} once the match is over
  }

  add(event) {
    this.pending.push(event);
  }

  /**
   * Start every event whose time has come.
   * @param {?number} serverTime  what the renderer is drawing; null = show everything now
   * @param {number} now          client time, seconds
   */
  update(serverTime, now) {
    const waiting = [];
    for (const e of this.pending) {
      if (serverTime !== null && e.t > serverTime) waiting.push(e);
      else if (serverTime !== null && serverTime - e.t > STALE_AFTER && e.kind !== "game_over") continue;
      else this._start(e, now);
    }
    this.pending = waiting;
    this.active = this.active.filter((fx) => now - fx.born < fx.life);
  }

  _start(e, now) {
    if (e.kind === "hit") {
      const big = e.attack === "smash";
      this.active.push({ kind: "spark", x: e.x, y: e.y, born: now, life: big ? 0.35 : 0.22, size: big ? 48 : 28, shielded: e.shielded });
      if (big && !e.shielded) this.shakeUntil = Math.max(this.shakeUntil, now + 0.15);
    } else if (e.kind === "ko") {
      const x = clamp(e.x, EDGE_MARGIN, this.width - EDGE_MARGIN);
      const y = clamp(e.y, EDGE_MARGIN, this.height - EDGE_MARGIN);
      this.active.push({ kind: "burst", x, y, born: now, life: 0.8, color: playerColor(e.player) });
      this.shakeUntil = Math.max(this.shakeUntil, now + 0.3);
    } else if (e.kind === "game_over") {
      this.banner = { winner: e.winner };
    }
  }

  /** Pixels to offset the stage by this frame (screen shake). */
  shakeOffset(now) {
    if (now >= this.shakeUntil) return [0, 0];
    return [Math.round((Math.random() - 0.5) * 12), Math.round((Math.random() - 0.5) * 12)];
  }

  /** @param {CanvasRenderingContext2D} ctx */
  draw(ctx, now) {
    for (const fx of this.active) {
      const p = (now - fx.born) / fx.life; // 0 -> 1 over the effect's life
      ctx.globalAlpha = 1 - p;
      if (fx.kind === "spark") drawSpark(ctx, fx, p);
      else drawBurst(ctx, fx, p);
    }
    ctx.globalAlpha = 1;
  }

  /** @param {Map<number, string>} names */
  drawBanner(ctx, names) {
    if (!this.banner) return;
    const { width, height } = this;
    ctx.fillStyle = "rgba(10, 12, 24, 0.55)";
    ctx.fillRect(0, 0, width, height);
    ctx.textAlign = "center";
    ctx.textBaseline = "middle";
    ctx.fillStyle = "#ffffff";
    ctx.font = "bold 140px system-ui, sans-serif";
    ctx.fillText("GAME!", width / 2, height / 2 - 40);
    const { winner } = this.banner;
    ctx.font = "bold 44px system-ui, sans-serif";
    if (winner === null) {
      ctx.fillText("Draw", width / 2, height / 2 + 50);
    } else {
      ctx.fillStyle = playerColor(winner);
      ctx.fillText(`${names.get(winner) ?? `P${winner + 1}`} wins`, width / 2, height / 2 + 50);
    }
  }
}

// A star of short rays; blue when the hit was blocked by a shield.
function drawSpark(ctx, fx, p) {
  const rays = 8;
  const inner = fx.size * 0.3 * (1 + p);
  const outer = fx.size * (0.6 + 0.6 * p);
  ctx.strokeStyle = fx.shielded ? "#78c8ff" : "#fff3a0";
  ctx.lineWidth = 4;
  ctx.beginPath();
  for (let i = 0; i < rays; i++) {
    const a = (i / rays) * Math.PI * 2;
    ctx.moveTo(fx.x + Math.cos(a) * inner, fx.y + Math.sin(a) * inner);
    ctx.lineTo(fx.x + Math.cos(a) * outer, fx.y + Math.sin(a) * outer);
  }
  ctx.stroke();
}

// An expanding ring in the KO'd player's color.
function drawBurst(ctx, fx, p) {
  ctx.strokeStyle = fx.color;
  ctx.lineWidth = 10 * (1 - p) + 2;
  ctx.beginPath();
  ctx.arc(fx.x, fx.y, 20 + 160 * p, 0, Math.PI * 2);
  ctx.stroke();
}

function clamp(v, lo, hi) {
  return Math.min(hi, Math.max(lo, v));
}
