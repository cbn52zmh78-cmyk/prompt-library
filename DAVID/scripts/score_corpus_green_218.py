#!/usr/bin/env python3
"""T4 #218 — score full Latin corpus (all chain shots + master) against GREEN_criteria.

Run AFTER full --force-all seamless re-gen. Metrics only — human-eye (Benjamin) external.
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import render_longform as rl  # noqa: E402
from color_cast_qa import probe_video_midframe  # noqa: E402
from proof_244_clamp_pass import (  # noqa: E402
    CLAMP_BURDEN_MAX,
    GREEN_CRITERIA_GATE,
    clamp_burden_guard,
    evaluate_green_gate,
    load_green_criteria,
    shot_metrics,
)

DEFAULT_SCRIPT = SCRIPTS / "longform_scripts" / "david_latin_corpus_v1_script.json"
DEFAULT_PROD = ROOT / "productions" / "david_latin_corpus_v1_longform_v1"
MASTER_GLOB = "david_david_latin_corpus_v1_seamless_v1.mp4"


def score_shot(sid: str, shots_dir: Path, criteria: dict) -> dict | None:
    raw = shots_dir / f"chain_{sid}.mp4"
    proc = shots_dir / f"chain_{sid}_processed.mp4"
    if not raw.is_file():
        return None
    before = shot_metrics(raw)
    after = shot_metrics(proc) if proc.is_file() else before
    guard = clamp_burden_guard(before["magenta"], after["magenta"])
    green_gate = evaluate_green_gate(
        raw_magenta=before["magenta"],
        graded_magenta=after["magenta"],
        graded_bmu=after["host_blue_mean"],
        clamp_burden=guard["clamp_burden"],
        criteria=criteria,
    )
    return {
        "shot_id": sid,
        "raw_chain": str(raw.relative_to(ROOT)),
        "processed_chain": str(proc.relative_to(ROOT)) if proc.is_file() else None,
        "before": before,
        "after": after,
        "green_gate": green_gate,
        **guard,
    }


def score_master(prod_dir: Path) -> dict | None:
    out_dir = prod_dir / "output"
    matches = sorted(out_dir.glob(MASTER_GLOB))
    if not matches:
        return None
    master = matches[-1]
    cast = probe_video_midframe(master)
    mag = rl.probe_magenta_score(master)
    yg = rl.probe_yellow_green_score(master)
    return {
        "path": str(master.relative_to(ROOT)),
        "magenta": round(mag, 4),
        "yellow_green": round(yg, 4),
        "host_blue_mean": round(cast.get("host_blue_mean", 0.0), 1),
        "host_br_ratio": round(cast.get("host_br_ratio", 0.0), 3),
        "rgb_skew": round(cast.get("rgb_skew", 0.0), 3),
        "magenta_pass": mag < rl.MAGENTA_SCORE_MAX,
        "yellow_green_pass": yg <= rl.YELLOW_GREEN_SCORE_MAX,
    }


def overall_verdict(rows: list[dict], master: dict | None, qa_pass: bool | None) -> str:
    if any(r.get("generation_defect") for r in rows):
        return "RED"
    if not rows or not all(r.get("green_gate", {}).get("metric_pass") for r in rows):
        return "RED"
    if master and not master.get("magenta_pass"):
        return "RED"
    if master and not master.get("yellow_green_pass"):
        return "AMBER"
    if qa_pass is False:
        return "AMBER"
    return "AMBER"


def main() -> int:
    parser = argparse.ArgumentParser(description="T4 #218 full-corpus GREEN scorer")
    parser.add_argument("--script", type=Path, default=DEFAULT_SCRIPT)
    parser.add_argument("--production", type=Path, default=DEFAULT_PROD)
    parser.add_argument("--human-eye", default="PENDING", help="PASS|SIGNED|PENDING")
    args = parser.parse_args()

    script = json.loads(args.script.read_text(encoding="utf-8"))
    shot_ids = [s["id"] for s in script.get("shots", []) if s.get("role") == "host"]
    shots_dir = args.production / "shots"
    criteria = load_green_criteria()

    rows = []
    missing = []
    for sid in shot_ids:
        row = score_shot(sid, shots_dir, criteria)
        if row is None:
            missing.append(sid)
            continue
        rows.append(row)

    master = score_master(args.production)
    qa_path = args.production / "qa_report.json"
    qa_pass = None
    qa_issues: list[str] = []
    if qa_path.is_file():
        qa = json.loads(qa_path.read_text(encoding="utf-8"))
        qa_pass = bool(qa.get("pass"))
        qa_issues = list(qa.get("issues") or [])

    metric_green = sum(1 for r in rows if r.get("green_gate", {}).get("metric_pass"))
    gen_defects = sum(1 for r in rows if r.get("generation_defect"))
    state = overall_verdict(rows, master, qa_pass)
    human = args.human_eye.upper()
    green_pass = (
        state in ("AMBER", "GREEN")
        and metric_green == len(shot_ids)
        and not missing
        and gen_defects == 0
        and human in ("PASS", "SIGNED")
        and (master is None or master.get("magenta_pass"))
    )
    if green_pass and qa_pass and state != "RED":
        state = "GREEN"

    report = {
        "issue": "218-FULL",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "state": state,
        "green_pass": green_pass,
        "proof_218": "HELD",
        "commit": "HOLD — NEXUS sign-off required before commit/unpark",
        "criteria_gate": str(GREEN_CRITERIA_GATE.relative_to(ROOT.parent)),
        "script": str(args.script.relative_to(ROOT)),
        "production": str(args.production.relative_to(ROOT)),
        "shot_count": len(shot_ids),
        "scored_count": len(rows),
        "missing_shots": missing,
        "metric_green_count": metric_green,
        "generation_defect_count": gen_defects,
        "human_eye": human,
        "human_eye_owner": "Benjamin + NEXUS",
        "qa_pass": qa_pass,
        "qa_issues": qa_issues,
        "master": master,
        "shots": rows,
    }

    out_dir = args.production / "proof_218"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_json = out_dir / "full_corpus_green_report.json"
    out_json.write_text(json.dumps(report, indent=2), encoding="utf-8")

    print(
        f"#218 full-corpus GREEN score — state={state}  "
        f"metric_green={metric_green}/{len(shot_ids)}  "
        f"gen_defects={gen_defects}  human_eye={human}"
    )
    if missing:
        print(f"  missing: {', '.join(missing)}")
    if master:
        print(
            f"  master: magenta={master['magenta']:.4f} "
            f"yg={master['yellow_green']:.4f} Bμ={master['host_blue_mean']:.1f}"
        )
    print(f"Report: {out_json}")
    return 0 if green_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())