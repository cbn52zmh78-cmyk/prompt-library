#!/usr/bin/env python3
"""Convenience launcher — delegates to tools/launcher.py (canonical)."""

import runpy
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TOOLS = ROOT / "tools"
for path in (ROOT, TOOLS):
    entry = str(path)
    if entry not in sys.path:
        sys.path.insert(0, entry)

runpy.run_path(str(TOOLS / "launcher.py"), run_name="__main__")