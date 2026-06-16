#!/usr/bin/env python3
"""Run DAVID Brain scheduler from workspace tools/."""

from __future__ import annotations

import _bootstrap  # noqa: F401
import subprocess
import sys

from workspace_paths import DAVID_DIR

SCHEDULER = DAVID_DIR / "scripts" / "david_brain_scheduler.py"


def main() -> None:
    if not SCHEDULER.exists():
        print(f"❌ DAVID brain scheduler not found: {SCHEDULER}")
        sys.exit(1)
    subprocess.run([sys.executable, str(SCHEDULER), *sys.argv[1:]], check=False)


if __name__ == "__main__":
    main()