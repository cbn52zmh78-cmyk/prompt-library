#!/usr/bin/env python3
"""Gate 0 v1.1 validation — three canonical test projects."""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from lib.bootstrap import ensure_paths

ensure_paths()

from legal_gate import LegalGate  # noqa: E402

TESTS = [
    {
        "id": "TEST_GREEN_Clean",
        "rating": "PG-13",
        "channels": ["social"],
        "text": (
            "16:9 narrative scene. Synthetic performer AikoGFE-001 from Casting Bible "
            "(synthetic: true, real_person_likeness: false). 24-year-old Japanese-American "
            "woman, agency_ready. Original score only; music cleared, cue sheet on file. "
            "AI disclosure planned: in-video label + platform description per Upon Tyne policy. "
            "SFW wardrobe. No real-person likeness."
        ),
        "expected_verdict": "GREEN",
    },
    {
        "id": "TEST_RED_Music",
        "rating": "PG-13",
        "channels": ["client"],
        "text": (
            "Client deliverable hero cut. Brand campaign 30s. Soundtrack: uncleared Taylor Swift "
            "track, no sync license, temp music only, no master use clearance. "
            "Work-for-hire deliverable to agency."
        ),
        "expected_verdict": "RED",
    },
    {
        "id": "TEST_COUNSEL_Likeness",
        "rating": "PG-13",
        "channels": ["festival"],
        "text": (
            "Festival submission cut. Lead uses living person celebrity likeness face and voice "
            "portrait, seeking replica of identifiable actor. 27-year-old synthetic stand-in "
            "discussed with counsel."
        ),
        "expected_verdict": "COUNSEL",
    },
]


def main() -> int:
    gate = LegalGate()
    failures = 0
    for t in TESTS:
        result = gate.review(
            t["text"],
            t["id"],
            target_rating=t["rating"],
            channels=t["channels"],
        )
        ok = result.verdict == t["expected_verdict"]
        if not ok:
            failures += 1
        print(f"\n{'='*60}")
        print(f"Project: {t['id']}")
        print(f"Expected: {t['expected_verdict']} | Actual: {result.verdict} | {'PASS' if ok else 'FAIL'}")
        print(f"hard_stops: {result.hard_stops}")
        print(f"counsel_flags: {result.counsel_flags}")
        print(f"distribution_flags: {result.distribution_flags}")
        print(f"warnings: {result.warnings}")
        if hasattr(result, "checklist_domains"):
            print(f"checklist_domains: {json.dumps(result.checklist_domains, indent=2)}")
    print(f"\n{'='*60}")
    print(f"Failures: {failures}/{len(TESTS)}")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())