#!/usr/bin/env python3
"""DAVID reports to us — consolidated brain research report."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from brain.reporter import build_report, write_report  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate DAVID brain research report.")
    parser.add_argument("--language", help="Single language slug (default: all)")
    parser.add_argument("--print", action="store_true", dest="do_print", help="Print to stdout")
    args = parser.parse_args()

    content = build_report(args.language)
    out = write_report(args.language)

    print(f"\n📋 DAVID Brain Report")
    print(f"   Saved: {out}")
    print(f"   Latest: {ROOT / 'reports' / 'latest_brain_report.md'}\n")

    if args.do_print:
        print(content)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())