#!/usr/bin/env python3
"""Generate categorized research queries for language corpus gathering and decipherment."""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

from _paths import REGISTRY_FILE, RESEARCH_OUT, language_dir

QUERY_TEMPLATES: dict[str, tuple[str, ...]] = {
    "corpus": (
        "{language} primary texts transliteration corpus",
        "{language} inscription database digital archive",
        "{language} bilingual text parallel translation",
        "{family} ancient texts critical edition PDF",
    ),
    "grammar": (
        "{language} grammar reference morphology syntax",
        "{language} historical linguistics scholarly overview",
        "{family} comparative grammar daughter languages",
        "{language} phonology reconstruction",
    ),
    "decipherment": (
        "{language} decipherment progress undeciphered script",
        "{language} sign list syllabary values",
        "{language} computational analysis character frequency",
        "{language} proposed decipherment critique scholarly",
    ),
    "revival": (
        "{language} revival constructed language community",
        "{language} neo-{family} learning resources",
        "{language} pronunciation reconstruction audio",
        "{language} pedagogical grammar modern edition",
    ),
    "digital": (
        "{language} ORACC CDLI ETCSL digital corpus",
        "{language} Perseus TLG PHI Greek Latin inscription",
        "{language} Open Access journal ancient language",
        "{language} Unicode script encoding proposal",
    ),
}


def load_entry(slug: str) -> dict:
    data = json.loads(REGISTRY_FILE.read_text(encoding="utf-8"))
    entry = next((e for e in data["languages"] if e["slug"] == slug), None)
    if not entry:
        raise SystemExit(f"Unknown language: {slug}")
    return entry


def generate_queries(slug: str, categories: list[str]) -> str:
    entry = load_entry(slug)
    name = entry["name"]
    family = entry.get("family", "")

    lines = [
        f"# Research Queries — {name}",
        f"Generated: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}",
        f"Slug: {slug}",
        f"Status: {entry['status']} | Decipherment: {entry.get('decipherment', 'unknown')}",
        "",
    ]

    for cat in categories:
        lines.append(f"## {cat.title()}")
        for template in QUERY_TEMPLATES.get(cat, ()):
            lines.append(f"- {template.format(language=name, family=family)}")
        lines.append("")

    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate language research search queries.")
    parser.add_argument("--language", required=True, help="Language slug")
    parser.add_argument(
        "--categories",
        default="corpus,grammar,decipherment,revival,digital",
        help="Comma-separated categories",
    )
    parser.add_argument("--output", type=Path, help="Output path (default: languages/.../research/)")
    args = parser.parse_args()

    cats = [c.strip() for c in args.categories.split(",") if c.strip()]
    content = generate_queries(args.language, cats)

    if args.output:
        out = args.output
    else:
        entry = load_entry(args.language)
        lang_path = language_dir(args.language, entry["status"])
        out = (lang_path / "research" / "search_queries.md") if lang_path else RESEARCH_OUT / f"{args.language}_queries.md"

    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(content, encoding="utf-8")
    print(f"✅ Research queries saved: {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())