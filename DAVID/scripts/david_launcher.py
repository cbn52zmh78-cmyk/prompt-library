#!/usr/bin/env python3
"""Master launcher for DAVID module tools."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent
PYTHON = sys.executable

TOOLS = [
    ("revival_status_reporter.py", "DAVID status report"),
    ("language_registry_manager.py list", "List all languages"),
    ("language_registry_manager.py list --tier high", "High-priority revival languages"),
    ("research_query_generator.py --language etruscan", "Etruscan research queries"),
    ("grok_training_pack_builder.py --language classical-latin", "Latin Grok training pack"),
    ("grok_training_pack_builder.py --language gothic", "Gothic Grok training pack"),
    ("corpus_cataloguer.py --help", "Catalog a new attested text"),
    ("language_initializer.py --help", "Scaffold a new language"),
]


def main() -> int:
    print("\n" + "=" * 60)
    print("DAVID — Dead Language Research & Revival")
    print("=" * 60)
    for i, (_, desc) in enumerate(TOOLS, 1):
        print(f"  {i:2}. {desc}")
    print("  0. Exit")
    print("=" * 60)

    choice = input("\nSelect: ").strip()
    if choice == "0":
        return 0
    try:
        idx = int(choice) - 1
        script, _ = TOOLS[idx]
        parts = script.split()
        subprocess.run([PYTHON, str(SCRIPTS / parts[0]), *parts[1:]], check=False)
    except (ValueError, IndexError):
        print("Invalid selection.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())