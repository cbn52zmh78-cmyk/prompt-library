"""ingest_registry.py — Oliver scheduled-ingest + normalization layer.

Oliver routinely scrapes box-score sites and detects the newest games.
That discover-newest → canonical append → trigger metrics pipeline is
what feeds 15-year accurate evaluate/project/compare.

Every Stonebridge variant needs the same plumbing:
  - OLIVER:   box-score sites → player grades
  - MERIDIAN: aerial epoch feeds → sector regression
  - ATREIDES: case feeds → entity resolution
  - MOVIE:    plate files / script revisions → continuity evaluate
  - ELEANOR:  wakes on new scrape landed → narrates Oliver's table

This module is product-agnostic. Products supply:
  1. Source definitions (URL pattern, parser, poll interval)
  2. A scrape function (fetch + normalize → canonical records)
  3. An evaluate callback (rerun grades/metrics on new data)

Usage:
    from ingest_registry import IngestRegistry

    reg = IngestRegistry.load("ingest_sources.json")
    source = reg.register_source("boxscore_espn", ...)
    if reg.newest_pointer("boxscore_espn"):
        records = my_scrape_fn(source)
        reg.record_scrape("boxscore_espn", records, evaluate_fn=my_grades)
"""
from __future__ import annotations

import csv
import json
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable


# ── Ingest source ─────────────────────────────────────────────────────────────

@dataclass
class IngestSource:
    """One tracked data source — Oliver's league list entry."""
    source_id: str               # Unique key (e.g., "boxscore_espn", "plate_actor")
    url_pattern: str             # URL template or glob (e.g., "https://espn.com/mlb/boxscore/*")
    parser_version: str          # Semver of the parser that normalizes this source
    source_type: str             # web | file | api | manual
    product: str                 # Which product owns this source (oliver, meridian, movie, etc.)
    description: str = ""

    status: str = "active"       # active | paused | failed | retired
    poll_interval_s: int = 3600  # How often to check newest-pointer (seconds)

    last_poll_at: str = ""       # ISO timestamp of last newest-pointer check
    last_success_at: str = ""    # ISO timestamp of last successful scrape
    last_failure_at: str = ""    # ISO timestamp of last failed scrape
    last_failure_reason: str = ""
    last_new_id: str = ""        # ID of newest record from this source
    total_records: int = 0       # Cumulative records ingested from this source
    total_scrapes: int = 0       # Cumulative successful scrapes

    created_at: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)


# ── Scrape batch record ───────────────────────────────────────────────────────

@dataclass
class ScrapeBatch:
    """One completed scrape — custody-logged."""
    batch_id: str
    source_id: str
    started_at: str
    completed_at: str
    record_count: int
    new_record_ids: list[str] = field(default_factory=list)
    newest_id: str = ""
    parser_version: str = ""
    status: str = "success"      # success | partial | failed
    custody_note: str = ""       # Free-text custody annotation
    evaluate_triggered: bool = False
    evaluate_result: dict[str, Any] = field(default_factory=dict)


# ── Fixture store (stub mode) ─────────────────────────────────────────────────

class FixtureStore:
    """Oliver's fixture box scores / MERIDIAN fixture epoch packs.

    Returns canned data for offline development so the pipeline
    can run end-to-end without live sources.
    """

    def __init__(self) -> None:
        self.fixtures: dict[str, list[dict[str, Any]]] = {}

    def register_fixture(
        self,
        source_id: str,
        records: list[dict[str, Any]],
    ) -> None:
        """Add fixture data for a source."""
        self.fixtures[source_id] = records

    def get_fixture(self, source_id: str) -> list[dict[str, Any]]:
        """Return fixture records or empty list."""
        return self.fixtures.get(source_id, [])

    def has_fixture(self, source_id: str) -> bool:
        return source_id in self.fixtures

    def save(self, path: Path | str) -> None:
        Path(path).write_text(
            json.dumps(self.fixtures, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )

    @classmethod
    def load(cls, path: Path | str) -> "FixtureStore":
        store = cls()
        p = Path(path)
        if p.is_file():
            store.fixtures = json.loads(p.read_text(encoding="utf-8"))
        return store


# ── Ingest registry ───────────────────────────────────────────────────────────

class IngestRegistry:
    """Oliver's league list — tracks all data sources and their freshness."""

    def __init__(self) -> None:
        self.sources: dict[str, IngestSource] = {}
        self.batches: list[ScrapeBatch] = []
        self.fixtures: FixtureStore = FixtureStore()
        self._batch_counter: int = 0

    # ── Persistence ───────────────────────────────────────────────────────

    def save(self, path: Path | str) -> None:
        path = Path(path)
        data = {
            "registry_version": "1.0",
            "saved_at": _now(),
            "source_count": len(self.sources),
            "batch_count": len(self.batches),
            "_batch_counter": self._batch_counter,
            "sources": {sid: asdict(s) for sid, s in self.sources.items()},
            "batches": [asdict(b) for b in self.batches[-200:]],  # Keep last 200
        }
        path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")

    @classmethod
    def load(cls, path: Path | str) -> "IngestRegistry":
        path = Path(path)
        reg = cls()
        if not path.is_file():
            return reg
        data = json.loads(path.read_text(encoding="utf-8"))
        reg._batch_counter = data.get("_batch_counter", 0)
        for sid, sdata in data.get("sources", {}).items():
            reg.sources[sid] = IngestSource(**sdata)
        for bdata in data.get("batches", []):
            reg.batches.append(ScrapeBatch(**bdata))
        return reg

    # ── Source management ─────────────────────────────────────────────────

    def register_source(
        self,
        source_id: str,
        url_pattern: str,
        parser_version: str,
        source_type: str = "web",
        product: str = "",
        description: str = "",
        poll_interval_s: int = 3600,
        metadata: dict[str, Any] | None = None,
    ) -> IngestSource:
        """Add a data source to the registry. Idempotent on source_id."""
        if source_id in self.sources:
            return self.sources[source_id]
        source = IngestSource(
            source_id=source_id,
            url_pattern=url_pattern,
            parser_version=parser_version,
            source_type=source_type,
            product=product,
            description=description,
            poll_interval_s=poll_interval_s,
            created_at=_now(),
            metadata=metadata or {},
        )
        self.sources[source_id] = source
        return source

    def get_source(self, source_id: str) -> IngestSource | None:
        return self.sources.get(source_id)

    def active_sources(self, product: str = "") -> list[IngestSource]:
        return [
            s for s in self.sources.values()
            if s.status == "active"
            and (not product or s.product == product)
        ]

    def stale_sources(self, max_age_s: int = 0) -> list[IngestSource]:
        """Sources that haven't been polled within their interval."""
        now = datetime.now(timezone.utc)
        stale = []
        for s in self.sources.values():
            if s.status != "active":
                continue
            interval = max_age_s or s.poll_interval_s
            if not s.last_poll_at:
                stale.append(s)
                continue
            last = datetime.fromisoformat(s.last_poll_at)
            if (now - last).total_seconds() > interval:
                stale.append(s)
        return stale

    # ── Newest-pointer (lightweight poll) ─────────────────────────────────

    def newest_pointer(
        self,
        source_id: str,
        *,
        check_fn: Callable[[IngestSource], str | None] | None = None,
        offline: bool = False,
    ) -> dict[str, Any]:
        """Lightweight check: has this source produced anything new?

        Oliver checks if there's a new box score before re-scraping.
        MERIDIAN checks if there's a new aerial epoch before reprocessing.

        Args:
            source_id: Which source to poll
            check_fn: Optional callable(source) → newest_id or None.
                       If None, returns fixture data in offline mode.
            offline: Use fixture data instead of live check.

        Returns:
            {"has_new": bool, "newest_id": str, "previous_id": str}
        """
        source = self.sources.get(source_id)
        if not source:
            return {"has_new": False, "newest_id": "", "previous_id": "", "error": "unknown_source"}

        source.last_poll_at = _now()
        previous = source.last_new_id

        if offline:
            # Stub: fixture always has "new" data
            if self.fixtures.has_fixture(source_id):
                fixture_data = self.fixtures.get_fixture(source_id)
                newest = fixture_data[-1].get("id", "fixture_latest") if fixture_data else ""
                return {"has_new": newest != previous, "newest_id": newest, "previous_id": previous}
            return {"has_new": False, "newest_id": previous, "previous_id": previous}

        if check_fn:
            try:
                newest = check_fn(source)
                if newest is None:
                    return {"has_new": False, "newest_id": previous, "previous_id": previous}
                return {"has_new": newest != previous, "newest_id": newest, "previous_id": previous}
            except Exception as exc:
                source.last_failure_at = _now()
                source.last_failure_reason = str(exc)
                return {"has_new": False, "newest_id": previous, "previous_id": previous, "error": str(exc)}

        return {"has_new": False, "newest_id": previous, "previous_id": previous, "error": "no_check_fn"}

    # ── Record scrape (scrape triggers evaluate) ──────────────────────────

    def record_scrape(
        self,
        source_id: str,
        records: list[dict[str, Any]],
        *,
        evaluate_fn: Callable[[list[dict[str, Any]]], dict[str, Any]] | None = None,
        custody_note: str = "",
        offline: bool = False,
    ) -> ScrapeBatch:
        """Log a completed scrape and optionally trigger evaluate.

        Oliver pattern: new box score → rerun player grades.
        MERIDIAN: new aerial epoch → rerun sector regression.
        Movie: new plate → rerun continuity evaluate.
        ELEANOR: new scrape landed → narrate Oliver's table.

        Args:
            source_id: Which source produced this data
            records: Normalized records from the scrape
            evaluate_fn: Optional callback(records) → eval_result.
                          Called automatically on new data (scrape triggers evaluate).
            custody_note: Free-text note for the custody log
            offline: If True, uses fixture data instead of live records
        """
        source = self.sources.get(source_id)
        if not source:
            raise ValueError(f"Unknown source: {source_id}")

        if offline and self.fixtures.has_fixture(source_id):
            records = self.fixtures.get_fixture(source_id)

        self._batch_counter += 1
        batch_id = f"batch_{self._batch_counter:05d}"
        now = _now()

        # Extract newest ID from records
        new_ids = [str(r.get("id", "")) for r in records if r.get("id")]
        newest = new_ids[-1] if new_ids else source.last_new_id

        batch = ScrapeBatch(
            batch_id=batch_id,
            source_id=source_id,
            started_at=now,
            completed_at=now,
            record_count=len(records),
            new_record_ids=new_ids,
            newest_id=newest,
            parser_version=source.parser_version,
            custody_note=custody_note or f"Batch {batch_id} from {source_id}",
        )

        # Scrape triggers evaluate — the core Oliver pattern
        if evaluate_fn and records:
            try:
                eval_result = evaluate_fn(records)
                batch.evaluate_triggered = True
                batch.evaluate_result = eval_result
            except Exception as exc:
                batch.evaluate_result = {"error": str(exc)}

        # Update source state
        source.last_success_at = now
        source.last_new_id = newest
        source.total_records += len(records)
        source.total_scrapes += 1

        self.batches.append(batch)
        return batch

    # ── Custody log (PUTSA/DTSA per batch) ────────────────────────────────

    def write_custody_log(self, path: Path | str) -> None:
        """Append custody log CSV — every scrape batch, timestamped.

        Dad already thinks this way for maps. Same discipline for all ingest.
        Existing rows are preserved; only batches not yet logged are appended.
        """
        path = Path(path)
        if not self.batches:
            return
        fields = [
            "batch_id", "source_id", "started_at", "completed_at",
            "record_count", "newest_id", "parser_version", "status",
            "custody_note", "evaluate_triggered",
        ]
        existing_ids: set[str] = set()
        write_header = not path.is_file()
        if path.is_file():
            with open(path, newline="", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                existing_ids = {row["batch_id"] for row in reader if row.get("batch_id")}

        new_batches = [b for b in self.batches if b.batch_id not in existing_ids]
        if not new_batches:
            return

        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "a", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
            if write_header:
                writer.writeheader()
            for batch in new_batches:
                row = asdict(batch)
                row["evaluate_triggered"] = str(row["evaluate_triggered"])
                writer.writerow(row)

    def custody_summary(self) -> dict[str, Any]:
        """Quick custody stats for the registry."""
        by_source: dict[str, int] = {}
        for batch in self.batches:
            by_source[batch.source_id] = by_source.get(batch.source_id, 0) + 1
        return {
            "total_batches": len(self.batches),
            "by_source": by_source,
            "last_batch": asdict(self.batches[-1]) if self.batches else None,
        }


# ── Product-specific source presets ───────────────────────────────────────────

def movie_sources() -> list[dict[str, Any]]:
    """Default ingest sources for the movie pipeline."""
    return [
        {
            "source_id": "plate_actor",
            "url_pattern": "productions/*/plates/actor_*.png",
            "parser_version": "1.0.0",
            "source_type": "file",
            "product": "movie",
            "description": "Actor/talent plate images",
            "poll_interval_s": 300,
        },
        {
            "source_id": "plate_set",
            "url_pattern": "productions/*/plates/set_*.png",
            "parser_version": "1.0.0",
            "source_type": "file",
            "product": "movie",
            "description": "Set/environment plate images",
            "poll_interval_s": 300,
        },
        {
            "source_id": "plate_zone",
            "url_pattern": "productions/*/plates/zone_*.png",
            "parser_version": "1.0.0",
            "source_type": "file",
            "product": "movie",
            "description": "Zone plate background stills",
            "poll_interval_s": 300,
        },
        {
            "source_id": "script_revision",
            "url_pattern": "scripts/longform_scripts/*.json",
            "parser_version": "1.0.0",
            "source_type": "file",
            "product": "movie",
            "description": "Script JSON revisions",
            "poll_interval_s": 600,
        },
        {
            "source_id": "identity_lock",
            "url_pattern": "productions/*/david_identity_lock.json",
            "parser_version": "1.0.0",
            "source_type": "file",
            "product": "movie",
            "description": "Identity lock revisions",
            "poll_interval_s": 3600,
        },
    ]


def oliver_sources() -> list[dict[str, Any]]:
    """Default ingest sources for Oliver MLS (reference architecture).

    Actual URLs are trade secrets — these are structural placeholders.
    Dad's scraper fills them; ELEANOR narrates the output.
    """
    return [
        {
            "source_id": "boxscore_feed",
            "url_pattern": "<trade_secret_url>",
            "parser_version": "1.0.0",
            "source_type": "web",
            "product": "oliver",
            "description": "Box score feed — new games trigger player re-grade",
            "poll_interval_s": 900,
        },
        {
            "source_id": "roster_feed",
            "url_pattern": "<trade_secret_url>",
            "parser_version": "1.0.0",
            "source_type": "web",
            "product": "oliver",
            "description": "Roster/transaction feed — new signings, DFA, callups",
            "poll_interval_s": 3600,
        },
    ]


def meridian_sources() -> list[dict[str, Any]]:
    """Default ingest sources for MERIDIAN — all four verticals + PitWall feeds."""
    vertical_epochs = [
        ("aerial_epoch_rally", "epochs/rally/*/epoch_*/metadata.json", "rally"),
        ("aerial_epoch_real_estate", "epochs/real_estate/*/epoch_*/metadata.json", "real_estate"),
        ("aerial_epoch_infrastructure", "epochs/infrastructure/*/epoch_*/metadata.json", "infrastructure"),
        ("aerial_epoch_airport", "epochs/airport/*/epoch_*/metadata.json", "airport"),
    ]
    sources: list[dict[str, Any]] = [
        {
            "source_id": source_id,
            "url_pattern": pattern,
            "parser_version": "1.0.0",
            "source_type": "file",
            "product": "meridian",
            "description": f"Aerial epoch feed — {vertical} — triggers box score regression",
            "poll_interval_s": 86400,
            "metadata": {"vertical": vertical},
        }
        for source_id, pattern, vertical in vertical_epochs
    ]
    sources.extend([
        {
            "source_id": "aerial_epoch",
            "url_pattern": "epochs/*/epoch_*/metadata.json",
            "parser_version": "1.0.0",
            "source_type": "file",
            "product": "meridian",
            "description": "Legacy catch-all aerial epoch source (all verticals)",
            "poll_interval_s": 86400,
        },
        {
            "source_id": "telemetry_feed",
            "url_pattern": "<telemetry_endpoint>",
            "parser_version": "1.0.0",
            "source_type": "api",
            "product": "meridian",
            "description": "Live telemetry — sector times, GPS traces (PitWall)",
            "poll_interval_s": 60,
        },
        {
            "source_id": "timing_feed",
            "url_pattern": "<timing_endpoint>",
            "parser_version": "1.0.0",
            "source_type": "api",
            "product": "meridian",
            "description": "Official timing/classification data (PitWall)",
            "poll_interval_s": 300,
        },
    ])
    return sources


def meridian_fixtures() -> dict[str, list[dict[str, Any]]]:
    """Fixture epoch records for offline MERIDIAN pipeline development."""
    return {
        "aerial_epoch_rally": [
            {
                "id": "@ST-SS4-S3:2026-03-15",
                "vertical": "rally",
                "feature_id": "@ST-SS4-S3",
                "epoch_date": "2026-03-15",
                "compiler_confidence": 0.85,
            },
        ],
        "aerial_epoch_airport": [
            {
                "id": "@APT-2847:2026-06-01",
                "vertical": "airport",
                "feature_id": "@APT-2847",
                "epoch_date": "2026-06-01",
                "compiler_confidence": 0.90,
            },
        ],
    }


def atreides_sources() -> list[dict[str, Any]]:
    """Default ingest sources for ATREIDES LE-analytics."""
    return [
        {
            "source_id": "case_feed",
            "url_pattern": "<case_management_api>",
            "parser_version": "1.0.0",
            "source_type": "api",
            "product": "atreides",
            "description": "Case management feed — new cases trigger entity resolution",
            "poll_interval_s": 1800,
        },
    ]


# ── Movie-specific fixture data ──────────────────────────────────────────────

def movie_fixtures() -> dict[str, list[dict[str, Any]]]:
    """Fixture plate records for offline movie pipeline development."""
    return {
        "plate_actor": [
            {
                "id": "actor_david_v3",
                "file": "david_talent_v3.png",
                "type": "actor",
                "character": "David",
                "url": "https://cdn.example.com/david_v3.png",
            },
        ],
        "plate_set": [
            {
                "id": "set_archive_v1",
                "file": "archive_set_reference_v5.png",
                "type": "set",
                "name": "Archive Chamber",
            },
        ],
        "script_revision": [
            {
                "id": "script_akkadian_v1",
                "file": "david_akkadian_corpus_v1_script.json",
                "slug": "david_akkadian_corpus_v1",
                "shot_count": 12,
            },
        ],
    }


# ── Product catalog wiring ────────────────────────────────────────────────────

def sources_for_product(product: str) -> list[dict[str, Any]]:
    """Return ingest source preset dicts for a product slug."""
    key = product.strip().lower()
    presets = {
        "movie": movie_sources,
        "david": movie_sources,
        "studio": movie_sources,
        "oliver": oliver_sources,
        "meridian": meridian_sources,
        "atreides": atreides_sources,
    }
    fn = presets.get(key)
    if not fn:
        raise ValueError(f"No ingest presets for product: {product}")
    return fn()


def register_sources_for_product(
    registry: IngestRegistry,
    product: str,
) -> list[IngestSource]:
    """Register product-specific ingest sources into a registry."""
    registered: list[IngestSource] = []
    for spec in sources_for_product(product):
        registered.append(registry.register_source(**spec))
    return registered


def catalog_path_for_product(product: str) -> Path:
    """Canonical master_catalog.json path for a product (delegates to production_catalog)."""
    from production_catalog import catalog_path_for_product as _catalog_path
    return _catalog_path(product)


# ── Utilities ─────────────────────────────────────────────────────────────────

def _now() -> str:
    return datetime.now(timezone.utc).isoformat()
