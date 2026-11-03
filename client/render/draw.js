// Drawing the stage and fighters on a 2D canvas.
//
// Owner: Person 4.
//
// Fighters are colored boxes until sprites exist.
// TODO(Person 4): load sprite atlases and draw the frame for each fighter's
// state and stateTime, falling back to the box when a character has no art.

export const PLAYER_COLORS = ["#e64646", "#4682e6", "#f0c83c", "#50c86e"]; // P1-P4, same as the Python renderer
const SKY = "#181a30";
const GROUND = "#5a5a6e";
const PLATFORM = "#9696af";
const HITBOX = "#fff078";

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

/**
 * @param {CanvasRenderingContext2D} ctx
 * @param {import("./protocol.js").FighterSnapshot} f
 * @param {{stateTime: number, time?: number, showHitboxes: boolean}} look
 */
export function drawFighter(ctx, f, { stateTime, time = 0, showHitboxes }) {
  // Blink while invulnerable after respawning.
  ctx.globalAlpha = f.invulnerable && Math.floor(time * 10) % 2 === 0 ? 0.35 : 1;
  const left = Math.round(f.x - f.w / 2);
  const top = Math.round(f.y - f.h);

  // Flash white while hurt so hits read clearly.
  const flashing = f.state === "hurt" && Math.floor(stateTime * 20) % 2 === 0;
  ctx.fillStyle = flashing ? "#ffffff" : playerColor(f.id);
  roundRect(ctx, left, top, f.w, f.h, 8);
  ctx.fill();

  // Eye shows which way the fighter faces.
  ctx.fillStyle = "#ffffff";
  ctx.beginPath();
  ctx.arc(f.x + f.facing * 14, top + 20, 6, 0, Math.PI * 2);
  ctx.fill();

  // A short arm sticks out during attacks, so attacks are visible before sprites exist.
  if (["jab", "smash", "special", "up_special", "grab"].includes(f.state)) {
    ctx.fillStyle = playerColor(f.id);
    const armX = f.facing > 0 ? left + f.w : left - 24;
    ctx.fillRect(armX, top + 30, 24, 12);
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
