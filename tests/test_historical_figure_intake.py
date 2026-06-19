"""Round-trip: historical-figure-documentary concept → intake → render_longform --script-only."""

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
CONCEPT = PIPELINE / "Concepts" / "historical_figures" / "david_hypatia_60s.concept.json"
TEMPLATE = PIPELINE / "Concepts" / "templates" / "historical-figure-documentary.concept.template.json"
SCRIPTS_OUT = ROOT / "DAVID" / "scripts" / "longform_scripts"


def test_template_exists():
    assert TEMPLATE.is_file()
    raw = json.loads(TEMPLATE.read_text(encoding="utf-8"))
    assert raw["format_id"] == "historical-figure-documentary"
    assert "historical_figure" in raw


def test_hypatia_round_trip(tmp_path: Path):
    if not CONCEPT.is_file():
        pytest.skip("hypatia concept missing")
    out = SCRIPTS_OUT / "david_hypatia_60s_script.json"
    proc = subprocess.run(
        [sys.executable, str(INTAKE), str(CONCEPT), "-o", str(out)],
        cwd=str(ROOT),
        capture_output=True,
        text=True,
    )
    assert out.is_file(), proc.stdout + proc.stderr
    script = json.loads(out.read_text(encoding="utf-8"))

    assert script["format_id"] == "historical-figure-documentary"
    hf = script["intake"]["historical_figure"]
    assert hf["figure_id"] == "hypatia_alexandria"
    assert hf["death_year"] == 415
    assert hf["era"] == "Late Roman Alexandria / Neoplatonism"
    assert len(hf["sources"]) == 3

    shot_ids = [s["id"] for s in script["shots"]]
    assert shot_ids == [
        "01_cold_open",
        "02_who_they_were",
        "03_their_world",
        "04_period_line",
        "05_legacy",
    ]

    period = next(s for s in script["shots"] if s["id"] == "04_period_line")
    assert period["on_screen_labels"] == ["RECONSTRUCTED", "PERIOD LANGUAGE"]
    assert period.get("speech_lang") == "Ancient Greek"

    prov = script["provenance_card"]
    assert prov["enabled"] is True
    assert prov.get("card_type") == "sources"
    assert "Hypatia" in prov["title"]
    assert prov.get("sources")

    render_proc = subprocess.run(
        [sys.executable, str(RENDER), str(out), "--script-only"],
        cwd=str(ROOT),
        capture_output=True,
        text=True,
    )
    assert render_proc.returncode == 0, render_proc.stdout + render_proc.stderr


def test_missing_historical_figure_raises():
    sys.path.insert(0, str(PIPELINE))
    from production_intake import build_longform_script, load_libraries  # noqa: WPS433

    with pytest.raises(ValueError, match="historical_figure"):
        build_longform_script(
            {"slug": "bad_figure", "format_id": "historical-figure-documentary"},
            load_libraries(),
        )