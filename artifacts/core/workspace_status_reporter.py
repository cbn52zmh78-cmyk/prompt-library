#!/usr/bin/env python3
"""
Workspace Status Reporter v1.2 — Producer
Shows counts and health of all major Studio folders.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from lib.bootstrap import ensure_paths
ensure_paths()
from lib.studio_paths import STUDIO_DIR, STUDIO_FOLDERS

from datetime import datetime


def _count_files(path: Path) -> int:
    if not path.is_dir():
        return 0
    return sum(1 for p in path.rglob("*") if p.is_file())


def report_status():
    print("\n" + "=" * 65)
    print("WORKSPACE STATUS REPORT —", datetime.now().strftime("%Y-%m-%d %H:%M"))
    print(f"Studio root: {STUDIO_DIR}")
    print("=" * 65)
    for folder in STUDIO_FOLDERS:
        path = STUDIO_DIR / folder
        if path.is_dir():
            count = _count_files(path)
            print(f"  {folder:<40} → {count:4} files")
        else:
            print(f"  {folder:<40} → (missing)")
    print("=" * 65)


if __name__ == "__main__":
    report_status()