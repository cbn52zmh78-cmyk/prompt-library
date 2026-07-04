#!/usr/bin/env python3
"""airport_flyby_demo.py — MERIDIAN airport AI fly-by demo orchestrator.

Builds everything needed before dad's video go-ahead:
  1. Load approach path (fixture or dad dataset)
  2. Load airport box scores
  3. Generate obstruction brief (brief_narrator)
  4. Generate render_longform-compatible flyby_script.json
  5. Optional: --render invokes render_longform.py

Usage:
    python airport_flyby_demo.py
    python airport_flyby_demo.py --approach path/to/approach_path.json
    python airport_flyby_demo.py --render
    python airport_flyby_demo.py --dad-drop path/to/dad/epoch_dir
"""
from __future__ import annotations

import argparse
import csv
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from _paths import WORKSPACE, DAVID_ROOT

MERIDIAN_ROOT = WORKSPACE / "Stonebridge" / "Products" / "MERIDIAN"
DEMO_DIR = MERIDIAN_ROOT / "airport" / "demo"
DEFAULT_APPROACH = DEMO_DIR / "approach_path_fixture.json"
DEFAULT_MANIFEST = DEMO_DIR / "demo_manifest.json"
SCRIPTS_DIR = DAVID_ROOT / "scripts"

if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from box_score_db import BoxScoreDB  # noqa: E402
from brief_narrator import BriefNarrator, MeridianBrief  # noqa: E402
from epoch_manager import EpochArchive, ingest_epoch, validate_epoch_kit  # noqa: E402
from production_catalog import catalog_for_product  # noqa: E402


VOICE_SUFFIX = (
    "warm measured female voice, slight British RP accent, "
    "professional aviation planning register — factual, never alarmist, "
    "synthetic narration only"
)

VISUAL_STYLE = (
    "first-person cockpit POV approach simulation, photogrammetry-derived terrain, "
    "Part 77 obstruction highlights as semi-transparent red wireframe boxes and "
    "amber vegetation growth cones, NOT a certified flight simulator, "
    "educational planning visualization only, 16:9, cool daylight, "
    "AI-GENERATED spatial visualization"
)


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def load_approach(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def load_manifest() -> dict[str, Any]:
    if DEFAULT_MANIFEST.is_file():
        return json.loads(DEFAULT_MANIFEST.read_text(encoding="utf-8"))
    return {}


def register_demo_catalog(approach: dict[str, Any]) -> list[str]:
    """Mint @APT- IDs for demo obstructions if not already in catalog."""
    cat = catalog_for_product("meridian")
    registered: list[str] = []
    for obs in approach.get("obstructions", []):
        oid = obs.get("object_id", "")
        parsed = oid.lstrip("@").split("-", 1)
        if len(parsed) != 2:
            continue
        prefix, slug = parsed[0], parsed[1]
        if cat.resolve(oid):
            continue
        cat.register_prefixed(
            prefix,
            slug,
            obs.get("name", slug),
            state={
                "object_type": obs.get("object_type", ""),
                "lat": obs.get("lat"),
                "lon": obs.get("lon"),
            },
            notes="airport_flyby_demo fixture bootstrap",
        )
        registered.append(oid)
    if registered:
        from production_catalog import catalog_path_for_product
        cat.save(catalog_path_for_product("meridian"))
    return registered


def ingest_dad_epoch(epoch_dir: Path, feature_id: str = "@APT-SITE") -> dict[str, Any]:
    """Ingest dad's anonymized epoch when dropped into demo."""
    archive = EpochArchive.load(MERIDIAN_ROOT / "epochs")
    result = ingest_epoch(
        archive,
        vertical="airport",
        feature_id=feature_id,
        epoch_dir=epoch_dir,
    )
    return {
        "success": result.success,
        "validation": result.validation,
        "record": result.record.__dict__ if result.record else None,
    }


def build_flyby_script(
    approach: dict[str, Any],
    brief: MeridianBrief,
) -> dict[str, Any]:
    """Generate render_longform-compatible script from approach waypoints."""
    runway = approach.get("runway", {})
    rwy_desig = runway.get("designation", "09/27")
    threshold = runway.get("primary_threshold", "09")
    demo_id = approach.get("demo_id", "airport_flyby_v1")
    target_s = approach.get("approach", {}).get("target_duration_s", 30)

    shots: list[dict[str, Any]] = []
    t = 0
    narration_text = brief.sections.get("what_changed", "")

    for wp in approach.get("waypoints", []):
        dur = wp.get("duration_s", 6)
        label = wp.get("label", f"wp_{wp.get('seq', 0)}")
        alt = wp.get("altitude_ft", 1000)
        dist = wp.get("distance_nm", 1)
        heading = wp.get("heading_deg", 90)
        highlight_ids = wp.get("highlight_ids", [])
        beat = wp.get("narration_beat", "")

        id_clause = ""
        if highlight_ids:
            id_clause = " OBSTRUCTION HIGHLIGHTS: " + ", ".join(highlight_ids) + "."

        video_prompt = (
            f"CONTINUITY LOCK — seamless cockpit POV approach to runway {threshold} "
            f"({rwy_desig}), heading {heading}°, {dist}nm final at {alt}ft.{id_clause} "
            f"{VISUAL_STYLE}. Camera: locked pilot eye-line through windshield, "
            f"subtle aircraft motion, glide slope indicator visible. "
            f"Beat: {beat}. AI-GENERATED · STONEBRIDGE compliance label required on export."
        )

        speech = _speech_for_beat(beat, brief, highlight_ids, approach)

        shots.append({
            "id": f"{wp.get('seq', len(shots) + 1):02d}_{label}",
            "duration": dur,
            "t_start": t,
            "t_end": t + dur,
            "role": "flyby_pov",
            "video_prompt": video_prompt,
            "speech_text": speech,
            "on_screen": f"RWY {threshold} · {dist}nm · {alt}ft",
            "meridian": {
                "waypoint_seq": wp.get("seq"),
                "highlight_ids": highlight_ids,
                "narration_beat": beat,
            },
        })
        t += dur

    slug = demo_id.replace("-", "_")
    return {
        "slug": slug,
        "title": f"MERIDIAN Airport Fly-By — Runway {threshold} Approach",
        "format_id": "meridian-airport-flyby",
        "target_seconds": target_s,
        "config": {
            "model_video": "grok-imagine-video-1.5",
            "resolution": "720p",
            "aspect_ratio": "16:9",
            "voice_suffix": VOICE_SUFFIX,
            "meridian_demo": demo_id,
            "compliance": {
                "eu_art50": True,
                "us_disclosure": True,
                "ai_generated_video": True,
                "auto_execute": False,
            },
            "seamless": {
                "primary": "extend",
                "xfade_s": 0.3,
                "match_color": True,
            },
        },
        "shots": shots,
        "provenance_card": {
            "product": "meridian",
            "vertical": "airport",
            "deliverable": "ai_flyby_simulation",
            "data_source": approach.get("status", "fixture"),
            "approach_path_id": approach.get("approach", {}).get("path_id", ""),
            "feature_ids": brief.feature_ids,
            "compiler_confidence": brief.compiler_confidence,
            "generated_at": _now(),
            "disclaimer": (
                "AI-generated planning visualization derived from photogrammetry. "
                "Not for navigation. Not a certified flight simulator."
            ),
        },
        "guardrails": [
            "No performance claims — terrain/obstruction facts only",
            "All @APT- IDs must match box score Layer 2 source",
            "EU Art. 50 + US disclosure on all output",
            "auto_execute: false — ELEANOR gate before client delivery",
        ],
        "qa_rules": {
            "max_shot_duration_s": 10,
            "min_shot_duration_s": 4,
            "require_speech_per_shot": True,
            "require_compliance_label": True,
        },
        "meta": {
            "agent": "airport_flyby_demo",
            "brief_deliverable": brief.deliverable_type,
            "narration_prompt": brief.llm_prompt[:500],
        },
    }


def _speech_for_beat(
    beat: str,
    brief: MeridianBrief,
    highlight_ids: list[str],
    approach: dict[str, Any],
) -> str:
    """Deterministic voiceover lines per waypoint beat."""
    airport = approach.get("airport", {})
    rwy = approach.get("runway", {})
    icao = airport.get("icao", "AIRPORT")
    threshold = rwy.get("primary_threshold", "09")

    obs_by_id = {o["object_id"]: o for o in approach.get("obstructions", [])}

    if beat == "establish":
        return (
            f"Approach to runway {threshold} at {icao}. "
            f"Five nautical miles final. This is an AI-generated planning visualization "
            f"derived from photogrammetry — not for navigation."
        )
    if beat == "descent":
        return (
            f"Three miles final, descending on the published glide path. "
            f"Obstruction database current through the latest survey epoch."
        )
    if beat == "obstruction":
        lines = []
        for oid in highlight_ids:
            obs = obs_by_id.get(oid, {})
            pen = obs.get("penetration_m", 0)
            if pen > 0:
                lines.append(
                    f"New obstruction: {oid}, {obs.get('name', '')} — "
                    f"penetrates the approach surface by {pen:.1f} metres."
                )
            else:
                lines.append(f"{oid} clear at this epoch.")
        return " ".join(lines) if lines else brief.sections.get("what_changed", "")[:200]
    if beat == "vegetation":
        lines = []
        for oid in highlight_ids:
            obs = obs_by_id.get(oid, {})
            ytp = obs.get("years_to_penetration")
            if ytp:
                lines.append(
                    f"{oid}: {obs.get('name', '')} — clear today, "
                    f"approximately {ytp:.1f} years to penetration at current growth."
                )
        return " ".join(lines) if lines else "Vegetation objects within approach corridor monitored."
    if beat == "threshold":
        return (
            f"Runway {threshold} threshold in sight. "
            f"This concludes the planning visualization. "
            f"All imagery AI-generated from survey data."
        )
    return f"Continuing approach to runway {threshold}."


def write_custody_log(outputs: dict[str, str], approach: dict[str, Any]) -> None:
    log_path = DEMO_DIR / "custody_log.csv"
    fields = ["timestamp", "action", "source", "output", "status"]
    row = {
        "timestamp": _now(),
        "action": "flyby_demo_build",
        "source": str(approach.get("status", "fixture")),
        "output": json.dumps(outputs),
        "status": "scaffold_ready",
    }
    write_header = not log_path.is_file()
    with open(log_path, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        if write_header:
            writer.writeheader()
        writer.writerow(row)


def run_render(script_path: Path) -> int:
    """Invoke render_longform.py when video go-ahead is granted."""
    render_py = SCRIPTS_DIR / "render_longform.py"
    if not render_py.is_file():
        print(f"[flyby] render_longform.py not found: {render_py}", file=sys.stderr)
        return 1
    cmd = [sys.executable, str(render_py), str(script_path)]
    print(f"[flyby] Running: {' '.join(cmd)}")
    return subprocess.call(cmd)


def build_demo(
    approach_path: Path | None = None,
    *,
    dad_epoch_dir: Path | None = None,
    render: bool = False,
) -> dict[str, Any]:
    """Full demo pipeline — ready to render when cleared."""
    approach_path = approach_path or DEFAULT_APPROACH
    approach = load_approach(approach_path)

    if dad_epoch_dir:
        ingest_result = ingest_dad_epoch(dad_epoch_dir)
        approach["status"] = "dad_dataset_ingested"
        approach["dad_ingest"] = ingest_result
        out_approach = DEMO_DIR / "approach_path.json"
        out_approach.write_text(json.dumps(approach, indent=2), encoding="utf-8")
        print(f"[flyby] Dad epoch ingested: {ingest_result['success']}")

    registered = register_demo_catalog(approach)
    if registered:
        print(f"[flyby] Catalog registered: {registered}")

    db = BoxScoreDB.load()
    db.load_fixture("airport")

    narrator = BriefNarrator(db=db)
    obstruction_brief = narrator.narrate_from_db("airport", "obstruction_change_report")
    flyby_brief = narrator.narrate_from_db(
        "airport",
        "ai_flyby_narration",
        context={"waypoints": approach.get("waypoints", [])},
    )

    brief_path = DEMO_DIR / "obstruction_brief.json"
    obstruction_brief.save(brief_path)

    script = build_flyby_script(approach, flyby_brief)
    script_path = DEMO_DIR / "flyby_script.json"
    script_path.write_text(json.dumps(script, indent=2, ensure_ascii=False), encoding="utf-8")

    outputs = {
        "brief": str(brief_path),
        "script": str(script_path),
        "obstruction_summary": obstruction_brief.sections["what_changed"][:300],
        "shot_count": len(script.get("shots", [])),
        "catalog_entries_added": registered,
    }
    write_custody_log(outputs, approach)

    print(f"[flyby] Brief: {brief_path}")
    print(f"[flyby] Script: {script_path} ({outputs['shot_count']} shots)")
    print(f"[flyby] Obstruction: {outputs['obstruction_summary'][:120]}...")

    if render:
        print("[flyby] --render requested — invoking render_longform")
        rc = run_render(script_path)
        outputs["render_exit_code"] = rc
    else:
        print("[flyby] Script ready. Run with --render when video go-ahead granted.")

    return outputs


def main() -> int:
    parser = argparse.ArgumentParser(description="MERIDIAN airport AI fly-by demo")
    parser.add_argument(
        "--approach",
        type=Path,
        default=None,
        help="Approach path JSON (default: approach_path_fixture.json)",
    )
    parser.add_argument(
        "--dad-drop",
        type=Path,
        default=None,
        help="Dad's anonymized epoch directory to ingest before build",
    )
    parser.add_argument(
        "--render",
        action="store_true",
        help="Invoke render_longform.py after script generation",
    )
    args = parser.parse_args()

    build_demo(
        approach_path=args.approach,
        dad_epoch_dir=args.dad_drop,
        render=args.render,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())