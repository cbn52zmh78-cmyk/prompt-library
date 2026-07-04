#!/usr/bin/env python3
"""ingest_watcher.py — Lightweight file watcher for movie ingest sources.

Detects new plates / script revisions / identity locks and automatically runs:
  newest_pointer → record_scrape → continuity_evaluate

Usage:
    python ingest_watcher.py              # single pass (--once default)
    python ingest_watcher.py --once       # explicit single pass
    python ingest_watcher.py --interval 60
    python ingest_watcher.py --offline    # fixture data, no live files
"""
from __future__ import annotations

import argparse
import json
import signal
import sys
import threading
import time
from pathlib import Path
from typing import Any, Callable

from _paths import DAVID_ROOT

sys.path.insert(0, str(Path(__file__).resolve().parent))

from ingest_registry import (  # noqa: E402
    IngestRegistry,
    IngestSource,
    ScrapeBatch,
    movie_fixtures,
    movie_sources,
)
from production_catalog import (  # noqa: E402
    Catalog,
    bootstrap_from_identity_lock,
    catalog_path_for_product,
    continuity_evaluate,
)

try:
    from watchdog.events import FileSystemEventHandler
    from watchdog.observers import Observer

    _HAS_WATCHDOG = True
except ImportError:
    _HAS_WATCHDOG = False

INGEST_PATH = DAVID_ROOT / "productions" / "ingest_registry.json"
PROD_DIR = DAVID_ROOT / "productions"
MASTER_CATALOG = catalog_path_for_product("movie")
CUSTODY_LOG = PROD_DIR / "ingest_custody_log.csv"
FIXTURES_PATH = PROD_DIR / "ingest_fixtures.json"

WATCH_DIRS = [
    PROD_DIR,
    DAVID_ROOT / "scripts" / "longform_scripts",
]

SOURCE_ENTITY: dict[str, tuple[str, str]] = {
    "plate_actor": ("CHAR", "actor"),
    "plate_set": ("SET", "environment"),
    "plate_zone": ("SET", "zone_plate"),
}

_running = True
_debounce_timer: threading.Timer | None = None


def _log(msg: str) -> None:
    print(msg, flush=True)


def _file_record(path: Path, base: Path) -> dict[str, Any]:
    st = path.stat()
    rel = path.relative_to(base).as_posix()
    return {
        "id": rel,
        "file": str(path),
        "mtime": st.st_mtime,
        "size": st.st_size,
    }


def _glob_records(source: IngestSource, base: Path) -> list[dict[str, Any]]:
    pattern = source.url_pattern.replace("\\", "/")
    matches = [p for p in base.glob(pattern) if p.is_file()]
    records = [_file_record(p, base) for p in matches]
    records.sort(key=lambda r: (r["mtime"], r["id"]))
    return records


def _newest_id(records: list[dict[str, Any]]) -> str | None:
    if not records:
        return None
    return str(records[-1]["id"])


def _records_since(
    source: IngestSource,
    records: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    if not records:
        return []
    if not source.last_new_id:
        return [records[-1]]
    previous = source.last_new_id
    for i, rec in enumerate(records):
        if rec["id"] == previous:
            return records[i + 1 :]
    newest = _newest_id(records)
    if newest and newest != previous:
        return [records[-1]]
    return []


SCRIPTS_DIR = DAVID_ROOT / "scripts" / "longform_scripts"


def _resolve_record_path(record: dict[str, Any], source_id: str) -> Path | None:
    """Resolve absolute or fixture-relative file paths."""
    raw = record.get("file", "")
    if not raw:
        return None
    path = Path(raw)
    if path.is_file():
        return path
    if source_id == "script_revision":
        candidate = SCRIPTS_DIR / path.name
        if candidate.is_file():
            return candidate
    matches = list(DAVID_ROOT.rglob(path.name))
    return matches[0] if matches else None


def catalog_find_plate(catalog: Catalog, plate_path: str) -> bool:
    plate_name = Path(plate_path).name
    plate_resolved = str(Path(plate_path).resolve())
    for entry in catalog.entries.values():
        stored = entry.state.get("plate_file", "")
        if not stored:
            continue
        if stored == plate_path or stored == plate_resolved:
            return True
        if Path(stored).name == plate_name:
            return True
    return False


def _plate_name(record: dict[str, Any]) -> str:
    stem = Path(record["file"]).stem
    return stem.replace("_", " ").replace("-", " ").title()


def make_evaluate_fn(source_id: str) -> Callable[[list[dict[str, Any]]], dict[str, Any]]:
    def run_evaluate(records: list[dict[str, Any]]) -> dict[str, Any]:
        catalog = Catalog.load(MASTER_CATALOG, product="movie")
        registered_ids: list[str] = []

        if source_id == "identity_lock":
            for rec in records:
                lock_path = _resolve_record_path(rec, source_id)
                if not lock_path or not lock_path.is_file():
                    continue
                lock = json.loads(lock_path.read_text(encoding="utf-8"))
                entries = bootstrap_from_identity_lock(catalog, lock)
                registered_ids.extend(e.id for e in entries)
            catalog.save(MASTER_CATALOG)
            return {"registered": len(registered_ids), "ids": registered_ids}

        if source_id in SOURCE_ENTITY:
            entity_type, plate_type = SOURCE_ENTITY[source_id]
            for rec in records:
                resolved = _resolve_record_path(rec, source_id)
                file_path = str(resolved) if resolved else rec.get("file", "")
                if not file_path or catalog_find_plate(catalog, file_path):
                    continue
                display_name = rec.get("character") or rec.get("name") or _plate_name({**rec, "file": file_path})
                entry = catalog.register(
                    entity_type,
                    display_name if isinstance(display_name, str) else _plate_name({**rec, "file": file_path}),
                    state={
                        "plate_file": file_path,
                        "plate_type": plate_type,
                        "ingest_id": rec.get("id", ""),
                        "mtime": rec.get("mtime"),
                        "size": rec.get("size"),
                    },
                    notes=f"Auto-registered from ingest watcher ({source_id})",
                )
                registered_ids.append(entry.id)
            catalog.save(MASTER_CATALOG)
            return {"registered": len(registered_ids), "ids": registered_ids}

        if source_id == "script_revision":
            report: dict[str, Any] | None = None
            for rec in records:
                script_path = _resolve_record_path(rec, source_id)
                if not script_path or not script_path.is_file():
                    continue
                script = json.loads(script_path.read_text(encoding="utf-8"))
                report = continuity_evaluate(catalog, script)
            catalog.save(MASTER_CATALOG)
            if report:
                return report
            return {"registered": 0}

        catalog.save(MASTER_CATALOG)
        return {"registered": 0}

    return run_evaluate


def _format_eval_summary(source_id: str, result: dict[str, Any]) -> str:
    if source_id == "script_revision" and "continuity_score" in result:
        return (
            f"continuity evaluate score={result['continuity_score']}/"
            f"{result.get('continuity_tier', '?')}"
        )
    ids = result.get("ids") or []
    if ids:
        return f"registered {ids[0]}" + (f" (+{len(ids) - 1} more)" if len(ids) > 1 else "")
    count = result.get("registered", 0)
    if count:
        return f"registered {count} entr{'y' if count == 1 else 'ies'}"
    if result.get("error"):
        return f"evaluate error: {result['error']}"
    return "evaluate complete"


def _ensure_registry(offline: bool) -> IngestRegistry:
    reg = IngestRegistry.load(INGEST_PATH)
    if not reg.sources:
        for spec in movie_sources():
            reg.register_source(**spec)
        _log(f"[ingest] bootstrapped {len(reg.sources)} movie sources")
    if offline:
        fixture_path = FIXTURES_PATH
        if fixture_path.is_file():
            reg.fixtures = reg.fixtures.load(fixture_path)
        else:
            for src_id, records in movie_fixtures().items():
                reg.fixtures.register_fixture(src_id, records)
    return reg


def _check_source_files(source: IngestSource) -> str | None:
    records = _glob_records(source, DAVID_ROOT)
    return _newest_id(records)


def _process_source(
    reg: IngestRegistry,
    source: IngestSource,
    *,
    offline: bool,
) -> ScrapeBatch | None:
    pointer = reg.newest_pointer(
        source.source_id,
        check_fn=None if offline else _check_source_files,
        offline=offline,
    )

    if offline:
        if not pointer.get("has_new"):
            _log(f"[ingest] {source.source_id}: no changes")
            return None
        batch = reg.record_scrape(
            source.source_id,
            [],
            evaluate_fn=make_evaluate_fn(source.source_id),
            offline=True,
        )
        newest = batch.newest_id or source.last_new_id
        file_hint = ""
        fixture = reg.fixtures.get_fixture(source.source_id)
        if fixture:
            file_hint = f" ({fixture[-1].get('file', newest)})"
        _log(f"[ingest] {source.source_id}: 1 new fixture{file_hint}")
        if batch.evaluate_triggered:
            summary = _format_eval_summary(source.source_id, batch.evaluate_result)
            _log(f"[ingest] → {summary}")
        return batch

    records = _glob_records(source, DAVID_ROOT)
    new_records = _records_since(source, records)

    if not pointer.get("has_new") or not new_records:
        _log(f"[ingest] {source.source_id}: no changes")
        return None

    names = ", ".join(Path(r["file"]).name for r in new_records[:3])
    if len(new_records) > 3:
        names += f" (+{len(new_records) - 3} more)"
    _log(f"[ingest] {source.source_id}: {len(new_records)} new file(s) ({names})")

    batch = reg.record_scrape(
        source.source_id,
        new_records,
        evaluate_fn=make_evaluate_fn(source.source_id),
    )
    if batch.evaluate_triggered:
        summary = _format_eval_summary(source.source_id, batch.evaluate_result)
        _log(f"[ingest] → {summary}")
    return batch


def run_once(*, offline: bool = False) -> list[str]:
    """Single ingest pass. Returns batch_ids created."""
    reg = _ensure_registry(offline)
    active = reg.active_sources(product="movie")
    stale = reg.stale_sources()

    _log(f"[ingest] checking {len(active)} sources ({len(stale)} stale)")

    if not stale:
        return []

    created: list[str] = []
    for source in stale:
        batch = _process_source(reg, source, offline=offline)
        if batch:
            created.append(batch.batch_id)

    if created:
        reg.write_custody_log(CUSTODY_LOG)
        last = created[-1]
        _log(f"[ingest] {last} logged, custody log updated")
    reg.save(INGEST_PATH)

    return created


def _handle_stop(signum: int, frame: Any) -> None:
    global _running
    _running = False
    _log("\n[ingest] stopping...")


def _poll_loop(interval: int, offline: bool) -> None:
    global _running
    _log(f"[ingest] polling every {interval}s (watchdog not installed)")

    while _running:
        run_once(offline=offline)
        for _ in range(interval):
            if not _running:
                break
            time.sleep(1)


def _watchdog_loop(interval: int, offline: bool) -> None:
    global _running, _debounce_timer

    def _debounced_run() -> None:
        global _debounce_timer
        if _debounce_timer:
            _debounce_timer.cancel()
        _debounce_timer = threading.Timer(2.0, lambda: run_once(offline=offline))
        _debounce_timer.daemon = True
        _debounce_timer.start()

    class _IngestHandler(FileSystemEventHandler):
        def on_any_event(self, event: Any) -> None:
            if event.is_directory:
                return
            src = str(event.src_path).replace("\\", "/")
            if any(
                marker in src
                for marker in ("/plates/", "/longform_scripts/", "identity_lock")
            ):
                _debounced_run()

    observer = Observer()
    for watch_dir in WATCH_DIRS:
        if watch_dir.is_dir():
            observer.schedule(_IngestHandler(), str(watch_dir), recursive=True)

    observer.start()
    _log(f"[ingest] watchdog active; backup poll every {interval}s")

    try:
        while _running:
            run_once(offline=offline)
            for _ in range(interval):
                if not _running:
                    break
                time.sleep(1)
    finally:
        observer.stop()
        observer.join(timeout=5)
        if _debounce_timer:
            _debounce_timer.cancel()


def run_loop(interval: int, *, offline: bool = False) -> None:
    signal.signal(signal.SIGINT, _handle_stop)
    if hasattr(signal, "SIGTERM"):
        signal.signal(signal.SIGTERM, _handle_stop)

    if _HAS_WATCHDOG and not offline:
        _watchdog_loop(interval, offline)
    else:
        _poll_loop(interval, offline)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Watch movie ingest sources and auto-evaluate continuity.",
    )
    parser.add_argument(
        "--once",
        action="store_true",
        help="Single pass over stale sources, then exit (default)",
    )
    parser.add_argument(
        "--interval",
        type=int,
        metavar="N",
        help="Loop every N seconds (watchdog or mtime polling)",
    )
    parser.add_argument(
        "--offline",
        action="store_true",
        help="Use FixtureStore data instead of live filesystem",
    )
    args = parser.parse_args()

    if args.interval is not None and args.interval > 0:
        run_loop(args.interval, offline=args.offline)
        return 0

    run_once(offline=args.offline)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())