// Server -> browser messages the renderer reads.
//
// Owner: Person 4, agreed with Person 3. The Python side that builds these is
// shared/protocol.py; change both together.
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
 * @property {?Rect} hitbox          active attack hitbox, or null
 */

export const GAME_WIDTH = 1280;
export const GAME_HEIGHT = 720;
export const SNAPSHOT_RATE = 30; // per second
