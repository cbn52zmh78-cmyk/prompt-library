"""box_score_db.py — MERIDIAN Layer 2 box score store (POC: JSON files).

One table per vertical, versioned schema from meridian_config.json.
Deterministic ingest only — no ML, no LLM. brief_narrator.py reads from here.

Usage:
    from box_score_db import BoxScoreDB

    db = BoxScoreDB.load()
    rows = db.query("airport", feature_id="@APT-2847")
    db.upsert_rows("airport", rows)
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from _paths import WORKSPACE
from epoch_manager import load_meridian_config

MERIDIAN_ROOT = WORKSPACE / "Stonebridge" / "Products" / "MERIDIAN"
DEFAULT_DATA_DIR = MERIDIAN_ROOT / "data" / "box_scores"


@dataclass
class BoxScoreRow:
    """One measurement row — feature_id × epoch_date (+ segment_id for infra)."""
    feature_id: str
    epoch_date: str
    vertical: str = ""
    segment_id: str = ""
    measurements: dict[str, Any] = field(default_factory=dict)
    residual_vs_expected: float | None = None
    compiler_confidence: float | None = None
    epoch_count: int = 1

    def to_dict(self) -> dict[str, Any]:
        base = {
            "feature_id": self.feature_id,
            "epoch_date": self.epoch_date,
            "residual_vs_expected": self.residual_vs_expected,
            "compiler_confidence": self.compiler_confidence,
            "epoch_count": self.epoch_count,
        }
        if self.segment_id:
            base["segment_id"] = self.segment_id
        base.update(self.measurements)
        return base

    @classmethod
    def from_dict(cls, vertical: str, data: dict[str, Any]) -> "BoxScoreRow":
        reserved = {
            "feature_id", "epoch_date", "segment_id",
            "residual_vs_expected", "compiler_confidence", "epoch_count", "vertical",
        }
        measurements = {k: v for k, v in data.items() if k not in reserved}
        return cls(
            feature_id=str(data.get("feature_id", "")),
            epoch_date=str(data.get("epoch_date", "")),
            vertical=vertical,
            segment_id=str(data.get("segment_id", "")),
            measurements=measurements,
            residual_vs_expected=_float_or_none(data.get("residual_vs_expected")),
            compiler_confidence=_float_or_none(data.get("compiler_confidence")),
            epoch_count=int(data.get("epoch_count", 1)),
        )


def _float_or_none(val: Any) -> float | None:
    if val is None or val == "":
        return None
    try:
        return float(val)
    except (TypeError, ValueError):
        return None


def _table_name(vertical: str, config: dict[str, Any]) -> str:
    vcfg = config.get("verticals", {}).get(vertical, {})
    return vcfg.get("box_score_table", f"{vertical}_box_score")


class BoxScoreDB:
    """JSON-backed box score database — PostGIS/Databricks upgrade path later."""

    def __init__(self, data_dir: Path | str, config: dict[str, Any] | None = None) -> None:
        self.data_dir = Path(data_dir)
        self.config = config or load_meridian_config()
        self._cache: dict[str, list[BoxScoreRow]] = {}

    @classmethod
    def load(
        cls,
        data_dir: Path | str | None = None,
        config: dict[str, Any] | None = None,
    ) -> "BoxScoreDB":
        return cls(data_dir or DEFAULT_DATA_DIR, config=config)

    def _path_for(self, vertical: str) -> Path:
        table = _table_name(vertical, self.config)
        return self.data_dir / f"{table}.json"

    def _load_table(self, vertical: str) -> list[BoxScoreRow]:
        if vertical in self._cache:
            return self._cache[vertical]
        path = self._path_for(vertical)
        rows: list[BoxScoreRow] = []
        if path.is_file():
            data = json.loads(path.read_text(encoding="utf-8"))
            for r in data.get("rows", []):
                rows.append(BoxScoreRow.from_dict(vertical, r))
        self._cache[vertical] = rows
        return rows

    def save_table(self, vertical: str) -> None:
        rows = self._cache.get(vertical, self._load_table(vertical))
        path = self._path_for(vertical)
        path.parent.mkdir(parents=True, exist_ok=True)
        schema = self.config.get("box_score_schemas", {}).get(
            _table_name(vertical, self.config), {}
        )
        payload = {
            "table": _table_name(vertical, self.config),
            "vertical": vertical,
            "schema_version": schema.get("version", "1.0"),
            "saved_at": _now(),
            "row_count": len(rows),
            "rows": [r.to_dict() for r in rows],
        }
        path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")

    def query(
        self,
        vertical: str,
        *,
        feature_id: str = "",
        epoch_date: str = "",
        segment_id: str = "",
        min_residual: float | None = None,
        limit: int = 0,
    ) -> list[BoxScoreRow]:
        rows = self._load_table(vertical)
        out: list[BoxScoreRow] = []
        for r in rows:
            if feature_id and r.feature_id != feature_id:
                continue
            if epoch_date and r.epoch_date != epoch_date:
                continue
            if segment_id and r.segment_id != segment_id:
                continue
            if min_residual is not None and (r.residual_vs_expected or 0) < min_residual:
                continue
            out.append(r)
        out.sort(key=lambda r: (r.feature_id, r.epoch_date))
        if limit > 0:
            out = out[:limit]
        return out

    def latest_epoch(self, vertical: str, feature_id: str) -> BoxScoreRow | None:
        rows = self.query(vertical, feature_id=feature_id)
        return rows[-1] if rows else None

    def upsert_rows(self, vertical: str, rows: list[BoxScoreRow | dict[str, Any]]) -> int:
        table = self._load_table(vertical)
        index: dict[tuple[str, ...], int] = {}
        for i, r in enumerate(table):
            key = (r.feature_id, r.epoch_date, r.segment_id)
            index[key] = i

        count = 0
        for item in rows:
            row = item if isinstance(item, BoxScoreRow) else BoxScoreRow.from_dict(vertical, item)
            row.vertical = vertical
            key = (row.feature_id, row.epoch_date, row.segment_id)
            if key in index:
                table[index[key]] = row
            else:
                table.append(row)
                index[key] = len(table) - 1
            count += 1

        self._cache[vertical] = table
        self.save_table(vertical)
        return count

    def load_fixture(self, vertical: str, fixture_name: str | None = None) -> int:
        """Load rows from *_fixture.json into the live table."""
        table = _table_name(vertical, self.config)
        fname = fixture_name or f"{table}_fixture.json"
        path = self.data_dir / fname
        if not path.is_file():
            raise FileNotFoundError(f"Fixture not found: {path}")
        data = json.loads(path.read_text(encoding="utf-8"))
        return self.upsert_rows(vertical, data.get("rows", []))

    def alerts(
        self,
        vertical: str,
        *,
        residual_threshold: float = 1.0,
        confidence_floor: float = 0.60,
    ) -> list[BoxScoreRow]:
        """Rows exceeding residual threshold on latest epoch per feature."""
        rows = self._load_table(vertical)
        latest: dict[str, BoxScoreRow] = {}
        for r in rows:
            prev = latest.get(r.feature_id)
            if not prev or r.epoch_date > prev.epoch_date:
                latest[r.feature_id] = r

        alerts: list[BoxScoreRow] = []
        for r in latest.values():
            residual = r.residual_vs_expected or 0
            conf = r.compiler_confidence or 0
            if residual >= residual_threshold or conf < confidence_floor:
                alerts.append(r)
        return sorted(alerts, key=lambda r: -(r.residual_vs_expected or 0))


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


if __name__ == "__main__":
    db = BoxScoreDB.load()
    for v in ("rally", "airport"):
        path = db._path_for(v)
        print(f"{v}: {path.name} exists={path.is_file()}")