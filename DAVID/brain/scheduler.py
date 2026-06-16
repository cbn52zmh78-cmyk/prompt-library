"""DAVID Brain scheduler — rotate languages and queue assignments on an interval."""

from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

DAVID_ROOT = Path(__file__).resolve().parents[1]
REGISTRY_FILE = DAVID_ROOT / "data" / "language_registry.json"
QUEUE_FILE = DAVID_ROOT / "data" / "research_queue.json"
SCHEDULE_FILE = DAVID_ROOT / "data" / "brain_schedule.json"
SCRAPE_LOG = DAVID_ROOT / "data" / "brain_cache" / "scrape_log.json"

PRIORITY_WEIGHT = {"high": 100, "medium": 50, "low": 20}
TIER_WEIGHT = {"high": 30, "active": 25, "medium": 15, "research": 10}


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _parse_ts(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


def load_schedule() -> dict[str, Any]:
    if SCHEDULE_FILE.exists():
        return json.loads(SCHEDULE_FILE.read_text(encoding="utf-8"))
    return {}


def save_schedule(state: dict[str, Any]) -> None:
    SCHEDULE_FILE.write_text(json.dumps(state, indent=2), encoding="utf-8")


def load_registry() -> list[dict[str, Any]]:
    return json.loads(REGISTRY_FILE.read_text(encoding="utf-8"))["languages"]


def load_queue() -> list[dict[str, Any]]:
    if not QUEUE_FILE.exists():
        return []
    return json.loads(QUEUE_FILE.read_text(encoding="utf-8")).get("queue", [])


def save_queue(queue: list[dict[str, Any]]) -> None:
    data = {"queue": queue}
    if QUEUE_FILE.exists():
        raw = json.loads(QUEUE_FILE.read_text(encoding="utf-8"))
        raw["queue"] = queue
        data = raw
    QUEUE_FILE.write_text(json.dumps(data, indent=2), encoding="utf-8")


def last_scrape_info(slug: str) -> dict[str, Any] | None:
    """Most recent scrape for a language from per-language file or log."""
    for entry in reversed(_load_scrape_log()):
        if entry.get("slug") == slug:
            return entry

    for lang in load_registry():
        if lang["slug"] != slug:
            continue
        path = (
            DAVID_ROOT
            / "languages"
            / lang["status"]
            / slug
            / "research"
            / "brain"
            / "latest_scrape.json"
        )
        if path.exists():
            data = json.loads(path.read_text(encoding="utf-8"))
            return {
                "slug": slug,
                "scraped_at": data.get("scraped_at"),
                "errors": data.get("errors", []),
                "sources": data.get("sources_used", []),
                "ipa_count": data.get("pronunciation_summary", {}).get("total_ipa_entries", 0),
            }
    return None


def _load_scrape_log() -> list[dict[str, Any]]:
    if not SCRAPE_LOG.exists():
        return []
    return json.loads(SCRAPE_LOG.read_text(encoding="utf-8"))


def pending_queue_by_language() -> dict[str, list[dict[str, Any]]]:
    grouped: dict[str, list[dict[str, Any]]] = {}
    for item in load_queue():
        if item.get("status") not in ("pending", "in_progress"):
            continue
        grouped.setdefault(item["language"], []).append(item)
    return grouped


def score_language(entry: dict[str, Any], *, stale_hours: float) -> tuple[int, list[str]]:
    slug = entry["slug"]
    reasons: list[str] = []
    score = 0

    queue_items = pending_queue_by_language().get(slug, [])
    for item in queue_items:
        w = PRIORITY_WEIGHT.get(item.get("priority", "low"), 10)
        score += w
        reasons.append(f"queue:{item.get('priority')}")

    last = last_scrape_info(slug)
    if not last:
        score += 200
        reasons.append("never_scraped")
    else:
        scraped = _parse_ts(last.get("scraped_at"))
        if scraped:
            age = _utcnow() - scraped
            if age > timedelta(hours=stale_hours):
                score += 40
                reasons.append(f"stale:{int(age.total_seconds() // 3600)}h")
            else:
                score -= int(age.total_seconds() // 60)
        if last.get("errors"):
            score += 60
            reasons.append("retry_errors")

    tier = entry.get("revival_tier", "medium")
    score += TIER_WEIGHT.get(tier, 10)
    reasons.append(f"tier:{tier}")

    return score, reasons


def next_batch(
    batch_size: int | None = None,
    stale_hours: float | None = None,
) -> list[dict[str, Any]]:
    """
    Return the next languages to scrape, highest priority first.
    Each item: {slug, name, score, reasons, assignments}
    """
    state = load_schedule()
    size = batch_size or int(state.get("batch_size", 1))
    stale = stale_hours if stale_hours is not None else float(state.get("stale_hours", 24))

    ranked: list[dict[str, Any]] = []
    queue_map = pending_queue_by_language()

    for entry in load_registry():
        score, reasons = score_language(entry, stale_hours=stale)
        ranked.append(
            {
                "slug": entry["slug"],
                "name": entry["name"],
                "status": entry["status"],
                "score": score,
                "reasons": reasons,
                "assignments": queue_map.get(entry["slug"], []),
            }
        )

    ranked.sort(key=lambda x: x["score"], reverse=True)
    return ranked[:size]


def mark_assignments_in_progress(slugs: list[str]) -> None:
    queue = load_queue()
    changed = False
    for item in queue:
        if item.get("language") in slugs and item.get("status") == "pending":
            item["status"] = "in_progress"
            item["brain_started_at"] = _utcnow().isoformat()
            changed = True
    if changed:
        save_queue(queue)


def record_batch(slugs: list[str], *, errors: dict[str, list[str]] | None = None) -> dict[str, Any]:
    state = load_schedule()
    now = _utcnow().isoformat()
    state["last_batch_at"] = now
    state["last_batch_languages"] = slugs
    state["total_batches_run"] = int(state.get("total_batches_run", 0)) + 1
    state["rotation_index"] = (int(state.get("rotation_index", 0)) + len(slugs)) % max(
        len(load_registry()), 1
    )

    registry_slugs = {e["slug"] for e in load_registry()}
    scraped_slugs = {
        e["slug"]
        for e in load_registry()
        if last_scrape_info(e["slug"]) is not None
    }
    if registry_slugs.issubset(scraped_slugs):
        state["current_cycle"] = int(state.get("current_cycle", 1)) + 1
        state["last_cycle_completed_at"] = now
        state["rotation_index"] = 0

    save_schedule(state)

    queue = load_queue()
    changed = False
    for item in queue:
        if item.get("language") not in slugs:
            continue
        item["last_brain_scrape"] = now
        if errors and item["language"] in errors and errors[item["language"]]:
            item["brain_last_errors"] = errors[item["language"]]
        changed = True
    if changed:
        save_queue(queue)

    return state


def schedule_status() -> dict[str, Any]:
    state = load_schedule()
    batch = next_batch()
    return {
        "schedule": state,
        "next_batch": batch,
        "languages_total": len(load_registry()),
        "languages_scraped": sum(
            1 for e in load_registry() if last_scrape_info(e["slug"])
        ),
        "queue_pending": sum(
            1 for q in load_queue() if q.get("status") in ("pending", "in_progress")
        ),
    }