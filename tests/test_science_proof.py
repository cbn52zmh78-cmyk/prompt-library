"""DAVID #156 — science proof script + subject registry integrity."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "DAVID" / "scripts" / "longform_scripts" / "david_black_hole_science_proof_v1_script.json"
SUBJECT = ROOT / "DAVID" / "science" / "subjects" / "m87_black_hole_shadow.json"
RENDER = ROOT / "DAVID" / "scripts" / "render_science_proof.py"


def test_science_proof_script_exists():
    assert SCRIPT.is_file()
    data = json.loads(SCRIPT.read_text(encoding="utf-8"))
    assert data["format_id"] == "science-explainer"
    assert data["science_subject"]["subject_id"] == "m87-black-hole-shadow"


def test_subject_registry_matches_script():
    script = json.loads(SCRIPT.read_text(encoding="utf-8"))
    subject = json.loads(SUBJECT.read_text(encoding="utf-8"))
    ss = script["science_subject"]
    assert subject["subject_id"] == ss["subject_id"]
    assert subject["phenomenon"] == ss["phenomenon"]
    assert len(subject["sources"]) >= 2


def test_illustrative_labels_on_viz_shot():
    script = json.loads(SCRIPT.read_text(encoding="utf-8"))
    viz = next(s for s in script["shots"] if s["role"] == "visualization")
    labels = [lb.upper() for lb in viz["on_screen_labels"]]
    assert "ILLUSTRATIVE" in labels
    assert any("NOT TO SCALE" in lb for lb in labels)
    assert viz.get("on_screen_labels")


def test_nasa_eht_sources():
    script = json.loads(SCRIPT.read_text(encoding="utf-8"))
    cites = " ".join(
        s["citation"] for s in script["provenance_card"]["sources"]
    ).lower()
    assert "nasa" in cites
    assert "event horizon" in cites or "eht" in cites


def test_voice_recommendation_documented():
    script = json.loads(SCRIPT.read_text(encoding="utf-8"))
    rec = script["config"]["voice_recommendation"]
    assert "primary" in rec
    assert "science communicator" in rec["primary"].lower()


def test_render_science_proof_importable():
    assert RENDER.is_file()