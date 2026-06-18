#!/usr/bin/env python3
from __future__ import annotations

import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from brain.modality_scraper import scrape_modality, write_crosslink_index_report  # noqa: E402

NEW = [
    "deixis",
    "speech-acts",
    "discourse-markers",
    "code-switching",
    "hangul",
    "devanagari",
    "phoenician-alphabet",
    "oracle-bone-script",
]

if __name__ == "__main__":
    for slug in NEW:
        r = scrape_modality(slug)
        cl = r.get("corpus_cross_links", {})
        src = ",".join(r.get("sources_used", []))
        flags = len(r.get("uncertainty_flags", []))
        print(
            f"{slug}: [{src}] flags={flags} "
            f"lang={cl.get('language_link_count', 0)} mod={cl.get('modality_link_count', 0)}"
        )
        time.sleep(0.5)
    out = write_crosslink_index_report()
    print(f"Cross-link index: {out}")