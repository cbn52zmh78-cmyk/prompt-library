#!/usr/bin/env python3
"""Gate 0 row 2 — clearance_manifest.json music bed validation."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from lib.bootstrap import ensure_paths

ensure_paths()

from legal_gate import LegalGate  # noqa: E402

PASS_TEXT = (
    "Client deliverable hero cut. Brand campaign 30s. "
    "Music bed: BED-DOC-001 — Archive Room cleared per STUDIO/Music_Sound/clearance_manifest.json "
    "(owned, no attribution required). Work-for-hire deliverable to agency."
)

UNLISTED_TEXT = (
    "Client deliverable hero cut. Music bed: BED-FAKE-999 for hero underscore. "
    "Work-for-hire deliverable to agency."
)

UNCLEARED_TEXT = (
    "Client deliverable hero cut. Soundtrack: uncleared Taylor Swift track, "
    "no sync license, temp music only. Work-for-hire deliverable."
)


def test_manifest_track_row2_pass() -> None:
    gate = LegalGate()
    result = gate.review(
        PASS_TEXT,
        "TEST_ROW2_MANIFEST_PASS",
        target_rating="PG-13",
        channels=["client"],
    )
    assert result.verdict != "RED", result.hard_stops
    assert result.checklist_domains["row_2_music_sync"] == "PASS", result.checklist_domains
    assert not any("Unlisted" in h for h in result.hard_stops)


def test_unlisted_track_row2_fail() -> None:
    gate = LegalGate()
    result = gate.review(
        UNLISTED_TEXT,
        "TEST_ROW2_UNLISTED",
        target_rating="PG-13",
        channels=["client"],
    )
    assert result.verdict == "RED", result.verdict
    assert result.checklist_domains["row_2_music_sync"] == "FAIL"
    assert any("Unlisted" in h for h in result.hard_stops)


def test_uncleared_chart_still_red() -> None:
    gate = LegalGate()
    result = gate.review(
        UNCLEARED_TEXT,
        "TEST_ROW2_UNCLEARED_CHART",
        target_rating="PG-13",
        channels=["client"],
    )
    assert result.verdict == "RED"
    assert result.checklist_domains["row_2_music_sync"] == "FAIL"
    assert any("[MUSIC]" in h for h in result.hard_stops)


def main() -> int:
    test_manifest_track_row2_pass()
    test_unlisted_track_row2_fail()
    test_uncleared_chart_still_red()
    print("PASS: manifest track BED-DOC-001 → row_2 PASS")
    print("PASS: unlisted BED-FAKE-999 → row_2 FAIL + RED")
    print("PASS: uncleared chart music → row_2 FAIL + RED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())