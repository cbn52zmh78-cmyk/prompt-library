#!/usr/bin/env python3
"""Historical Figure Gate #147 — three canonical test cases wired through Gate 0."""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from lib.bootstrap import ensure_paths

ensure_paths()

from legal_gate import LegalGate  # noqa: E402

# Shared Gate 0 boilerplate — avoids unrelated YELLOW from performer-age / channel checks
_BASE = (
    "Channels: social, streaming\n"
    "Rating target: PG\n"
    "Casting Bible synthetic: true, real_person_likeness: false.\n"
    "AI disclosure planned in provenance card and platform metadata.\n"
    "Music plan: original score only — music cleared, cue sheet on file.\n"
)

TESTS = [
    {
        "id": "TEST_HISTFIG_PRE1900_GREEN",
        "expected_verdict": "GREEN",
        "expected_histfig_status": "PASS",
        "text": (
            _BASE
            + "Historical figure: Marcus Aurelius\n"
            + "death_year: 180\n"
            + "Reconstruction disclosure: AI-rendered likeness is speculative reconstruction "
            + "from Roman busts and coin portraits — not a photographic likeness.\n"
            + "Sources: Cassius Dio; British Museum bust BM 1863; scholarly consensus Antonine era.\n"
            + "Dignity: SFW scholarly portrayal only; no explicit content; no humiliation or anachronistic caricature.\n"
        ),
    },
    {
        "id": "TEST_HISTFIG_UNDER100_BLOCKED",
        "expected_verdict": "RED",
        "expected_histfig_status": "BLOCKED",
        "text": (
            _BASE
            + "Historical figure: John F. Kennedy\n"
            + "death_year: 1963\n"
            + "Reconstruction disclosure: AI-rendered likeness is speculative reconstruction "
            + "from archival photographs — not a photographic likeness.\n"
            + "Sources: JFK Presidential Library public domain materials.\n"
            + "Dignity: SFW scholarly documentary portrayal only; no explicit content.\n"
        ),
    },
    {
        "id": "TEST_HISTFIG_POST1900_BLOCKED",
        "expected_verdict": "RED",
        "expected_histfig_status": "BLOCKED",
        "text": (
            _BASE
            + "Historical figure: Vladimir Lenin\n"
            + "death_year: 1924\n"
            + "Reconstruction disclosure: AI-rendered likeness is speculative reconstruction "
            + "from archival photographs and sculptures — not a photographic likeness.\n"
            + "Sources: Soviet state archives public domain; Wikipedia CC BY-SA attribution.\n"
            + "Dignity: SFW scholarly portrayal only; no explicit content; no humiliation.\n"
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
        hist = result.historical_figure_gate
        verdict_ok = result.verdict == t["expected_verdict"]
        hist_ok = hist.get("status") == t["expected_histfig_status"]
        ok = verdict_ok and hist_ok
        if not ok:
            failures += 1

        print(f"\n{'=' * 60}")
        print(f"Project: {t['id']}")
        print(
            f"Expected: {t['expected_verdict']} / histfig={t['expected_histfig_status']} | "
            f"Actual: {result.verdict} / histfig={hist.get('status')} | "
            f"{'PASS' if ok else 'FAIL'}"
        )
        print(f"death_year: {hist.get('death_year')}")
        print(f"histfig hard_stops: {hist.get('hard_stops')}")
        print(f"histfig warnings: {hist.get('warnings')}")
        if not verdict_ok:
            print(f"gate hard_stops: {result.hard_stops}")
            print(f"gate warnings: {result.warnings}")

    print(f"\n{'=' * 60}")
    print(f"Failures: {failures}/{len(TESTS)}")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())