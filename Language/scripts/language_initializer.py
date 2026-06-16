#!/usr/bin/env python3
"""Scaffold folder structure for a new language in the Language Atlas."""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone

from _paths import DATA_DIR, LANGUAGES_DIR, REGISTRY_FILE, STATUS_DIRS


def load_registry() -> dict:
    return json.loads(REGISTRY_FILE.read_text(encoding="utf-8"))


def save_registry(data: dict) -> None:
    data["updated"] = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    REGISTRY_FILE.write_text(json.dumps(data, indent=2), encoding="utf-8")


def init_language(slug: str, name: str, status: str, family: str, period: str) -> None:
    if status not in STATUS_DIRS:
        raise ValueError(f"status must be one of: {', '.join(STATUS_DIRS)}")

    lang_root = STATUS_DIRS[status] / slug
    for sub in ("corpus", "research", "grok_training"):
        (lang_root / sub).mkdir(parents=True, exist_ok=True)

    profile = {
        "id": slug,
        "name": name,
        "status": status,
        "revival_tier": "medium",
        "family": family,
        "period": period,
        "script": "",
        "region": "",
        "training_readiness": "scaffold",
        "primary_sources": [],
    }
    (lang_root / "profile.json").write_text(json.dumps(profile, indent=2), encoding="utf-8")

    corpus = {"language": slug, "texts": []}
    (lang_root / "corpus" / "known_texts.json").write_text(
        json.dumps(corpus, indent=2), encoding="utf-8"
    )
    (lang_root / "research" / "notes.md").write_text(
        f"# {name} — research notes\n\n", encoding="utf-8"
    )
    (lang_root / "research" / "sources.md").write_text(
        f"# {name} — sources\n\n", encoding="utf-8"
    )

    registry = load_registry()
    if not any(entry["slug"] == slug for entry in registry["languages"]):
        registry["languages"].append(
            {
                "id": slug,
                "name": name,
                "slug": slug,
                "status": status,
                "revival_tier": "medium",
                "family": family,
                "period": period,
                "script": "",
                "corpus_size": "unknown",
                "decipherment": "unknown",
                "history_links": [],
                "notes": "",
            }
        )
        save_registry(registry)

    print(f"✅ Language scaffolded: {lang_root}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Initialize a language in the Language Atlas.")
    parser.add_argument("--slug", required=True)
    parser.add_argument("--name", required=True)
    parser.add_argument(
        "--status",
        required=True,
        choices=sorted(STATUS_DIRS),
    )
    parser.add_argument("--family", required=True)
    parser.add_argument("--period", required=True)
    args = parser.parse_args()
    init_language(args.slug, args.name, args.status, args.family, args.period)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())