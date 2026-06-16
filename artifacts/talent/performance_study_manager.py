#!/usr/bin/env python3
"""
Performance Study Manager v1.0 — Talent Agency
Tracks actor performance studies, rubric scores, and agency readiness.
No approved renders required — study phase only.
"""

from __future__ import annotations

import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from lib.bootstrap import ensure_paths

ensure_paths()

from talent.performance_rubric import (
    AGENCY_READY_THRESHOLD,
    AGENCY_STATUSES,
    DIMENSION_LABELS,
    MIN_SCORED_DIMENSIONS,
    PERFORMANCE_DIMENSIONS,
    RUBRIC_VERSION,
    STATUS_GUIDANCE,
)
from talent.roster_scanner import TalentRecord, agency_root, discover_all_talent, slugify

STUDIES_DIR_NAME = "Performance_Studies"
REPORTS_DIR_NAME = "Reports"
RUBRIC_FILE = "Scoring_Rubrics/performance_rubric_v1.json"
INDEX_FILE = "roster_index.json"


class PerformanceStudyManager:
    def __init__(self) -> None:
        self.agency_dir = agency_root()
        self.studies_dir = self.agency_dir / STUDIES_DIR_NAME
        self.reports_dir = self.agency_dir / REPORTS_DIR_NAME
        for path in (self.agency_dir, self.studies_dir, self.reports_dir,
                     self.agency_dir / "Scoring_Rubrics", self.agency_dir / "Pairing_Notes"):
            path.mkdir(parents=True, exist_ok=True)
        self._ensure_rubric_file()

    def _ensure_rubric_file(self) -> None:
        rubric_path = self.agency_dir / RUBRIC_FILE
        if rubric_path.exists():
            return
        payload = {
            "version": RUBRIC_VERSION,
            "scale": "0-10",
            "dimensions": {k: DIMENSION_LABELS[k] for k in PERFORMANCE_DIMENSIONS},
            "agency_ready_threshold": AGENCY_READY_THRESHOLD,
            "min_scored_dimensions": MIN_SCORED_DIMENSIONS,
            "statuses": {k: STATUS_GUIDANCE[k] for k in AGENCY_STATUSES},
        }
        rubric_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    def _study_path(self, talent_id: str) -> Path:
        return self.studies_dir / talent_id / "performance_study.json"

    def _infer_status(self, record: TalentRecord, study: dict[str, Any]) -> str:
        if study.get("agency_status") == "represented":
            return "represented"
        scores = study.get("performance_scores") or {}
        scored = [v for v in scores.values() if isinstance(v, (int, float))]
        if scored and len(scored) >= MIN_SCORED_DIMENSIONS:
            avg = sum(scored) / len(scored)
            if avg >= AGENCY_READY_THRESHOLD:
                return "agency_ready"
            return "performance_review"
        if study.get("scene_studies"):
            return "performance_review"
        if record.has_casting_jpg:
            return "plate_locked"
        return "development"

    def _blank_study(self, record: TalentRecord) -> dict[str, Any]:
        return {
            "talent_id": record.talent_id,
            "display_name": record.display_name,
            "roster_source": record.roster_source,
            "roster_path": record.roster_path,
            "gender": record.gender,
            "world_region": record.world_region,
            "age_locked": record.age_locked,
            "archetype_tags": record.archetypes,
            "performance_style": record.performance_style,
            "voice_notes": record.voice_notes,
            "agency_status": "development",
            "performance_scores": {d: None for d in PERFORMANCE_DIMENSIONS},
            "strengths": [],
            "growth_areas": [],
            "pairing_notes": {},
            "scene_studies": [],
            "casting_assets": {
                "has_profile": record.has_profile_md,
                "has_casting_jpg": record.has_casting_jpg,
                "has_clips": record.has_clips,
                "has_performance_reel": False,
            },
            "reviewer_notes": "",
            "last_review": None,
            "rubric_version": RUBRIC_VERSION,
            "created": datetime.now().isoformat(),
        }

    def sync_from_rosters(self) -> dict[str, Any]:
        """Discover cast folders and create/update performance study stubs."""
        records = discover_all_talent()
        created = updated = 0
        for record in records:
            path = self._study_path(record.talent_id)
            path.parent.mkdir(parents=True, exist_ok=True)
            if path.exists():
                with open(path, encoding="utf-8") as f:
                    study = json.load(f)
                study["casting_assets"] = {
                    "has_profile": record.has_profile_md,
                    "has_casting_jpg": record.has_casting_jpg,
                    "has_clips": record.has_clips,
                    "has_performance_reel": study.get("casting_assets", {}).get("has_performance_reel", False),
                }
                if record.archetypes and not study.get("archetype_tags"):
                    study["archetype_tags"] = record.archetypes
                if record.performance_style and not study.get("performance_style"):
                    study["performance_style"] = record.performance_style
                study["agency_status"] = self._infer_status(record, study)
                study["last_sync"] = datetime.now().isoformat()
                path.write_text(json.dumps(study, indent=2), encoding="utf-8")
                updated += 1
            else:
                study = self._blank_study(record)
                study["agency_status"] = self._infer_status(record, study)
                path.write_text(json.dumps(study, indent=2), encoding="utf-8")
                created += 1

        index = {
            "synced_at": datetime.now().isoformat(),
            "total_talent": len(records),
            "by_source": {},
            "by_status": {},
            "talent": [
                {
                    "talent_id": r.talent_id,
                    "display_name": r.display_name,
                    "roster_source": r.roster_source,
                    "has_casting_jpg": r.has_casting_jpg,
                }
                for r in records
            ],
        }
        for r in records:
            index["by_source"][r.roster_source] = index["by_source"].get(r.roster_source, 0) + 1
        for study_file in self.studies_dir.glob("*/performance_study.json"):
            with open(study_file, encoding="utf-8") as f:
                st = json.load(f).get("agency_status", "development")
            index["by_status"][st] = index["by_status"].get(st, 0) + 1
        (self.agency_dir / INDEX_FILE).write_text(json.dumps(index, indent=2), encoding="utf-8")
        return {"created": created, "updated": updated, "total": len(records)}

    def get_study(self, talent_id: str) -> dict[str, Any] | None:
        path = self._study_path(talent_id)
        if not path.exists():
            return None
        with open(path, encoding="utf-8") as f:
            return json.load(f)

    def log_scene_study(
        self,
        talent_id: str,
        *,
        project: str,
        scene: str,
        medium: str,
        notes: str,
        scores: dict[str, float] | None = None,
    ) -> dict[str, Any]:
        path = self._study_path(talent_id)
        if not path.exists():
            raise FileNotFoundError(f"No study for {talent_id}. Run sync first.")
        with open(path, encoding="utf-8") as f:
            study = json.load(f)
        entry = {
            "timestamp": datetime.now().isoformat(),
            "project": project,
            "scene": scene,
            "medium": medium,
            "notes": notes,
            "scores": scores or {},
        }
        study.setdefault("scene_studies", []).append(entry)
        if scores:
            for dim, val in scores.items():
                if dim in study["performance_scores"]:
                    existing = study["performance_scores"][dim]
                    if existing is None:
                        study["performance_scores"][dim] = val
                    else:
                        study["performance_scores"][dim] = round((existing + val) / 2, 1)
        study["last_review"] = entry["timestamp"]
        study["reviewer_notes"] = notes
        records = {r.talent_id: r for r in discover_all_talent()}
        rec = records.get(talent_id)
        if rec:
            study["agency_status"] = self._infer_status(rec, study)
        path.write_text(json.dumps(study, indent=2), encoding="utf-8")
        return study

    def set_scores(self, talent_id: str, scores: dict[str, float], notes: str = "") -> dict[str, Any]:
        path = self._study_path(talent_id)
        if not path.exists():
            raise FileNotFoundError(f"No study for {talent_id}. Run sync first.")
        with open(path, encoding="utf-8") as f:
            study = json.load(f)
        for dim, val in scores.items():
            if dim in study["performance_scores"]:
                study["performance_scores"][dim] = val
        if notes:
            study["reviewer_notes"] = notes
        study["last_review"] = datetime.now().isoformat()
        records = {r.talent_id: r for r in discover_all_talent()}
        rec = records.get(talent_id)
        if rec:
            study["agency_status"] = self._infer_status(rec, study)
        path.write_text(json.dumps(study, indent=2), encoding="utf-8")
        return study

    def represent(self, talent_id: str) -> dict[str, Any]:
        path = self._study_path(talent_id)
        if not path.exists():
            raise FileNotFoundError(f"No study for {talent_id}.")
        with open(path, encoding="utf-8") as f:
            study = json.load(f)
        study["agency_status"] = "represented"
        study["represented_at"] = datetime.now().isoformat()
        path.write_text(json.dumps(study, indent=2), encoding="utf-8")
        return study

    def write_agency_report(self) -> Path:
        lines = [
            "# Talent Agency — Performance Study Report",
            f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
            "",
            "## Status Summary",
            "",
        ]
        by_status: dict[str, list[str]] = {}
        for study_file in sorted(self.studies_dir.glob("*/performance_study.json")):
            with open(study_file, encoding="utf-8") as f:
                s = json.load(f)
            st = s.get("agency_status", "development")
            by_status.setdefault(st, []).append(
                f"- **{s['display_name']}** ({s['roster_source']}) — "
                f"plate: {'✓' if s.get('casting_assets', {}).get('has_casting_jpg') else '✗'} — "
                f"scenes studied: {len(s.get('scene_studies', []))}"
            )
        for status in AGENCY_STATUSES:
            if status in by_status:
                lines.append(f"### {status.replace('_', ' ').title()}")
                lines.append("")
                lines.extend(by_status[status])
                lines.append("")
        out = self.reports_dir / f"agency_report_{datetime.now().strftime('%Y%m%d_%H%M')}.md"
        out.write_text("\n".join(lines), encoding="utf-8")
        return out


def main() -> int:
    import argparse

    parser = argparse.ArgumentParser(description="Talent Agency — Performance Study Manager v1.0")
    parser.add_argument("command", choices=["sync", "report", "show", "scene", "scores", "represent"])
    parser.add_argument("--talent", help="talent_id or display name slug")
    parser.add_argument("--project", default="")
    parser.add_argument("--scene", default="")
    parser.add_argument("--medium", default="video")
    parser.add_argument("--notes", default="")
    parser.add_argument("--scores", help='JSON dict e.g. {"emotional_range": 8, "camera_presence": 7}')
    args = parser.parse_args()

    mgr = PerformanceStudyManager()
    if args.command == "sync":
        result = mgr.sync_from_rosters()
        print(f"✅ Synced {result['total']} talent ({result['created']} new, {result['updated']} updated)")
        return 0
    if args.command == "report":
        path = mgr.write_agency_report()
        print(f"✅ Report: {path}")
        return 0
    if not args.talent:
        print("❌ --talent required")
        return 1
    tid = slugify(args.talent) if " " in args.talent else args.talent
    if args.command == "show":
        study = mgr.get_study(tid)
        if not study:
            print(f"❌ No study for {tid}")
            return 1
        print(json.dumps(study, indent=2))
        return 0
    if args.command == "scene":
        scores = json.loads(args.scores) if args.scores else None
        study = mgr.log_scene_study(tid, project=args.project, scene=args.scene,
                                    medium=args.medium, notes=args.notes, scores=scores)
        print(f"✅ Scene study logged — status: {study['agency_status']}")
        return 0
    if args.command == "scores":
        if not args.scores:
            print("❌ --scores JSON required")
            return 1
        study = mgr.set_scores(tid, json.loads(args.scores), notes=args.notes)
        print(f"✅ Scores updated — status: {study['agency_status']}")
        return 0
    if args.command == "represent":
        study = mgr.represent(tid)
        print(f"✅ {study['display_name']} now represented")
        return 0
    return 1


if __name__ == "__main__":
    sys.exit(main())