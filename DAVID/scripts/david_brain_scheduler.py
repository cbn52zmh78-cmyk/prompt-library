#!/usr/bin/env python3
"""
DAVID Brain Scheduler — continuous / interval scraping with automatic rotation.

Runs batches of language scrapes, prioritizing research-queue assignments and
stale/error languages. Shifts to the next language when each batch completes.

Usage:
  python david_brain_scheduler.py --once              # one batch, exit
  python david_brain_scheduler.py --daemon            # loop forever
  python david_brain_scheduler.py --daemon --interval 1800
  python david_brain_scheduler.py --status            # show next batch without scraping
"""

from __future__ import annotations

import argparse
import json
import signal
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from brain.reporter import write_report  # noqa: E402
from brain.scheduler import (  # noqa: E402
    load_schedule,
    mark_assignments_in_progress,
    next_batch,
    record_batch,
    save_schedule,
    schedule_status,
)
from brain.scraper import scrape_language  # noqa: E402

_running = True


def _handle_stop(signum, frame) -> None:
    global _running
    _running = False
    print("\n⏹ Scheduler stopping (finish current batch first if running)...")


def _print_status() -> None:
    info = schedule_status()
    state = info["schedule"]
    print("\n=== DAVID BRAIN SCHEDULER STATUS ===\n")
    print(f"  Enabled:           {state.get('enabled', True)}")
    print(f"  Interval:          {state.get('interval_seconds', 3600)}s")
    print(f"  Batch size:        {state.get('batch_size', 1)}")
    print(f"  Stale threshold:   {state.get('stale_hours', 24)}h")
    print(f"  Current cycle:     {state.get('current_cycle', 1)}")
    print(f"  Batches run:       {state.get('total_batches_run', 0)}")
    print(f"  Last batch:        {state.get('last_batch_at', '—')}")
    print(f"  Languages scraped: {info['languages_scraped']}/{info['languages_total']}")
    print(f"  Queue pending:     {info['queue_pending']}")
    print("\n  Next batch:")
    if not info["next_batch"]:
        print("    (none — all languages fresh; will rotate on interval)")
    for item in info["next_batch"]:
        assigns = len(item.get("assignments", []))
        print(
            f"    • {item['name']} ({item['slug']}) score={item['score']}"
            f" [{', '.join(item['reasons'])}] assignments={assigns}"
        )
    print()


def _run_batch(*, deep: bool, report: bool) -> list[str]:
    targets = next_batch()
    if not targets:
        print("  No targets this batch (waiting for stale rotation).")
        return []

    slugs = [t["slug"] for t in targets]
    mark_assignments_in_progress(slugs)

    print(f"\n🧠 Batch @ {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}")
    batch_errors: dict[str, list[str]] = {}

    for item in targets:
        slug = item["slug"]
        print(f"\n→ Scraping: {item['name']} ({slug})")
        if item.get("assignments"):
            for a in item["assignments"][:2]:
                print(f"   assignment: {a.get('task', '')[:72]}")
        try:
            result = scrape_language(slug, deep=deep)
            errs = result.get("errors", [])
            if errs:
                batch_errors[slug] = errs
            ipa = result.get("pronunciation_summary", {}).get("total_ipa_entries", 0)
            src = ", ".join(result.get("sources_used", []))
            warn = f" ⚠️ {len(errs)} warnings" if errs else ""
            print(f"   ✅ IPA={ipa} sources=[{src}]{warn}")
        except Exception as exc:
            batch_errors[slug] = [str(exc)]
            print(f"   ❌ {exc}")

    record_batch(slugs, errors=batch_errors)

    if report:
        out = write_report()
        print(f"\n📋 Report: {out}")

    return slugs


def main() -> int:
    parser = argparse.ArgumentParser(description="DAVID Brain interval scheduler.")
    parser.add_argument("--once", action="store_true", help="Run one batch and exit")
    parser.add_argument("--daemon", action="store_true", help="Loop continuously at interval")
    parser.add_argument("--status", action="store_true", help="Show schedule status only")
    parser.add_argument("--interval", type=int, help="Seconds between batches (overrides config)")
    parser.add_argument("--batch-size", type=int, help="Languages per batch")
    parser.add_argument("--stale-hours", type=float, help="Re-scrape after N hours")
    parser.add_argument("--deep", action="store_true", help="Deep scrape (corpus lemmas)")
    parser.add_argument("--no-report", action="store_true", help="Skip report after batch")
    parser.add_argument(
        "--set-interval",
        type=int,
        help="Persist interval to brain_schedule.json and exit",
    )
    args = parser.parse_args()

    state = load_schedule()

    if args.set_interval is not None:
        state["interval_seconds"] = args.set_interval
        save_schedule(state)
        print(f"✅ Interval saved: {args.set_interval}s")
        return 0

    if args.interval is not None:
        state["interval_seconds"] = args.interval
    if args.batch_size is not None:
        state["batch_size"] = args.batch_size
    if args.stale_hours is not None:
        state["stale_hours"] = args.stale_hours
    save_schedule(state)

    if args.status:
        _print_status()
        return 0

    if not args.once and not args.daemon:
        parser.error("Specify --once, --daemon, or --status")

    deep = args.deep or bool(state.get("deep", True))
    report = not args.no_report and bool(state.get("report_after_batch", True))
    interval = int(state.get("interval_seconds", 3600))

    signal.signal(signal.SIGINT, _handle_stop)
    if hasattr(signal, "SIGTERM"):
        signal.signal(signal.SIGTERM, _handle_stop)

    print("\n=== DAVID BRAIN SCHEDULER ===")
    print(f"  Mode: {'daemon' if args.daemon else 'once'}")
    print(f"  Interval: {interval}s | Batch: {state.get('batch_size', 1)} | Deep: {deep}")

    if args.once:
        _run_batch(deep=deep, report=report)
        _print_status()
        return 0

    while _running:
        if not state.get("enabled", True):
            print("Scheduler disabled in brain_schedule.json. Sleeping...")
            time.sleep(interval)
            state = load_schedule()
            continue

        _run_batch(deep=deep, report=report)
        _print_status()

        if not _running:
            break

        print(f"💤 Next batch in {interval}s (Ctrl+C to stop)")
        slept = 0
        while _running and slept < interval:
            time.sleep(min(5, interval - slept))
            slept += 5

    print("Scheduler stopped.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())