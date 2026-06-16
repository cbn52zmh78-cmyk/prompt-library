#!/usr/bin/env python3
"""AGENTS wrapper for NEXUS Market Edge Quarterly Generator."""

from __future__ import annotations

import runpy
import sys
from pathlib import Path

NEXUS_SCRIPTS = Path(r"C:\Users\NCG\Videos\Grok Projects\Nexus\scripts")
NEXUS_SCRIPT = NEXUS_SCRIPTS / "market_edge_quarterly.py"

if __name__ == "__main__":
    if not NEXUS_SCRIPT.exists():
        print(f"Error: Nexus generator not found at {NEXUS_SCRIPT}")
        raise SystemExit(1)
    sys.path.insert(0, str(NEXUS_SCRIPTS))
    sys.argv[0] = str(NEXUS_SCRIPT)
    runpy.run_path(str(NEXUS_SCRIPT), run_name="__main__")