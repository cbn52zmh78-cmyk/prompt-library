"""Frame-level rgb_skew + join QA — proof_194 after must FAIL, neutral must PASS."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pytest
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "DAVID" / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from color_cast_qa import RGB_SKEW_MAX, yellow_green_fraction  # noqa: E402
from frame_level_color_seam_qa import (  # noqa: E402
    detect_join_issues,
    evaluate_still,
    verify_master,
)

PROOF_AFTER = ROOT / "DAVID/productions/david_latin_corpus_v1_longform_v1/proof_194/after"
AFTER_MASTER = PROOF_AFTER / "master_full_rerender_v2.mp4"
NEUTRAL_REF = ROOT / "STUDIO/Pipeline/references/seamless_neutral_grey_reference.jpg"
ARCHIVE_REF = ROOT / "DAVID/productions/host_identity_v1/references/archive_set_reference.jpg"
PROOF_REPORT = PROOF_AFTER / "frame_level_qa_proof.json"


@pytest.mark.parametrize(
    "name",
    [
        "after_01_cold_open_mid.jpg",
        "after_05_method_mid.jpg",
        "after_07_demonstration_mid.jpg",
        "after_join_03_04_xfade.jpg",
    ],
)
def test_proof_194_after_stills_fail_rgb_skew(name: str):
    path = PROOF_AFTER / name
    if not path.is_file():
        pytest.skip(f"missing {path}")
    ev = evaluate_still(path)
    assert ev["legacy_yg_pass"], f"legacy yg should false-pass: {ev['yellow_green']}"
    assert ev["rgb_skew"] > RGB_SKEW_MAX
    assert not ev["color_pass"]


def test_neutral_reference_passes_rgb_skew():
    if not NEUTRAL_REF.is_file():
        pytest.skip("neutral reference missing")
    ev = evaluate_still(NEUTRAL_REF)
    assert ev["rgb_skew"] <= RGB_SKEW_MAX
    assert ev["color_pass"]


@pytest.mark.skipif(not ARCHIVE_REF.is_file(), reason="archive reference missing")
def test_archive_reference_passes_rgb_skew():
    ev = evaluate_still(ARCHIVE_REF)
    assert ev["rgb_skew"] <= RGB_SKEW_MAX
    assert ev["color_pass"]


@pytest.mark.skipif(not AFTER_MASTER.is_file(), reason="proof_194 after master missing")
def test_proof_194_after_master_verdict_fail():
    result = verify_master(
        AFTER_MASTER,
        fps=2.0,
        proof_dir=PROOF_AFTER / "frame_proof",
    )
    assert result["verdict"] == "FAIL"
    assert result["measured"]["color_fail_frames"] >= 20
    assert result["measured"]["legacy_false_pass_frames"] >= 10
    assert result["measured"]["rgb_skew_max"] > RGB_SKEW_MAX
    assert result["measured"]["join_issues"] >= 1

    slim = {k: v for k, v in result.items() if k != "per_frame"}
    PROOF_REPORT.write_text(json.dumps(slim, indent=2), encoding="utf-8")
    assert PROOF_REPORT.is_file()


def test_join_detector_finds_spike_on_synthetic_hard_cut():
    a = np.full((64, 64, 3), 120, dtype=np.uint8)
    b = np.full((64, 64, 3), 20, dtype=np.uint8)
    issues = detect_join_issues([a, b], fps=1.0)
    assert any(j["kind"] == "hard_cut" for j in issues)