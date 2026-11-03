# Smash CV

A Smash Bros-style fighter where your laptop camera is the controller. Punch at
the camera and your character punches. Lean to run, throw your hands up to
jump.

## Setup

Python 3.10+.

```bash
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python tools/download_models.py    # MediaPipe pose + gesture models into models/
```

## Multiplayer framework prototype

Person 3's prototype runs an authoritative headless server and 2–4 independent
Pygame clients. It uses simple shapes and supports movement, double jump,
crouch/drop-through, jab, heavy (`smash`), and a longer-range melee special.
Damage, knockback, stocks, respawn, results, and disconnect forfeits are handled
by the server. Shields, grabs, recovery moves, and detailed assets are deferred.

Camera packages and models are **not needed** to try this version:

```bash
pip install -r requirements-game.txt

# Terminal 1: host (waits for two connected, ready players)
python main.py server

# Terminal 2: your window
python main.py client --name Alice

# Terminal 3: another window, or a bot while testing alone
python main.py client --name Bob
# Alternatively: python main.py client --name Bot --input demo
```

Controls: **A/D or left/right** to move, **Space/W/up** to jump, **S/down** to
crouch/drop through platforms, **J** jab, **K** heavy, **L** special. **Tab** toggles
hitboxes; **Esc** closes the client. Focus a client's window to control it.
Clients ready automatically on first connection. Use `--manual-ready` and press
**Enter** if you want to wait. A short countdown starts once all slots are ready.
After a match, everyone presses **R** to return to the lobby, then **Enter** to
ready again. Disconnecting during a match eliminates that fighter.

For separate laptops on the same LAN:

```bash
# Host machine; --players can be 2, 3, or 4
python main.py server --host 0.0.0.0 --players 2

# Each player uses the host's LAN IP, not 0.0.0.0
python main.py client --host 192.168.1.10 --name Alice
```

Allow the chosen port (default TCP 8765) through the host's firewall if needed.
The prototype targets a local/LAN demo; latency under real network loss has not
been tuned for internet play.

Other input modes use exactly the same network path:

```bash
python main.py client --input camera --calibration Alice --name Alice
python main.py client --input replay --replay recordings/jab/clip.jsonl --name Replay
python main.py client --input demo --headless --duration 10 --name Bot
python main.py client --input idle --headless --duration 10 --name Observer
```

`idle` occupies a player slot with neutral controls; it is not a spectator mode.
Camera mode needs the full setup above. Replay needs a landmark recording and
the relevant calibration. There are no committed recordings yet.

The server simulates at 60 Hz, sends full snapshots at 30 Hz, and never waits for
a client's rendering or camera. Clients poll at 60 Hz, send inputs at 30 Hz, and
interpolate authoritative positions with a small buffer. Jumps/attacks are
queued separately from held movement so polling cannot erase them. The server
rejects invalid inputs and assigns identities from the connection.

Person 4's handoff is `shared/game_state.py`: immutable `MatchView`, `StageView`,
and `FighterView` records. Replace `client/render.py` with asset-based drawing;
`network/client.py` and the server simulation stay the same. Gameplay events
are available on `NetworkClient.events`. See [the current scope and architecture](docs/person3-plan.md).

```bash
# Full suite needs the original requirements (OpenCV/NumPy tests included)
python -m pytest -q

# Game/network-only checks need requirements-game.txt plus pytest
python -m pytest -q tests/test_game.py tests/test_client.py tests/test_protocol.py tests/test_network.py
```

## Run

```bash
python main.py overlay                     # camera debug view: skeleton, gestures, live ControllerState
python main.py calibrate --name <you>      # sit neutral for a few seconds; saves calibration/<you>.json
python main.py play --calibration <you>    # you (camera) vs CPU
python main.py play --replay recordings/jab/<file>.jsonl   # a recording vs CPU, no camera needed

python -m gestures.recorder --label jab --player <you>      # record a labeled gesture clip
python -m ui.sprite_pipeline sheet.png assets/characters/<name>/<action>   # slice a sprite sheet
pytest                                     # tests, no camera needed
```

Close the game window to quit. In the overlay and recorder windows, press `q`.

## How it fits together

```
webcam (OpenCV) -> MediaPipe Pose + Gesture Recognizer -> smoothing -> gesture recognizer
    -> ControllerState -> game engine -> renderer
```

Each local input source exposes `controller.poll()` and returns a `ControllerState`
(`shared/controller_state.py`). That file is the contract between the vision
side and the game side: **change it only when all four of us agree.**

The multiplayer prototype includes optional keyboard/demo inputs for development
while vision is in progress. `ReplayController` still feeds recordings through
the same gesture recognizer a live camera uses. Network messages wrap this
contract; they do not change its fields.

## Who owns what

| Folder | Owner | What's there | Start here |
| --- | --- | --- | --- |
| `vision/` | Person 1 | Camera thread, MediaPipe wrapper, smoothing, calibration, debug overlay | `TODO(Person 1)` in `vision/pose.py`, `vision/smoothing.py` |
| `gestures/` | Person 2 | Gesture detectors, recognizer (edges and cooldowns), recorder | Stubs at the bottom of `gestures/detectors.py` |
| `controllers/` | Person 1 + 2 | Camera and replay controllers | |
| `game/` | Person 3 | Physics, fighters, combat, stage, CPU, game loop | `TODO(Person 3)` in `game/` |
| `network/`, `client/` | Person 3 | Authoritative server, transport, input buffering, interpolation, runtime, placeholder renderer | `network/server.py`, `client/runtime.py` |
| `ui/` | Person 4 | Rendering, sprites, HUD, menus, OpenCV sprite pipeline | `TODO(Person 4)` in `ui/` |
| `shared/` | Everyone | The ControllerState contract, landmark types, config | |

Find your work with `grep -rn "TODO(Person 2)" .` and so on.

## What works today (phase 1 starting point)

- Live pose + hand tracking with gesture names, and an overlay showing FPS and latency
- Detectors: lean → `move_x`, duck → `crouch`, both hands up → `jump`, fast wrist → `jab`, both fists → `smash`, fingertip → `pointer`
- Calibration saved per person
- Record and replay gesture clips
- Box fighters on a Battlefield-style stage: running, double jump, jab/smash hitboxes, damage %, knockback that grows with damage, stocks, CPU opponent
- Sprite sheet slicer (background removal + contour detection)

Still stubs: special, up special, shield, grab, taunt, pause detectors; menus;
real sprites; multi-person tracking for shared-camera local play. Networked
players each use their own laptop/controller and do not require shared-camera
tracking. The online prototype accepts jab, smash, and special only.

## Conventions

- Work on a branch per feature (`p2/shield-detector`), open a PR, get one review from the other pair.
- Detectors read `LandmarkFrame`s, never the camera, so they can be tested on recordings. Add a test for each new detector in `tests/`.
- Measure distances in shoulder widths (from calibration), not pixels, so thresholds work at any distance from the camera.
- Commit landmark recordings (`.jsonl`) to `recordings/<label>/`. They are our test data. Don't commit raw video.
- `calibration/` and `models/` are per laptop and ignored by git.

## Assets

Sprites from The Spriters Resource and stage art are fine for a class demo.
Don't publish Nintendo assets publicly. Put sprite frames in
`assets/characters/<character>/<state>/frame_XX.png`. State names: idle, run,
jump, fall, crouch, shield, hurt, taunt, jab, smash, special, up_special, grab.
