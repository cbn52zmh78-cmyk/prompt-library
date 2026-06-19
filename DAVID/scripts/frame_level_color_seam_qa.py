#!/usr/bin/env python3
"""Frame-level color + seam QA from ffmpeg-extracted delivered MP4 frames (#194).

Never trusts qa_report.json. Samples the actual delivered timeline:
  - color-cast: rgb_skew = ((R+G)/2 − B) / 255 on host crop — FAIL > 0.12
  - join/seam: inter-frame MAD spikes + skew discontinuity at shot boundaries

CLI
---
    python DAVID/scripts/frame_level_color_seam_qa.py <master.mp4> [--fps 2] [--json]
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

import numpy as np
from PIL import Image

from color_cast_qa import (
    RGB_SKEW_MAX,
    YELLOW_GREEN_LEGACY_PASS_MAX,
    color_cast_breaches,
    color_cast_passes,
    host_channel_means,
    measure_color_cast,
    rgb_skew_index,
)

JOIN_MAD_SPIKE_MIN = 18.0
HARD_CUT_MAD_MIN = 30.0
SKEW_JUMP_AT_JOIN_MIN = 0.08


def _ffmpeg() -> str:
    import imageio_ffmpeg

    return imageio_ffmpeg.get_ffmpeg_exe()


def extract_frames(master: Path, out_dir: Path, fps: float) -> list[Path]:
    out_dir.mkdir(parents=True, exist_ok=True)
    for old in out_dir.glob("frame_*.jpg"):
        try:
            old.unlink()
        except OSError:
            pass
    subprocess.run(
        [
            _ffmpeg(),
            "-y",
            "-i",
            str(master),
            "-vf",
            f"fps={fps}",
            "-qscale:v",
            "3",
            str(out_dir / "frame_%04d.jpg"),
        ],
        check=True,
        capture_output=True,
    )
    return sorted(out_dir.glob("frame_*.jpg"))


def frame_mad(a: np.ndarray, b: np.ndarray) -> float:
    return float(np.abs(a.astype(np.float32) - b.astype(np.float32)).mean())


def detect_join_issues(
    arrays: list[np.ndarray],
    fps: float,
) -> list[dict[str, Any]]:
    """Hard-cut / seam spikes from consecutive delivered frames."""
    issues: list[dict[str, Any]] = []
    if len(arrays) < 2:
        return issues

    mads: list[float] = []
    for i in range(1, len(arrays)):
        mads.append(frame_mad(arrays[i - 1], arrays[i]))

    for i, mad in enumerate(mads, start=1):
        skew_prev = rgb_skew_index(arrays[i - 1])
        skew_curr = rgb_skew_index(arrays[i])
        skew_jump = abs(skew_curr - skew_prev)
        next_mad = mads[i] if i < len(mads) else None
        t_s = round(i / fps, 2)

        if mad >= HARD_CUT_MAD_MIN and (next_mad is None or next_mad < mad * 0.55):
            issues.append(
                {
                    "t_s": t_s,
                    "kind": "hard_cut",
                    "frame_mad": round(mad, 2),
                    "skew_jump": round(skew_jump, 4),
                }
            )
        elif mad >= JOIN_MAD_SPIKE_MIN:
            kind = "join_color_seam" if skew_jump >= 0.02 else "join_spike"
            issues.append(
                {
                    "t_s": t_s,
                    "kind": kind,
                    "frame_mad": round(mad, 2),
                    "skew_jump": round(skew_jump, 4),
                }
            )
        elif skew_jump >= SKEW_JUMP_AT_JOIN_MIN:
            issues.append(
                {
                    "t_s": t_s,
                    "kind": "skew_discontinuity",
                    "frame_mad": round(mad, 2),
                    "skew_jump": round(skew_jump, 4),
                }
            )
    return issues


def evaluate_frame(arr: np.ndarray, *, t_s: float, frame_name: str) -> dict[str, Any]:
    cast = measure_color_cast(arr)
    breaches = color_cast_breaches(cast)
    r, g, b, _ = host_channel_means(arr)
    return {
        "t_s": t_s,
        "frame": frame_name,
        "r_mean": round(r, 1),
        "g_mean": round(g, 1),
        "b_mean": round(b, 1),
        "rgb_skew": round(cast["rgb_skew"], 4),
        "yellow_green": round(cast["yellow_green"], 4),
        "legacy_yg_pass": cast["yellow_green"] <= YELLOW_GREEN_LEGACY_PASS_MAX,
        "lum": round(cast["lum"], 1),
        "host_blue_mean": round(cast["host_blue_mean"], 1),
        "color_pass": color_cast_passes(cast),
        "color_issues": breaches,
    }


def verify_master(master: Path, fps: float = 2.0, *, proof_dir: Path | None = None) -> dict[str, Any]:
    prod_dir = master.parent.parent if master.parent.name == "output" else master.parent
    out_dir = proof_dir or (prod_dir / "frame_proof")
    frame_paths = extract_frames(master, out_dir, fps)
    if not frame_paths:
        return {"master": str(master), "error": "no frames extracted", "verdict": "ERROR"}

    arrays = [np.asarray(Image.open(p).convert("RGB")) for p in frame_paths]
    rows = []
    for i, (fp, arr) in enumerate(zip(frame_paths, arrays)):
        rows.append(evaluate_frame(arr, t_s=round(i / fps, 2), frame_name=fp.name))

    join_issues = detect_join_issues(arrays, fps)
    color_fails = [r for r in rows if not r["color_pass"]]
    legacy_false_passes = [r for r in rows if r["legacy_yg_pass"] and not r["color_pass"]]

    color_ok = not color_fails
    seam_ok = not any(j["kind"] in ("hard_cut", "join_color_seam", "skew_discontinuity") for j in join_issues)
    verdict = "PASS" if color_ok and seam_ok else "FAIL"

    return {
        "master": str(master),
        "source": "ffmpeg_extracted",
        "frames_checked": len(rows),
        "fps_sampled": fps,
        "frame_proof_dir": str(out_dir),
        "thresholds": {
            "rgb_skew_max": RGB_SKEW_MAX,
            "join_mad_spike_min": JOIN_MAD_SPIKE_MIN,
            "hard_cut_mad_min": HARD_CUT_MAD_MIN,
            "skew_jump_at_join_min": SKEW_JUMP_AT_JOIN_MIN,
            "legacy_yg_pass_max": YELLOW_GREEN_LEGACY_PASS_MAX,
        },
        "measured": {
            "rgb_skew_max": max(r["rgb_skew"] for r in rows),
            "rgb_skew_mean": round(float(np.mean([r["rgb_skew"] for r in rows])), 4),
            "yellow_green_max": max(r["yellow_green"] for r in rows),
            "color_fail_frames": len(color_fails),
            "legacy_false_pass_frames": len(legacy_false_passes),
            "join_issues": len(join_issues),
            "hard_cuts": sum(1 for j in join_issues if j["kind"] == "hard_cut"),
        },
        "join_issues": join_issues,
        "color_failures": [
            {"t_s": r["t_s"], "frame": r["frame"], "rgb_skew": r["rgb_skew"], "issues": r["color_issues"]}
            for r in color_fails[:10]
        ],
        "legacy_false_pass_sample": legacy_false_passes[:3],
        "verdict": verdict,
        "per_frame": rows,
    }


def evaluate_still(path: Path) -> dict[str, Any]:
    arr = np.asarray(Image.open(path).convert("RGB"))
    return evaluate_frame(arr, t_s=0.0, frame_name=path.name)


def main() -> int:
    ap = argparse.ArgumentParser(description="Frame-level color+seam QA from delivered MP4")
    ap.add_argument("master", type=Path, help="delivered master MP4")
    ap.add_argument("--fps", type=float, default=2.0, help="timeline sample rate (default 2)")
    ap.add_argument("--proof-dir", type=Path, default=None, help="where to write extracted frames")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    if not args.master.is_file():
        print(f"!! not found: {args.master}")
        return 2

    result = verify_master(args.master, args.fps, proof_dir=args.proof_dir)
    out = args.master.parent / "frame_level_qa.json"
    slim = {k: v for k, v in result.items() if k != "per_frame"}
    out.write_text(json.dumps(slim, indent=2), encoding="utf-8")

    if args.json:
        print(json.dumps(result, indent=2))
    else:
        m = result.get("measured", {})
        print(f"\n[{result['verdict']}] {args.master.name}  ({result['frames_checked']} frames @ {args.fps}fps)")
        print(f"  rgb_skew max     {m.get('rgb_skew_max')}  (<= {RGB_SKEW_MAX})")
        print(f"  yellow-green max {m.get('yellow_green_max')}  [legacy false-pass trap]")
        print(f"  color fails      {m.get('color_fail_frames')} / {result['frames_checked']}")
        print(f"  legacy false-pass {m.get('legacy_false_pass_frames')} frames (yg≤{YELLOW_GREEN_LEGACY_PASS_MAX}, rgb_skew fail)")
        print(f"  join issues      {m.get('join_issues')}  (hard_cuts={m.get('hard_cuts')})")
        for j in result.get("join_issues", [])[:6]:
            print(f"    @{j['t_s']}s {j['kind']} mad={j['frame_mad']} skew_jump={j['skew_jump']}")
        print(f"  report: {out}")
    return 0 if result["verdict"] == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())