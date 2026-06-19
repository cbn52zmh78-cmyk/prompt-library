"""ACTORS #196 — next-12 History figure plates from R6 harvest."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
BUILDER = ROOT / "STUDIO" / "Pipeline" / "build_figure_next12_plates.py"
R6 = ROOT / "History" / "reference_plates" / "figure_reference_manifest.json"
REGISTRY = ROOT / "History" / "Historical_Figures_Bible" / "registry" / "v1_next_12.json"
NOTES = ROOT / "History" / "Historical_Figures_Bible" / "registry" / "actors_196_fidelity_review.json"

NEXT_12 = (
    "marcus-aurelius",
    "henry-ii",
    "thomas-becket",
    "alexander-the-great",
    "tutankhamun",
    "qin-shi-huang",
    "montezuma-ii",
    "william-the-conqueror",
    "saladin",
    "murasaki-shikibu",
    "hypatia-alexandria",
    "augustus",
)


def test_r6_harvest_has_next_12():
    data = json.loads(R6.read_text(encoding="utf-8"))
    harvested = {e["slug"] for e in data.get("entries", []) if e.get("harvest_status") == "OK"}
    for slug in NEXT_12:
        assert slug in harvested


def test_builder_exists():
    assert BUILDER.is_file()


@pytest.mark.parametrize("slug", NEXT_12)
def test_plate_locked_after_196(slug: str):
    root = ROOT / "History" / "figures" / slug / "01_reconstruction_plates"
    full = root / "reconstruction_turnaround_v1.jpg"
    head = root / "head_turnaround_v1.jpg"
    full_meta = full.with_suffix(".json")
    head_meta = head.with_suffix(".json")
    if not full_meta.is_file():
        pytest.skip("run build_figure_next12_plates.py first")
    fm = json.loads(full_meta.read_text(encoding="utf-8"))
    hm = json.loads(head_meta.read_text(encoding="utf-8"))
    assert fm["status"] == "PLATE_LOCKED"
    assert hm["status"] == "PLATE_LOCKED"
    assert fm["render_safe"] is True
    assert hm["render_safe"] is True
    assert fm["background"] == "#FFFFFF"
    assert fm["fidelity_review"]["pass"] is True
    assert hm["fidelity_review"]["pass"] is True
    harvest = ROOT / fm["harvest_image"].replace("/", "\\") if "\\" in str(ROOT) else ROOT / fm["harvest_image"]
    assert full.read_bytes() != harvest.read_bytes()
    death = fm.get("death_year")
    if death is not None:
        assert death <= 1900


def test_fidelity_notes_all_pass():
    if not NOTES.is_file():
        pytest.skip("run build_figure_next12_plates.py first")
    notes = json.loads(NOTES.read_text(encoding="utf-8"))
    assert notes["all_pass"] is True
    assert notes["figure_count"] == 12
    assert notes["plate_count"] == 24