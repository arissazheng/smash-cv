// Drawing the stage and fighters on a 2D canvas.
//
// Owner: Person 4.
//
// Fighters are drawn with their character's sprite (see sprites.js), or as
// colored boxes until it loads.

import { SPRITE_SCALE } from "./sprites.js";

export const PLAYER_COLORS = ["#e64646", "#4682e6", "#f0c83c", "#50c86e"]; // P1-P4, same as the Python renderer
const SKY = "#181a30";
const GROUND = "#5a5a6e";
const PLATFORM = "#9696af";
const HITBOX = "#fff078";
const BODY_HEIGHT = 90; // standing body height in game/fighter.py

export function playerColor(id) {
  return PLAYER_COLORS[id % PLAYER_COLORS.length];
}

/** @param {CanvasRenderingContext2D} ctx  @param {import("./protocol.js").Stage} stage */
export function drawStage(ctx, stage, background = null) {
  if (background) {
    ctx.drawImage(background, 0, 0, stage.width, stage.height); // the art already shows the platforms
    return;
  }
  ctx.fillStyle = SKY;
  ctx.fillRect(0, 0, stage.width, stage.height);
  ctx.fillStyle = GROUND;
  ctx.fillRect(...stage.main);
  ctx.fillStyle = PLATFORM;
  for (const platform of stage.platforms) ctx.fillRect(...platform);
}

const ATTACKS = ["jab", "smash", "special", "up_special", "grab"];

/**
 * @param {CanvasRenderingContext2D} ctx
 * @param {import("./protocol.js").FighterSnapshot} f
 * @param {{stateTime: number, time?: number, showHitboxes: boolean, sprite?: CanvasImageSource | null}} look
 */
export function drawFighter(ctx, f, { stateTime, time = 0, showHitboxes, sprite = null }) {
  // Blink while invulnerable after respawning.
  ctx.globalAlpha = f.invulnerable && Math.floor(time * 10) % 2 === 0 ? 0.35 : 1;
  const hurtFlash = f.state === "hurt" && Math.floor(stateTime * 20) % 2 === 0;
  const attacking = ATTACKS.includes(f.state);

  if (sprite) {
    drawSprite(ctx, f, sprite, { hurtFlash, attacking });
  } else {
    drawBox(ctx, f, { hurtFlash, attacking });
  }

  if (f.shield) {
    ctx.strokeStyle = "rgba(120, 200, 255, 0.9)";
    ctx.lineWidth = 4;
    ctx.beginPath();
    ctx.arc(f.x, f.y - f.h / 2, Math.max(f.w, f.h) * 0.62, 0, Math.PI * 2);
    ctx.stroke();
  }

  ctx.globalAlpha = 1;

  if (showHitboxes && f.hitbox) {
    ctx.strokeStyle = HITBOX;
    ctx.lineWidth = 2;
    ctx.strokeRect(...f.hitbox);
  }
}

/** The character's frame for this state, feet on (x, y), mirrored when facing left. */
function drawSprite(ctx, f, sprite, { hurtFlash }) {
  const w = sprite.width * SPRITE_SCALE;
  const fullHeight = sprite.height * SPRITE_SCALE;
  const h = Math.round(fullHeight * Math.min(1, f.h / BODY_HEIGHT)); // shorter while crouching
  const x = Math.round(f.x - w / 2);
  const y = Math.round(f.y - h);
  const alpha = ctx.globalAlpha;
  if (hurtFlash) ctx.globalAlpha = alpha * 0.45; // flicker when hit
  if (f.facing < 0) {
    ctx.save();
    ctx.translate(x + w, y);
    ctx.scale(-1, 1);
    ctx.drawImage(sprite, 0, 0, w, h);
    ctx.restore();
  } else {
    ctx.drawImage(sprite, x, y, w, h);
  }
  ctx.globalAlpha = alpha;
}

/** Placeholder while a character has no art (or it hasn't loaded yet). */
function drawBox(ctx, f, { hurtFlash, attacking }) {
  const left = Math.round(f.x - f.w / 2);
  const top = Math.round(f.y - f.h);
  ctx.fillStyle = hurtFlash ? "#ffffff" : playerColor(f.id);
  roundRect(ctx, left, top, f.w, f.h, 8);
  ctx.fill();

  // Eye shows which way the fighter faces.
  ctx.fillStyle = "#ffffff";
  ctx.beginPath();
  ctx.arc(f.x + f.facing * 14, top + 20, 6, 0, Math.PI * 2);
  ctx.fill();

  // A short arm sticks out during attacks.
  if (attacking) {
    ctx.fillStyle = playerColor(f.id);
    const armX = f.facing > 0 ? left + f.w : left - 24;
    ctx.fillRect(armX, top + 30, 24, 12);
  }
}

export function drawMessage(ctx, width, height, text) {
  ctx.fillStyle = SKY;
  ctx.fillRect(0, 0, width, height);
  ctx.fillStyle = "#d8dcef";
  ctx.font = "32px system-ui, sans-serif";
  ctx.textAlign = "center";
  ctx.textBaseline = "middle";
  ctx.fillText(text, width / 2, height / 2);
}

function roundRect(ctx, x, y, w, h, r) {
  ctx.beginPath();
  ctx.moveTo(x + r, y);
  ctx.arcTo(x + w, y, x + w, y + h, r);
  ctx.arcTo(x + w, y + h, x, y + h, r);
  ctx.arcTo(x, y + h, x, y, r);
  ctx.arcTo(x, y, x + w, y, r);
  ctx.closePath();
}
