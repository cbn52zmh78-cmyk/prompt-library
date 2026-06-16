#!/usr/bin/env python3
"""List, search, and inspect languages in the DAVID registry."""

from __future__ import annotations

import argparse
import json

from _paths import REGISTRY_FILE, language_dir


def load_registry() -> dict:
    return json.loads(REGISTRY_FILE.read_text(encoding="utf-8"))


def list_languages(status: str | None = None, tier: str | None = None) -> None:
    data = load_registry()
    print(f"\n=== LANGUAGE REGISTRY ({len(data['languages'])} languages) ===\n")
    for entry in sorted(data["languages"], key=lambda e: e["name"]):
        if status and entry["status"] != status:
            continue
        if tier and entry.get("revival_tier") != tier:
            continue
        links = ", ".join(entry.get("history_links") or []) or "—"
        print(f"  {entry['name']} ({entry['slug']})")
        print(f"    status: {entry['status']} | revival: {entry.get('revival_tier')} | family: {entry['family']}")
        print(f"    period: {entry['period']} | history: {links}")
        print()


def show_language(slug: str) -> None:
    data = load_registry()
    entry = next((e for e in data["languages"] if e["slug"] == slug), None)
    if not entry:
        print(f"❌ Not in registry: {slug}")
        return

    print(json.dumps(entry, indent=2))
    path = language_dir(slug, entry["status"])
    if path:
        print(f"\nFolder: {path}")
        corpus = path / "corpus" / "known_texts.json"
        if corpus.exists():
            texts = json.loads(corpus.read_text(encoding="utf-8")).get("texts", [])
            print(f"Corpus texts: {len(texts)}")


def main() -> int:
    parser = argparse.ArgumentParser(description="DAVID registry manager.")
    sub = parser.add_subparsers(dest="cmd", required=True)

    ls = sub.add_parser("list")
    ls.add_argument("--status")
    ls.add_argument("--tier")

    show = sub.add_parser("show")
    show.add_argument("slug")

    args = parser.parse_args()
    if args.cmd == "list":
        list_languages(args.status, args.tier)
    elif args.cmd == "show":
        show_language(args.slug)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())