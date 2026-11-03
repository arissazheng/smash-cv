"""Pygame stays on the main thread; sockets and frame pacing yield to asyncio."""

from __future__ import annotations

import asyncio
from pathlib import Path
import time

from controllers.development import DemoController, KeyboardController
from network.client import NetworkClient
from shared import config
from shared.controller_state import ControllerState


def make_controller(args, client):
    camera = None
    if args.input == "keyboard":
        controller = KeyboardController(client.player_id)
    elif args.input == "demo":
        controller = DemoController(client.player_id, lambda: client.latest)
    elif args.input == "idle":
        class IdleController:
            def poll(self):
                return ControllerState(player_id=client.player_id)
        controller = IdleController()
    else:
        from vision.calibration import Calibration
        calibration = Calibration.load(args.calibration)
        if args.input == "replay":
            from controllers.replay_controller import ReplayController
            controller = ReplayController(Path(args.replay), calibration, player_id=client.player_id)
        else:
            from controllers.camera_controller import CameraController
            from vision.camera import CameraSource
            camera = CameraSource().start()
            controller = CameraController(camera, calibration, player_id=client.player_id)
    return controller, camera


async def run_client(args):
    if args.headless and args.input == "keyboard":
        raise ValueError("use --input demo or idle with --headless")
    if args.input == "replay" and not args.replay:
        raise ValueError("--input replay requires --replay PATH")
    client = NetworkClient(args.host, args.port, args.name)
    camera = None
    pygame = None
    try:
        await client.connect()
        controller, camera = make_controller(args, client)
        print(f"Connected as P{client.player_id + 1} ({args.name}), input={args.input}", flush=True)
        if not args.manual_ready:
            client.ready()
        if not args.headless:
            import pygame
            from client.render import PrototypeRenderer
            pygame.display.init()
            screen = pygame.display.set_mode((config.SCREEN_WIDTH, config.SCREEN_HEIGHT), pygame.RESIZABLE)
            pygame.display.set_caption(f"Smash CV | {args.name} | P{client.player_id + 1}")
            renderer = PrototypeRenderer()
        loop = asyncio.get_running_loop()
        started = next_frame = loop.time()
        previous_phase = None
        running = True
        while running and not client.closed:
            now = loop.time()
            if args.duration is not None and now - started >= args.duration:
                break
            if pygame:
                events = pygame.event.get()
                if isinstance(controller, KeyboardController):
                    controller.handle(events)
                for event in events:
                    if event.type == pygame.QUIT or (event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE):
                        running = False
                    elif event.type == pygame.KEYDOWN:
                        if event.key == pygame.K_RETURN:
                            client.ready()
                        elif event.key == pygame.K_r and client.latest and client.latest.phase == "finished":
                            client.rematch()
                        elif event.key == pygame.K_TAB:
                            renderer.show_hitboxes = not renderer.show_hitboxes
            phase = client.latest.phase if client.latest else "lobby"
            if phase != previous_phase:
                print(f"P{client.player_id + 1}: {phase}", flush=True)
                previous_phase = phase
            state = controller.poll()
            # A connected client can outlive a stalled camera worker. Camera
            # timestamps use this laptop's monotonic clock; replay stamps don't.
            if args.input == "camera" and time.monotonic() - state.timestamp > 0.25:
                state = ControllerState(player_id=client.player_id)
            client.inputs.capture(state, allow_actions=phase == "playing")
            if pygame:
                age = 1000 * (now - client.last_snapshot_at) if client.last_snapshot_at is not None else 0
                tick = client.latest.tick if client.latest else 0
                status = f"SERVER TICK {tick}  |  SNAPSHOT {age:.0f}ms  |  {args.host}:{args.port}"
                renderer.draw(screen, client.buffer.sample(now), client.lobby, client.player_id,
                              client.countdown, status, args.input)
                pygame.display.flip()
            next_frame += 1 / config.GAME_FPS
            if next_frame < now - 0.1:
                next_frame = now
            await asyncio.sleep(max(0.0, next_frame - loop.time()))
        if client.error:
            raise ConnectionError(client.error)
        if client.latest:
            print(f"P{client.player_id + 1}: final tick={client.latest.tick}, "
                  f"phase={client.latest.phase}, winner={client.latest.winner}", flush=True)
    finally:
        if camera:
            camera.stop()
        await client.close()
        if pygame:
            pygame.quit()
