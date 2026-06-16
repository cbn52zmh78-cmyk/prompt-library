"""Canonical paths for the DAVID module."""

from __future__ import annotations

import sys
from pathlib import Path

DAVID_ROOT = Path(__file__).resolve().parents[1]
WORKSPACE = DAVID_ROOT.parent
TOOLS = WORKSPACE / "tools"
HISTORY_ROOT = WORKSPACE / "History"

if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

DATA_DIR = DAVID_ROOT / "data"
LANGUAGES_DIR = DAVID_ROOT / "languages"
PROMPTS_DIR = DAVID_ROOT / "prompts"
REGISTRY_FILE = DATA_DIR / "language_registry.json"
QUEUE_FILE = DATA_DIR / "research_queue.json"
TRAINING_OUT = DAVID_ROOT / "training_packs"
RESEARCH_OUT = DAVID_ROOT / "research"

STATUS_DIRS = {
    "living": LANGUAGES_DIR / "living",
    "dead": LANGUAGES_DIR / "dead",
    "extinct": LANGUAGES_DIR / "extinct",
    "reconstructed": LANGUAGES_DIR / "reconstructed",
    "undeciphered": LANGUAGES_DIR / "undeciphered",
}


def language_dir(slug: str, status: str | None = None) -> Path | None:
    if status and status in STATUS_DIRS:
        candidate = STATUS_DIRS[status] / slug
        if candidate.exists():
            return candidate
    for folder in STATUS_DIRS.values():
        candidate = folder / slug
        if candidate.exists():
            return candidate
    return None