"""DAVID #183 — B183 batch manifest armed, not fired."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "DAVID" / "batches" / "B183_benjamin_go" / "manifest.json"

DEAD_FIVE = {
    "david_ancient_greek_corpus_v1",
    "david_old_english_corpus_v1",
    "david_old_norse_corpus_v1",
    "david_gothic_corpus_v1",
    "david_sumerian_corpus_v1",
}
ROYAL_THREE = {
    "david_eleanor_aquitaine_v1",
    "david_richard_lionheart_v1",
    "david_elizabeth_tudor_v1",
}


def test_manifest_armed_not_fired():
    data = json.loads(MANIFEST.read_text(encoding="utf-8"))
    assert data["status"] == "ARMED"
    assert data["resolution"] == "720p"
    assert data["reference_ship"]["slug"] == "david_latin_corpus_v1"
    slugs = {i["slug"] for i in data["items"]}
    assert slugs == DEAD_FIVE | ROYAL_THREE
    assert "david_latin_corpus_v1" not in slugs


@pytest.mark.parametrize("slug", sorted(DEAD_FIVE | ROYAL_THREE))
def test_script_paths_exist(slug: str):
    data = json.loads(MANIFEST.read_text(encoding="utf-8"))
    item = next(i for i in data["items"] if i["slug"] == slug)
    assert (ROOT / item["script_path"]).is_file()


def test_go_command_documented():
    data = json.loads(MANIFEST.read_text(encoding="utf-8"))
    assert "--go" in data["go_command"]
    assert "fire_batch_manifest.py" in data["go_command"]