#!/usr/bin/env python3
"""NEXUS Tools Launcher — quick menu for AGENTS tooling."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

TOOLS = Path(__file__).resolve().parent
WORKSPACE = Path.home() / "Videos" / "Grok Projects"
NEXUS_SCRIPTS = WORKSPACE / "Nexus" / "scripts"

MENU = """
NEXUS Tools Launcher
====================
1  RE Pulse (market data)
2  Magazine shot-list templater
3  Professional Editorial Writer v2.0
4  X MCP auth check
5  Market Edge issue generator
6  Compliance report
0  Exit
"""


def run_script(path: Path, *args: str) -> None:
    if not path.exists():
        print(f"Not found: {path}")
        return
    subprocess.run([sys.executable, str(path), *args], check=False)


def main() -> int:
    print(MENU)
    choice = input("Select option: ").strip()

    if choice == "1":
        run_script(NEXUS_SCRIPTS / "re_market_pulse.py")
    elif choice == "2":
        run_script(WORKSPACE / "Studio" / "MAGAZINE" / "scripts" / "magazine_shotlist_templater.py")
    elif choice == "3":
        title = input("Document title: ").strip() or "Untitled Brief"
        summary = input("Research summary: ").strip() or "Summary pending."
        run_script(
            WORKSPACE / "tools" / "professional_editorial_writer.py",
            "--title", title,
            "--summary", summary,
            "--style", "Chicago",
            "--type", "Research Brief",
        )
    elif choice == "4":
        run_script(TOOLS / "x_mcp" / "x_mcp_server.py", "--auth")
    elif choice == "5":
        title = input("Issue title: ").strip() or "Q3 2026 Market Conditions"
        focus = input("Focus: ").strip() or "Regional Opportunities"
        run_script(
            TOOLS / "market_edge" / "market_edge_generator.py",
            "--title", title,
            "--focus", focus,
        )
    elif choice == "6":
        state = input("State name: ").strip() or "Pennsylvania"
        run_script(WORKSPACE / "tools" / "compliance_report.py", state)
    elif choice == "0":
        return 0
    else:
        print("Invalid option.")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())