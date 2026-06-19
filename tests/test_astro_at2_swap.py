"""ACTORS #157 — @2 plug-and-play on fixed black-hole scaffold."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SCAFFOLD = ROOT / "STUDIO" / "Pipeline" / "scaffolds" / "black_hole_at2_swap_scaffold.json"
BUILDER = ROOT / "STUDIO" / "Pipeline" / "build_astro_at2_swap.py"
PLATE_LIBRARY = ROOT / "Science" / "reference_plates" / "science_plate_library_v1.json"
RENDER = ROOT / "DAVID" / "scripts" / "render_longform.py"


def test_scaffold_exists_and_locked():
    assert SCAFFOLD.is_file()
    data = json.loads(SCAFFOLD.read_text(encoding="utf-8"))
    assert data["scaffold_id"] == "black_hole_at2_swap_v1"
    assert data["swap_slot"] == "@2"
    assert len(data["shots"]) == 2
    viz = next(s for s in data["shots"] if s["id"] == "02_at2_viz_payoff")
    assert viz["reference_slots"] == {"@2": "visualization"}
    assert "see attached render" in viz["video_prompt"]


def test_plate_library_has_astro_swaps():
    lib = json.loads(PLATE_LIBRARY.read_text(encoding="utf-8"))
    slugs = {p["slug"] for p in lib["plates"] if p["domain"] == "astro"}
    for slug in ("black-hole", "neutron-star", "nebula", "galaxy"):
        assert slug in slugs


def test_builder_script_only_neutron_star():
    proc = subprocess.run(
        [
            sys.executable,
            str(BUILDER),
            "--plates",
            "neutron-star",
            "--build-only",
            "--skip-plates",
        ],
        cwd=str(ROOT),
        capture_output=True,
        text=True,
    )
    assert proc.returncode == 0, proc.stdout + proc.stderr
    slug = "actors_157_at2_swap_neutron-star_480p_v1"
    script_path = ROOT / "DAVID" / "scripts" / "longform_scripts" / f"{slug}_script.json"
    assert script_path.is_file(), proc.stdout + proc.stderr
    script = json.loads(script_path.read_text(encoding="utf-8"))
    assert script["production_meta"]["plate_slug"] == "neutron-star"
    assert script["production_meta"]["swap_slot"] == "@2"
    viz = next(s for s in script["shots"] if s["id"] == "02_at2_viz_payoff")
    assert viz["reference_slots"]["@2"] == "visualization"
    scaffold = json.loads(SCAFFOLD.read_text(encoding="utf-8"))
    assert script["shots"][0]["video_prompt"] == scaffold["shots"][0]["video_prompt"]
    assert script["shots"][1]["video_prompt"] == scaffold["shots"][1]["video_prompt"]


def test_render_longform_script_only_swap():
    slug = "actors_157_at2_swap_neutron-star_480p_v1"
    script_path = ROOT / "DAVID" / "scripts" / "longform_scripts" / f"{slug}_script.json"
    if not script_path.is_file():
        pytest.skip("run test_builder_script_only_neutron_star first")
    proc = subprocess.run(
        [sys.executable, str(RENDER), str(script_path), "--script-only"],
        cwd=str(ROOT),
        capture_output=True,
        text=True,
    )
    assert proc.returncode == 0, proc.stdout + proc.stderr