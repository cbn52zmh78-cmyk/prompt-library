#!/usr/bin/env python3
"""Science Gate #154 — three canonical test cases wired through Gate 0."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from lib.bootstrap import ensure_paths

ensure_paths()

from legal_gate import LegalGate  # noqa: E402

_BASE = (
    "Channels: social, streaming\n"
    "Rating target: PG\n"
    "Casting Bible synthetic: true, real_person_likeness: false.\n"
    "AI disclosure planned in provenance card and platform metadata.\n"
    "Music plan: original score only — music cleared, cue sheet on file.\n"
)

TESTS = [
    {
        "id": "TEST_SCIENCE_ILLUSTRATIVE_GREEN",
        "expected_verdict": "GREEN",
        "expected_science_status": "PASS",
        "text": (
            _BASE
            + "Science visualization: PD-L1 protein binding schematic\n"
            + "Illustrative disclosure: educational illustration only — illustrative not simulation; "
            + "not real data from live instruments.\n"
            + "Sources: Nature 2020; PDB 1YZ8; peer-reviewed structural biology review.\n"
        ),
    },
    {
        "id": "TEST_SCIENCE_MISSING_DISCLOSURE_YELLOW",
        "expected_verdict": "YELLOW",
        "expected_science_status": "CAUTION",
        "text": (
            _BASE
            + "Science content: molecular visualization of ATP synthase rotation\n"
            + "Sources: Science 2016; doi:10.1126/science.aaf6324\n"
        ),
    },
    {
        "id": "TEST_SCIENCE_OVERCLAIM_YELLOW",
        "expected_verdict": "YELLOW",
        "expected_science_status": "CAUTION",
        "text": (
            _BASE
            + "Science visualization: black hole accretion disk\n"
            + "Illustrative disclosure: educational illustration only — illustrative not simulation.\n"
            + "Sources: NASA Chandra public domain gallery.\n"
            + "This segment shows an accurate simulation from real data captured by the Event Horizon Telescope.\n"
        ),
    },
]


def main() -> int:
    gate = LegalGate()
    failures = 0

    for t in TESTS:
        result = gate.review(
            t["text"],
            t["id"],
            target_rating="PG",
            channels=["social", "streaming"],
            has_performers=False,
        )
        sci = result.science_gate
        verdict_ok = result.verdict == t["expected_verdict"]
        sci_ok = sci.get("status") == t["expected_science_status"]
        ok = verdict_ok and sci_ok
        if not ok:
            failures += 1

        print(f"\n{'=' * 60}")
        print(f"Project: {t['id']}")
        print(
            f"Expected: {t['expected_verdict']} / science={t['expected_science_status']} | "
            f"Actual: {result.verdict} / science={sci.get('status')} | "
            f"{'PASS' if ok else 'FAIL'}"
        )
        print(f"science overclaims: {sci.get('overclaims')}")
        print(f"science warnings: {sci.get('warnings')}")
        if not verdict_ok:
            print(f"gate hard_stops: {result.hard_stops}")
            print(f"gate warnings: {result.warnings}")

    print(f"\n{'=' * 60}")
    print(f"Failures: {failures}/{len(TESTS)}")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())