#!/usr/bin/env python3
"""
C4 Frame-Proof QA verifier (#195).

Why this exists
---------------
The render pipeline's `qa_report.json` is SELF-REPORTED by the same process that did the
render, and its colour gate samples ONE frame per segment (at the segment midpoint —
`probe_magenta_score` / `probe_yellow_green_score` / `_probe_grey_balance` in
render_longform.py). A cast that lands between those midpoints is never measured — that is
how a false `pass:true` slips through.

This verifier does NOT trust the JSON. It:
  1. extracts the ACTUAL delivered frames across the WHOLE timeline (1 fps by default),
  2. re-measures each frame with the pipeline's own colour formulas + thresholds,
  3. keeps the extracted frames on disk as viewable *frame proof*,
  4. cross-checks its own per-frame finding against the JSON self-report and flags
     INCOHERENCE (JSON says pass, frames say fail) — the false-pass signal.

A C4 colour verdict is issued ONLY from this frame measurement, never from the JSON alone.

Thresholds mirror render_longform.py:
    magenta fraction      <= 0.42
    yellow-green fraction <= 0.12
    grey-balance drift (range across timeline) <= 0.12

Tooling: ffmpeg via `imageio_ffmpeg` (no PATH ffmpeg / ffprobe needed); Pillow + numpy.

CLI
---
    python DAVID/scripts/c4_frame_proof_qa.py <master.mp4|production_dir> [--fps 1] [--json]
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

import numpy as np
from PIL import Image

MAGENTA_SCORE_MAX = 0.42
YELLOW_GREEN_SCORE_MAX = 0.12
GREY_BALANCE_DRIFT_MAX = 0.12


def _ffmpeg() -> str:
    import imageio_ffmpeg

    return imageio_ffmpeg.get_ffmpeg_exe()


# ── per-image metrics — identical formulas to render_longform.py, vectorised ──
def magenta_fraction(arr: np.ndarray) -> float:
    """probe_magenta_score, per delivered frame (step-6 subsample to mirror pipeline)."""
    a = arr[::6, ::6].astype(np.float64)
    r, g, b = a[..., 0], a[..., 1], a[..., 2]
    lum = 0.299 * r + 0.587 * g + 0.114 * b
    valid = (lum >= 40) & (lum <= 200)
    total = int(valid.sum())
    if not total:
        return 0.0
    mag = ((b > r * 1.08) & (b > g * 1.05)) | (((r + b) > g * 1.35) & (b > g * 0.95))
    return float((mag & valid).sum()) / total


def yellow_green_fraction(arr: np.ndarray) -> float:
    """probe_yellow_green_score, host region h[0.18,0.72] x w[0.08,0.48], step 6."""
    h, w = arr.shape[:2]
    region = arr[int(h * 0.18):int(h * 0.72):6, int(w * 0.08):int(w * 0.48):6].astype(np.float64)
    r, g, b = region[..., 0], region[..., 1], region[..., 2]
    lum = 0.299 * r + 0.587 * g + 0.114 * b
    valid = (lum >= 35) & (lum <= 210)
    total = int(valid.sum())
    if not total:
        return 0.0
    bias = (g > r * 1.06) & (g > b * 1.04)
    return float((bias & valid).sum()) / total


def grey_balance(arr: np.ndarray) -> float:
    """_probe_grey_balance, region h[0.1,0.55] x w[0.15,0.85], step 8."""
    h, w = arr.shape[:2]
    region = arr[int(h * 0.1):int(h * 0.55):8, int(w * 0.15):int(w * 0.85):8].astype(np.float64)
    if region.size == 0:
        return 0.0
    r_mean, g_mean, b_mean = region[..., 0].mean(), region[..., 1].mean(), region[..., 2].mean()
    return abs(r_mean - g_mean) / 255.0 + abs(b_mean - g_mean) / 255.0


def extract_frames(master: Path, out_dir: Path, fps: float) -> list[Path]:
    out_dir.mkdir(parents=True, exist_ok=True)
    for old in out_dir.glob("frame_*.jpg"):
        old.unlink()
    subprocess.run(
        [_ffmpeg(), "-y", "-i", str(master), "-vf", f"fps={fps}", "-qscale:v", "3",
         str(out_dir / "frame_%04d.jpg")],
        check=True, capture_output=True,
    )
    return sorted(out_dir.glob("frame_*.jpg"))


def verify(master: Path, fps: float) -> dict:
    prod_dir = master.parent.parent if master.parent.name == "output" else master.parent
    proof_dir = prod_dir / "frame_proof"
    frames = extract_frames(master, proof_dir, fps)
    if not frames:
        return {"master": str(master), "error": "no frames extracted", "frame_verdict": "ERROR"}

    rows = []
    for i, fp in enumerate(frames):
        arr = np.asarray(Image.open(fp).convert("RGB"))
        rows.append({
            "t_s": round(i / fps, 2),
            "frame": fp.name,
            "magenta": round(magenta_fraction(arr), 4),
            "yellow_green": round(yellow_green_fraction(arr), 4),
            "grey_balance": round(grey_balance(arr), 4),
        })

    mags = [r["magenta"] for r in rows]
    ygs = [r["yellow_green"] for r in rows]
    greys = [r["grey_balance"] for r in rows]
    grey_drift = max(greys) - min(greys)

    mag_bad = [r for r in rows if r["magenta"] > MAGENTA_SCORE_MAX]
    yg_bad = [r for r in rows if r["yellow_green"] > YELLOW_GREEN_SCORE_MAX]

    color_pass = not mag_bad and not yg_bad and grey_drift <= GREY_BALANCE_DRIFT_MAX

    # ── coherence vs self-reported JSON ──────────────────────────────────────
    qa_path = prod_dir / "qa_report.json"
    coherence = "NO_JSON"
    json_pass = None
    if qa_path.is_file():
        qa = json.loads(qa_path.read_text(encoding="utf-8"))
        json_pass = bool(qa.get("pass"))
        if json_pass and not color_pass:
            coherence = "INCOHERENT_FALSE_PASS"   # JSON green, frames fail — the #195 trap
        elif json_pass == color_pass:
            coherence = "COHERENT"
        else:
            coherence = "JSON_STRICTER"            # JSON fails but frames clean (rare)

    return {
        "master": str(master),
        "frames_checked": len(rows),
        "fps_sampled": fps,
        "frame_proof_dir": str(proof_dir),
        "thresholds": {
            "magenta_max": MAGENTA_SCORE_MAX,
            "yellow_green_max": YELLOW_GREEN_SCORE_MAX,
            "grey_balance_drift_max": GREY_BALANCE_DRIFT_MAX,
        },
        "measured": {
            "magenta_max": max(mags), "magenta_mean": round(float(np.mean(mags)), 4),
            "yellow_green_max": max(ygs), "yellow_green_mean": round(float(np.mean(ygs)), 4),
            "grey_balance_drift": round(grey_drift, 4),
        },
        "breaches": {
            "magenta": [(r["t_s"], r["magenta"]) for r in mag_bad],
            "yellow_green": [(r["t_s"], r["yellow_green"]) for r in yg_bad],
            "grey_drift_over": round(grey_drift, 4) if grey_drift > GREY_BALANCE_DRIFT_MAX else None,
        },
        "json_self_report_pass": json_pass,
        "coherence": coherence,
        "frame_verdict": "FRAME-PASS" if color_pass else "FRAME-FAIL",
        "per_frame": rows,
    }


def main() -> int:
    ap = argparse.ArgumentParser(description="C4 Frame-Proof QA (#195) — measure delivered frames, not the JSON")
    ap.add_argument("target", help="master *.mp4 OR a production dir containing output/*_seamless_v1.mp4")
    ap.add_argument("--fps", type=float, default=1.0, help="frames per second to sample across the timeline (default 1)")
    ap.add_argument("--json", action="store_true", help="emit full JSON (incl. per-frame table)")
    args = ap.parse_args()

    target = Path(args.target)
    if target.is_dir():
        masters = sorted(target.glob("output/*_seamless_v1.mp4"))
        if not masters:
            print(f"!! no output/*_seamless_v1.mp4 under {target}")
            return 2
        master = masters[0]
    else:
        master = target
    if not master.is_file():
        print(f"!! master not found: {master}")
        return 2

    result = verify(master, args.fps)
    out = master.parent.parent / "frame_proof_qa.json" if master.parent.name == "output" else master.parent / "frame_proof_qa.json"
    out.write_text(json.dumps(result, indent=2), encoding="utf-8")

    if args.json:
        print(json.dumps(result, indent=2))
    else:
        m = result.get("measured", {})
        print(f"\n[{result['frame_verdict']}] {master.name}  ({result['frames_checked']} frames @ {args.fps}fps)")
        print(f"  magenta      max {m.get('magenta_max')}  (<= {MAGENTA_SCORE_MAX})")
        print(f"  yellow-green max {m.get('yellow_green_max')}  (<= {YELLOW_GREEN_SCORE_MAX})")
        print(f"  grey drift       {m.get('grey_balance_drift')}  (<= {GREY_BALANCE_DRIFT_MAX})")
        print(f"  json self-report pass={result.get('json_self_report_pass')}  ->  coherence: {result['coherence']}")
        for axis, items in result.get("breaches", {}).items():
            if items:
                print(f"  BREACH {axis}: {items}")
        print(f"  frame proof: {result['frame_proof_dir']}")
        print(f"  report: {out}")
    return 0 if result["frame_verdict"] == "FRAME-PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
