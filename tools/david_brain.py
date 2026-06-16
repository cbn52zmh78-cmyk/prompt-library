#!/usr/bin/env python3
"""Run DAVID Brain scraper from workspace tools/."""

from __future__ import annotations

import _bootstrap  # noqa: F401
import subprocess
import sys

from workspace_paths import DAVID_DIR

SCRAPER = DAVID_DIR / "scripts" / "david_brain_scraper.py"


def main() -> None:
    if not SCRAPER.exists():
        print(f"❌ DAVID brain scraper not found: {SCRAPER}")
        sys.exit(1)
    subprocess.run([sys.executable, str(SCRAPER), *sys.argv[1:]], check=False)


if __name__ == "__main__":
    main()