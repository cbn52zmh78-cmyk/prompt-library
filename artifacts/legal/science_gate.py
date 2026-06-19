#!/usr/bin/env python3
"""Science Gate — illustrative-not-simulation spine for Gate 0 (issue #154).

Applies when brief/content references science visualization or scientific claims.

Rules:
  - illustrative-not-simulation disclosure required
  - cited source required for scientific assertions
  - flag overclaims: accurate simulation, real data, ground-truth measurements, etc.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

SCIENCE_TRIGGER = re.compile(
    r"science\s+visualization|scientific\s+visualization|science\s+content|science\s+gate|"
    r"molecular\s+visualization|astrophysics|physics\s+simulation|data\s+visualization|"
    r"science\s+episode|scientific\s+claim",
    re.I,
)
ILLUSTRATIVE_DISCLOSURE_PATTERN = re.compile(
    r"illustrative\s+not\s+simulation|illustrative-only|illustrative\s+disclosure|"
    r"not\s+a\s+simulation|not\s+real\s+data|educational\s+illustration|"
    r"artistic\s+interpretation|schematic\s+illustration|conceptual\s+visualization",
    re.I,
)
SCIENCE_SOURCE_PATTERN = re.compile(
    r"\bsources\s*:|cited\s+source|source\s*:|peer[- ]reviewed|doi\s*:|arxiv|"
    r"nasa|esa|nature\s+\d{4}|science\s+\d{4}|published\s+in|dataset\s*:|"
    r"instrument\s*:|catalog\s+reference",
    re.I,
)
NEGATED_GUARD_PREFIX = re.compile(r"\bno[\s-]|non[\s-]|not[\s-]|zero[\s-]|without[\s-]", re.I)

OVERCLAIM_PATTERNS: list[tuple[str, str]] = [
    (r"\baccurate\s+simulation\b", "Overclaim: 'accurate simulation' — requires instrument-backed data proof"),
    (r"\bscientifically\s+accurate\s+simulation\b", "Overclaim: 'scientifically accurate simulation'"),
    (r"\breal\s+data\b", "Overclaim: 'real data' — verify instrument source and license"),
    (r"\bactual\s+measurements?\b", "Overclaim: 'actual measurement(s)' — verify cited instrument run"),
    (r"\bground[- ]truth\s+data\b", "Overclaim: 'ground-truth data' — simulation cannot claim ground truth without dataset citation"),
    (r"\bobservational\s+data\s+shown\b", "Overclaim: implies observational data on screen without source"),
    (r"\bverified\s+by\s+experiment\b", "Overclaim: experimental verification claim requires peer-reviewed citation"),
]


@dataclass
class ScienceGateResult:
    applies: bool = False
    hard_stops: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)
    overclaims: list[str] = field(default_factory=list)
    status: str = "N/A"  # N/A | PASS | CAUTION | BLOCKED

    def to_dict(self) -> dict:
        return {
            "applies": self.applies,
            "status": self.status,
            "hard_stops": self.hard_stops,
            "warnings": self.warnings,
            "notes": self.notes,
            "overclaims": self.overclaims,
        }


def _is_science_content(text: str) -> bool:
    return bool(SCIENCE_TRIGGER.search(text))


def _affirmed_pattern_match(pattern: str, text: str) -> bool:
    for match in re.finditer(pattern, text, re.I):
        prefix = text[max(0, match.start() - 16) : match.start()]
        if NEGATED_GUARD_PREFIX.search(prefix):
            continue
        return True
    return False


def _has_illustrative_disclosure(text: str) -> bool:
    return bool(ILLUSTRATIVE_DISCLOSURE_PATTERN.search(text))


def _has_cited_source(text: str) -> bool:
    return bool(SCIENCE_SOURCE_PATTERN.search(text))


def _detect_overclaims(text: str) -> list[str]:
    hits: list[str] = []
    for pattern, msg in OVERCLAIM_PATTERNS:
        if _affirmed_pattern_match(pattern, text):
            hits.append(f"[SCIENCE] {msg}")
    return hits


def evaluate_science_gate(text: str) -> ScienceGateResult:
    """Evaluate Science Gate. No-op when content is not science-scoped."""
    if not _is_science_content(text):
        return ScienceGateResult(applies=False, status="N/A")

    result = ScienceGateResult(applies=True)
    result.notes.append("Science Gate: illustrative-not-simulation policy applies.")

    if not _has_illustrative_disclosure(text):
        result.warnings.append(
            "[SCIENCE] illustrative-not-simulation disclosure required — "
            "state visuals are educational illustration, not simulation output"
        )

    if not _has_cited_source(text):
        result.warnings.append(
            "[SCIENCE] cited source required — name peer-reviewed paper, catalog, or instrument dataset"
        )

    result.overclaims = _detect_overclaims(text)
    result.warnings.extend(result.overclaims)

    if result.hard_stops:
        result.status = "BLOCKED"
    elif result.warnings:
        result.status = "CAUTION"
    else:
        result.status = "PASS"
        result.notes.append("Science Gate: disclosure + source present; no simulation overclaims flagged.")

    return result