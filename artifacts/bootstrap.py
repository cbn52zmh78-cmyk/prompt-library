"""Add artifacts root to sys.path — call via _bootstrap() from subfolder tools."""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def setup() -> Path:
    if str(ROOT) not in sys.path:
        sys.path.insert(0, str(ROOT))
    return ROOT


setup()