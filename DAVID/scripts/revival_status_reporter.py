#!/usr/bin/env python3
"""DAVID status report — registry, corpus coverage, research queue."""

from __future__ import annotations

import json
from collections import Counter
from datetime import datetime

from _paths import QUEUE_FILE, REGISTRY_FILE, language_dir


def main() -> int:
    registry = json.loads(REGISTRY_FILE.read_text(encoding="utf-8"))
    queue = json.loads(QUEUE_FILE.read_text(encoding="utf-8"))

    print(f"\n{'=' * 60}")
    print(f"DAVID STATUS — {datetime.now().strftime('%Y-%m-%d %H:%M')}")
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

    from pathlib import Path as _Path

    brain_log = _Path(__file__).resolve().parents[1] / "data" / "brain_cache" / "scrape_log.json"
    brain_scraped = 0
    for entry in registry["languages"]:
        brain_file = (
            _Path(__file__).resolve().parents[1]
            / "languages"
            / entry["status"]
            / entry["slug"]
            / "research"
            / "brain"
            / "latest_scrape.json"
        )
        if brain_file.exists():
            brain_scraped += 1
    print(f"\nDAVID Brain: {brain_scraped}/{len(registry['languages'])} languages scraped")
    if brain_log.exists():
        import json as _json

        log = _json.loads(brain_log.read_text(encoding="utf-8"))
        if log:
            last = log[-1]
            print(f"  Last scrape: {last.get('slug')} @ {last.get('scraped_at', '')[:16]}")

    latest_report = _Path(__file__).resolve().parents[1] / "reports" / "latest_brain_report.md"
    if latest_report.exists():
        print(f"  Latest report: {latest_report}")

    sched_file = _Path(__file__).resolve().parents[1] / "data" / "brain_schedule.json"
    if sched_file.exists():
        import json as _json2

        sched = _json2.loads(sched_file.read_text(encoding="utf-8"))
        print(
            f"\nBrain scheduler: cycle {sched.get('current_cycle', 1)} | "
            f"batches {sched.get('total_batches_run', 0)} | "
            f"interval {sched.get('interval_seconds', 3600)}s"
        )
        if sched.get("last_batch_at"):
            print(f"  Last batch: {sched['last_batch_at'][:16]} → {sched.get('last_batch_languages', [])}")

    pending = [t for t in queue.get("queue", []) if t.get("status") == "pending"]
    print(f"\nResearch queue: {len(pending)} pending / {len(queue.get('queue', []))} total")
    for task in pending[:5]:
        print(f"  [{task.get('priority', '?').upper()}] {task['language']}: {task['task']}")

    print(f"\n{'=' * 60}\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())