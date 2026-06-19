"""Tests for seamless shot duration pre-clamp policy (#177)."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
PIPELINE = ROOT / "STUDIO" / "Pipeline"
sys.path.insert(0, str(PIPELINE))

from shot_duration import (  # noqa: E402
    apply_duration_clamp_to_shots,
    av_sync_drift_label,
    clamp_shot_duration,
    check_shot_duration_band,
    effective_shot_duration,
    should_clamp_shot_durations,
)

INTAKE = PIPELINE / "production_intake.py"
SCIENCE_CONCEPT = PIPELINE / "Concepts" / "science" / "julian_why_sky_blue_60s.concept.json"


def test_clamp_shot_duration_bounds():
    assert clamp_shot_duration(10) == 9
    assert clamp_shot_duration(6) == 7
    assert clamp_shot_duration(8) == 8


def test_apply_duration_clamp_recomputes_timeline():
    shots = [
        {"id": "01_hook", "duration": 7},
        {"id": "04_visualization_payoff", "duration": 10},
        {"id": "05_significance", "duration": 9},
    ]
    clamped, meta = apply_duration_clamp_to_shots(shots)
    assert meta["shots_clamped"] == 1
    assert clamped[1]["duration"] == 9
    assert clamped[1].get("duration_raw") == 10
    assert clamped[0]["t_start"] == 0
    assert clamped[0]["t_end"] == 7
    assert clamped[1]["t_start"] == 7
    assert clamped[1]["t_end"] == 16
    assert clamped[2]["t_start"] == 16
    assert clamped[2]["t_end"] == 25


def test_seamless_chain_gate():
    assert should_clamp_shot_durations({"primary": "extend"}) is True
    assert should_clamp_shot_durations({"primary": "hard_cut"}) is False


def test_av_sync_drift_uses_effective_duration():
    shot = {"id": "04_visualization_payoff", "duration": 9}
    assert av_sync_drift_label(shot, 9.05, seamless=True) is None
    assert av_sync_drift_label(shot, 10.0, seamless=True) == "04_visualization_payoff:1.000s"


def test_duration_band_passes_when_pre_clamped():
    shot = {"id": "02_phenomenon", "duration": 9}
    assert check_shot_duration_band(shot, seamless=True) is None


def test_duration_band_fails_out_of_band():
    shot = {"id": "04_visualization_payoff", "duration": 10}
    issue = check_shot_duration_band(shot, seamless=True)
    assert issue is not None
    assert "outside 7–9s" in issue


def test_science_explainer_intake_clamps_viz_shot():
    if not SCIENCE_CONCEPT.is_file():
        pytest.skip("sky blue concept missing")
    out = ROOT / "DAVID" / "scripts" / "longform_scripts" / "_test_clamp_sky_blue_script.json"
    proc = subprocess.run(
        [sys.executable, str(INTAKE), str(SCIENCE_CONCEPT), "-o", str(out)],
        cwd=str(ROOT),
        capture_output=True,
        text=True,
    )
    assert proc.returncode in (0, 3), proc.stdout + proc.stderr
    script = json.loads(out.read_text(encoding="utf-8"))
    viz = next(s for s in script["shots"] if s["id"] == "04_visualization_payoff")
    assert viz["duration"] == 9
    assert viz.get("duration_raw") == 10
    assert script["intake"].get("duration_clamp", {}).get("applied") is True
    out.unlink(missing_ok=True)


def test_effective_shot_duration_idempotent():
    shot = {"id": "01_hook", "duration": 9}
    assert effective_shot_duration(shot, seamless=True) == 9
    assert effective_shot_duration(shot, seamless=False) == 9