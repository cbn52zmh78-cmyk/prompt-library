"""#194 T4 — blue-starvation color-cast QA metric."""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pytest
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
DAVID_SCRIPTS = ROOT / "DAVID" / "scripts"
if str(DAVID_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(DAVID_SCRIPTS))

from color_cast_qa import (  # noqa: E402
    color_cast_passes,
    measure_color_cast,
    summarize_color_cast,
)

PROOF_194 = ROOT / "DAVID" / "productions" / "david_latin_corpus_v1_longform_v1" / "proof_194"
ARCHIVE_REF = ROOT / "DAVID" / "productions" / "host_identity_v1" / "references" / "archive_set_reference.jpg"


def _load_rgb(path: Path) -> np.ndarray:
    return np.asarray(Image.open(path).convert("RGB"))


@pytest.mark.parametrize(
    "name",
    [
        "before_01_cold_open_mid.jpg",
        "before_05_method_mid.jpg",
        "before_07_demonstration_mid.jpg",
        "before_join_03_04_xfade.jpg",
        "after_01_cold_open_mid.jpg",
        "after_05_method_mid.jpg",
        "after_07_demonstration_mid.jpg",
        "after_join_03_04_xfade.jpg",
    ],
)
def test_proof_194_bad_frames_fail_color_cast(name: str):
    path = PROOF_194 / ("before" if name.startswith("before") else "after") / name
    if not path.is_file():
        pytest.skip(f"missing proof frame {path}")
    metrics = measure_color_cast(_load_rgb(path))
    summary = summarize_color_cast(metrics)
    assert not summary["pass"], f"{name} should fail: {summary}"
    assert metrics["host_blue_mean"] < 25
    assert metrics["host_br_ratio"] < 0.22


def test_proof_194_yellow_green_false_passes():
    """Legacy metric passes ~0.007 on visibly cast frames — documents the trap."""
    path = PROOF_194 / "before" / "before_01_cold_open_mid.jpg"
    if not path.is_file():
        pytest.skip("missing proof frame")
    arr = _load_rgb(path)
    h, w = arr.shape[:2]
    region = arr[int(h * 0.18):int(h * 0.72):6, int(w * 0.08):int(w * 0.48):6].astype(float)
    r, g, b = region[..., 0], region[..., 1], region[..., 2]
    lum = 0.299 * r + 0.587 * g + 0.114 * b
    valid = (lum >= 35) & (lum <= 210)
    yg = float(((g > r * 1.06) & (g > b * 1.04) & valid).sum()) / max(int(valid.sum()), 1)
    assert yg < 0.012
    assert not color_cast_passes(measure_color_cast(arr))


@pytest.mark.skipif(not ARCHIVE_REF.is_file(), reason="archive reference missing")
def test_archive_reference_passes_color_cast():
    metrics = measure_color_cast(_load_rgb(ARCHIVE_REF))
    assert color_cast_passes(metrics), summarize_color_cast(metrics)


def test_frame_proof_timeline_majority_fails():
    proof_dir = PROOF_194 / "before" / "frame_proof"
    if not proof_dir.is_dir():
        pytest.skip("run c4_frame_proof_qa on before master first")
    frames = sorted(proof_dir.glob("frame_*.jpg"))
    fails = sum(1 for f in frames if not color_cast_passes(measure_color_cast(_load_rgb(f))))
    assert fails >= 60, f"expected ~62/68 host frames to fail, got {fails}/{len(frames)}"