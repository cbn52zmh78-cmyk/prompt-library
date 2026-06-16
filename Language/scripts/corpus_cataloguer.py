#!/usr/bin/env python3
"""Add attested texts to a language corpus (known_texts.json)."""

from __future__ import annotations

import argparse
import json
import re
from datetime import datetime, timezone

from _paths import REGISTRY_FILE, language_dir


def slugify(text: str) -> str:
    slug = text.lower().strip()
    slug = re.sub(r"[^a-z0-9]+", "-", slug)
    return slug.strip("-")[:48]


def load_entry(slug: str) -> dict:
    data = json.loads(REGISTRY_FILE.read_text(encoding="utf-8"))
    entry = next((e for e in data["languages"] if e["slug"] == slug), None)
    if not entry:
        raise SystemExit(f"Unknown language: {slug}")
    return entry


def add_text(
    language: str,
    title: str,
    transliteration: str,
    translation: str,
    source: str,
    text_type: str = "inscription",
    confidence: str = "attested",
    notes: str = "",
) -> None:
    entry = load_entry(language)
    lang_path = language_dir(language, entry["status"])
    if not lang_path:
        raise SystemExit(f"Language folder missing for {language}. Run language_initializer.py first.")

    corpus_file = lang_path / "corpus" / "known_texts.json"
    corpus = json.loads(corpus_file.read_text(encoding="utf-8"))

    text_id = slugify(title)
    record = {
        "id": text_id,
        "title": title,
        "type": text_type,
        "source": source,
        "transliteration": transliteration,
        "translation": translation,
        "confidence": confidence,
        "catalogued": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
        "notes": notes,
    }
    corpus["texts"] = [t for t in corpus.get("texts", []) if t.get("id") != text_id]
    corpus["texts"].append(record)
    corpus_file.write_text(json.dumps(corpus, indent=2), encoding="utf-8")
    print(f"✅ Catalogued [{confidence}]: {title} → {corpus_file}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Catalog an attested text.")
    parser.add_argument("--language", required=True)
    parser.add_argument("--title", required=True)
    parser.add_argument("--transliteration", required=True)
    parser.add_argument("--translation", required=True)
    parser.add_argument("--source", required=True)
    parser.add_argument("--type", default="inscription")
    parser.add_argument("--confidence", default="attested", choices=["attested", "reconstructed", "hypothesis", "unknown"])
    parser.add_argument("--notes", default="")
    args = parser.parse_args()

    add_text(
        args.language,
        args.title,
        args.transliteration,
        args.translation,
        args.source,
        args.type,
        args.confidence,
        args.notes,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())