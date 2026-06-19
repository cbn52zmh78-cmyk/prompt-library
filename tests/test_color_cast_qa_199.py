"""#199 — clinical_channel_balance fails the +66 false-pass proof frames."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pytest
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
sys_path = ROOT / "DAVID" / "scripts"
import sys

if str(sys_path) not in sys.path:
    sys.path.insert(0, str(sys_path))

import color_cast_qa as cc  # noqa: E402
from c4_frame_proof_qa import grey_balance  # noqa: E402

PROOF_ROOTS = [
    ROOT / "STUDIO/Productions/Editorial/science_black_hole_anatomy_v1_longform_v1/frame_proof",
    ROOT / "STUDIO/Productions/Editorial/science_star_lifecycle_v1_longform_v1/frame_proof",
    ROOT / "STUDIO/Productions/Editorial/science_galaxy_formation_v1_longform_v1/frame_proof",
]
LATIN_BEFORE = ROOT / "DAVID/productions/david_latin_corpus_v1_longform_v1/proof_194/before/before_01_cold_open_mid.jpg"
METRIC_REPORT = ROOT / "STUDIO/Pipeline/color_cast_metric_T4_199.json"


def _load_frames() -> list[Path]:
    frames: list[Path] = []
    for d in PROOF_ROOTS:
        if d.is_dir():
            frames.extend(sorted(d.glob("frame_*.jpg")))
    return frames


def _false_pass_cohort(frames: list[Path]) -> list[tuple[Path, dict]]:
    cohort = []
    for fp in frames:
        arr = np.asarray(Image.open(fp).convert("RGB"))
        yg = cc.yellow_green_fraction(arr)
        gb = grey_balance(arr)
        if cc.legacy_false_pass_cohort(yg, gb):
            cohort.append((fp, cc.evaluate_clinical_cast(arr)))
    return cohort


def test_plus_66_cohort_exists():
    frames = _load_frames()
    cohort = _false_pass_cohort(frames)
    assert len(cohort) >= 66, f"expected ≥66 legacy false-pass frames, got {len(cohort)}"


def test_new_metric_fails_all_66_false_pass_frames():
    frames = _load_frames()
    cohort = _false_pass_cohort(frames)
    failed = [fp for fp, ev in cohort if ev["pass"]]
    assert not failed, f"new metric should fail all 66; still passing: {len(failed)}"


def test_legacy_yg_passed_false_cohort_mean():
    frames = _load_frames()
    cohort = _false_pass_cohort(frames)
    ygs = [ev["yellow_green"] for _, ev in cohort]
    assert max(ygs) <= cc.YELLOW_GREEN_SCORE_MAX


def test_latin_before_blue_starvation_detected():
    if not LATIN_BEFORE.is_file():
        pytest.skip("proof_194 before frame missing")
    arr = np.asarray(Image.open(LATIN_BEFORE).convert("RGB"))
    ev = cc.evaluate_clinical_cast(arr)
    assert ev["blue_starvation"] is True
    assert ev["b_mean"] < 12


def test_metric_report_written():
    frames = _load_frames()
    cohort = _false_pass_cohort(frames)
    report = {
        "issue": 199,
        "metric": "clinical_channel_balance",
        "threshold": cc.CLINICAL_CHANNEL_BALANCE_MAX,
        "legacy_false_pass_count": len(cohort),
        "new_metric_fail_count": sum(1 for _, ev in cohort if not ev["pass"]),
        "sample": [
            {"frame": fp.name, "parent": fp.parent.name, **ev}
            for fp, ev in cohort[:3]
        ],
    }
    METRIC_REPORT.parent.mkdir(parents=True, exist_ok=True)
    METRIC_REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
    assert report["new_metric_fail_count"] == len(cohort)
    assert report["new_metric_fail_count"] >= 66