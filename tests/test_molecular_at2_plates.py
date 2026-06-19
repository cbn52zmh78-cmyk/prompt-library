"""ACTORS #172 — molecular @2 plates from R2 harvest."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
BUILDER = ROOT / "STUDIO" / "Pipeline" / "build_molecular_at2_plates.py"
LIBRARY = ROOT / "Science" / "reference_plates" / "science_plate_library_v1.json"
R2 = ROOT / "Science" / "reference_plates" / "molecular" / "molecular_reference_manifest.json"
NOTES = ROOT / "Science" / "reference_plates" / "molecular" / "actors_172_fidelity_review.json"

SLUGS = ("protein-hemoglobin", "dna-double-helix", "eukaryotic-cell")


def test_r2_harvest_has_three_targets():
    data = json.loads(R2.read_text(encoding="utf-8"))
    harvested = {s["slug"] for s in data["subjects"] if s["status"] == "HARVESTED"}
    for slug in SLUGS:
        assert slug in harvested


def test_builder_exists():
    assert BUILDER.is_file()


@pytest.mark.parametrize("slug,pdb", [
    ("protein-hemoglobin", "4HHB"),
    ("dna-double-helix", "1BNA"),
    ("eukaryotic-cell", None),
])
def test_plate_locked_after_172(slug: str, pdb: str | None):
    lib = json.loads(LIBRARY.read_text(encoding="utf-8"))
    plate = next(p for p in lib["plates"] if p["slug"] == slug)
    ref = ROOT / plate["plate_spec"]["reference_file"]
    meta = ref.with_suffix(".json")
    if not meta.is_file():
        pytest.skip("run build_molecular_at2_plates.py first")
    m = json.loads(meta.read_text(encoding="utf-8"))
    assert m["status"] == "PLATE_LOCKED"
    assert m["fidelity_review"]["pass"] is True
    if pdb:
        assert m.get("pdb_id") == pdb
    assert ref.read_bytes() != (ROOT / m["harvest_image"]).read_bytes()


def test_fidelity_notes_all_pass():
    if not NOTES.is_file():
        pytest.skip("run build_molecular_at2_plates.py first")
    notes = json.loads(NOTES.read_text(encoding="utf-8"))
    assert notes["all_pass"] is True
    assert len(notes["plates"]) == 3