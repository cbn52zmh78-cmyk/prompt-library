#!/usr/bin/env python3
"""Historical Figure Gate — safety spine for Gate 0 (issue #147).

Applies when brief/content references a historical figure subject.

Rules:
  - death_year missing → RED hard stop
  - death_year within 100-year recency floor → RED hard stop
  - death_year post-1900 (and outside recency floor) → YELLOW caution
  - reconstruction disclosure required
  - sourced claims required
  - dignity / no-NSFW required (NSFW cues → RED)
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import datetime

RECENCY_YEARS = 100
POST_1900_CAUTION_YEAR = 1900

HISTORICAL_FIGURE_TRIGGER = re.compile(
    r"historical\s+figure|historical_figure|death_year\s*[:=]|figure\s+subject\s*:",
    re.I,
)
DEATH_YEAR_PATTERN = re.compile(r"death_year\s*[:=]\s*(-?\d{1,4})\b", re.I)
RECONSTRUCTION_DISCLOSURE_PATTERN = re.compile(
    r"reconstruction\s+disclosure|speculative\s+reconstruction|ai[- ]rendered\s+likeness|"
    r"not\s+(a\s+)?photographic\s+likeness|likeness\s+is\s+speculative",
    re.I,
)
SOURCED_CLAIMS_PATTERN = re.compile(
    r"\bsources\s*:|sourced\s+claims|primary\s+source|scholarly\s+source|citation\s*:|"
    r"attributed\s+to\s+\w|wikisource|british\s+museum|archive",
    re.I,
)
DIGNITY_SFW_PATTERN = re.compile(
    r"dignity\s*:|sfw\s+scholarly|scholarly\s+portrayal|no\s+explicit|no\s+humiliation|"
    r"adult\s+scholarly|documentary\s+dignity",
    re.I,
)
NEGATED_GUARD_PREFIX = re.compile(r"\bno[\s-]|non[\s-]|zero[\s-]|without[\s-]", re.I)
DIGNITY_NSFW_VIOLATION_PATTERNS: list[tuple[str, str]] = [
    (r"\b(nude|naked|topless|nsfw|erotic|sexual|porn|humiliat(e|ion)|degrad(e|ing))\b.*\b(historical|figure|portrait|subject)\b", "NSFW or humiliating historical portrayal"),
    (r"\b(historical|figure|portrait|subject)\b.*\b(nude|naked|topless|nsfw|erotic|sexual|porn|humiliat(e|ion)|degrad(e|ing))\b", "NSFW or humiliating historical portrayal"),
]


@dataclass
class HistoricalFigureGateResult:
    applies: bool = False
    death_year: int | None = None
    hard_stops: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)
    status: str = "N/A"  # N/A | PASS | CAUTION | BLOCKED

    def to_dict(self) -> dict:
        return {
            "applies": self.applies,
            "death_year": self.death_year,
            "status": self.status,
            "hard_stops": self.hard_stops,
            "warnings": self.warnings,
            "notes": self.notes,
            "recency_floor_year": _recency_floor_year(),
            "post_1900_caution": (
                self.death_year is not None and self.death_year > POST_1900_CAUTION_YEAR
            ),
        }


def _current_year() -> int:
    return datetime.now().year


def _recency_floor_year() -> int:
    return _current_year() - RECENCY_YEARS


def _is_historical_figure_content(text: str) -> bool:
    return bool(HISTORICAL_FIGURE_TRIGGER.search(text))


def _parse_death_year(text: str) -> int | None:
    match = DEATH_YEAR_PATTERN.search(text)
    if not match:
        return None
    return int(match.group(1))


def _has_reconstruction_disclosure(text: str) -> bool:
    return bool(RECONSTRUCTION_DISCLOSURE_PATTERN.search(text))


def _has_sourced_claims(text: str) -> bool:
    return bool(SOURCED_CLAIMS_PATTERN.search(text))


def _has_dignity_sfw(text: str) -> bool:
    return bool(DIGNITY_SFW_PATTERN.search(text))


def _affirmed_pattern_match(pattern: str, text: str) -> bool:
    for match in re.finditer(pattern, text, re.I):
        prefix = text[max(0, match.start() - 12) : match.start()]
        if NEGATED_GUARD_PREFIX.search(prefix):
            continue
        return True
    return False


def _dignity_nsfw_violations(text: str) -> list[str]:
    lower = text.lower()
    hits: list[str] = []
    for pattern, msg in DIGNITY_NSFW_VIOLATION_PATTERNS:
        if _affirmed_pattern_match(pattern, lower):
            hits.append(msg)
    if not _has_dignity_sfw(text) and _affirmed_pattern_match(
        r"\b(nsfw|nude|erotic|sexual|humiliat)\b", lower
    ):
        hits.append("NSFW or undignified historical content without explicit SFW dignity guard")
    return hits


def evaluate_historical_figure_gate(
    text: str,
    *,
    current_year: int | None = None,
) -> HistoricalFigureGateResult:
    """Evaluate Historical Figure Gate safety spine. No-op when content is not figure-scoped."""
    if not _is_historical_figure_content(text):
        return HistoricalFigureGateResult(applies=False, status="N/A")

    year = current_year or _current_year()
    recency_floor = year - RECENCY_YEARS
    result = HistoricalFigureGateResult(applies=True)
    result.death_year = _parse_death_year(text)

    if result.death_year is None:
        result.hard_stops.append(
            "[HISTFIG] death_year missing — Historical Figure Gate requires documented death year"
        )
    elif result.death_year > recency_floor:
        result.hard_stops.append(
            f"[HISTFIG] death_year {result.death_year} within {RECENCY_YEARS}-year recency floor "
            f"(>{recency_floor}) — living-memory / estate risk; portrayal BLOCKED"
        )
    elif result.death_year > POST_1900_CAUTION_YEAR:
        result.warnings.append(
            f"[HISTFIG] death_year {result.death_year} post-1900 — living-memory caution; "
            "extra dignity review and counsel flags apply"
        )
        result.notes.append(
            f"Historical Figure Gate: post-1900 subject (died {result.death_year}); proceed YELLOW only."
        )
    else:
        result.notes.append(
            f"Historical Figure Gate: pre-1900 subject (died {result.death_year}); recency clear."
        )

    if not _has_reconstruction_disclosure(text):
        result.warnings.append(
            "[HISTFIG] reconstruction disclosure required — state likeness is speculative AI reconstruction"
        )

    if not _has_sourced_claims(text):
        result.warnings.append(
            "[HISTFIG] sourced claims required — cite primary or scholarly sources for historical assertions"
        )

    for msg in _dignity_nsfw_violations(text):
        result.hard_stops.append(f"[HISTFIG] {msg}")

    if not _has_dignity_sfw(text) and not result.hard_stops:
        result.warnings.append(
            "[HISTFIG] dignity guard required — affirm SFW scholarly portrayal (no NSFW, no humiliation)"
        )

    if result.hard_stops:
        result.status = "BLOCKED"
    elif result.warnings:
        result.status = "CAUTION"
    else:
        result.status = "PASS"

    return result