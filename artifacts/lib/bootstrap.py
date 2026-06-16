"""Add artifacts root and tool paths to sys.path."""

import sys
from pathlib import Path

ARTIFACTS_ROOT = Path(__file__).resolve().parents[1]


def ensure_paths() -> Path:
    for root in (ARTIFACTS_ROOT, ARTIFACTS_ROOT / "profile", ARTIFACTS_ROOT / "core"):
        entry = str(root)
        if entry not in sys.path:
            sys.path.insert(0, entry)
    return ARTIFACTS_ROOT