"""Chemistry / physics field routing at science-explainer intake (#179)."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
PIPELINE = ROOT / "STUDIO" / "Pipeline"
INTAKE = PIPELINE / "production_intake.py"
SCRIPTS_OUT = ROOT / "DAVID" / "scripts" / "longform_scripts"
RENDER = ROOT / "DAVID" / "scripts" / "render_longform.py"

CHEM_CONCEPT = PIPELINE / "Concepts" / "science" / "julian_covalent_bonding_60s.concept.json"
PHYS_CONCEPT = PIPELINE / "Concepts" / "science" / "julian_em_field_lines_60s.concept.json"


def _intake_round_trip(concept: Path, slug: str) -> dict:
    out = SCRIPTS_OUT / f"{slug}_script.json"
    proc = subprocess.run(
        [sys.executable, str(INTAKE), str(concept), "-o", str(out)],
        cwd=str(ROOT),
        capture_output=True,
        text=True,
    )
    assert proc.returncode in (0, 3), proc.stdout + proc.stderr
    script = json.loads(out.read_text(encoding="utf-8"))
    render_proc = subprocess.run(
        [sys.executable, str(RENDER), str(out), "--script-only"],
        cwd=str(ROOT),
        capture_output=True,
        text=True,
    )
    assert render_proc.returncode == 0, render_proc.stdout + render_proc.stderr
    return script


def test_chemistry_field_round_trip():
    if not CHEM_CONCEPT.is_file():
        pytest.skip("chemistry concept missing")
    script = _intake_round_trip(CHEM_CONCEPT, "julian_covalent_bonding_60s")
    ss = script["intake"]["science_subject"]
    assert ss["field"] == "chemistry"
    assert ss["principle_set"] == "jantzen_molecular_cellular"
    assert ss.get("plate_id") == "@Sci-ChemBond-001"
    assert ss.get("visualization_ref", "").startswith("Science/reference_plates/chemistry/")
    viz = next(s for s in script["shots"] if s["id"] == "04_visualization_payoff")
    assert viz["duration"] == 9
    assert script["config"].get("visualization_reference") == ss["visualization_ref"]
    assert script["production_meta"]["principle_set"] == "jantzen_molecular_cellular"


def test_physics_field_round_trip():
    if not PHYS_CONCEPT.is_file():
        pytest.skip("physics concept missing")
    script = _intake_round_trip(PHYS_CONCEPT, "julian_em_field_lines_60s")
    ss = script["intake"]["science_subject"]
    assert ss["field"] == "physics"
    assert ss["principle_set"] == "general_scientific"
    assert ss.get("plate_id") == "@Sci-EMField-001"
    assert "physics/images" in ss.get("visualization_ref", "")
    viz = next(s for s in script["shots"] if s["id"] == "04_visualization_payoff")
    assert viz["duration"] == 9
    assert script["production_meta"]["science_subject"]["field"] == "physics"


def test_science_field_module_unit():
    sys.path.insert(0, str(PIPELINE))
    from science_field import enrich_science_subject, normalize_field  # noqa: WPS433

    assert normalize_field("chemistry", domain="") == "chemistry"
    assert normalize_field(None, domain="Atmospheric physics") == "physics"
    out = enrich_science_subject({
        "subject_id": "covalent-bonding-water",
        "field": "chemistry",
        "domain": "Chemistry",
        "phenomenon": "Water bonding",
        "sources": [{"citation": "NIST WebBook"}],
    })
    assert out["visualization_ref"]
    assert out["principle_set"] == "jantzen_molecular_cellular"