#!/usr/bin/env python3
"""Language Atlas status — delegates to Language/scripts/revival_status_reporter.py."""

from __future__ import annotations

import _bootstrap  # noqa: F401
import subprocess
import sys

from workspace_paths import LANGUAGE_DIR

REPORTER = LANGUAGE_DIR / "scripts" / "revival_status_reporter.py"


def main() -> None:
    if not REPORTER.exists():
        print(f"❌ Language module not found: {REPORTER}")
        sys.exit(1)
    subprocess.run([sys.executable, str(REPORTER)], check=False)


if __name__ == "__main__":
    main()