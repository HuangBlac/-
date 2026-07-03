"""Generate local content with Ollama and save it under game/data/generated."""

from __future__ import annotations

import os
import sys


PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from game.content_generation import main


if __name__ == "__main__":
    raise SystemExit(main())
