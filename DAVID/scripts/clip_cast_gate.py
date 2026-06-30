#!/usr/bin/env python3
"""clip_cast_gate — per-clip color-cast deviation gate.

Closes the open-loop gap in render_longform.py: measure_color_cast() feeds the
generation reference gate (lines 776, 1622) but the assembled clips were never
checked against that same reference for *deviation*.

Public API
----------
    cast_gate_shot(video_path, shot_id, beat_id, shot_role, reference_metrics=None)
    measure_clip_cast(video_path, n_samples=4)

`measure_clip_cast` samples N frames evenly across the clip and returns per-frame
metrics + aggregate stats (mean, worst-frame).

`cast_gate_shot` compares the clip against a reference (color_ref metrics dict) if
provided, or applies absolute thresholds from color_cast_qa.py otherwise. Returns a
structured result ready to pass to taxonomy_writer.append_failure().

Deviation thresholds (reference-anchored)
------------------------------------------
    rgb_skew_delta > 0.08        → color drift (host warmth shift)
    host_br_ratio_delta < -0.10  → blue bleed across cuts
    blue_starvation_delta > 0.15 → progressive starvation in clip chain

These are conservative: real-world drift on concatenated Grok Imagine clips is
typically 0.02–0.05 per cut; 0.08 is a visible cast shift.

CLI usage
---------
    python clip_cast_gate.py --input shots/chain_01_hook_processed.mp4 --shot 01_hook
    python clip_cast_gate.py --input shots/chain_01_hook_processed.mp4 \\
        --ref-json /path/to/color_ref_metrics.json --json
"""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np

# ---------------------------------------------------------------------------
# Deviation thresholds — reference-anchored
# ---------------------------------------------------------------------------
RGB_SKEW_DELTA_MAX: float = 0.08          # host warmth shift across cuts
HOST_BR_RATIO_DELTA_MIN: float = -0.10    # blue drain (negative = getting bluer is ok)
BLUE_STARVATION_DELTA_MAX: float = 0.15   # progressive starvation in chain
HOST_BLUE_MEAN_DELTA_MIN: float = -20.0   # blue mean drop across cuts

# Number of frames to sample per clip (first, 33%, 66%, last)
DEFAULT_N_SAMPLES: int = 4


def _ffmpeg_exe() -> str:
    try:
        import imageio_ffmpeg  # type: ignore[import]
        return imageio_ffmpeg.get_ffmpeg_exe()
    except ImportError:
        return "ffmpeg"


def _extract_frame(video: Path, at_s: float) -> np.ndarray:
    """Extract one frame at `at_s` seconds; return RGB uint8 HxWx3 array."""
    from PIL import Image  # type: ignore[import]

    ff = _ffmpeg_exe()
    with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as tmp:
        jpg = Path(tmp.name)
    try:
        subprocess.run(
            [ff, "-y", "-ss", f"{at_s:.3f}", "-i", str(video),
             "-frames:v", "1", "-q:v", "2", str(jpg)],
            check=True,
            capture_output=True,
        )
        with Image.open(jpg) as img:
            return np.asarray(img.convert("RGB"))
    finally:
        jpg.unlink(missing_ok=True)


def _video_duration(video: Path) -> float:
    """Return video duration in seconds."""
    ff = _ffmpeg_exe()
    r = subprocess.run(
        [ff, "-i", str(video)],
        capture_output=True, text=True,
    )
    for line in (r.stderr or "").splitlines():
        if "Duration:" in line:
            t = line.split("Duration:", 1)[1].split(",")[0].strip()
            h, m, s = t.split(":")
            return int(h) * 3600 + int(m) * 60 + float(s)
    return 8.0  # fallback — typical shot floor


def measure_clip_cast(
    video: Path | str,
    n_samples: int = DEFAULT_N_SAMPLES,
) -> dict[str, Any]:
    """Sample N frames evenly across the clip; return per-frame metrics + aggregate.

    Returns
    -------
    {
        "frame_metrics": [dict, ...],   # one per sample
        "mean": dict,                   # mean of each float metric
        "worst": dict,                  # worst-case by rgb_skew
        "n_samples": int,
        "duration_s": float,
    }
    """
    from color_cast_qa import measure_color_cast  # noqa: PLC0415

    video = Path(video)
    dur = _video_duration(video)

    # Sample positions: avoid the first/last 5% to skip leader/tail frames
    guard = max(0.1, dur * 0.05)
    usable = dur - 2 * guard
    if usable < 0.2:
        positions = [dur * 0.5]
    else:
        positions = [guard + usable * i / max(n_samples - 1, 1)
                     for i in range(n_samples)]

    frames: list[dict[str, float]] = []
    for t in positions:
        try:
            arr = _extract_frame(video, t)
            frames.append(measure_color_cast(arr))
        except Exception:  # noqa: BLE001
            # frame extraction failure — skip, warn at aggregate level
            continue

    if not frames:
        return {
            "frame_metrics": [],
            "mean": {},
            "worst": {},
            "n_samples": n_samples,
            "duration_s": dur,
            "error": "all frame extractions failed",
        }

    keys = list(frames[0].keys())
    mean_metrics: dict[str, float] = {
        k: float(np.mean([f[k] for f in frames])) for k in keys
    }
    worst = max(frames, key=lambda f: f.get("rgb_skew", 0.0))

    return {
        "frame_metrics": frames,
        "mean": mean_metrics,
        "worst": worst,
        "n_samples": n_samples,
        "duration_s": dur,
    }


def cast_gate_shot(
    video: Path | str,
    shot_id: str,
    beat_id: str,
    shot_role: str,
    *,
    reference_metrics: dict[str, float] | None = None,
    n_samples: int = DEFAULT_N_SAMPLES,
    production_slug: str = "unknown",
) -> dict[str, Any]:
    """Gate a single clip against the color reference.

    Parameters
    ----------
    video             : path to the processed clip (chain_{sid}_processed.mp4)
    shot_id           : shot id string (e.g. "01_cold_open")
    beat_id           : beat id from the concept template (e.g. "hook")
    shot_role         : shot role string ("host", "b_roll", etc.)
    reference_metrics : output of measure_color_cast() on the color reference image.
                        If None, absolute thresholds from color_cast_qa are used.
    n_samples         : how many frames to sample (default 4)
    production_slug   : slug of the production (for failure entry)

    Returns
    -------
    {
        "shot_id": str,
        "beat_id": str,
        "shot_role": str,
        "pass": bool,
        "deviations": {metric: delta, ...},   # only populated if reference provided
        "breaches": [str, ...],
        "clip_cast": {mean + worst metrics},
        "taxonomy_entry": dict | None,  # ready for taxonomy_writer.append_failure()
    }
    """
    from color_cast_qa import color_cast_breaches  # noqa: PLC0415

    video = Path(video)
    clip_result = measure_clip_cast(video, n_samples=n_samples)

    clip_mean = clip_result.get("mean", {})
    clip_worst = clip_result.get("worst", {})

    breaches: list[str] = []
    deviations: dict[str, float] = {}
    suppression_flags: list[str] = []

    if reference_metrics:
        # Reference-anchored deviation check
        rgb_skew_delta = clip_mean.get("rgb_skew", 0.0) - reference_metrics.get("rgb_skew", 0.0)
        br_delta = clip_mean.get("host_br_ratio", 1.0) - reference_metrics.get("host_br_ratio", 1.0)
        starve_delta = (clip_mean.get("blue_starvation_fraction", 0.0)
                        - reference_metrics.get("blue_starvation_fraction", 0.0))
        bmean_delta = (clip_mean.get("host_blue_mean", 0.0)
                       - reference_metrics.get("host_blue_mean", 0.0))

        deviations = {
            "rgb_skew_delta": round(rgb_skew_delta, 4),
            "host_br_ratio_delta": round(br_delta, 4),
            "blue_starvation_delta": round(starve_delta, 4),
            "host_blue_mean_delta": round(bmean_delta, 1),
        }

        if rgb_skew_delta > RGB_SKEW_DELTA_MAX:
            breaches.append(
                f"rgb_skew drift Δ={rgb_skew_delta:.4f} > {RGB_SKEW_DELTA_MAX} "
                f"(ref={reference_metrics.get('rgb_skew', 0):.4f}, clip={clip_mean.get('rgb_skew', 0):.4f})"
            )
        if br_delta < HOST_BR_RATIO_DELTA_MIN:
            breaches.append(
                f"host B/R drain Δ={br_delta:.4f} < {HOST_BR_RATIO_DELTA_MIN} "
                f"(ref={reference_metrics.get('host_br_ratio', 0):.3f}, clip={clip_mean.get('host_br_ratio', 0):.3f})"
            )
        if starve_delta > BLUE_STARVATION_DELTA_MAX:
            breaches.append(
                f"blue_starvation growth Δ={starve_delta:.3f} > {BLUE_STARVATION_DELTA_MAX} "
                f"(ref={reference_metrics.get('blue_starvation_fraction', 0):.3f}, clip={clip_mean.get('blue_starvation_fraction', 0):.3f})"
            )
        if bmean_delta < HOST_BLUE_MEAN_DELTA_MIN:
            breaches.append(
                f"host B mean drop Δ={bmean_delta:.1f} < {HOST_BLUE_MEAN_DELTA_MIN} "
                f"(ref={reference_metrics.get('host_blue_mean', 0):.1f}, clip={clip_mean.get('host_blue_mean', 0):.1f})"
            )

        if clip_worst:
            abs_breaches = color_cast_breaches(clip_worst)
            for b in abs_breaches:
                tag = f"worst_frame:{b}"
                if tag not in breaches:
                    breaches.append(tag)
                    suppression_flags.append("worst_frame_abs_fail")
    else:
        # Absolute threshold check (no reference available)
        if clip_worst:
            breaches = color_cast_breaches(clip_worst)
            suppression_flags = ["no_reference_abs_gate"]

    gate_pass = len(breaches) == 0

    taxonomy_entry: dict[str, Any] | None = None
    if not gate_pass:
        taxonomy_entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "production_slug": production_slug,
            "shot_id": shot_id,
            "beat_id": beat_id,
            "shot_role": shot_role,
            "failure_type": "color_cast_deviation" if reference_metrics else "color_cast_absolute",
            "suppression_flags_applied": suppression_flags,
            "attempts": 1,
            "resolved": False,
            "resolution_flags": [],
            "deviations": deviations,
            "breaches": breaches,
        }

    return {
        "shot_id": shot_id,
        "beat_id": beat_id,
        "shot_role": shot_role,
        "pass": gate_pass,
        "deviations": deviations,
        "breaches": breaches,
        "clip_cast": {
            "mean": clip_mean,
            "worst": clip_worst,
            "duration_s": clip_result.get("duration_s", 0.0),
            "n_samples": clip_result.get("n_samples", n_samples),
        },
        "taxonomy_entry": taxonomy_entry,
    }


def gate_all_shots(
    shots_dir: Path | str,
    shots: list[dict[str, Any]],
    *,
    reference_metrics: dict[str, float] | None = None,
    production_slug: str = "unknown",
    taxonomy_path: Path | str | None = None,
) -> dict[str, Any]:
    """Gate every processed clip in shots_dir.

    Calls cast_gate_shot() for each shot, collects failures, optionally writes
    them to the taxonomy via taxonomy_writer.append_failure().

    Returns a summary: {"pass": bool, "failures": [...], "results": [...]}
    """
    shots_dir = Path(shots_dir)
    results = []
    failures = []

    for shot in shots:
        sid = shot.get("id") or shot.get("shot_id", "unknown")
        beat_id = shot.get("beat_id") or shot.get("pacing_beat", "unknown")
        shot_role = shot.get("role", "unknown")
        proc_path = shots_dir / f"chain_{sid}_processed.mp4"

        if not proc_path.is_file():
            # Fall back to non-processed path
            proc_path = shots_dir / f"chain_{sid}.mp4"
        if not proc_path.is_file():
            results.append({
                "shot_id": sid, "pass": None, "error": f"file not found: {proc_path.name}"
            })
            continue

        r = cast_gate_shot(
            proc_path, sid, str(beat_id), shot_role,
            reference_metrics=reference_metrics,
            production_slug=production_slug,
        )
        results.append(r)

        if not r["pass"] and r.get("taxonomy_entry") and taxonomy_path:
            try:
                import taxonomy_writer as tw  # noqa: PLC0415
                tw.append_failure(taxonomy_path, r["taxonomy_entry"])
            except Exception as exc:  # noqa: BLE001
                results[-1]["taxonomy_write_error"] = str(exc)

        if not r["pass"]:
            failures.append(r)

    return {
        "pass": len(failures) == 0,
        "total_shots": len(shots),
        "failed_shots": len(failures),
        "failures": failures,
        "results": results,
    }


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def _cli() -> int:
    import argparse

    ap = argparse.ArgumentParser(
        description="Per-clip color-cast deviation gate (#phase-a-v3)"
    )
    ap.add_argument("--input", required=True, help="Path to clip or shots/ directory")
    ap.add_argument("--shot", default=None, help="Shot ID label")
    ap.add_argument("--beat", default="unknown", help="Beat ID")
    ap.add_argument("--role", default="host", help="Shot role (host, b_roll, etc.)")
    ap.add_argument("--slug", default="unknown", help="Production slug")
    ap.add_argument(
        "--ref-json", default=None,
        help="Path to JSON file with reference color_cast metrics dict",
    )
    ap.add_argument("--taxonomy", default=None, help="Path to failure_taxonomy.json")
    ap.add_argument("--n-samples", type=int, default=DEFAULT_N_SAMPLES,
                    help="Frames to sample per clip (default 4)")
    ap.add_argument("--json", action="store_true", help="Output full JSON report")
    args = ap.parse_args()

    video = Path(args.input)
    if not video.is_file():
        print(f"!! not found: {video}")
        return 2

    ref: dict[str, float] | None = None
    if args.ref_json:
        ref_path = Path(args.ref_json)
        if ref_path.is_file():
            ref = json.loads(ref_path.read_text(encoding="utf-8"))
        else:
            print(f"!! ref-json not found: {ref_path} — using absolute gate")

    shot_id = args.shot or video.stem
    result = cast_gate_shot(
        video, shot_id, args.beat, args.role,
        reference_metrics=ref,
        n_samples=args.n_samples,
        production_slug=args.slug,
    )

    if args.taxonomy and result.get("taxonomy_entry"):
        try:
            import taxonomy_writer as tw  # noqa: PLC0415
            tw.append_failure(args.taxonomy, result["taxonomy_entry"])
            result["taxonomy_written"] = True
        except Exception as exc:  # noqa: BLE001
            result["taxonomy_write_error"] = str(exc)

    verdict = "PASS" if result["pass"] else "FAIL"
    if args.json:
        print(json.dumps(result, indent=2))
    else:
        m = result["clip_cast"].get("mean", {})
        print(f"[{verdict}] {video.name}  shot={shot_id}")
        print(
            f"  Bμ={m.get('host_blue_mean', 0):.1f}  "
            f"B/R={m.get('host_br_ratio', 0):.3f}  "
            f"rgb_skew={m.get('rgb_skew', 0):.4f}  "
            f"starve={m.get('blue_starvation_fraction', 0):.3f}"
        )
        if result["deviations"]:
            print(f"  deviations: {result['deviations']}")
        if result["breaches"]:
            print(f"  breaches: {result['breaches']}")

    return 0 if result["pass"] else 1


if __name__ == "__main__":
    raise SystemExit(_cli())
