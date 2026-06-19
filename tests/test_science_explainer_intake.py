"""Round-trip: science-explainer concept → intake → render_longform --script-only."""

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
CONCEPT = PIPELINE / "Concepts" / "science" / "julian_why_sky_blue_60s.concept.json"
TEMPLATE = PIPELINE / "Concepts" / "templates" / "science-explainer.concept.template.json"
SCRIPTS_OUT = ROOT / "DAVID" / "scripts" / "longform_scripts"


def test_template_exists():
    assert TEMPLATE.is_file()
    raw = json.loads(TEMPLATE.read_text(encoding="utf-8"))
    assert raw["format_id"] == "science-explainer"
    assert "science_subject" in raw


def test_sky_blue_round_trip():
    if not CONCEPT.is_file():
        pytest.skip("sky blue concept missing")
    out = SCRIPTS_OUT / "julian_why_sky_blue_60s_script.json"
    proc = subprocess.run(
        [sys.executable, str(INTAKE), str(CONCEPT), "-o", str(out)],
        cwd=str(ROOT),
        capture_output=True,
        text=True,
    )
    assert out.is_file(), proc.stdout + proc.stderr
    script = json.loads(out.read_text(encoding="utf-8"))

    assert script["format_id"] == "science-explainer"
    ss = script["intake"]["science_subject"]
    assert ss["subject_id"] == "rayleigh_scattering"
    assert ss["domain"] == "atmospheric physics"
    assert ss["phenomenon"] == "Why the sky appears blue"
    assert len(ss["sources"]) == 3

    shot_ids = [s["id"] for s in script["shots"]]
    assert shot_ids == [
        "01_hook",
        "02_phenomenon",
        "03_how_we_know",
        "04_visualization_payoff",
        "05_significance",
    ]

    viz = next(s for s in script["shots"] if s["id"] == "04_visualization_payoff")
    assert viz["duration"] == 9
    assert viz.get("duration_raw") == 10
    assert script["intake"].get("duration_clamp", {}).get("applied") is True
    assert viz["on_screen_labels"] == ["SCIENCE VISUALIZATION", "NOT TO SCALE"]
    assert viz["reference_slots"] == {"@2": "visualization"}
    assert viz.get("science_subject_ref") == "rayleigh_scattering"
    assert "Rayleigh" in viz.get("visualization_prompt", "")

    prov = script["provenance_card"]
    assert prov["enabled"] is True
    assert prov.get("card_type") == "sources"
    assert "sky" in prov["title"].lower() or "blue" in prov["title"].lower()
    assert prov.get("sources")

    render_proc = subprocess.run(
        [sys.executable, str(RENDER), str(out), "--script-only"],
        cwd=str(ROOT),
        capture_output=True,
        text=True,
    )
    assert render_proc.returncode == 0, render_proc.stdout + render_proc.stderr


def test_missing_science_subject_raises():
    sys.path.insert(0, str(PIPELINE))
    from production_intake import build_longform_script, load_libraries  # noqa: WPS433

    with pytest.raises(ValueError, match="science_subject"):
        build_longform_script(
            {"slug": "bad_science", "format_id": "science-explainer"},
            load_libraries(),
        )