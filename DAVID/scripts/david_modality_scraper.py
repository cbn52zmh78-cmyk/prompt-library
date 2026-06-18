#!/usr/bin/env python3
"""
DAVID Scraper 2 — communication modalities beyond lexicon.

Sources: Wikipedia, Wiktionary, Wikidata (public APIs only; CC BY-SA / CC0).
Categories: phonetics-ipa, non-verbal, sign-languages, writing-systems.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from brain.modality_scraper import (  # noqa: E402
    coverage_report,
    scrape_modality,
    scrape_modality_batch,
)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="DAVID Scraper 2 — ingest public sources on how humans communicate."
    )
    parser.add_argument("--topic", help="Modality slug (e.g. gesture, cuneiform)")
    parser.add_argument("--category", help="Scrape all topics in category")
    parser.add_argument("--all", action="store_true", help="Scrape all registered modality topics")
    parser.add_argument("--deep", action="store_true", help="Include extra etymology/pronunciation sections")
    parser.add_argument("--coverage", action="store_true", help="Print coverage report (no network)")
    args = parser.parse_args()

    if args.coverage:
        report = coverage_report()
        print(json.dumps(report, indent=2))
        return 0

    if not args.topic and not args.category and not args.all:
        parser.error("Specify --topic <slug>, --category <cat>, --all, or --coverage")

    print("\n=== DAVID SCRAPER 2 — COMMUNICATION MODALITIES ===\n")

    if args.topic:
        results = [scrape_modality(args.topic, deep=args.deep)]
    else:
        results = scrape_modality_batch(category=args.category, deep=args.deep)

    for result in results:
        _print_summary(result)

    report = coverage_report()
    print(
        f"\n📊 Coverage: {report['scraped_topics']}/{report['total_topics']} topics scraped"
    )
    return 0


def _print_summary(result: dict) -> None:
    slug = result.get("slug", "?")
    if result.get("errors") and not result.get("sources_used"):
        print(f"❌ {slug}: {result['errors']}")
        return
    cat = result.get("category", "?")
    sources = ", ".join(result.get("sources_used", []))
    summary = result.get("modality_summary", {})
    kw = summary.get("keyword_count", 0)
    flags = summary.get("uncertainty_flag_count", 0)
    warns = f" ({len(result['errors'])} warnings)" if result.get("errors") else ""
    print(f"✅ {slug} [{cat}]: sources=[{sources}] keywords={kw} uncertainty_flags={flags}{warns}")


if __name__ == "__main__":
    raise SystemExit(main())