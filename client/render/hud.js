// Damage %, stock icons and names along the bottom of the screen.
//
// Owner: Person 4.
// TODO(Person 4): Berkeley-styled font and character portraits.

import { playerColor } from "./draw.js";

/** White at 0%, through yellow and red, like Smash. Same formula as ui/hud.py. */
export function damageColor(damage) {
  const t = Math.min(damage / 150, 1);
  const g = Math.round(255 * (1 - t));
  const b = Math.round(255 * Math.max(0, 1 - 2 * t));
  return `rgb(255, ${g}, ${b})`;
}

/**
 * @param {CanvasRenderingContext2D} ctx
 * @param {import("./protocol.js").FighterSnapshot[]} fighters
 * @param {Map<number, string>} names  player id -> name
 */
export function drawHud(ctx, fighters, names, width, height) {
  const slot = width / (fighters.length + 1);
  ctx.textAlign = "center";
  ctx.textBaseline = "middle";

  fighters.forEach((f, i) => {
    const cx = Math.round(slot * (i + 1));

    const name = names.get(f.id) ?? `P${f.id + 1}`;
    ctx.font = "bold 22px system-ui, sans-serif";
    ctx.lineWidth = 5;
    ctx.strokeStyle = "#101220"; // dark edge so names read over any stage art
    ctx.strokeText(name, cx, height - 98);
    ctx.fillStyle = playerColor(f.id);
    ctx.fillText(name, cx, height - 98);

    ctx.font = "bold 56px system-ui, sans-serif";
    ctx.lineWidth = 6;
    ctx.strokeStyle = "#101220";
    const pct = `${Math.floor(f.damage)}%`;
    ctx.strokeText(pct, cx, height - 55);
    ctx.fillStyle = damageColor(f.damage);
    ctx.fillText(pct, cx, height - 55);

    ctx.fillStyle = playerColor(f.id);
    for (let s = 0; s < f.stocks; s++) {
      ctx.beginPath();
      ctx.arc(cx + (s - (f.stocks - 1) / 2) * 20, height - 18, 7, 0, Math.PI * 2);
      ctx.fill();
    }
  });
}
