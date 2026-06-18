#!/usr/bin/env python3
"""T2 batch: finish pending + scrape expansion topics."""

from __future__ import annotations

import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from brain.modality_scraper import scrape_modality  # noqa: E402

NEW_TOPICS = [
    "prosody",
    "intonation",
    "turn-taking",
    "french-sign-language",
    "german-sign-language",
    "japanese-sign-language",
    "linear-b-script",
    "manyogana",
    "hiragana",
    "futhorc",
    "aztec-script",
]

DEEP_TOPICS = ["linear-a-script", "paralinguistics"]

CORPUS_RELINK = [
    "cuneiform",
    "gothic-alphabet",
    "etruscan-alphabet",
    "latin-script",
    "hiragana",
    "linear-b-script",
]

def main() -> int:
    plan: list[tuple[str, bool]] = []
    for slug in DEEP_TOPICS:
        plan.append((slug, True))
    for slug in NEW_TOPICS:
        if slug not in DEEP_TOPICS:
            plan.append((slug, False))
    for slug in CORPUS_RELINK:
        if slug not in {s for s, _ in plan}:
            plan.append((slug, False))

    print(f"Scraping {len(plan)} topics...")
    for slug, deep in plan:
        result = scrape_modality(slug, deep=deep)
        src = ",".join(result.get("sources_used", []))
        flags = len(result.get("uncertainty_flags", []))
        links = result.get("corpus_cross_links", {})
        ll = links.get("language_link_count", 0)
        ml = links.get("modality_link_count", 0)
        print(f"  {slug}: sources=[{src}] flags={flags} corpus_links={ll} modality_links={ml}")
        time.sleep(0.5)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())