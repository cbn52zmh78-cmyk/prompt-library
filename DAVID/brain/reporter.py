"""DAVID Brain — human-readable research reports from scrape data."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

DAVID_ROOT = Path(__file__).resolve().parents[1]
REGISTRY_FILE = DAVID_ROOT / "data" / "language_registry.json"
REPORTS_DIR = DAVID_ROOT / "reports"
BRAIN_CACHE = DAVID_ROOT / "data" / "brain_cache"


def _load_registry() -> dict:
    return json.loads(REGISTRY_FILE.read_text(encoding="utf-8"))


def _find_scrape(slug: str, status: str) -> dict[str, Any] | None:
    path = DAVID_ROOT / "languages" / status / slug / "research" / "brain" / "latest_scrape.json"
    if path.exists():
        return json.loads(path.read_text(encoding="utf-8"))
    return None


def build_report(slug: str | None = None) -> str:
    registry = _load_registry()
    entries = registry["languages"]
    if slug:
        entries = [e for e in entries if e["slug"] == slug]
        if not entries:
            return f"# DAVID Brain Report\n\nUnknown language: `{slug}`\n"

    lines = [
        "# DAVID Brain Report",
        f"Generated: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}",
        "",
        "Public sources only: Wikipedia, Wiktionary, Wikidata (CC BY-SA / CC0).",
        "",
        "---",
        "",
    ]

    scraped = 0
    for entry in entries:
        data = _find_scrape(entry["slug"], entry["status"])
        if not data:
            lines.extend(_section_missing(entry))
            continue
        scraped += 1
        lines.extend(_section_language(entry, data))

    lines.extend(_section_log_summary())
    lines.append(f"\n---\n\n**Languages with brain data:** {scraped}/{len(entries)}\n")
    return "\n".join(lines)


def _section_missing(entry: dict) -> list[str]:
    return [
        f"## {entry['name']} (`{entry['slug']}`)",
        "",
        "⚠️ No brain scrape yet. Run:",
        f"`python DAVID/scripts/david_brain_scraper.py --language {entry['slug']}`",
        "",
    ]


def _section_language(entry: dict, data: dict[str, Any]) -> list[str]:
    lines = [
        f"## {entry['name']} (`{entry['slug']}`)",
        "",
        f"**Scraped:** {data.get('scraped_at', '—')} | **Sources:** {', '.join(data.get('sources_used', []))}",
        "",
    ]

    if data.get("errors"):
        lines.append("**Scrape warnings:**")
        for err in data["errors"]:
            lines.append(f"- {err}")
        lines.append("")

    wp = data.get("wikipedia", {})
    if wp.get("extract"):
        excerpt = wp["extract"][:1200].strip()
        if len(wp["extract"]) > 1200:
            excerpt += "…"
        lines.extend(["### Overview (Wikipedia)", "", excerpt, ""])
        if wp.get("url"):
            lines.append(f"Source: {wp['url']}")
            lines.append("")

    wd = data.get("wikidata", {})
    if wd:
        lines.extend(
            [
                "### Classification (Wikidata)",
                "",
                f"- **Label:** {wd.get('label', '—')}",
                f"- **ISO 639-3:** {wd.get('iso639_3') or '—'}",
                f"- **Description:** {wd.get('description', '—')}",
                "",
            ]
        )

    pron = data.get("pronunciation_summary", {})
    if pron.get("total_ipa_entries"):
        lines.extend(
            [
                "### Pronunciation map",
                "",
                f"**IPA entries found:** {pron['total_ipa_entries']} | **Accent buckets:** {pron.get('accent_count', 0)}",
                "",
            ]
        )
        for quality, ipas in pron.get("by_quality", {}).items():
            lines.append(f"- **{quality}:** {', '.join(ipas[:4]) or '—'}")
        lines.append("")
        for accent, ipas in list(pron.get("by_accent", {}).items())[:6]:
            lines.append(f"- *{accent}:* {', '.join(ipas[:3])}")
        lines.append("")

    wt = data.get("wiktionary", {})
    if wt.get("etymology_blocks"):
        lines.append("### Etymology (Wiktionary)")
        lines.append("")
        for block in wt["etymology_blocks"][:3]:
            text = block.get("text", "")[:800]
            lines.append(text)
            lines.append("")

    if wt.get("pronunciation_notes"):
        lines.append("### Pronunciation notes (Wiktionary)")
        lines.append("")
        for note in wt["pronunciation_notes"][:2]:
            lines.append(note.get("text", "")[:600])
            lines.append("")

    lines.append("---")
    lines.append("")
    return lines


def _section_log_summary() -> list[str]:
    log_file = BRAIN_CACHE / "scrape_log.json"
    if not log_file.exists():
        return ["## Brain activity log", "", "_No scrapes logged yet._", ""]
    log = json.loads(log_file.read_text(encoding="utf-8"))
    recent = log[-8:]
    lines = ["## Brain activity log (recent)", ""]
    for row in reversed(recent):
        err = f" ⚠️ {len(row['errors'])} errors" if row.get("errors") else ""
        lines.append(
            f"- `{row['slug']}` @ {row['scraped_at'][:16]} — "
            f"{row.get('ipa_count', 0)} IPA, sources: {', '.join(row.get('sources', []))}{err}"
        )
    lines.append("")
    return lines


def write_report(slug: str | None = None) -> Path:
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    content = build_report(slug)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    suffix = slug or "all"
    out = REPORTS_DIR / f"brain_report_{suffix}_{stamp}.md"
    out.write_text(content, encoding="utf-8")

    latest = REPORTS_DIR / "latest_brain_report.md"
    latest.write_text(content, encoding="utf-8")
    return out