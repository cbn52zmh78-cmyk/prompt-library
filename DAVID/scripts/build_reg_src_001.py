#!/usr/bin/env python3
"""Aggregate scrape citations into REG-SRC-001 source registry."""

from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from brain.modality_scraper import coverage_report  # noqa: E402


def _feed(
    entries: list[dict],
    seen: set[tuple],
    slug: str,
    target_type: str,
    scrape_path: Path,
) -> None:
    if not scrape_path.exists():
        return
    data = json.loads(scrape_path.read_text(encoding="utf-8"))
    retrieved_default = data.get("retrieval_date") or data.get("scraped_at", "")[:10]

    for cite in data.get("citations", []):
        url = cite.get("url") or (
            f"https://www.wikidata.org/wiki/{cite['qid']}" if cite.get("qid") else ""
        )
        key = (slug, cite.get("source"), url)
        if key in seen:
            continue
        seen.add(key)
        entries.append(
            {
                "record_id": f"{target_type}:{slug}:{cite.get('source', '?').lower()}",
                "target_slug": slug,
                "target_type": target_type,
                "source_name": cite.get("source"),
                "source_url": url,
                "retrieved_date": cite.get("retrieved", retrieved_default),
                "license": cite.get("license", ""),
                "title": cite.get("title") or cite.get("qid", ""),
            }
        )

    for src in ("wikipedia", "wikidata", "wiktionary"):
        block = data.get(src)
        if not block:
            continue
        url = block.get("url") or (
            f"https://www.wikidata.org/wiki/{block['qid']}" if block.get("qid") else ""
        )
        key = (slug, src, url)
        if key in seen:
            continue
        seen.add(key)
        entries.append(
            {
                "record_id": f"{target_type}:{slug}:{src}",
                "target_slug": slug,
                "target_type": target_type,
                "source_name": "Wikidata" if src == "wikidata" else src.capitalize(),
                "source_url": url,
                "retrieved_date": data.get("scraped_at", "")[:10] or retrieved_default,
                "license": block.get("license", ""),
                "title": block.get("title") or block.get("label", slug),
            }
        )


def main() -> int:
    retrieved = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    entries: list[dict] = []
    seen: set[tuple] = set()

    for path in (ROOT / "communication-modalities").rglob("latest_scrape.json"):
        slug = path.parents[2].name  # .../{category}/{slug}/research/brain/
        _feed(entries, seen, slug, "modality", path)

    for path in (ROOT / "languages").rglob("latest_scrape.json"):
        slug = path.parents[2].name  # .../{status}/{slug}/research/brain/
        _feed(entries, seen, slug, "language", path)

    cov = coverage_report()
    lang_total = len(json.loads((ROOT / "data" / "language_registry.json").read_text())["languages"])
    lang_scraped = len(list((ROOT / "languages").rglob("latest_scrape.json")))
    brain_cfg = json.loads((ROOT / "data" / "brain_sources.json").read_text())

    out = {
        "id": "REG-SRC-001",
        "version": "1.0",
        "updated": retrieved,
        "description": "DAVID public-source citation registry (REG-SRC-001)",
        "guardrails": {
            "public_pages_only": True,
            "robots_txt_compliant": True,
            "tos_compliant": True,
            "rate_limit_seconds": brain_cfg.get("rate_limit_seconds", 3.5),
            "no_logins": True,
            "no_captcha": True,
            "no_gated_data": True,
        },
        "allowed_sources": brain_cfg["sources"],
        "entries": sorted(entries, key=lambda e: (e["target_type"], e["target_slug"], e["source_name"])),
        "coverage": {
            "languages": {"scraped": lang_scraped, "total": lang_total},
            "modalities": {"scraped": cov["scraped_topics"], "total": cov["total_topics"]},
            "citation_count": len(entries),
        },
    }

    out_path = ROOT / "data" / "REG-SRC-001_source_registry.json"
    out_path.write_text(json.dumps(out, indent=2), encoding="utf-8")
    print(json.dumps({"written": str(out_path), "entries": len(entries), "coverage": out["coverage"]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())