#!/usr/bin/env python3
"""
DAVID Brain Scraper — public-source deep dive on etymology, diction, pronunciation.

Sources: Wikipedia, Wiktionary, Wikidata (APIs only; respectful rate limits).
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from brain.reporter import write_report  # noqa: E402
from brain.scraper import scrape_batch, scrape_language  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description="DAVID Brain — scrape public linguistic sources.")
    parser.add_argument("--language", help="Language slug (e.g. etruscan, gothic)")
    parser.add_argument("--all", action="store_true", help="Scrape all registered languages")
    parser.add_argument("--tier", help="Scrape languages with this revival tier (e.g. high)")
    parser.add_argument("--deep", action="store_true", help="Also look up corpus lemmas on Wiktionary")
    parser.add_argument("--report", action="store_true", help="Generate human report after scrape")
    args = parser.parse_args()

    if not args.language and not args.all and not args.tier:
        parser.error("Specify --language <slug>, --all, or --tier <tier>")

    print("\n=== DAVID BRAIN SCRAPER ===\n")

    if args.language:
        result = scrape_language(args.language, deep=args.deep)
        _print_summary(result)
    else:
        results = scrape_batch(tier=args.tier, deep=args.deep)
        for result in results:
            _print_summary(result)

    if args.report:
        out = write_report(args.language)
        print(f"\n📋 Report written: {out}")
        print(f"   Latest: {ROOT / 'reports' / 'latest_brain_report.md'}")

    return 0


def _print_summary(result: dict) -> None:
    slug = result.get("slug", "?")
    if result.get("errors") and not result.get("sources_used"):
        print(f"❌ {slug}: {result['errors']}")
        return
    ipa = result.get("pronunciation_summary", {}).get("total_ipa_entries", 0)
    ety = result.get("etymology_count", 0)
    sources = ", ".join(result.get("sources_used", []))
    warns = f" ({len(result['errors'])} warnings)" if result.get("errors") else ""
    print(f"✅ {slug}: sources=[{sources}] IPA={ipa} etymology_blocks={ety}{warns}")


if __name__ == "__main__":
    raise SystemExit(main())