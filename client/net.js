// The browser's connection to the game server.
//
// Owner: Person 3.
//
// One WebSocket per player, at /ws on the same server that served the page.
// The browser sends who it is, readiness, calibration and landmarks (never
// controller inputs; the server runs the gesture recognizer). The server's
// messages are passed to every listener, e.g. Renderer.receive.

export const PROTOCOL_VERSION = 2; // must match VERSION in network/protocol.py (a test checks)

export function serverUrl(location = globalThis.location) {
  const scheme = location.protocol === "https:" ? "wss" : "ws";
  return `${scheme}://${location.host}/ws`;
}

export class Connection {
  constructor(url = serverUrl()) {
    this.url = url;
    this.socket = null;
    this.listeners = new Set();
  }

  /** Opens the socket; resolves once connected. */
  open() {
    return new Promise((resolve, reject) => {
      this.socket = new WebSocket(this.url);
      this.socket.onopen = () => resolve(this);
      this.socket.onerror = () => reject(new Error(`couldn't reach the game server at ${this.url}`));
      this.socket.onmessage = (e) => {
        const message = JSON.parse(e.data);
        for (const listener of this.listeners) listener(message);
      };
      this.socket.onclose = (e) => {
        for (const listener of this.listeners) listener({ type: "closed", reason: e.reason });
      };
    });
  }

  /** listener(message) is called for every server message, plus {type: "closed"}. */
  listen(listener) {
    this.listeners.add(listener);
    return () => this.listeners.delete(listener);
  }

  get isOpen() {
    return this.socket?.readyState === WebSocket.OPEN;
  }

  send(message) {
    if (this.isOpen) this.socket.send(JSON.stringify(message));
  }

  hello(name, character) {
    this.send({ type: "hello", version: PROTOCOL_VERSION, name, character });
  }

  ready(ready = true) {
    this.send({ type: "ready", ready });
  }

  /** calibration: {center_x, shoulder_y, nose_y, shoulder_width}, from client/vision/calibration.js */
  calibrate(calibration) {
    this.send({ type: "calibrate", calibration });
  }

  /** frame: a LandmarkFrame {t, pose, hands} from client/vision/tracker.js */
  landmarks(frame) {
    this.send({ type: "landmarks", frame });
  }

  rematch() {
    this.send({ type: "rematch" });
  }

  close() {
    this.send({ type: "leave" });
    this.socket?.close();
  }
}
