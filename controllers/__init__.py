"""Controllers: anything that produces a ControllerState for the game.

Every controller has `poll() -> ControllerState`. The game only ever calls
poll(), so it can't tell a live camera from a recording.
"""
