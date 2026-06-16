#!/usr/bin/env python3
"""Build Grok training/context packs from attested corpus texts — David protocol."""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

from _paths import HISTORY_ROOT, PROMPTS_DIR, REGISTRY_FILE, TRAINING_OUT, language_dir

DAVID_PROMPT = PROMPTS_DIR / "david_linguist_system.md"


def load_entry(slug: str) -> dict:
    data = json.loads(REGISTRY_FILE.read_text(encoding="utf-8"))
    entry = next((e for e in data["languages"] if e["slug"] == slug), None)
    if not entry:
        raise SystemExit(f"Unknown language: {slug}")
    return entry


def history_cross_links(links: list[str]) -> str:
    if not links:
        return "_No History figure links yet._"
    lines = []
    for slug in links:
        fig_dir = HISTORY_ROOT / "figures" / slug
        status = "✅" if fig_dir.exists() else "⚠️ missing"
        lines.append(f"- `{slug}` {status} — `History/figures/{slug}/`")
    return "\n".join(lines)


def build_pack(slug: str) -> str:
    entry = load_entry(slug)
    lang_path = language_dir(slug, entry["status"])
    profile = {}
    texts: list[dict] = []

    if lang_path:
        profile_file = lang_path / "profile.json"
        if profile_file.exists():
            profile = json.loads(profile_file.read_text(encoding="utf-8"))
        corpus_file = lang_path / "corpus" / "known_texts.json"
        if corpus_file.exists():
            texts = json.loads(corpus_file.read_text(encoding="utf-8")).get("texts", [])

    lines = [
        f"# Grok Training Pack — {entry['name']}",
        f"Generated: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}",
        f"Protocol: DAVID (corpus-first, uncertainty-tagged)",
        "",
        "## System context",
        "",
    ]

    if DAVID_PROMPT.exists():
        lines.append(DAVID_PROMPT.read_text(encoding="utf-8"))
    else:
        lines.append("_David linguist system prompt not found._")

    lines.extend(
        [
            "",
            "---",
            "",
            f"## Language profile: {entry['name']}",
            "",
            f"- **Status:** {entry['status']}",
            f"- **Revival tier:** {entry.get('revival_tier')}",
            f"- **Family:** {entry['family']}",
            f"- **Period:** {entry['period']}",
            f"- **Script:** {entry.get('script') or profile.get('script', '—')}",
            f"- **Decipherment:** {entry.get('decipherment', 'unknown')}",
            f"- **Training readiness:** {profile.get('training_readiness', 'unknown')}",
            "",
            "## History cross-links",
            "",
            history_cross_links(entry.get("history_links") or profile.get("history_links") or []),
            "",
            "## Attested corpus (training blocks)",
            "",
        ]
    )

    if not texts:
        lines.append("_No texts catalogued yet. Use corpus_cataloguer.py to add attestations._")
    else:
        for i, text in enumerate(texts, 1):
            conf = text.get("confidence", "unknown")
            lines.extend(
                [
                    f"### Block {i}: {text.get('title', 'untitled')} `[{conf}]`",
                    "",
                    f"**Source:** {text.get('source', '—')}",
                    "",
                    "**Transliteration / original:**",
                    "```",
                    text.get("transliteration", ""),
                    "```",
                    "",
                    "**Translation / gloss:**",
                    text.get("translation", ""),
                    "",
                ]
            )
            if text.get("notes"):
                lines.append(f"**Notes:** {text['notes']}")
                lines.append("")

    lines.extend(
        [
            "## Instructions for Grok",
            "",
            "1. Treat each block as primary evidence — do not invent unattested forms.",
            "2. When asked to 'speak' this language, produce glossed excerpts or revival drafts tagged `[reconstructed]`.",
            "3. For editorial foreign-language copy in living languages, use native idiom.",
            "4. Queue next research via `research_query_generator.py --language " + slug + "`.",
            "",
            "## Next research tasks",
            "",
            f"- Expand corpus for {entry['name']}",
            "- Add grammar sketch with sourced morphology tables",
            "- Link additional History figures if applicable",
            "",
        ]
    )

    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Build Grok training pack from language corpus.")
    parser.add_argument("--language", required=True, help="Language slug")
    parser.add_argument("--output", type=Path, help="Output .md path")
    args = parser.parse_args()

    content = build_pack(args.language)
    entry = load_entry(args.language)
    lang_path = language_dir(args.language, entry["status"])

    if args.output:
        out = args.output
    elif lang_path:
        out = lang_path / "grok_training" / f"training_pack_{args.language}.md"
    else:
        out = TRAINING_OUT / f"training_pack_{args.language}.md"

    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(content, encoding="utf-8")
    print(f"✅ Training pack saved: {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())