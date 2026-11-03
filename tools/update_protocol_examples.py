"""Rewrite shared/protocol_examples/*.json from the current code.

    python tools/update_protocol_examples.py

Run this only when you change a message format on purpose. Then run both test
suites, fix the side that broke, and tell the team what changed.
"""

import json
import os
from pathlib import Path
import sys

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from shared import config  # noqa: E402
from shared.protocol_samples import EXAMPLES_DIR_NAME, build_examples  # noqa: E402


def main():
    out = config.ROOT / "shared" / EXAMPLES_DIR_NAME
    out.mkdir(exist_ok=True)
    for name, message in build_examples().items():
        path = out / f"{name}.json"
        path.write_text(json.dumps(message, indent=2) + "\n")
        print(f"wrote {path.relative_to(config.ROOT)}")


if __name__ == "__main__":
    main()
