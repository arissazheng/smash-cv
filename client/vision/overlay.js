// Debug overlay: mirrored camera + skeleton + hands + FPS. Owner: Person 1.
const POSE_EDGES = [[11,12],[11,13],[13,15],[12,14],[14,16],[11,23],[12,24],[23,24]]; // shared/landmarks.py POSE_EDGES

export function drawOverlay(ctx, image, frame, fps) {
  const { width: w, height: h } = ctx.canvas;
  ctx.drawImage(image, 0, 0, w, h);
  ctx.lineWidth = 3; ctx.strokeStyle = "#0f0"; ctx.fillStyle = "#0f0";
  if (frame?.pose) {
    for (const [a, b] of POSE_EDGES) {
      ctx.beginPath(); ctx.moveTo(frame.pose[a][0] * w, frame.pose[a][1] * h); ctx.lineTo(frame.pose[b][0] * w, frame.pose[b][1] * h); ctx.stroke();
    }
  }
  ctx.fillStyle = "#f80";
  for (const hand of frame?.hands ?? []) {
    for (const [x, y] of hand.lm) { ctx.beginPath(); ctx.arc(x * w, y * h, 3, 0, 7); ctx.fill(); }
    ctx.fillStyle = "#fff"; ctx.fillText(`${hand.side}: ${hand.g}`, hand.lm[0][0] * w, hand.lm[0][1] * h - 8); ctx.fillStyle = "#f80";
  }
  ctx.fillStyle = "#fff"; ctx.font = "16px monospace"; ctx.fillText(`${fps.toFixed(0)} fps`, 8, 20);
}
