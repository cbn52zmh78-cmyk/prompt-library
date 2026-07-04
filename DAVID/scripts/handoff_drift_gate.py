#!/usr/bin/env python3
"""Temporal drift gate for branch-chain handoff stills (Grok 1.5 last-frame seeds).

AI temporal drift is cumulative degradation across chained i2v generations — not one
failure mode. This module classifies drift, scores the handoff JPG against a reference
(anchor plate or prior-good last frame), and recommends an adaptation before upload.

Drift categories
----------------
  color_grade     — rgb_skew / blue_deficit vs anchor (yellow, magenta, night)
  structural      — host-crop similarity vs anchor (face/torso geometry shift)
  feature_loss    — zone contrast drop for locked accessories (earrings, belt, tattoos)
  lip_clip        — mouth/chin too close to frame bottom (tail-frame crop risk)
  exposure        — host luminance delta vs anchor

Adaptation ladder (cheapest first)
----------------------------------
  pass              — upload handoff as-is
  sanitize_color    — ffmpeg still pull toward anchor (color only)
  prompt_reinforce  — inject drift-specific lock into next-branch prompt
  regen_prev        — structural/feature fail — regenerate previous branch
  fallback_seed     — use origin composite instead of poisoned chain frame

CLI
---
    python handoff_drift_gate.py \\
        --handoff productions/.../branch_frames/b05_last_frame.jpg \\
        --reference productions/.../branch_frames/b04_europe_last_frame.jpg \\
        --json
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Mapping, Sequence

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from color_cast_qa import (  # noqa: E402
    RGB_SKEW_MAX,
    blue_deficit_index,
    evaluate_clinical_cast,
    host_channel_means,
    host_region,
    measure_color_cast,
    rgb_skew_index,
)

# ---------------------------------------------------------------------------
# Thresholds — tuned for documentary-host clinical neutral (Matilda / DAVID)
# ---------------------------------------------------------------------------
COLOR_SKEW_DELTA_MAX = 0.08
BLUE_DEFICIT_DELTA_MAX = 0.10
LUM_DELTA_MAX = 28.0
STRUCTURAL_SSIM_MIN = 0.72
EAR_CONTRAST_DROP_MAX = 0.45
FEATURE_MIN_CONTRAST = 10.0
FEATURE_REF_RATIO_MIN = 0.55
LIP_CLIP_BOTTOM_MARGIN_MIN = 0.04
FEATURE_KEYWORDS = (
    ("earring", ("left_ear", "right_ear")),
    ("filigree", ("left_ear", "right_ear")),
    ("belt", ("belt_buckle",)),
    ("buckle", ("belt_buckle",)),
    ("tattoo", ("left_forearm", "right_forearm")),
    ("necklace", ("neckline",)),
)


@dataclass
class ContinuityFeature:
    zone: str
    label: str
    min_contrast: float = FEATURE_MIN_CONTRAST
    chain_ratio_min: float = FEATURE_REF_RATIO_MIN


@dataclass
class DriftFinding:
    category: str
    severity: str
    metric: float
    threshold: float
    detail: str
    adaptation: str


@dataclass
class DriftReport:
    handoff: str
    reference: str
    pass_: bool
    adaptation: str
    findings: list[DriftFinding] = field(default_factory=list)
    metrics: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["pass"] = self.pass_
        d.pop("pass_")
        return d


def _load_rgb(path: Path) -> np.ndarray:
    from PIL import Image

    with Image.open(path) as img:
        return np.asarray(img.convert("RGB"))


def _zone(arr: np.ndarray, *, x0: float, y0: float, x1: float, y1: float, step: int = 4) -> np.ndarray:
    h, w = arr.shape[:2]
    return arr[
        int(h * y0): int(h * y1): step,
        int(w * x0): int(w * x1): step,
    ]


def _zone_contrast(arr: np.ndarray) -> float:
    if arr.size == 0:
        return 0.0
    lum = 0.299 * arr[..., 0] + 0.587 * arr[..., 1] + 0.114 * arr[..., 2]
    return float(lum.std())


# Normalized cross-correlation on flattened host crops — cheap structural proxy.
def _structural_similarity(a: np.ndarray, b: np.ndarray) -> float:
    ha = host_region(a).astype(np.float64).reshape(-1)
    hb = host_region(b).astype(np.float64).reshape(-1)
    n = min(ha.size, hb.size)
    if n < 64:
        return 1.0
    ha, hb = ha[:n], hb[:n]
    ha -= ha.mean()
    hb -= hb.mean()
    denom = np.linalg.norm(ha) * np.linalg.norm(hb)
    if denom < 1e-6:
        return 1.0
    return float(max(0.0, min(1.0, (ha @ hb) / denom)))


def _probe_lip_clip(arr: np.ndarray) -> dict[str, float]:
    """Mouth/chin proximity to frame bottom — tail extraction often clips lips."""
    h, w = arr.shape[:2]
    mouth = _zone(arr, x0=0.28, y0=0.38, x1=0.58, y1=0.72)
    if mouth.size == 0:
        return {"bottom_margin": 1.0, "lip_clip_risk": 0.0}
    lum = 0.299 * mouth[..., 0] + 0.587 * mouth[..., 1] + 0.114 * mouth[..., 2]
    skinish = (lum > 60) & (lum < 220)
    rows = np.where(skinish.any(axis=1))[0]
    if rows.size == 0:
        return {"bottom_margin": 1.0, "lip_clip_risk": 0.0}
    mouth_bottom_frac = (int(h * 0.38) + int(rows.max())) / h
    bottom_margin = 1.0 - mouth_bottom_frac
    lip_clip_risk = max(0.0, (LIP_CLIP_BOTTOM_MARGIN_MIN - bottom_margin) / LIP_CLIP_BOTTOM_MARGIN_MIN)
    return {"bottom_margin": round(bottom_margin, 4), "lip_clip_risk": round(lip_clip_risk, 4)}


ZONE_MAP: dict[str, tuple[float, float, float, float]] = {
    "left_ear": (0.06, 0.18, 0.22, 0.42),
    "right_ear": (0.52, 0.18, 0.68, 0.42),
    "belt_buckle": (0.30, 0.58, 0.50, 0.72),
    "neckline": (0.28, 0.40, 0.52, 0.56),
    "left_forearm": (0.04, 0.48, 0.18, 0.72),
    "right_forearm": (0.58, 0.48, 0.72, 0.72),
}


def parse_continuity_features(
    branch_cfg: Mapping[str, Any] | None,
    *,
    wardrobe_lock: str = "",
) -> list[ContinuityFeature]:
    """Load explicit continuity_features from script; fallback to wardrobe_lock keywords."""
    cfg = branch_cfg or {}
    raw = cfg.get("continuity_features")
    out: list[ContinuityFeature] = []
    if isinstance(raw, list):
        for item in raw:
            if not isinstance(item, dict):
                continue
            zone = str(item.get("zone") or "").strip()
            label = str(item.get("label") or zone).strip()
            if not zone or zone not in ZONE_MAP:
                continue
            out.append(
                ContinuityFeature(
                    zone=zone,
                    label=label,
                    min_contrast=float(item.get("min_contrast") or FEATURE_MIN_CONTRAST),
                    chain_ratio_min=float(item.get("chain_ratio_min") or FEATURE_REF_RATIO_MIN),
                )
            )
    if out:
        return out
    zones = _zones_from_wardrobe_lock(wardrobe_lock)
    return [ContinuityFeature(zone=z, label=z.replace("_", " ")) for z in zones]


def _zones_from_wardrobe_lock(lock: str) -> list[str]:
    low = lock.lower()
    zones: list[str] = []
    for keyword, mapped in FEATURE_KEYWORDS:
        if keyword in low:
            for z in mapped:
                if z not in zones:
                    zones.append(z)
    return zones or ["left_ear", "right_ear", "belt_buckle"]


def _probe_feature_zones(
    handoff: np.ndarray,
    features: Sequence[ContinuityFeature],
    *,
    baseline: np.ndarray | None = None,
    regen_on_absence: bool = True,
) -> list[DriftFinding]:
    """Absolute feature presence + optional chain drift vs baseline (prev branch)."""
    findings: list[DriftFinding] = []
    for feat in features:
        box = ZONE_MAP.get(feat.zone)
        if not box:
            continue
        hc = _zone_contrast(_zone(handoff, x0=box[0], y0=box[1], x1=box[2], y1=box[3]))
        if hc < feat.min_contrast:
            findings.append(
                DriftFinding(
                    category="feature_loss",
                    severity="fail",
                    metric=round(hc, 2),
                    threshold=feat.min_contrast,
                    detail=f"{feat.zone}: {feat.label} missing (contrast={hc:.1f})",
                    adaptation="regen_prev" if regen_on_absence else "prompt_reinforce",
                )
            )
            continue
        if baseline is None:
            continue
        rc = _zone_contrast(_zone(baseline, x0=box[0], y0=box[1], x1=box[2], y1=box[3]))
        if rc < 8.0:
            continue
        ratio = hc / rc
        if ratio < feat.chain_ratio_min:
            findings.append(
                DriftFinding(
                    category="feature_loss",
                    severity="fail",
                    metric=round(ratio, 4),
                    threshold=feat.chain_ratio_min,
                    detail=f"{feat.zone}: {feat.label} faded to {ratio:.0%} of prior branch",
                    adaptation="regen_prev",
                )
            )
    return findings


def probe_handoff_drift(
    handoff_path: Path,
    color_reference_path: Path,
    *,
    wardrobe_lock: str = "",
    continuity_reference_path: Path | None = None,
    continuity_features: Sequence[ContinuityFeature] | None = None,
    branch_cfg: Mapping[str, Any] | None = None,
) -> DriftReport:
    """Score handoff still. Color vs grade anchor; chain drift vs prior branch frame."""
    handoff_path = Path(handoff_path)
    color_reference_path = Path(color_reference_path)
    hf = _load_rgb(handoff_path)
    rf = _load_rgb(color_reference_path)
    chain_ref = (
        _load_rgb(continuity_reference_path)
        if continuity_reference_path and Path(continuity_reference_path).is_file()
        else None
    )

    h_cast = evaluate_clinical_cast(hf)
    r_cast = evaluate_clinical_cast(rf)
    h_skew = h_cast["rgb_skew"]
    r_skew = r_cast["rgb_skew"]
    skew_delta = h_skew - r_skew
    h_bd = blue_deficit_index(hf)
    r_bd = blue_deficit_index(rf)
    bd_delta = h_bd - r_bd
    _, _, _, h_lum = host_channel_means(hf)
    _, _, _, r_lum = host_channel_means(rf)
    lum_delta = abs(h_lum - r_lum)
    structural = _structural_similarity(hf, chain_ref) if chain_ref is not None else 1.0
    lip = _probe_lip_clip(hf)

    findings: list[DriftFinding] = []

    if abs(skew_delta) > COLOR_SKEW_DELTA_MAX:
        findings.append(
            DriftFinding(
                category="color_grade",
                severity="fail" if abs(skew_delta) > COLOR_SKEW_DELTA_MAX * 1.5 else "warn",
                metric=round(skew_delta, 4),
                threshold=COLOR_SKEW_DELTA_MAX,
                detail=f"rgb_skew delta {skew_delta:+.3f} (handoff={h_skew:.3f} ref={r_skew:.3f})",
                adaptation="sanitize_color",
            )
        )
    if bd_delta > BLUE_DEFICIT_DELTA_MAX:
        findings.append(
            DriftFinding(
                category="color_grade",
                severity="fail",
                metric=round(bd_delta, 4),
                threshold=BLUE_DEFICIT_DELTA_MAX,
                detail=f"blue_deficit worsened +{bd_delta:.3f} — yellow/warm cast",
                adaptation="sanitize_color",
            )
        )
    if lum_delta > LUM_DELTA_MAX:
        findings.append(
            DriftFinding(
                category="exposure",
                severity="warn",
                metric=round(lum_delta, 2),
                threshold=LUM_DELTA_MAX,
                detail=f"host luminance delta {lum_delta:.1f} — day/night drift risk",
                adaptation="sanitize_color",
            )
        )
    if chain_ref is not None and structural < STRUCTURAL_SSIM_MIN:
        findings.append(
            DriftFinding(
                category="structural",
                severity="warn",
                metric=round(structural, 4),
                threshold=STRUCTURAL_SSIM_MIN,
                detail=f"host structural similarity {structural:.3f} vs prior branch",
                adaptation="prompt_reinforce",
            )
        )
    if lip["lip_clip_risk"] > 0.35:
        findings.append(
            DriftFinding(
                category="lip_clip",
                severity="fail",
                metric=lip["lip_clip_risk"],
                threshold=0.35,
                detail=f"mouth/chin margin {lip['bottom_margin']:.2%} — lip clip at tail",
                adaptation="regen_prev",
            )
        )
    elif lip["lip_clip_risk"] > 0.15:
        findings.append(
            DriftFinding(
                category="lip_clip",
                severity="warn",
                metric=lip["lip_clip_risk"],
                threshold=0.15,
                detail=f"tight chin margin {lip['bottom_margin']:.2%}",
                adaptation="prompt_reinforce",
            )
        )

    cfg = branch_cfg or {}
    features = list(continuity_features or parse_continuity_features(cfg, wardrobe_lock=wardrobe_lock))
    regen_on_absence = bool(cfg.get("handoff_drift_regen_on_feature_loss", True))
    findings.extend(
        _probe_feature_zones(
            hf, features, baseline=chain_ref, regen_on_absence=regen_on_absence,
        )
    )

    fails = [f for f in findings if f.severity == "fail"]
    adaptation = _recommend_adaptation(findings)

    return DriftReport(
        handoff=str(handoff_path),
        reference=str(color_reference_path),
        pass_=not fails,
        adaptation=adaptation,
        findings=findings,
        metrics={
            "handoff_cast": h_cast,
            "reference_cast": r_cast,
            "skew_delta": round(skew_delta, 4),
            "blue_deficit_delta": round(bd_delta, 4),
            "lum_delta": round(lum_delta, 2),
            "structural_similarity": round(structural, 4),
            "lip_clip": lip,
            "continuity_features": [asdict(f) for f in features],
        },
    )


def _recommend_adaptation(findings: list[DriftFinding]) -> str:
    if not findings:
        return "pass"
    severity_order = ("regen_prev", "fallback_seed", "sanitize_color", "prompt_reinforce", "pass")
    adaptations = {f.adaptation for f in findings if f.severity in ("fail", "warn")}
    for action in severity_order:
        if action in adaptations:
            return action
    return "pass"


def needs_prev_regen(report: DriftReport) -> bool:
    """True when previous branch should be regenerated before seeding next."""
    if report.adaptation == "regen_prev":
        return True
    return any(
        f.severity == "fail" and f.adaptation == "regen_prev"
        for f in report.findings
    )


def drift_prompt_clauses(
    report: DriftReport,
    features: Sequence[ContinuityFeature] | None = None,
) -> list[str]:
    """Prompt reinforcements derived from drift findings."""
    by_zone = {f.zone: f.label for f in (features or [])}
    clauses: list[str] = []
    for finding in report.findings:
        if finding.category == "feature_loss":
            label = by_zone.get(finding.detail.split(":")[0], finding.detail)
            if "CONTINUITY FEATURE LOCK" not in " ".join(clauses):
                for feat in features or []:
                    if feat.zone in finding.detail:
                        label = feat.label
                        break
            clauses.append(
                f"CONTINUITY FEATURE LOCK: {label} — must remain fully visible, "
                f"identical to prior branch, zero drift or omission"
            )
        elif finding.category == "lip_clip":
            clauses.append(
                "LIP FRAME LOCK: full mouth and chin visible in frame — not cropped at bottom edge"
            )
        elif finding.category == "color_grade":
            clauses.append(
                "COLOR LOCK: D65 5000K neutral WB — zero yellow amber wash, blue channel intact on skin"
            )
    seen: set[str] = set()
    unique: list[str] = []
    for c in clauses:
        key = c[:48]
        if key not in seen:
            seen.add(key)
            unique.append(c)
    return unique


def sanitize_handoff_color(handoff: Path, reference: Path, out: Path) -> Path:
    """Single-frame color pull toward anchor — still-safe ffmpeg histogram match."""
    from render_longform import _ffmpeg_exe, apply_living_room_skin_recovery  # noqa: E402

    out.parent.mkdir(parents=True, exist_ok=True)
    if handoff.suffix.lower() in (".jpg", ".jpeg", ".png", ".webp"):
        ff = _ffmpeg_exe()
        vfilter = "[0:v][1:v]histogrammatching=pattern=1:strength=0.35[outv]"
        subprocess.run(
            [
                ff, "-y", "-loop", "1", "-i", str(handoff),
                "-loop", "1", "-i", str(reference),
                "-filter_complex", vfilter,
                "-map", "[outv]", "-frames:v", "1", "-q:v", "2", "-update", "1",
                str(out),
            ],
            check=True,
            capture_output=True,
        )
        return out
    return apply_living_room_skin_recovery(handoff, out, reference, strength=0.45)


def log_drift_report(report: DriftReport, *, shot_id: str = "") -> None:
    tag = f"[drift-gate] {shot_id}" if shot_id else "[drift-gate]"
    status = "PASS" if report.pass_ else "FAIL"
    print(
        f"{tag} {status} adaptation={report.adaptation} "
        f"skew_Δ={report.metrics.get('skew_delta')} "
        f"blue_Δ={report.metrics.get('blue_deficit_delta')} "
        f"struct={report.metrics.get('structural_similarity')}",
        flush=True,
    )
    for f in report.findings:
        print(f"  [{f.severity}] {f.category}: {f.detail} → {f.adaptation}", flush=True)


def main() -> int:
    ap = argparse.ArgumentParser(description="Handoff temporal drift gate")
    ap.add_argument("--handoff", required=True, type=Path)
    ap.add_argument("--reference", required=True, type=Path, help="Color grade anchor")
    ap.add_argument(
        "--continuity", type=Path, default=None,
        help="Prior-branch frame for chain drift (optional)",
    )
    ap.add_argument("--wardrobe-lock", default="", help="Wardrobe lock text for feature zones")
    ap.add_argument(
        "--features-json", type=Path, default=None,
        help="JSON file with continuity_features array",
    )
    ap.add_argument("--sanitize", action="store_true", help="Write color-sanitized handoff to --out")
    ap.add_argument("--out", type=Path, default=None)
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    if not args.handoff.is_file():
        raise SystemExit(f"handoff not found: {args.handoff}")
    if not args.reference.is_file():
        raise SystemExit(f"reference not found: {args.reference}")

    branch_cfg: dict[str, Any] = {}
    features: list[ContinuityFeature] | None = None
    if args.features_json and args.features_json.is_file():
        branch_cfg = json.loads(args.features_json.read_text(encoding="utf-8"))
        features = parse_continuity_features(branch_cfg, wardrobe_lock=args.wardrobe_lock)
    report = probe_handoff_drift(
        args.handoff,
        args.reference,
        wardrobe_lock=args.wardrobe_lock,
        continuity_reference_path=args.continuity,
        continuity_features=features,
        branch_cfg=branch_cfg,
    )

    if args.sanitize and report.adaptation in ("sanitize_color", "prompt_reinforce", "regen_prev"):
        out = args.out or args.handoff.with_name(
            f"{args.handoff.stem}_sanitized{args.handoff.suffix}"
        )
        sanitize_handoff_color(args.handoff, args.reference, out)
        report.metrics["sanitized_path"] = str(out)

    if args.json:
        print(json.dumps(report.to_dict(), indent=2))
    else:
        log_drift_report(report, shot_id=args.handoff.stem)
    return 0 if report.pass_ else 1


if __name__ == "__main__":
    raise SystemExit(main())