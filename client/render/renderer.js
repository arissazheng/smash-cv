// The browser renderer: messages in, pictures out.
//
// Owner: Person 4.
//
//   const renderer = new Renderer(canvas);
//   socket.onmessage = (e) => renderer.receive(JSON.parse(e.data));
//   renderer.start();
//
// The renderer never decides anything about the game. It draws what the
// server sent, slightly in the past, sliding between snapshots.

import { drawFighter, drawMessage, drawStage } from "./draw.js";
import { drawHud } from "./hud.js";
import { SnapshotBuffer } from "./interpolation.js";
import { GAME_HEIGHT, GAME_WIDTH } from "./protocol.js";

const now = () => performance.now() / 1000;

export class Renderer {
  /** @param {HTMLCanvasElement} canvas */
  constructor(canvas, { showHitboxes = false, smoothing = true } = {}) {
    this.canvas = canvas;
    this.canvas.width = GAME_WIDTH;
    this.canvas.height = GAME_HEIGHT;
    this.ctx = canvas.getContext("2d");
    this.showHitboxes = showHitboxes;
    this.smoothing = smoothing; // false = draw the newest snapshot as-is (to compare)
    this.buffer = new SnapshotBuffer();
    this.stage = null;
    this.names = new Map();
    this.stateSince = new Map(); // fighter id -> {state, since}, for animation timing
    this._running = false;
  }

  /** Feed every server message here. */
  receive(message, arrival = now()) {
    if (message.type === "match_start") {
      this.stage = message.stage;
      this.names = new Map(message.players.map((p) => [p.id, p.name]));
      this.buffer = new SnapshotBuffer({ delay: this.buffer.delay });
      this.stateSince.clear();
      // TODO(Person 4): load message.stage.background and each player's sprite atlas here.
    } else if (message.type === "snapshot") {
      this.buffer.push(message, arrival);
    }
  }

  start() {
    if (this._running) return;
    this._running = true;
    const frame = () => {
      if (!this._running) return;
      this.draw(now());
      requestAnimationFrame(frame);
    };
    requestAnimationFrame(frame);
  }

  stop() {
    this._running = false;
  }

  draw(time) {
    const ctx = this.ctx;
    ctx.imageSmoothingEnabled = false; // keep pixel art crisp

    if (!this.stage) {
      drawMessage(ctx, GAME_WIDTH, GAME_HEIGHT, "Waiting for the match to start…");
      return;
    }
    drawStage(ctx, this.stage);

    const snapshot = this.smoothing ? this.buffer.sample(time) : this.buffer.latest;
    if (!snapshot) return;

    for (const fighter of snapshot.fighters) {
      drawFighter(ctx, fighter, {
        stateTime: this._stateTime(fighter, time),
        showHitboxes: this.showHitboxes,
      });
    }
    drawHud(ctx, snapshot.fighters, this.names, GAME_WIDTH, GAME_HEIGHT);
  }

  /** Seconds the fighter has been in its current state, tracked on the client. */
  _stateTime(fighter, time) {
    const entry = this.stateSince.get(fighter.id);
    if (!entry || entry.state !== fighter.state) {
      this.stateSince.set(fighter.id, { state: fighter.state, since: time });
      return 0;
    }
    return time - entry.since;
  }
}
