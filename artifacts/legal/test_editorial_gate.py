#!/usr/bin/env python3
"""Editorial Gate #212 — canonical rail cases (standalone or via pytest)."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from editorial_gate import evaluate_editorial_gate  # noqa: E402

_CLEAN = (
    "# The Salt Road — Chapter One\n\n"
    "Genre: literary fiction. Work-for-hire: client owns all rights; chain of title on file.\n"
    "Originality confirmed — written from scratch, originality scan pass.\n\n"
    "## Scene 1\nThe caravan crossed the dunes at dawn.\n\n"
    "## Scene 2\nBy dusk the wells were dry.\n\n"
    "Sources: author interviews; field notes 2025.\n"
)

DELIVERABLE = {"client_deliverable": True, "genre": "literary fiction"}


def test_clean_manuscript_is_green():
    r = evaluate_editorial_gate(_CLEAN, DELIVERABLE)
    assert r.applies and r.verdict == "GREEN" and r.status == "PASS"
    assert not r.blocked and not r.requires_human_signoff
    assert all(v == "PASS" for v in r.checklist.values()), r.checklist


def test_non_editorial_is_noop():
    r = evaluate_editorial_gate("A weather report for Tuesday.", None)
    assert r.applies is False and r.status == "N/A"


def test_plagiarism_marker_is_red_blocked():
    text = _CLEAN + "\nNote: paragraph copied verbatim from another author.\n"
    r = evaluate_editorial_gate(text, DELIVERABLE)
    assert r.verdict == "RED" and r.blocked is True
    assert r.checklist["row_2_originality"] == "FAIL"
    assert any("ORIGINALITY" in h for h in r.hard_stops)


def test_unlicensed_third_party_is_red():
    text = _CLEAN + "\nLyrics reprinted without permission in the epigraph.\n"
    r = evaluate_editorial_gate(text, DELIVERABLE)
    assert r.verdict == "RED" and r.checklist["row_1_client_ip"] == "FAIL"


def test_missing_ip_attestation_is_yellow():
    text = (
        "# Untitled Memoir\n\nGenre: memoir.\n\n## Chapter 1\nI was born in spring.\n"
        "## Chapter 2\nThen came the war.\n"
    )
    r = evaluate_editorial_gate(text, {"client_deliverable": True, "genre": "memoir"})
    assert r.verdict == "YELLOW" and r.requires_human_signoff is True
    assert r.checklist["row_1_client_ip"] == "CAUTION"
    assert r.checklist["row_2_originality"] == "CAUTION"  # also no originality attestation


def test_coverage_overclaim_is_yellow():
    text = _CLEAN + "\nThis manuscript is a guaranteed bestseller and is 100% fact-checked.\n"
    r = evaluate_editorial_gate(text, DELIVERABLE)
    assert r.verdict == "YELLOW"
    assert r.checklist["row_3_honest_coverage"] == "CAUTION"
    assert any("COVERAGE" in w for w in r.warnings)


def test_defamation_unhedged_flags_counsel():
    text = _CLEAN + "\nThe mayor, Gerald Thompson, is a fraud who embezzled the pension fund.\n"
    r = evaluate_editorial_gate(text, DELIVERABLE)
    assert r.checklist["row_4_no_defamation"] == "CAUTION"
    assert r.counsel_flags and any("DEFAMATION" in w for w in r.warnings)


def test_defamation_hedged_is_clear():
    text = _CLEAN + "\nProsecutors allege that Gerald Thompson embezzled the pension fund.\n"
    r = evaluate_editorial_gate(text, DELIVERABLE)
    assert r.checklist["row_4_no_defamation"] == "PASS"


def test_placeholder_left_is_yellow():
    text = _CLEAN + "\nTKTK finish this section.\n"
    r = evaluate_editorial_gate(text, DELIVERABLE)
    assert r.checklist["row_2_originality"] == "CAUTION"


def test_missing_genre_is_yellow():
    text = (
        "# A Story\n\nWork-for-hire: client owns all rights. Originality confirmed.\n\n"
        "## One\nA.\n## Two\nB.\n"
    )
    r = evaluate_editorial_gate(text, {"client_deliverable": True})
    assert r.checklist["row_7_genre"] == "CAUTION"


def _run() -> int:
    tests = [v for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)]
    failures = 0
    for fn in tests:
        try:
            fn()
            print(f"PASS  {fn.__name__}")
        except Exception as exc:  # noqa: BLE001
            failures += 1
            print(f"FAIL  {fn.__name__}: {exc}")
    print(f"\n{len(tests) - failures}/{len(tests)} passed")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(_run())
