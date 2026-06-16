#!/usr/bin/env python3
"""
Workspace Initializer v1.2 — Producer
Sets up the complete recommended folder structure under Grok Projects/Studio.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from lib.bootstrap import ensure_paths
ensure_paths()
from lib.studio_paths import STUDIO_DIR, STUDIO_FOLDERS


def initialize_workspace():
    created = []
    STUDIO_DIR.mkdir(parents=True, exist_ok=True)
    for folder in STUDIO_FOLDERS:
        path = STUDIO_DIR / folder
        if not path.exists():
            path.mkdir(parents=True, exist_ok=True)
            created.append(path)
    if created:
        print("✅ Workspace initialized. Created folders:")
        for path in created:
            print(f"   - {path}")
    else:
        print(f"✅ Workspace already fully initialized under {STUDIO_DIR}")


if __name__ == "__main__":
    initialize_workspace()