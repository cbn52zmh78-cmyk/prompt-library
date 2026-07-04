"""epoch_manager.py — MERIDIAN shared epoch ingest, validation, CRS alignment.

Vertical-agnostic: rally, real estate, infrastructure, and airport all use the
same epoch file kit structure (Scaffold v1 §3A / Unified Architecture §6.1).

Oliver pattern: each aerial survey is an epoch; aligned epochs compound into the
longitudinal moat. Missing epochs lower confidence — never interpolated.

Usage:
    from epoch_manager import EpochArchive, validate_epoch_kit, ingest_epoch

    archive = EpochArchive.load("epochs/")
    report = validate_epoch_kit(archive.epoch_path("rally", "@ST-SS4", "2026-03-15"))
    result = ingest_epoch(archive, vertical="rally", feature_id="@ST-SS4", epoch_dir=...)
"""
from __future__ import annotations

import json
import re
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from _paths import WORKSPACE

MERIDIAN_ROOT = WORKSPACE / "Stonebridge" / "Products" / "MERIDIAN"
DEFAULT_CONFIG_PATH = MERIDIAN_ROOT / "meridian_config.json"
DEFAULT_ARCHIVE_ROOT = MERIDIAN_ROOT / "epochs"

EPOCH_DATE_PATTERN = re.compile(r"^\d{4}-\d{2}-\d{2}$")

# Tier 1 (must have) + standard kit files per Scaffold v1
REQUIRED_KIT_FILES = ("metadata.json", "ortho_cog.tif", "dsm.tif", "gcp.csv")
OPTIONAL_KIT_FILES = (
    "dtm.tif",
    "surface_delta.tif",
    "vectors.gpkg",
    "cloud_ground.laz",
    "qa_report.json",
)

VERTICAL_SLUGS = ("rally", "real_estate", "infrastructure", "airport")

METADATA_REQUIRED_KEYS = (
    "epoch_date",
    "vertical",
    "feature_id",
    "crs",
    "horizontal_datum",
    "vertical_datum",
    "gsd_m",
    "survey_method",
)

GCP_REQUIRED_COLUMNS = ("id", "x", "y", "z")


# ── Config loader ─────────────────────────────────────────────────────────────

def load_meridian_config(path: Path | str | None = None) -> dict[str, Any]:
    """Load meridian_config.json; return sensible defaults if missing."""
    p = Path(path) if path else DEFAULT_CONFIG_PATH
    if p.is_file():
        return json.loads(p.read_text(encoding="utf-8"))
    return {
        "config_version": "1.0",
        "epoch_file_kit": {
            "required": list(REQUIRED_KIT_FILES),
            "optional": list(OPTIONAL_KIT_FILES),
        },
        "verticals": {v: {"id_prefix": _default_prefix(v)} for v in VERTICAL_SLUGS},
        "compiler_confidence": {
            "automated_default": 0.45,
            "dad_validated_default": 0.85,
            "publish_threshold": 0.60,
        },
    }


def _default_prefix(vertical: str) -> str:
    return {
        "rally": "ST",
        "real_estate": "RE",
        "infrastructure": "INF",
        "airport": "APT",
    }.get(vertical, "ST")


# ── Validation report ─────────────────────────────────────────────────────────

@dataclass
class ValidationIssue:
    severity: str   # BLOCK | WARN | INFO
    category: str
    detail: str
    action_needed: str = ""


@dataclass
class EpochValidationReport:
    """Result of validate_epoch_kit()."""
    pass_: bool = True
    epoch_path: str = ""
    vertical: str = ""
    feature_id: str = ""
    epoch_date: str = ""
    issues: list[ValidationIssue] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)
    crs_aligned_with_prior: bool | None = None
    prior_epoch_date: str = ""
    compiler_confidence: float | None = None

    def add(
        self,
        severity: str,
        category: str,
        detail: str,
        action_needed: str = "",
    ) -> None:
        self.issues.append(ValidationIssue(severity, category, detail, action_needed))
        if severity == "BLOCK":
            self.pass_ = False

    def to_dict(self) -> dict[str, Any]:
        blocks = [i for i in self.issues if i.severity == "BLOCK"]
        return {
            "pass": self.pass_,
            "epoch_path": self.epoch_path,
            "vertical": self.vertical,
            "feature_id": self.feature_id,
            "epoch_date": self.epoch_date,
            "issue_count": len(self.issues),
            "block_count": len(blocks),
            "crs_aligned_with_prior": self.crs_aligned_with_prior,
            "prior_epoch_date": self.prior_epoch_date,
            "compiler_confidence": self.compiler_confidence,
            "issues": [asdict(i) for i in self.issues],
            "metadata": self.metadata,
        }


# ── Epoch kit validation ──────────────────────────────────────────────────────

def _read_metadata(epoch_dir: Path) -> dict[str, Any]:
    meta_path = epoch_dir / "metadata.json"
    if not meta_path.is_file():
        return {}
    try:
        return json.loads(meta_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {"_parse_error": True}


def _validate_gcp(epoch_dir: Path, report: EpochValidationReport) -> None:
    gcp_path = epoch_dir / "gcp.csv"
    if not gcp_path.is_file():
        return
    try:
        lines = gcp_path.read_text(encoding="utf-8").strip().splitlines()
    except OSError as exc:
        report.add("BLOCK", "gcp_read", f"Cannot read gcp.csv: {exc}")
        return
    if not lines:
        report.add("BLOCK", "gcp_empty", "gcp.csv is empty")
        return
    header = [c.strip().lower() for c in lines[0].split(",")]
    missing = [c for c in GCP_REQUIRED_COLUMNS if c not in header]
    if missing:
        report.add(
            "BLOCK",
            "gcp_schema",
            f"gcp.csv missing columns: {missing}",
            "Add id,x,y,z columns per Scaffold v1",
        )


def _validate_qa_report(epoch_dir: Path, report: EpochValidationReport) -> None:
    qa_path = epoch_dir / "qa_report.json"
    if not qa_path.is_file():
        report.add(
            "WARN",
            "qa_missing",
            "No qa_report.json — automated-only epoch, lower compiler_confidence",
            "Dad QA review produces qa_report.json with compiler_confidence",
        )
        return
    try:
        qa = json.loads(qa_path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as exc:
        report.add("WARN", "qa_parse", f"qa_report.json unreadable: {exc}")
        return
    conf = qa.get("compiler_confidence")
    if conf is not None:
        try:
            report.compiler_confidence = float(conf)
        except (TypeError, ValueError):
            report.add("WARN", "qa_confidence", "compiler_confidence not numeric")
    flagged = qa.get("flagged_sectors") or qa.get("flagged_features") or []
    if flagged:
        report.add(
            "INFO",
            "qa_flagged",
            f"{len(flagged)} feature(s)/sector(s) flagged in QA report",
        )


def validate_epoch_kit(
    epoch_dir: Path | str,
    *,
    vertical: str = "",
    feature_id: str = "",
    prior_metadata: dict[str, Any] | None = None,
    config: dict[str, Any] | None = None,
) -> EpochValidationReport:
    """Validate a single epoch directory against the standard file kit.

    Args:
        epoch_dir: Path to /feature_{id}/epoch_{YYYY-MM-DD}/ or equivalent
        vertical: Expected vertical slug (rally, real_estate, infrastructure, airport)
        feature_id: Expected permanent ID (@ST-SS4, @RE-4472, …)
        prior_metadata: metadata.json from previous epoch for CRS alignment check
        config: Optional meridian_config.json contents
    """
    epoch_dir = Path(epoch_dir)
    cfg = config or load_meridian_config()
    required = tuple(cfg.get("epoch_file_kit", {}).get("required", REQUIRED_KIT_FILES))

    report = EpochValidationReport(epoch_path=str(epoch_dir))

    if not epoch_dir.is_dir():
        report.add("BLOCK", "path_missing", f"Epoch directory not found: {epoch_dir}")
        return report

    # Required files
    for fname in required:
        fpath = epoch_dir / fname
        if not fpath.is_file():
            report.add(
                "BLOCK",
                "kit_missing",
                f"Required file missing: {fname}",
                f"Add {fname} per epoch file kit spec",
            )
        elif fpath.stat().st_size == 0:
            report.add("BLOCK", "kit_empty", f"Required file is empty: {fname}")

    # Optional files — informational only
    for fname in OPTIONAL_KIT_FILES:
        if not (epoch_dir / fname).is_file():
            report.add("INFO", "kit_optional", f"Optional file not present: {fname}")

    metadata = _read_metadata(epoch_dir)
    if metadata.get("_parse_error"):
        report.add("BLOCK", "metadata_parse", "metadata.json is not valid JSON")
        return report

    if not metadata:
        report.add("BLOCK", "metadata_missing", "metadata.json missing or empty")
        return report

    report.metadata = metadata
    report.epoch_date = str(metadata.get("epoch_date", ""))
    report.vertical = str(metadata.get("vertical", vertical))
    report.feature_id = str(metadata.get("feature_id", feature_id))

    # Metadata schema
    for key in METADATA_REQUIRED_KEYS:
        if key not in metadata or metadata[key] in (None, ""):
            report.add(
                "BLOCK",
                "metadata_field",
                f"metadata.json missing required field: {key}",
            )

    if report.epoch_date and not EPOCH_DATE_PATTERN.match(report.epoch_date):
        report.add("BLOCK", "epoch_date", f"Invalid epoch_date format: {report.epoch_date}")

    if vertical and report.vertical and report.vertical != vertical:
        report.add(
            "BLOCK",
            "vertical_mismatch",
            f"Expected vertical={vertical}, metadata has {report.vertical}",
        )

    if feature_id and report.feature_id and report.feature_id != feature_id:
        report.add(
            "WARN",
            "feature_id_mismatch",
            f"Expected feature_id={feature_id}, metadata has {report.feature_id}",
            "Align metadata.feature_id with catalog permanent ID",
        )

    _validate_gcp(epoch_dir, report)
    _validate_qa_report(epoch_dir, report)

    # CRS alignment with prior epoch (Oliver comparable-eras rule)
    if prior_metadata:
        report.prior_epoch_date = str(prior_metadata.get("epoch_date", ""))
        report.crs_aligned_with_prior = _crs_aligned(metadata, prior_metadata)
        if report.crs_aligned_with_prior is False:
            report.add(
                "WARN",
                "crs_drift",
                "CRS or datum differs from prior epoch — document in metadata.epoch_notes",
                "Align epochs explicitly; note GSD/sensor/pipeline changes",
            )

    return report


def _crs_aligned(current: dict[str, Any], prior: dict[str, Any]) -> bool:
    """True if horizontal CRS + datums match between epochs."""
    keys = ("crs", "horizontal_datum", "vertical_datum")
    return all(
        str(current.get(k, "")).strip().lower() == str(prior.get(k, "")).strip().lower()
        for k in keys
        if current.get(k) and prior.get(k)
    )


# ── Epoch archive ─────────────────────────────────────────────────────────────

@dataclass
class EpochRecord:
    """One ingested epoch in the archive index."""
    vertical: str
    feature_id: str
    epoch_date: str
    path: str
    ingested_at: str
    compiler_confidence: float | None = None
    validation_pass: bool = True
    crs_aligned_with_prior: bool | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


class EpochArchive:
    """Longitudinal epoch store — feature_id × epoch_date index.

    Directory layout:
        {root}/{vertical}/{feature_slug}/epoch_{YYYY-MM-DD}/
    """

    def __init__(self, root: Path | str) -> None:
        self.root = Path(root)
        self.records: list[EpochRecord] = []
        self.index_version: str = "1.0"

    def save_index(self, path: Path | str | None = None) -> None:
        index_path = Path(path) if path else self.root / "epoch_index.json"
        index_path.parent.mkdir(parents=True, exist_ok=True)
        data = {
            "index_version": self.index_version,
            "saved_at": _now(),
            "record_count": len(self.records),
            "records": [asdict(r) for r in self.records],
        }
        index_path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")

    @classmethod
    def load(cls, root: Path | str) -> "EpochArchive":
        root = Path(root)
        archive = cls(root)
        index_path = root / "epoch_index.json"
        if index_path.is_file():
            data = json.loads(index_path.read_text(encoding="utf-8"))
            archive.index_version = data.get("index_version", "1.0")
            for rdata in data.get("records", []):
                archive.records.append(EpochRecord(**rdata))
        return archive

    @staticmethod
    def feature_slug(feature_id: str) -> str:
        """@ST-SS4-S3 → ST-SS4-S3 for filesystem paths."""
        return feature_id.lstrip("@").replace("/", "_")

    def epoch_path(self, vertical: str, feature_id: str, epoch_date: str) -> Path:
        slug = self.feature_slug(feature_id)
        return self.root / vertical / slug / f"epoch_{epoch_date}"

    def prior_epoch(
        self,
        vertical: str,
        feature_id: str,
        before_date: str,
    ) -> EpochRecord | None:
        """Most recent epoch strictly before before_date for same feature."""
        candidates = [
            r for r in self.records
            if r.vertical == vertical
            and r.feature_id == feature_id
            and r.epoch_date < before_date
            and r.validation_pass
        ]
        if not candidates:
            return None
        return max(candidates, key=lambda r: r.epoch_date)

    def epoch_count(self, vertical: str, feature_id: str) -> int:
        return sum(
            1 for r in self.records
            if r.vertical == vertical and r.feature_id == feature_id and r.validation_pass
        )

    def gap_years(
        self,
        vertical: str,
        feature_id: str,
    ) -> list[int]:
        """Years with no epoch — Oliver missing-data rule (flag, never fill)."""
        dates = sorted(
            r.epoch_date[:4]
            for r in self.records
            if r.vertical == vertical and r.feature_id == feature_id and r.validation_pass
        )
        if len(dates) < 2:
            return []
        years = [int(d) for d in dates]
        return [y for y in range(min(years), max(years) + 1) if str(y) not in dates]


# ── Ingest ────────────────────────────────────────────────────────────────────

@dataclass
class IngestResult:
    success: bool
    record: EpochRecord | None = None
    validation: dict[str, Any] = field(default_factory=dict)
    error: str = ""


def ingest_epoch(
    archive: EpochArchive,
    *,
    vertical: str,
    feature_id: str,
    epoch_dir: Path | str,
    config: dict[str, Any] | None = None,
    allow_failed_validation: bool = False,
) -> IngestResult:
    """Validate and register an epoch in the archive index.

    Does not move/copy files — epoch_dir should already be at archive location
    or symlinked. Updates epoch_index.json on success.
    """
    epoch_dir = Path(epoch_dir)
    cfg = config or load_meridian_config()

    metadata = _read_metadata(epoch_dir)
    epoch_date = str(metadata.get("epoch_date", ""))

    prior = archive.prior_epoch(vertical, feature_id, epoch_date) if epoch_date else None
    prior_meta = prior.metadata if prior else None

    validation = validate_epoch_kit(
        epoch_dir,
        vertical=vertical,
        feature_id=feature_id,
        prior_metadata=prior_meta,
        config=cfg,
    )

    if not validation.pass_ and not allow_failed_validation:
        return IngestResult(
            success=False,
            validation=validation.to_dict(),
            error="Validation failed — see issues",
        )

    conf = validation.compiler_confidence
    if conf is None:
        conf = cfg.get("compiler_confidence", {}).get("automated_default", 0.45)

    record = EpochRecord(
        vertical=vertical,
        feature_id=feature_id,
        epoch_date=epoch_date,
        path=str(epoch_dir),
        ingested_at=_now(),
        compiler_confidence=conf,
        validation_pass=validation.pass_,
        crs_aligned_with_prior=validation.crs_aligned_with_prior,
        metadata=metadata,
    )

    # Replace duplicate epoch_date for same feature
    archive.records = [
        r for r in archive.records
        if not (r.vertical == vertical and r.feature_id == feature_id and r.epoch_date == epoch_date)
    ]
    archive.records.append(record)
    archive.save_index()

    return IngestResult(success=True, record=record, validation=validation.to_dict())


def ingest_record_for_registry(record: EpochRecord) -> dict[str, Any]:
    """Normalize epoch record for ingest_registry.record_scrape()."""
    return {
        "id": f"{record.feature_id}:{record.epoch_date}",
        "vertical": record.vertical,
        "feature_id": record.feature_id,
        "epoch_date": record.epoch_date,
        "compiler_confidence": record.compiler_confidence,
        "epoch_count": 1,
        "path": record.path,
    }


# ── CLI smoke ─────────────────────────────────────────────────────────────────

def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


if __name__ == "__main__":
    cfg = load_meridian_config()
    print(f"config: {cfg.get('config_version', '?')} verticals={list(cfg.get('verticals', {}))}")

    archive = EpochArchive(DEFAULT_ARCHIVE_ROOT)
    print(f"archive root: {archive.root}")
    print(f"epoch_path example: {archive.epoch_path('rally', '@ST-SS4-S3', '2026-03-15')}")

    # Dry validation of non-existent path
    report = validate_epoch_kit("/nonexistent/epoch")
    assert not report.pass_
    print("smoke: validate missing dir → BLOCK OK")