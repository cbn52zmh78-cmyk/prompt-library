"""Color-cast QA metrics (#194 / #199 T4).

Detects generation-source casts post-grade cannot fix:
  - Legacy yellow-green (g>r) misses warm/blue-deficit host (yg≈0.007, CCB≈0.30).
  - Blue-starvation (B≈8) on low-key archive masters (proof_194 trap).

Primary host gate (archive + clinical):
  rgb_skew — ((R+G)/2 − B) / 255 on host crop; warm/blue-deficit casts FAIL > 0.12.
  Catches proof_194 frames the legacy yg gate passed at ~0.007.

Clinical seamless (@Set-Seamless-Neutral-001):
  clinical_channel_balance (CCB) — |R−G|/255 + |B−G|/255; FAIL > 0.12 on lum 80–220.
"""

from __future__ import annotations

from typing import Any

import numpy as np

YELLOW_GREEN_SCORE_MAX = 0.12
YELLOW_GREEN_LEGACY_PASS_MAX = 0.012  # +66 cohort: legacy gate passed at ~0.007
GREY_CAST_COHORT_MIN = 0.20  # T4 #199 audit: visible cast missed by yg-only
CLINICAL_CHANNEL_BALANCE_MAX = 0.12
RGB_SKEW_MAX = 0.12  # (R+G)/2−B on host; proof_194 after ≈0.20, neutral ref ≈0.06

# Low-key archive / concat-only trap (Latin proof_194: host B≈5–8).
BLUE_STARVATION_FRACTION_MAX = 0.50
HOST_BR_RATIO_MIN = 0.22
HOST_BLUE_MEAN_MIN = 25.0
# T243 generation-source gate (pre-render) — stricter than post-grade QA
GENERATION_HOST_BLUE_MEAN_MIN = 40.0
GENERATION_HOST_BR_RATIO_MIN = 0.35
GENERATION_BLUE_STARVATION_FRACTION_MAX = 0.30
BLUE_STARVATION_B_MAX = 12.0
BLUE_STARVATION_LUM_MAX = 90.0


def host_region(arr: np.ndarray, *, step: int = 6) -> np.ndarray:
    h, w = arr.shape[:2]
    return arr[int(h * 0.18): int(h * 0.72): step, int(w * 0.08): int(w * 0.48): step]


def host_channel_means(arr: np.ndarray) -> tuple[float, float, float, float]:
    region = host_region(arr).astype(np.float64)
    if region.size == 0:
        return 0.0, 0.0, 0.0, 0.0
    r = float(region[..., 0].mean())
    g = float(region[..., 1].mean())
    b = float(region[..., 2].mean())
    lum = 0.299 * r + 0.587 * g + 0.114 * b
    return r, g, b, lum


def yellow_green_fraction(arr: np.ndarray) -> float:
    """Legacy gate — misses warm/blue-deficit casts (#199)."""
    region = host_region(arr).astype(np.float64)
    r, g, b = region[..., 0], region[..., 1], region[..., 2]
    lum = 0.299 * r + 0.587 * g + 0.114 * b
    valid = (lum >= 35) & (lum <= 210)
    total = int(valid.sum())
    if not total:
        return 0.0
    bias = (g > r * 1.06) & (g > b * 1.04)
    return float((bias & valid).sum()) / total


def clinical_channel_balance(arr: np.ndarray) -> float:
    """Absolute host RGB imbalance — FAIL >0.12 on neutral clinical (#199)."""
    r, g, b, _ = host_channel_means(arr)
    return abs(r - g) / 255.0 + abs(b - g) / 255.0


def blue_deficit_index(arr: np.ndarray) -> float:
    r, g, b, _ = host_channel_means(arr)
    return (min(r, g) - b) / 255.0


def rgb_skew_index(arr: np.ndarray) -> float:
    """Warm/blue-deficit host skew: ((R+G)/2 − B) / 255 — fails proof_194, passes neutral."""
    r, g, b, _ = host_channel_means(arr)
    return ((r + g) / 2.0 - b) / 255.0


def measure_color_cast(arr: np.ndarray) -> dict[str, float]:
    """Host-region color-cast metrics from RGB uint8 array."""
    region = host_region(arr).astype(np.float64)
    r, g, b, lum = host_channel_means(arr)
    if region.size == 0:
        return {
            "blue_starvation_fraction": 0.0,
            "host_br_ratio": 1.0,
            "host_blue_mean": 255.0,
            "warm_cast_index": 0.0,
            "rgb_skew": 0.0,
            "clinical_channel_balance": 0.0,
            "yellow_green": 0.0,
            "lum": 0.0,
        }
    r_pix, g_pix, b_pix = region[..., 0], region[..., 1], region[..., 2]
    lum_pix = 0.299 * r_pix + 0.587 * g_pix + 0.114 * b_pix
    valid = (lum_pix >= 35) & (lum_pix <= 210)
    rv, gv, bv = r_pix[valid], g_pix[valid], b_pix[valid]
    if rv.size == 0:
        starve_frac = 0.0
        br = 1.0
    else:
        starved = (bv < 40) | (bv < rv * 0.35)
        starve_frac = float(starved.sum()) / float(rv.size)
        br = float(bv.mean()) / max(float(rv.mean()), 1.0)
    return {
        "blue_starvation_fraction": starve_frac,
        "host_br_ratio": br,
        "host_blue_mean": b,
        "warm_cast_index": (r - b) / 255.0,
        "rgb_skew": rgb_skew_index(arr),
        "clinical_channel_balance": clinical_channel_balance(arr),
        "yellow_green": yellow_green_fraction(arr),
        "lum": lum,
    }


def color_cast_breaches(metrics: dict[str, float]) -> list[str]:
    issues: list[str] = []
    lum = metrics.get("lum", 0.0)
    skew = metrics.get("rgb_skew", 0.0)
    if skew > RGB_SKEW_MAX:
        issues.append(f"rgb_skew {skew:.4f} > {RGB_SKEW_MAX}")
    ccb = metrics.get("clinical_channel_balance", 0.0)
    if 80 <= lum <= 220 and ccb > CLINICAL_CHANNEL_BALANCE_MAX:
        issues.append(f"clinical_channel_balance {ccb:.4f} > {CLINICAL_CHANNEL_BALANCE_MAX}")
    starve = metrics.get("blue_starvation_fraction", 0.0)
    br = metrics.get("host_br_ratio", 1.0)
    bmean = metrics.get("host_blue_mean", 255.0)
    if starve > BLUE_STARVATION_FRACTION_MAX:
        issues.append(f"blue_starvation_fraction {starve:.3f} > {BLUE_STARVATION_FRACTION_MAX}")
    if br < HOST_BR_RATIO_MIN:
        issues.append(f"host B/R {br:.3f} < {HOST_BR_RATIO_MIN}")
    if lum < BLUE_STARVATION_LUM_MAX and bmean < BLUE_STARVATION_B_MAX:
        issues.append(f"blue_starvation B={bmean:.1f} lum={lum:.1f}")
    elif bmean < HOST_BLUE_MEAN_MIN and lum < BLUE_STARVATION_LUM_MAX:
        issues.append(f"host B mean {bmean:.1f} < {HOST_BLUE_MEAN_MIN}")
    return issues


def color_cast_passes(metrics: dict[str, float]) -> bool:
    return not color_cast_breaches(metrics)


def generation_reference_breaches(
    metrics: dict[str, float],
    *,
    host: bool = True,
) -> list[str]:
    """T243 pre-render gate — generation stills must carry blue before i2v."""
    issues: list[str] = []
    bmean = metrics.get("host_blue_mean", 0.0)
    br = metrics.get("host_br_ratio", 0.0)
    starve = metrics.get("blue_starvation_fraction", 1.0)
    label = "host" if host else "set_shadow"
    if bmean < GENERATION_HOST_BLUE_MEAN_MIN:
        issues.append(f"{label} Bμ {bmean:.1f} < {GENERATION_HOST_BLUE_MEAN_MIN}")
    if br < GENERATION_HOST_BR_RATIO_MIN:
        issues.append(f"{label} B/R {br:.3f} < {GENERATION_HOST_BR_RATIO_MIN}")
    if starve > GENERATION_BLUE_STARVATION_FRACTION_MAX:
        issues.append(
            f"{label} blue_starvation_fraction {starve:.3f} > "
            f"{GENERATION_BLUE_STARVATION_FRACTION_MAX}"
        )
    return issues


def generation_reference_passes(metrics: dict[str, float], *, host: bool = True) -> bool:
    return not generation_reference_breaches(metrics, host=host)


def measure_set_shadow_blue_health(arr: np.ndarray) -> dict[str, float]:
    """Set plate gate — shadow/mid pixels must retain blue (no global amber wash)."""
    h, w = arr.shape[:2]
    region = arr[int(h * 0.25): int(h * 0.92): 4, int(w * 0.12): int(w * 0.88): 4]
    if region.size == 0:
        return {
            "host_blue_mean": 0.0,
            "host_br_ratio": 0.0,
            "blue_starvation_fraction": 1.0,
        }
    rs = region[..., 0].astype(np.float64)
    gs = region[..., 1].astype(np.float64)
    bs = region[..., 2].astype(np.float64)
    lum = 0.299 * rs + 0.587 * gs + 0.114 * bs
    valid = (lum >= 35) & (lum <= 160)
    rv, gv, bv = rs[valid], gs[valid], bs[valid]
    if rv.size == 0:
        return {
            "host_blue_mean": 0.0,
            "host_br_ratio": 0.0,
            "blue_starvation_fraction": 1.0,
        }
    starved = (bv < 40) | (bv < rv * 0.35)
    return {
        "host_blue_mean": float(bv.mean()),
        "host_br_ratio": float(bv.mean()) / max(float(rv.mean()), 1.0),
        "blue_starvation_fraction": float(starved.sum()) / float(rv.size),
    }


def evaluate_clinical_cast(arr: np.ndarray) -> dict[str, Any]:
    m = measure_color_cast(arr)
    breaches = color_cast_breaches(m)
    r, g, b, _ = host_channel_means(arr)
    return {
        "r_mean": round(r, 1),
        "g_mean": round(g, 1),
        "b_mean": round(b, 1),
        "lum": round(m["lum"], 1),
        "yellow_green": round(m["yellow_green"], 4),
        "rgb_skew": round(m["rgb_skew"], 4),
        "clinical_channel_balance": round(m["clinical_channel_balance"], 4),
        "blue_deficit": round(blue_deficit_index(arr), 4),
        "blue_starvation": any("blue_starvation" in b for b in breaches),
        "pass": not breaches,
        "issues": breaches,
    }


def legacy_false_pass_cohort(yg: float, grey_balance: float) -> bool:
    """True for +66 audit cohort: legacy yg≤0.012 passed, grey_balance≥0.20 failed."""
    return yg <= YELLOW_GREEN_LEGACY_PASS_MAX and grey_balance >= GREY_CAST_COHORT_MIN


def legacy_false_pass(yg: float, ccb: float) -> bool:
    """Broader trap: old yg gate green while CCB red (includes borderline yg 0.007–0.12)."""
    return yg <= YELLOW_GREEN_SCORE_MAX and ccb > CLINICAL_CHANNEL_BALANCE_MAX


def summarize_color_cast(metrics: dict[str, float]) -> dict[str, Any]:
    breaches = color_cast_breaches(metrics)
    return {
        **{k: round(v, 4) if isinstance(v, float) else v for k, v in metrics.items()},
        "pass": not breaches,
        "breaches": breaches,
    }


def probe_video_midframe(video: Path, at_s: float | None = None) -> dict[str, float]:
    """Extract one frame from video and measure color cast."""
    import subprocess
    import tempfile
    from pathlib import Path as _Path

    from PIL import Image

    try:
        import imageio_ffmpeg

        ff = imageio_ffmpeg.get_ffmpeg_exe()
    except ImportError:
        ff = "ffmpeg"
    if at_s is None:
        r = subprocess.run([ff, "-i", str(video)], capture_output=True, text=True)
        dur = 4.0
        for line in (r.stderr or "").splitlines():
            if "Duration:" in line:
                t = line.split("Duration:", 1)[1].split(",")[0].strip()
                h, m, s = t.split(":")
                dur = max(0.5, (int(h) * 3600 + int(m) * 60 + float(s)) * 0.5)
                break
        at_s = dur
    with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as tmp:
        jpg = _Path(tmp.name)
    subprocess.run(
        [ff, "-y", "-ss", f"{at_s:.3f}", "-i", str(video), "-frames:v", "1", str(jpg)],
        check=True,
        capture_output=True,
    )
    with Image.open(jpg) as img:
        metrics = measure_color_cast(np.asarray(img.convert("RGB")))
    jpg.unlink(missing_ok=True)
    return metrics


def main() -> int:
    import argparse
    import json
    from pathlib import Path

    ap = argparse.ArgumentParser(description="Color-cast QA probe (#218/#244)")
    ap.add_argument("--input", required=True, help="Image or video path")
    ap.add_argument("--shot", default=None, help="Shot id label for report")
    ap.add_argument("--generation-gate", action="store_true", help="Use pre-render reference thresholds")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    path = Path(args.input)
    if not path.is_file():
        print(f"!! not found: {path}")
        return 2
    if path.suffix.lower() in (".mp4", ".mov", ".webm", ".mkv"):
        metrics = probe_video_midframe(path)
    else:
        from PIL import Image

        metrics = measure_color_cast(np.asarray(Image.open(path).convert("RGB")))
    if args.generation_gate:
        breaches = generation_reference_breaches(metrics, host=True)
        ok = not breaches
    else:
        breaches = color_cast_breaches(metrics)
        ok = not breaches
    report = {
        "input": str(path),
        "shot": args.shot,
        **summarize_color_cast(metrics),
        "generation_reference_passes": generation_reference_passes(metrics, host=True),
        "breaches": breaches,
        "verdict": "PASS" if ok else "FAIL",
    }
    if args.json:
        print(json.dumps(report, indent=2))
    else:
        print(f"[{report['verdict']}] {path.name}" + (f" shot={args.shot}" if args.shot else ""))
        print(f"  Bμ={metrics['host_blue_mean']:.1f}  B/R={metrics['host_br_ratio']:.3f}  "
              f"rgb_skew={metrics['rgb_skew']:.4f}  starve={metrics['blue_starvation_fraction']:.3f}")
        if breaches:
            print(f"  breaches: {breaches}")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())