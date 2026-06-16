#!/usr/bin/env python3
"""Convenience launcher — delegates to tools/dual_ai_helper.py (canonical)."""

import runpy
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TOOLS = ROOT / "tools"
for path in (ROOT, TOOLS):
    entry = str(path)
    if entry not in sys.path:
        sys.path.insert(0, entry)

runpy.run_path(str(TOOLS / "dual_ai_helper.py"), run_name="__main__")