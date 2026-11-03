// Server -> browser messages the renderer reads.
//
// Owner: Person 4, agreed with Person 3. The Python side that builds these is
// shared/protocol.py; change both together. One real example of each message
// lives in shared/protocol_examples/, and tests on both sides check against it.
//
// Coordinates are game pixels on a 1280x720 stage, y grows downward, and a
// fighter's (x, y) is the middle of its feet.

/** @typedef {[number, number, number, number]} Rect  x, y, width, height */

/**
 * Sent once when a match begins.
 * @typedef {object} MatchStart
 * @property {"match_start"} type
 * @property {Stage} stage
 * @property {{id: number, name: string, character: string}[]} players
 * @property {number} countdown      seconds until play begins
 */

/**
 * @typedef {object} Stage
 * @property {string} name
 * @property {number} width
 * @property {number} height
 * @property {Rect} main             solid ground
 * @property {Rect[]} platforms      pass-through from below
 * @property {?string} background    file in assets/stages/, or null
 */

/**
 * Sent about 30 times a second during a match.
 * @typedef {object} Snapshot
 * @property {"snapshot"} type
 * @property {number} tick           server game tick, always increasing
 * @property {number} t              server time in seconds
 * @property {FighterSnapshot[]} fighters
 */

/**
 * @typedef {object} FighterSnapshot
 * @property {number} id
 * @property {string} character      folder name in assets/characters/
 * @property {number} x
 * @property {number} y
 * @property {number} w              body box, for drawing boxes before sprites exist
 * @property {number} h
 * @property {1 | -1} facing
 * @property {string} state          animation name: idle, run, jump, fall, crouch, shield,
 *                                   hurt, taunt, jab, smash, special, up_special, grab
 * @property {number} damage         percent
 * @property {number} stocks
 * @property {boolean} shield
 * @property {number} life_id      goes up on every respawn
 * @property {boolean} invulnerable just respawned; can't be hit
 * @property {?Rect} hitbox          active attack hitbox, or null
 */

/**
 * Sent to everyone in a room whenever anyone joins, leaves, picks or readies up.
 * @typedef {object} Lobby
 * @property {"lobby"} type
 * @property {string} room           room code, e.g. "ABCD"
 * @property {string} link           shareable link to the room
 * @property {number} host           player id of the room's creator
 * @property {string} stage
 * @property {"lobby" | "countdown" | "playing" | "finished"} phase
 * @property {number} capacity       players needed to start
 * @property {{id: number, name: string, character: string, ready: boolean, connected: boolean, rematch: boolean}[]} players
 */

/**
 * Something that happened, stamped with the server time it happened at.
 * Fields after `kind` depend on the kind (see EVENT_FIELDS).
 * @typedef {object} GameEvent
 * @property {"event"} type
 * @property {number} tick
 * @property {number} t
 * @property {"hit" | "ko" | "game_over" | "disconnect"} kind
 */

// Exact field lists, checked against shared/protocol_examples/ by the tests.
export const FIGHTER_FIELDS = ["id", "character", "x", "y", "w", "h", "facing", "state", "damage", "stocks", "shield", "life_id", "invulnerable", "hitbox"];
export const STAGE_FIELDS = ["name", "width", "height", "main", "platforms", "background"];
export const LOBBY_PLAYER_FIELDS = ["id", "name", "character", "ready", "connected", "rematch"];
export const EVENT_FIELDS = {
  hit: ["attacker", "target", "attack", "damage", "shielded", "x", "y"], // x, y = where it landed
  ko: ["player", "stocks_left", "x", "y"],                               // x, y = where they left (off-screen)
  game_over: ["winner"],                                                 // winner = player id, or null for a draw
  disconnect: ["player"],                                                // left mid-match
};

export const GAME_WIDTH = 1280;
export const GAME_HEIGHT = 720;
export const SNAPSHOT_RATE = 30; // per second
