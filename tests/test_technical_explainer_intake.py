"""Round-trip: technical-explainer concept → intake → render_longform --script-only."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
PIPELINE = ROOT / "STUDIO" / "Pipeline"
INTAKE = PIPELINE / "production_intake.py"
RENDER = ROOT / "DAVID" / "scripts" / "render_longform.py"
CONCEPT = PIPELINE / "Concepts" / "technical" / "elijah_heat_pump_valve_60s.concept.json"
TEMPLATE = PIPELINE / "Concepts" / "templates" / "technical-explainer.concept.template.json"
SCRIPTS_OUT = ROOT / "DAVID" / "scripts" / "longform_scripts"


def test_template_exists():
    assert TEMPLATE.is_file()
    raw = json.loads(TEMPLATE.read_text(encoding="utf-8"))
    assert raw["format_id"] == "technical-explainer"
    assert "technical_subject" in raw
    assert raw["brand"]["title"] == "Blueprint"


def test_heat_pump_round_trip():
    if not CONCEPT.is_file():
        pytest.skip("heat pump concept missing")
    out = SCRIPTS_OUT / "elijah_heat_pump_valve_60s_script.json"
    proc = subprocess.run(
        [sys.executable, str(INTAKE), str(CONCEPT), "-o", str(out)],
        cwd=str(ROOT),
        capture_output=True,
        text=True,
    )
    assert proc.returncode in (0, 3), proc.stdout + proc.stderr
    assert out.is_file(), proc.stdout + proc.stderr
    script = json.loads(out.read_text(encoding="utf-8"))

    assert script["format_id"] == "technical-explainer"
    ts = script["intake"]["technical_subject"]
    assert ts["subject_id"] == "heat_pump_reversing_valve"
    assert ts["domain"] == "Mechanical Systems — HVAC"
    assert ts["system"] == "Heat pump reversing valve"
    assert len(ts["sources"]) == 3

    shot_ids = [s["id"] for s in script["shots"]]
    assert shot_ids == [
        "01_hook",
        "02_mechanism",
        "03_how_we_know",
        "04_diagram_payoff",
        "05_significance",
    ]

    diagram = next(s for s in script["shots"] if s["id"] == "04_diagram_payoff")
    assert diagram["duration"] == 9
    assert diagram.get("duration_raw") == 10
    assert script["intake"].get("duration_clamp", {}).get("applied") is True
    assert diagram["on_screen_labels"] == ["EXPLODED VIEW", "ILLUSTRATIVE", "NOT TO SCALE"]
    assert diagram["reference_slots"] == {"@2": "diagram"}
    assert diagram.get("technical_subject_ref") == "heat_pump_reversing_valve"
    assert "reversing valve" in diagram.get("diagram_prompt", "").lower()

    assert script["config"].get("use_identity_lock") is False
    assert "identity_lock" not in script["config"]
    assert script["config"]["seamless"]["lamp_lock"] is False

    prov = script["provenance_card"]
    assert prov["enabled"] is True
    assert prov.get("card_type") == "sources"
    assert "heat pump" in prov["title"].lower() or "reversing" in prov["title"].lower()
    assert prov.get("sources")

    render_proc = subprocess.run(
        [sys.executable, str(RENDER), str(out), "--script-only"],
        cwd=str(ROOT),
        capture_output=True,
        text=True,
    )
    assert render_proc.returncode == 0, render_proc.stdout + render_proc.stderr


def test_missing_technical_subject_raises():
    sys.path.insert(0, str(PIPELINE))
    from production_intake import build_longform_script, load_libraries  # noqa: WPS433

    with pytest.raises(ValueError, match="technical_subject"):
        build_longform_script(
            {"slug": "bad_technical", "format_id": "technical-explainer"},
            load_libraries(),
        )


def test_select_format_technical_explainer():
    sys.path.insert(0, str(PIPELINE))
    from production_intake import concept_selector, load_libraries  # noqa: WPS433

    libs = load_libraries()
    fmt = concept_selector(
        {
            "slug": "x",
            "title": "Heat pump reversing valve exploded view mechanism",
            "tags": ["technical explainer", "HVAC", "blueprint"],
        },
        libs,
    )
    assert fmt == "technical-explainer"