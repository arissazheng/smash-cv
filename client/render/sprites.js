// Character animation frames for the renderer.
//
// Owner: Person 4.
//
// Each character folder has sprites.json ({frame_time, states: {state: count}})
// and <state>/frame_00.png ... facing right (32x44, drawn at 2x). The renderer
// asks for the frame matching what the server says the fighter is doing, and
// mirrors it when the fighter faces left. Fighters show as colored boxes until
// their frames load, or if a character has no art.

export const SPRITE_SCALE = 2;
const FALLBACK = { fall: "jump", crouch: "idle", shield: "idle" }; // if a state has no frames

export class SpriteSet {
  /** @param {string} assetBase  URL of the repo's assets/ folder */
  constructor(assetBase) {
    this.assetBase = assetBase;
    this.characters = new Map(); // character -> {frameTime, states: Map(state -> [images])}
    this.requested = new Set();
  }

  /** Start loading a character's frames. Safe to call repeatedly. */
  async load(character) {
    if (typeof Image === "undefined" || !character || this.requested.has(character)) return;
    this.requested.add(character);
    const base = `${this.assetBase}/characters/${character}`;
    let manifest;
    try {
      manifest = await (await fetch(`${base}/sprites.json`)).json();
    } catch {
      console.warn(`no sprites.json for ${character}`);
      return;
    }
    const entry = { frameTime: manifest.frame_time ?? 0.12, states: new Map() };
    for (const [state, count] of Object.entries(manifest.states)) {
      const frames = [];
      for (let i = 0; i < count; i++) {
        const image = new Image();
        image.src = `${base}/${state}/frame_${String(i).padStart(2, "0")}.png`;
        frames.push(image);
      }
      entry.states.set(state, frames);
    }
    this.characters.set(character, entry);
  }

  /**
   * The frame for this character doing `state` for `stateTime` seconds, or null
   * if nothing has loaded yet. Frames face right; the caller mirrors for left.
   */
  frame(character, state, stateTime = 0) {
    const entry = this.characters.get(character);
    if (!entry) return null;
    const frames = entry.states.get(state) ?? entry.states.get(FALLBACK[state]) ?? entry.states.get("idle");
    if (!frames?.length) return null;
    const image = frames[Math.floor(stateTime / entry.frameTime) % frames.length];
    return image.complete !== false && image.naturalWidth !== 0 ? image : null;
  }
}
