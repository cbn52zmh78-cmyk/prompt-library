#!/usr/bin/env python3
"""Language Atlas status report — registry, corpus coverage, research queue."""

from __future__ import annotations

import json
from collections import Counter
from datetime import datetime

from _paths import QUEUE_FILE, REGISTRY_FILE, language_dir


def main() -> int:
    registry = json.loads(REGISTRY_FILE.read_text(encoding="utf-8"))
    queue = json.loads(QUEUE_FILE.read_text(encoding="utf-8"))

    print(f"\n{'=' * 60}")
    print(f"LANGUAGE ATLAS STATUS — {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print(f"{'=' * 60}\n")

    by_status = Counter(e["status"] for e in registry["languages"])
    by_tier = Counter(e.get("revival_tier", "?") for e in registry["languages"])

    print(f"Languages registered: {len(registry['languages'])}")
    print(f"  by status: {dict(by_status)}")
    print(f"  by revival tier: {dict(by_tier)}")
    print()

    print("Corpus coverage:")
    total_texts = 0
    for entry in sorted(registry["languages"], key=lambda e: e["name"]):
        path = language_dir(entry["slug"], entry["status"])
        count = 0
        training = False
        if path:
            corpus = path / "corpus" / "known_texts.json"
            if corpus.exists():
                count = len(json.loads(corpus.read_text(encoding="utf-8")).get("texts", []))
            training = (path / "grok_training").exists() and any(
                (path / "grok_training").glob("training_pack_*.md")
            )
        total_texts += count
        pack = "✅" if training else "—"
        print(f"  {entry['name']:24} texts:{count:3}  training_pack:{pack}")

    print(f"\n  Total attested texts catalogued: {total_texts}")

    pending = [t for t in queue.get("queue", []) if t.get("status") == "pending"]
    print(f"\nResearch queue: {len(pending)} pending / {len(queue.get('queue', []))} total")
    for task in pending[:5]:
        print(f"  [{task.get('priority', '?').upper()}] {task['language']}: {task['task']}")

    print(f"\n{'=' * 60}\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())