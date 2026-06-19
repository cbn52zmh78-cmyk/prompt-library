"""ACTORS #241 — GroundTruth bible visual/design spec (no render)."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
BUILDER = ROOT / "STUDIO" / "Pipeline" / "build_groundtruth_bible_visual_spec.py"
SPEC = (
    ROOT
    / "STUDIO"
    / "Reference_Library"
    / "style_bibles"
    / "GroundTruth_Bible_Visual_Design_Spec_v1.json"
)
NOTES = SPEC.parent / "actors_241_fidelity_review.json"

WEDGE_STATUSES = (
    "FOUND",
    "EXEMPT",
    "REQUIRES_CONFIRMATION",
    "NOT FOUND",
    "ACCESS_RESTRICTED",
    "SAMPLE",
)


def test_builder_exists():
    assert BUILDER.is_file()


def test_spec_exists_and_locked():
    spec = json.loads(SPEC.read_text(encoding="utf-8"))
    assert spec["artifact"] == "groundtruth_bible_visual_design_spec"
    assert spec["issue"] == 241
    assert spec["status"] == "SPEC_LOCKED"
    assert spec["render"] is False
    assert spec["principle"] == "credible_academic_house_style"


def test_status_taxonomy_matches_sot():
    spec = json.loads(SPEC.read_text(encoding="utf-8"))
    assert spec["status_taxonomy"]["values"] == list(WEDGE_STATUSES)
    for status in WEDGE_STATUSES:
        assert status in spec["status_taxonomy"]["meanings"]


@pytest.mark.parametrize(
    "token",
    [
        "heading_h1",
        "heading_h2",
        "inline_cite",
        "disclosure_ink",
        "status_not_found",
        "gate_pass",
    ],
)
def test_color_tokens_hex(token: str):
    spec = json.loads(SPEC.read_text(encoding="utf-8"))
    value = spec["tokens"]["color"][token]
    assert value.startswith("#") and len(value) == 7


def test_vertical_variants_and_citation_systems():
    spec = json.loads(SPEC.read_text(encoding="utf-8"))
    assert set(spec["vertical_variants"]) == {
        "compliance_sot",
        "science_synthesis",
        "figure_bible",
    }
    assert spec["vertical_variants"]["compliance_sot"]["citation_system"] == "STD-CITE-001"
    assert spec["vertical_variants"]["science_synthesis"]["citation_system"] == "APA7_INLINE"
    assert "render_in_this_issue" in spec["prohibitions"]


def test_implementation_anchors_on_disk():
    spec = json.loads(SPEC.read_text(encoding="utf-8"))
    for rel in spec["implementation_anchors"]:
        assert (ROOT / rel).is_file(), rel


def test_builder_validates_clean():
    proc = subprocess.run(
        [sys.executable, str(BUILDER)],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode == 0, proc.stdout + proc.stderr


def test_fidelity_review_pass():
    if not NOTES.is_file():
        pytest.skip("run build_groundtruth_bible_visual_spec.py first")
    notes = json.loads(NOTES.read_text(encoding="utf-8"))
    assert notes["pass"] is True
    assert notes["render"] is False
    assert notes["issue"] == 241
    assert notes["checks"]["no_render_flag"] is True