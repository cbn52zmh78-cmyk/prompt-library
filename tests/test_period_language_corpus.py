"""DAVID #149 — period-language corpus integrity (attested lines + IPA, no invented quotes)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
LANG_ROOT = ROOT / "DAVID" / "languages" / "extinct"

CORPORA = {
    "anglo-norman": LANG_ROOT / "anglo-norman" / "corpus" / "known_texts.json",
    "tudor-english": LANG_ROOT / "tudor-english" / "corpus" / "known_texts.json",
}

FIGURE_LINKS = {
    "anglo-norman": {"richard-i", "eleanor-of-aquitaine"},
    "tudor-english": {"elizabeth-i"},
}


@pytest.mark.parametrize("language,path", list(CORPORA.items()))
def test_corpus_file_exists(language: str, path: Path) -> None:
    assert path.is_file(), f"missing corpus for {language}"


@pytest.mark.parametrize("language,path", list(CORPORA.items()))
def test_attested_entries_have_ipa(language: str, path: Path) -> None:
    data = json.loads(path.read_text(encoding="utf-8"))
    assert data["language"] == language
    speakable = [t for t in data["texts"] if t.get("type") != "meta"]
    assert speakable, "corpus needs at least one speakable entry"
    for entry in speakable:
        assert entry.get("confidence") == "attested", entry["id"]
        assert entry.get("transliteration"), entry["id"]
        assert entry.get("line_ipa", "").startswith("["), entry["id"]
        assert entry.get("source"), entry["id"]


@pytest.mark.parametrize("language,path", list(CORPORA.items()))
def test_figure_history_links(language: str, path: Path) -> None:
    data = json.loads(path.read_text(encoding="utf-8"))
    linked: set[str] = set()
    for entry in data["texts"]:
        linked.update(entry.get("history_links") or [])
    expected = FIGURE_LINKS[language]
    assert expected <= linked, f"missing figure links {expected - linked}"


def test_eleanor_corpus_has_no_invented_quote_attribution() -> None:
    data = json.loads(CORPORA["anglo-norman"].read_text(encoding="utf-8"))
    for entry in data["texts"]:
        if "eleanor-of-aquitaine" in (entry.get("history_links") or []):
            notes = (entry.get("notes") or "").lower()
            if entry.get("type") != "meta":
                assert "not eleanor" in notes or "not" in notes, entry["id"]


def test_elizabeth_proof_script_matches_corpus() -> None:
    script_path = (
        ROOT / "DAVID" / "scripts" / "longform_scripts" / "david_elizabeth_tudor_proof_v1_script.json"
    )
    assert script_path.is_file()
    script = json.loads(script_path.read_text(encoding="utf-8"))
    corpus = json.loads(CORPORA["tudor-english"].read_text(encoding="utf-8"))
    entry = next(t for t in corpus["texts"] if t["id"] == script["corpus"]["corpus_id"])
    assert script["corpus"]["attested_text"] == entry["transliteration"]
    assert script["corpus"]["line_ipa"] == entry["line_ipa"]