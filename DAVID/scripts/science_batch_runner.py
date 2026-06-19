#!/usr/bin/env python3
"""Observable science batch runner — stand up post-R1, render Observable slate.

Gates on R1 astrophysics reference harvest completeness, stages @2 plate files
from harvest → reference paths, wires visualization_ref into concepts, then
delegates to batch_runner for intake → 480p draft → manifest.

Usage:
    python DAVID/scripts/science_batch_runner.py check
    python DAVID/scripts/science_batch_runner.py stage-plates
    python DAVID/scripts/science_batch_runner.py standup --dry-run
    python DAVID/scripts/science_batch_runner.py standup
    python DAVID/scripts/science_batch_runner.py render-first
    python DAVID/scripts/science_batch_runner.py render-first --resolution 720p
"""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

ROOT = Path(__file__).resolve().parents[2]
DAVID = ROOT / "DAVID"
PIPELINE = ROOT / "STUDIO" / "Pipeline"
SCIENCE = ROOT / "Science"
CONCEPTS_DIR = PIPELINE / "Concepts" / "astro_mini_slate"
SCRIPTS_DIR = DAVID / "scripts" / "longform_scripts"
INTAKE = PIPELINE / "production_intake.py"
RENDER = DAVID / "scripts" / "render_longform.py"
BATCH = DAVID / "scripts" / "batch_runner.py"

R1_MANIFEST = SCIENCE / "reference_plates" / "astro_reference_manifest.json"
PLATE_LIBRARY = SCIENCE / "reference_plates" / "science_plate_library_v1.json"
HARVEST_DIR = SCIENCE / "reference_plates" / "astro" / "harvest"

# Publish order (#153) — slug → @2 plate slug
OBSERVABLE_SLATE: list[dict[str, Any]] = [
    {"order": 1, "slug": "science_black_hole_anatomy_v1", "plate_slug": "black-hole"},
    {"order": 2, "slug": "science_star_lifecycle_v1", "plate_slug": "supernova"},
    {"order": 3, "slug": "science_galaxy_formation_v1", "plate_slug": "galaxy"},
]

FIRST_EPISODE = OBSERVABLE_SLATE[0]["slug"]
DRAFT_RES = "480p"


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


def load_plate_library() -> dict[str, Any]:
    return _load_json(PLATE_LIBRARY)


def find_plate(library: dict[str, Any], slug: str) -> dict[str, Any]:
    key = slug.strip().lower()
    for plate in library.get("plates", []):
        if plate.get("slug", "").lower() == key:
            return plate
    astro = [p["slug"] for p in library.get("plates", []) if p.get("domain") == "astro"]
    raise KeyError(f"No plate {slug!r} (astro: {', '.join(astro)})")


def check_r1() -> dict[str, Any]:
    """Return readiness report; raises SystemExit(1) when R1 incomplete."""
    if not R1_MANIFEST.is_file():
        raise SystemExit(f"R1 manifest missing: {R1_MANIFEST}")

    manifest = _load_json(R1_MANIFEST)
    expected = int(manifest.get("subject_count") or 0)
    harvested = int(manifest.get("harvested_count") or 0)
    entries = manifest.get("entries") or []
    failed = [e for e in entries if e.get("harvest_status") != "OK"]

    report = {
        "ready": harvested >= expected and expected > 0 and not failed,
        "task": manifest.get("task"),
        "expected": expected,
        "harvested": harvested,
        "failed_slugs": [e.get("slug") for e in failed],
        "manifest": str(R1_MANIFEST.relative_to(ROOT)).replace("\\", "/"),
        "checked_at": _utc_now(),
    }
    return report


def _harvest_path(plate_slug: str) -> Path:
    return HARVEST_DIR / f"{plate_slug}_harvest.jpg"


def stage_plates(*, force: bool = False) -> list[dict[str, Any]]:
    """Copy R1 harvest files into plate reference_file paths when missing."""
    r1 = check_r1()
    if not r1["ready"]:
        raise SystemExit(
            f"R1 not ready: {r1['harvested']}/{r1['expected']} harvested; "
            f"failed={r1['failed_slugs']}"
        )

    library = load_plate_library()
    manifest = _load_json(R1_MANIFEST)
    harvest_by_slug = {e["slug"]: e for e in manifest.get("entries", [])}
    staged: list[dict[str, Any]] = []

    for plate in library.get("plates", []):
        if plate.get("domain") != "astro":
            continue
        slug = plate["slug"]
        ref_rel = plate["plate_spec"]["reference_file"]
        ref_path = ROOT / ref_rel.replace("/", "\\" if "\\" in str(ROOT) else "/")
        harvest = _harvest_path(slug)
        harvest_meta = harvest_by_slug.get(slug, {})

        if ref_path.is_file() and ref_path.stat().st_size > 5000 and not force:
            staged.append(
                {
                    "plate_slug": slug,
                    "plate_id": plate["plate_id"],
                    "reference_file": ref_rel,
                    "action": "reused",
                    "bytes": ref_path.stat().st_size,
                }
            )
            continue

        if not harvest.is_file():
            staged.append(
                {
                    "plate_slug": slug,
                    "plate_id": plate["plate_id"],
                    "reference_file": ref_rel,
                    "action": "missing_harvest",
                    "harvest": str(harvest.relative_to(ROOT)).replace("\\", "/"),
                }
            )
            continue

        ref_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(harvest, ref_path)
        meta_path = ref_path.with_suffix(".json")
        meta = {
            "plate_id": plate["plate_id"],
            "slug": slug,
            "subject": plate.get("subject"),
            "path": str(ref_path),
            "source": "R1_harvest",
            "harvest_file": str(harvest.relative_to(ROOT)).replace("\\", "/"),
            "image_url": harvest_meta.get("image_url"),
            "source_url": harvest_meta.get("source_url"),
            "primary_citation": harvest_meta.get("primary_citation") or plate.get("source", {}).get("primary_citation"),
            "license": harvest_meta.get("license") or plate.get("source", {}).get("license"),
            "staged_at": _utc_now(),
        }
        _write_json(meta_path, meta)
        staged.append(
            {
                "plate_slug": slug,
                "plate_id": plate["plate_id"],
                "reference_file": ref_rel,
                "action": "staged_from_harvest",
                "bytes": ref_path.stat().st_size,
            }
        )

    report_path = CONCEPTS_DIR / "r1_plate_staging_report.json"
    _write_json(
        report_path,
        {"generated_at": _utc_now(), "r1": r1, "plates": staged},
    )
    return staged


def wire_concepts() -> list[dict[str, Any]]:
    """Ensure each Observable concept carries science_subject.visualization_ref."""
    library = load_plate_library()
    wired: list[dict[str, Any]] = []

    for row in OBSERVABLE_SLATE:
        slug = row["slug"]
        plate = find_plate(library, row["plate_slug"])
        ref_rel = plate["plate_spec"]["reference_file"]
        concept_path = CONCEPTS_DIR / f"{slug}.concept.json"
        if not concept_path.is_file():
            raise FileNotFoundError(concept_path)

        concept = _load_json(concept_path)
        ss = concept.setdefault("science_subject", {})
        prev = ss.get("visualization_ref")
        ss["visualization_ref"] = ref_rel
        ss.setdefault("plate_id", plate["plate_id"])
        ss.setdefault("plate_slug", plate["slug"])
        _write_json(concept_path, concept)

        script_path = SCRIPTS_DIR / f"{slug}_script.json"
        proc = subprocess.run(
            [sys.executable, str(INTAKE), str(concept_path), "-o", str(script_path)],
            cwd=str(ROOT),
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
        wired.append(
            {
                "slug": slug,
                "plate_slug": row["plate_slug"],
                "plate_id": plate["plate_id"],
                "visualization_ref": ref_rel,
                "previous_ref": prev,
                "intake_exit": proc.returncode,
                "script_path": str(script_path.relative_to(ROOT)).replace("\\", "/"),
            }
        )
        if proc.returncode != 0:
            raise SystemExit(
                f"Intake failed for {slug} (exit {proc.returncode}):\n"
                f"{proc.stdout}\n{proc.stderr}"
            )

    report_path = CONCEPTS_DIR / "observable_wiring_report.json"
    _write_json(report_path, {"generated_at": _utc_now(), "episodes": wired})
    return wired


def cmd_check(_: argparse.Namespace) -> int:
    report = check_r1()
    print(json.dumps(report, indent=2))
    if not report["ready"]:
        return 1
    print(f"R1 ready — {report['harvested']}/{report['expected']} astro subjects harvested")
    return 0


def cmd_stage_plates(args: argparse.Namespace) -> int:
    staged = stage_plates(force=args.force)
    for row in staged:
        print(f"  {row['action']:22} {row['plate_slug']} → {row.get('reference_file', '?')}")
    missing = [r for r in staged if r["action"] == "missing_harvest"]
    if missing:
        print(f"[stage] warning: {len(missing)} plate(s) lack R1 harvest copies")
        return 1
    print(f"[stage] {len(staged)} astro plate(s) checked")
    return 0


def cmd_standup(args: argparse.Namespace) -> int:
    r1 = check_r1()
    if not r1["ready"]:
        print(json.dumps(r1, indent=2))
        raise SystemExit("R1 incomplete — cannot stand up Observable slate")

    print(f"[standup] R1 OK ({r1['harvested']}/{r1['expected']})")
    stage_plates()
    wired = wire_concepts()
    for row in wired:
        print(f"  wired {row['slug']} ← {row['plate_id']} ({row['visualization_ref']})")

    cmd = [
        sys.executable,
        str(BATCH),
        "run",
        str(CONCEPTS_DIR.relative_to(ROOT)),
    ]
    if args.dry_run:
        cmd.append("--dry-run")
    if args.no_seamless:
        cmd.append("--no-seamless")
    if args.batch_id:
        cmd.extend(["--batch-id", args.batch_id])

    print(f"[standup] batch_runner {' '.join(cmd[2:])}")
    return subprocess.run(cmd, cwd=str(ROOT)).returncode


def _patch_resolution(script_path: Path, resolution: str) -> Path:
    script = _load_json(script_path)
    script.setdefault("config", {})["resolution"] = resolution
    out = script_path.with_name(script_path.stem.replace("_script", f"_{resolution}_script") + ".json")
    if out == script_path:
        out = script_path.with_name(f"{script['slug']}_{resolution}_script.json")
    _write_json(out, script)
    return out


def cmd_render_first(args: argparse.Namespace) -> int:
    """Render episode #1 (Anatomy of a Black Hole) after post-R1 stand-up prep."""
    r1 = check_r1()
    if not r1["ready"]:
        raise SystemExit("R1 incomplete")

    stage_plates()
    wire_concepts()

    slug = args.slug or FIRST_EPISODE
    script_path = SCRIPTS_DIR / f"{slug}_script.json"
    if not script_path.is_file():
        raise SystemExit(f"Script missing after intake: {script_path}")

    resolution = args.resolution or DRAFT_RES
    render_script = _patch_resolution(script_path, resolution)

    validate = subprocess.run(
        [sys.executable, str(RENDER), str(render_script), "--script-only"],
        cwd=str(ROOT),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    if validate.returncode != 0:
        print(validate.stdout)
        print(validate.stderr)
        raise SystemExit(f"--script-only failed (exit {validate.returncode})")

    print(f"[render-first] {slug} @ {resolution}")
    cmd = [sys.executable, str(RENDER), str(render_script)]
    if not args.no_seamless:
        cmd.extend(["--seamless", "--match-color", "--cut-on-motion"])
    if args.package:
        cmd.append("--package")

    proc = subprocess.run(cmd, cwd=str(ROOT))
    if proc.returncode != 0:
        return proc.returncode

    prod_dir = ROOT / "STUDIO" / "Productions" / "Editorial" / f"{slug}_longform_v1"
    qa_path = prod_dir / "qa_report.json"
    if qa_path.is_file():
        qa = _load_json(qa_path)
        print(f"[render-first] qa_pass={qa.get('pass')} issues={qa.get('issues', [])}")
    out_dir = prod_dir / "output"
    if out_dir.is_dir():
        mp4s = sorted(out_dir.glob("*.mp4"), key=lambda p: p.stat().st_mtime, reverse=True)
        if mp4s:
            print(f"[render-first] output → {mp4s[0]}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Observable science batch — post-R1 stand-up and first-episode render"
    )
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("check", help="Verify R1 astro harvest completeness").set_defaults(func=cmd_check)

    stage_p = sub.add_parser("stage-plates", help="Stage R1 harvest → @2 reference files")
    stage_p.add_argument("--force", action="store_true", help="Overwrite existing reference files")
    stage_p.set_defaults(func=cmd_stage_plates)

    stand_p = sub.add_parser("standup", help="R1 gate → stage → wire → batch_runner run")
    stand_p.add_argument("--dry-run", action="store_true")
    stand_p.add_argument("--no-seamless", action="store_true")
    stand_p.add_argument("--batch-id", help="Batch id passed to batch_runner")
    stand_p.set_defaults(func=cmd_standup)

    rf = sub.add_parser("render-first", help=f"Prep + render first Observable episode ({FIRST_EPISODE})")
    rf.add_argument("--slug", help="Override first-episode slug")
    rf.add_argument("--resolution", default=DRAFT_RES, help="Render resolution (default 480p)")
    rf.add_argument("--no-seamless", action="store_true")
    rf.add_argument("--package", action="store_true", help="Run package_episode after render")
    rf.set_defaults(func=cmd_render_first)

    return parser


def main(argv: Optional[list[str]] = None) -> int:
    args = build_parser().parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())