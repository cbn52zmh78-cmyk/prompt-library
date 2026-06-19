#!/usr/bin/env python3
"""T4 #244 — single-pass saturation clamp proof on real per-shot _processed pass (480p).

Runs process_shot_segment (not reassembly) on raw chain segments, reports before/after
magenta + host_blue_mean per shot. HOLD — no commit; proof_218 stays HELD.
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


def run_proof(
    *,
    script_path: Path,
    prod_dir: Path,
    shot_ids: tuple[str, ...],
    resolution_label: str = "480p",
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
        if marker.is_file():
            marker.unlink()

        rl.process_shot_segment(
            scaled, processed, shot, refs, opts, work_dir, color_ref,
        )
        after = shot_metrics(processed)
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
            "verdict": verdict_state(after["magenta"], before["magenta"]),
            "clamp_marker": clamp_marker,
        })

    overall = "RED" if any(r["verdict"] == "RED" for r in rows) else "AMBER"
    report = {
        "issue": 244,
        "state": overall,
        "target": "AMBER on validated single-pass; GREEN after dual-verify + #218",
        "proof_218": "HELD",
        "commit": "HOLD — NEXUS + human-eye sign-off required",
        "clamp_method": "saturation-reduction",
        "clamp_baseline": {"gamma_b": 0.90, "saturation": 0.93},
        "clamp_ceiling": "Safety net — cannot pass raw-magenta 0.634 alone",
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
    args = parser.parse_args()

    report = run_proof(
        script_path=args.script,
        prod_dir=args.production,
        shot_ids=tuple(args.shots),
    )
    print(f"T4 #244 clamp proof — state={report['state']}  commit={report['commit']}")
    print(f"Report: {args.production / 'proof_244' / 'proof_244_clamp_report.json'}")
    for row in report["shots"]:
        b, a = row["before"], row["after"]
        print(
            f"  {row['shot_id']}: magenta {b['magenta']:.4f} → {a['magenta']:.4f}  "
            f"Bμ {b['host_blue_mean']:.1f} → {a['host_blue_mean']:.1f}  "
            f"verdict={row['verdict']}"
        )
    return 0 if report["state"] != "RED" else 1


if __name__ == "__main__":
    raise SystemExit(main())