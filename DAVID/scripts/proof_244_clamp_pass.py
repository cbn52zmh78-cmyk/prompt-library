#!/usr/bin/env python3
"""T4 #244 — single-pass saturation clamp proof on real per-shot _processed pass (480p).

Runs process_shot_segment (not reassembly) on raw chain segments, reports before/after
magenta + host_blue_mean per shot. #244-B adds clamp-burden guard: flags when raw−graded
magenta exceeds threshold → GENERATION DEFECT even if final metric passes.

HOLD — no commit; proof_218 stays HELD.
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import render_longform as rl  # noqa: E402

DEFAULT_SCRIPT = SCRIPTS / "longform_scripts" / "david_latin_corpus_v1_script.json"
DEFAULT_PROD = ROOT / "productions" / "david_latin_corpus_v1_longform_v1"
DEFAULT_SHOTS = ("01_cold_open", "05_method")
MAGENTA_MAX = rl.MAGENTA_SCORE_MAX
# #244-B — single-pass clamp burden ceiling (raw_magenta − graded_magenta)
CLAMP_BURDEN_MAX = 0.20
GENERATION_DEFECT_LABEL = "GENERATION DEFECT — clamp masking"


def scale_to_480p(src: Path, dst: Path) -> Path:
    ff = rl._ffmpeg_exe()
    dst.parent.mkdir(parents=True, exist_ok=True)
    vf = "scale=854:480:force_original_aspect_ratio=decrease,pad=854:480:(ow-iw)/2:(oh-ih)/2"
    cmd = [
        ff, "-y", "-i", str(src),
        "-vf", vf,
        "-c:v", "libx264", "-pix_fmt", "yuv420p",
        "-c:a", "copy", str(dst),
    ]
    subprocess.run(cmd, check=True, capture_output=True, text=True)
    return dst


def shot_metrics(video: Path) -> dict[str, float]:
    cast = rl.probe_color_cast_score(video)
    return {
        "magenta": round(rl.probe_magenta_score(video), 4),
        "host_blue_mean": round(cast.get("host_blue_mean", 0.0), 1),
        "host_br_ratio": round(cast.get("host_br_ratio", 0.0), 3),
    }


def verdict_state(after_mag: float, before_mag: float) -> str:
    if after_mag > MAGENTA_MAX:
        return "RED"
    if after_mag <= MAGENTA_MAX and after_mag < before_mag:
        return "AMBER"
    return "YELLOW"


def clamp_burden_guard(raw_magenta: float, graded_magenta: float) -> dict:
    """#244-B — detect clamp masking a generation defect (calibrated vs T1 single-pass)."""
    burden = round(raw_magenta - graded_magenta, 4)
    masked = burden > CLAMP_BURDEN_MAX
    return {
        "clamp_burden": burden,
        "clamp_burden_max": CLAMP_BURDEN_MAX,
        "generation_defect": masked,
        "generation_defect_label": GENERATION_DEFECT_LABEL if masked else None,
        "generation_defect_reason": (
            f"raw−graded magenta {burden:.4f} > {CLAMP_BURDEN_MAX} — clamp masking bad generation"
            if masked
            else None
        ),
    }


def overall_state(rows: list[dict]) -> str:
    if any(r.get("generation_defect") for r in rows):
        return "RED"
    if any(r["metric_verdict"] == "RED" for r in rows):
        return "RED"
    return "AMBER"


def run_proof(
    *,
    script_path: Path,
    prod_dir: Path,
    shot_ids: tuple[str, ...],
    resolution_label: str = "480p",
    force: bool = False,
    metrics_only: bool = False,
) -> dict:
    script = json.loads(script_path.read_text(encoding="utf-8"))
    refs = rl.resolve_refs(script)
    seam = script.get("config", {}).get("seamless") or {}
    opts = rl.SeamlessOptions(
        enabled=True,
        xfade_s=float(seam.get("xfade_s", rl.DEFAULT_XFADE_S)),
        match_color=bool(seam.get("match_color")),
        cut_on_motion=bool(seam.get("cut_on_motion")),
        lamp_lock=bool(seam.get("lamp_lock", True)),
        glasses_lock=bool(seam.get("glasses_lock", True)),
        loudnorm=bool(seam.get("loudnorm", True)),
        pin_audio_sync=bool(seam.get("pin_audio_sync", True)),
        reground_interval=int(seam.get("reground_interval", rl.REGROUND_EVERY_N)),
        magenta_clamp=bool(seam.get("magenta_clamp", True)),
        neutral_grade=bool(seam.get("neutral_grade", False)),
        neutral_generation=bool(seam.get("neutral_generation", False)),
    )
    opts = rl._apply_grade_policy(script, refs, opts)

    shots_dir = prod_dir / "shots"
    proof_dir = prod_dir / "proof_244"
    work_dir = proof_dir / "shots"
    work_dir.mkdir(parents=True, exist_ok=True)
    color_ref = rl.resolve_color_reference(refs, shots_dir)

    shot_map = {s["id"]: s for s in script.get("shots", [])}
    rows: list[dict] = []

    for sid in shot_ids:
        if sid not in shot_map:
            raise KeyError(f"shot {sid!r} not in script")
        shot = shot_map[sid]
        raw_chain = shots_dir / f"chain_{sid}.mp4"
        if not raw_chain.is_file():
            raise FileNotFoundError(f"missing raw chain: {raw_chain}")

        scaled = work_dir / f"chain_{sid}_{resolution_label}.mp4"
        if not scaled.is_file() or scaled.stat().st_mtime < raw_chain.stat().st_mtime:
            scale_to_480p(raw_chain, scaled)

        before = shot_metrics(scaled)
        processed = work_dir / f"chain_{sid}_{resolution_label}_processed.mp4"
        marker = processed.with_suffix(processed.suffix + ".clamp244.json")
        if force and not metrics_only:
            for stale in (
                processed,
                marker,
                work_dir / f"{scaled.stem}_clamped.mp4",
                work_dir / f"{scaled.stem}_clamped.mp4.clamp244.json",
                work_dir / f"{scaled.stem}_pinned.mp4",
                work_dir / f"{scaled.stem}_loud.mp4",
                work_dir / f"{scaled.stem}_final.mp4",
            ):
                stale.unlink(missing_ok=True)

        if metrics_only:
            if not processed.is_file():
                raise FileNotFoundError(
                    f"--metrics-only: missing processed output {processed} (run without --metrics-only first)"
                )
        else:
            rl.process_shot_segment(
                scaled, processed, shot, refs, opts, work_dir, color_ref,
            )
        after = shot_metrics(processed)
        guard = clamp_burden_guard(before["magenta"], after["magenta"])
        clamp_marker = None
        for candidate in (
            marker,
            work_dir / f"{scaled.stem}_clamped.mp4.clamp244.json",
        ):
            if candidate.is_file():
                clamp_marker = json.loads(candidate.read_text(encoding="utf-8"))
                break

        rows.append({
            "shot_id": sid,
            "resolution": resolution_label,
            "clamp_vf": rl.MAGENTA_SATURATION_CLAMP_VF,
            "clamp_stage": rl.CLAMP_STAGE_NAME,
            "raw_chain": str(raw_chain.relative_to(ROOT)),
            "scaled_input": str(scaled.relative_to(ROOT)),
            "processed_output": str(processed.relative_to(ROOT)),
            "before": before,
            "after": after,
            "delta": {
                "magenta": round(after["magenta"] - before["magenta"], 4),
                "host_blue_mean": round(after["host_blue_mean"] - before["host_blue_mean"], 1),
            },
            "metric_verdict": verdict_state(after["magenta"], before["magenta"]),
            "clamp_marker": clamp_marker,
            **guard,
        })

    gen_defects = [r for r in rows if r.get("generation_defect")]
    report = {
        "issue": "244-B",
        "state": overall_state(rows),
        "target": "GREEN only when raw generation clean + dual-verify + #218",
        "proof_218": "HELD",
        "commit": "HOLD — NEXUS + human-eye sign-off required",
        "clamp_method": "saturation-reduction",
        "clamp_baseline": {"gamma_b": 0.90, "saturation": 0.93},
        "clamp_ceiling": "Safety net — cannot pass raw-magenta 0.634 alone",
        "clamp_burden_guard": {
            "threshold": CLAMP_BURDEN_MAX,
            "label": GENERATION_DEFECT_LABEL,
            "calibrated_for": "T1 single-pass",
            "defect_count": len(gen_defects),
        },
        "magenta_max": MAGENTA_MAX,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "script": str(script_path.relative_to(ROOT)),
        "production": str(prod_dir.relative_to(ROOT)),
        "shots": rows,
    }
    out_json = proof_dir / "proof_244_clamp_report.json"
    out_json.write_text(json.dumps(report, indent=2), encoding="utf-8")
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description="T4 #244 single-pass clamp proof (480p)")
    parser.add_argument("--script", type=Path, default=DEFAULT_SCRIPT)
    parser.add_argument("--production", type=Path, default=DEFAULT_PROD)
    parser.add_argument("--shots", nargs="+", default=list(DEFAULT_SHOTS))
    parser.add_argument("--force", action="store_true", help="Re-run process_shot_segment from scratch")
    parser.add_argument(
        "--metrics-only",
        action="store_true",
        help="Re-score existing proof outputs only (no render / no process_shot_segment)",
    )
    args = parser.parse_args()

    report = run_proof(
        script_path=args.script,
        prod_dir=args.production,
        shot_ids=tuple(args.shots),
        force=args.force,
        metrics_only=args.metrics_only,
    )
    guard = report["clamp_burden_guard"]
    print(
        f"T4 #244-B clamp proof — state={report['state']}  "
        f"gen_defects={guard['defect_count']}/{len(report['shots'])}  "
        f"commit={report['commit']}"
    )
    print(f"Report: {args.production / 'proof_244' / 'proof_244_clamp_report.json'}")
    for row in report["shots"]:
        b, a = row["before"], row["after"]
        defect = f"  ⚠ {row['generation_defect_label']}" if row.get("generation_defect") else ""
        print(
            f"  {row['shot_id']}: magenta {b['magenta']:.4f} → {a['magenta']:.4f}  "
            f"(burden {row['clamp_burden']:.4f})  "
            f"Bμ {b['host_blue_mean']:.1f} → {a['host_blue_mean']:.1f}  "
            f"metric={row['metric_verdict']}{defect}"
        )
    return 0 if report["state"] != "RED" else 1


if __name__ == "__main__":
    raise SystemExit(main())