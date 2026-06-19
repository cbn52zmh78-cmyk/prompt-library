#!/usr/bin/env python3
"""Editorial Gate — compliance spine for the editorial engine (issue #212).

The sibling of science_gate.py / historical_figure_gate.py, but for *written*
client deliverables (manuscripts, editorial briefs, ghostwritten work, coverage).
It enforces, machine-checkable, the seven editorial rails:

    row_1_client_ip        client owns the IP (work-for-hire / rights assigned)
    row_2_originality      original work — no plagiarism / no placeholder shipped
    row_3_honest_coverage  coverage is honest — no inflated promises, claims sourced
    row_4_no_defamation    no unhedged derogatory factual claim about a real person
    row_5_format           document meets its declared format template
    row_6_structure        document is structured (sections/chapters/scenes/beats)
    row_7_genre            a genre / category is declared

Verdict maps onto the house Gate-0 stamp so the engine can gate exactly like the
video pipeline does:

    hard_stops      -> RED    (blocked=True)
    warnings/counsel -> YELLOW (requires_human_signoff=True)
    clean           -> GREEN

``meta`` supplies structured context the prose alone can't carry (is this a client
deliverable? declared genre/format? IP + originality attestations on file? sources
list?). A requirement is satisfied by EITHER the prose or the meta.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

# --------------------------------------------------------------------------- triggers
EDITORIAL_TRIGGER = re.compile(
    r"manuscript|editorial|ghostwrit|ghost-writ|screenplay|teleplay|novel|"
    r"\bprose\b|\bchapter\b|coverage\s+report|book\s+proposal|client\s+deliverable|"
    r"developmental\s+edit|copy\s*edit|line\s*edit|treatment|memoir",
    re.I,
)

# Hedges that defuse a defamation hit (claim is attributed / alleged, not asserted).
DEFAMATION_HEDGE = re.compile(
    r"alleg(e|es|ed|edly|ation)|reportedly|accus(e|es|ed)\s+of|according\s+to|"
    r"claims?\s+(that|to)|is\s+said\s+to|purportedly|denies|lawsuit\s+claims|"
    r"charged\s+with|indicted|prosecutors?\s+(say|allege)|in\s+court\s+filings|sources?\s+say",
    re.I,
)
# Derogatory factual assertions that carry defamation risk for a named real person.
DEFAMATION_TERMS = re.compile(
    r"\bis\s+a\s+(fraud|criminal|liar|crook|con\s+artist|fraudster|pedophile|racist|thief)\b|"
    r"\bembezzl|\bdefrauded\b|\bmolested\b|\braped\b|\bmurdered\b|"
    r"\bsecretly\s+(stole|laundered|bribed)\b|\bis\s+corrupt\b|"
    r"\bcommitted\s+(fraud|perjury|assault)\b",
    re.I,
)

IP_ASSERTION = re.compile(
    r"work[\s-]for[\s-]hire|client\s+owns|owns\s+all\s+rights|all\s+rights\s+(are\s+)?assigned|"
    r"assignment\s+of\s+(all\s+)?rights|rights\s+(are\s+)?transferred|chain\s+of\s+title|"
    r"copyright\s+(assigned|transfers?)\s+to\s+client|©\s*client|ip\s+transfer",
    re.I,
)
THIRD_PARTY_UNLICENSED = re.compile(
    r"(reprinted|excerpt|quoted|lyrics?|passage|photograph)[^.\n]{0,60}\b"
    r"(without\s+permission|unlicensed|no\s+permission|uncleared)\b",
    re.I,
)
ORIGINALITY_ASSERTION = re.compile(
    r"original\s+work|originality\s+(confirmed|attested|verified|scan)|no\s+plagiarism|"
    r"plagiarism[\s-]free|written\s+from\s+scratch|wholly\s+original|"
    r"originality\s+(check|report)\s+pass",
    re.I,
)
PLAGIARISM_HARD = re.compile(
    r"plagiari[sz]ed|copied\s+verbatim\s+from|lifted\s+from|uncredited\s+copy|"
    r"copy[\s-]paste(d)?\s+from\s+\w|\blorem\s+ipsum\b",
    re.I,
)
PLACEHOLDER_LEFT = re.compile(r"\bTKTK\b|\bTODO\b|\[INSERT[^\]]*\]|\bXXX\b|\bplaceholder\b", re.I)

COVERAGE_OVERCLAIM: list[tuple[str, str]] = [
    (r"guaranteed?\s+(best\s*seller|publication|deal|sales)", "inflated promise: guaranteed outcome"),
    (r"will\s+(definitely\s+)?be\s+a\s+best\s*seller", "inflated promise: guaranteed bestseller"),
    (r"100%\s+(fact[\s-]checked|accurate|original)", "absolute claim: 100% — cannot be machine-guaranteed"),
    (r"every\s+(claim|fact)\s+(is\s+)?verified", "completeness claim without per-claim sourcing"),
    (r"fully\s+fact[\s-]checked", "completeness claim — requires source list"),
    (r"flawless|impeccable\s+prose|perfect\s+manuscript", "quality overclaim in coverage"),
]
COMPLETENESS_CLAIM = re.compile(
    r"comprehensive\s+coverage|fully\s+researched|exhaustively\s+sourced|all\s+sources\s+verified",
    re.I,
)
SOURCE_PRESENT = re.compile(
    r"\bsources?\s*:|\bbibliograph|\breferences?\s*:|\bcitation|\bworks\s+cited|doi\s*:|\[\d+\]",
    re.I,
)

# Structural division markers across formats (markdown headers, chapters, scenes).
STRUCTURE_MARKER = re.compile(
    r"^#{1,6}\s+\S|^\s*chapter\s+\w+|^\s*(INT|EXT|EST)[\.\s/]|^\s*act\s+\w+|^\s*part\s+\w+|"
    r"^\s*scene\s+\d+|^\s*§",
    re.I | re.M,
)
GENRE_DECLARATION = re.compile(r"genre\s*:|category\s*:|format\s*:", re.I)

PROPER_NAME = re.compile(r"\b([A-Z][a-z]+\s+[A-Z][a-z]+)\b")


@dataclass
class EditorialGateResult:
    applies: bool = False
    verdict: str = "GREEN"  # GREEN | YELLOW | RED
    status: str = "N/A"  # N/A | PASS | CAUTION | BLOCKED
    blocked: bool = False
    requires_human_signoff: bool = False
    human_signoff: bool = False
    hard_stops: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    counsel_flags: list[str] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)
    checklist: dict[str, str] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "gate": "editorial",
            "applies": self.applies,
            "verdict": self.verdict,
            "status": self.status,
            "blocked": self.blocked,
            "requires_human_signoff": self.requires_human_signoff,
            "human_signoff": self.human_signoff,
            "hard_stops": self.hard_stops,
            "warnings": self.warnings,
            "counsel_flags": self.counsel_flags,
            "notes": self.notes,
            "checklist": self.checklist,
        }


def _truthy(value: Any) -> bool:
    if isinstance(value, str):
        return value.strip().lower() not in {"", "false", "no", "0", "none", "pending"}
    return bool(value)


def _is_editorial(text: str, meta: Optional[dict[str, Any]]) -> bool:
    if meta:
        return True
    return bool(EDITORIAL_TRIGGER.search(text))


# --------------------------------------------------------------------------- rows
def _row_client_ip(text: str, meta: dict[str, Any], res: EditorialGateResult) -> str:
    if THIRD_PARTY_UNLICENSED.search(text):
        res.hard_stops.append("[IP] third-party material used without permission/license — clear or remove before delivery")
        return "FAIL"
    deliverable = _truthy(meta.get("client_deliverable")) or bool(re.search(r"client\s+deliverable", text, re.I))
    asserted = _truthy(meta.get("ip_attestation")) or bool(IP_ASSERTION.search(text))
    if deliverable and not asserted:
        res.warnings.append("[IP] client-ownership not asserted — record work-for-hire / assignment of rights before delivery")
        return "CAUTION"
    if asserted:
        res.notes.append("[IP] client IP ownership asserted (work-for-hire / rights assigned).")
    return "PASS"


def _row_originality(text: str, meta: dict[str, Any], res: EditorialGateResult) -> str:
    if PLAGIARISM_HARD.search(text):
        res.hard_stops.append("[ORIGINALITY] plagiarism / verbatim copy marker present — cannot deliver")
        return "FAIL"
    status = "PASS"
    if PLACEHOLDER_LEFT.search(text):
        res.warnings.append("[ORIGINALITY] placeholder text (TKTK/TODO/[INSERT]/lorem ipsum) still in document")
        status = "CAUTION"
    deliverable = _truthy(meta.get("client_deliverable")) or bool(re.search(r"client\s+deliverable", text, re.I))
    asserted = _truthy(meta.get("originality_attestation")) or bool(ORIGINALITY_ASSERTION.search(text))
    if deliverable and not asserted:
        res.warnings.append("[ORIGINALITY] no originality attestation — run/record an originality check before delivery")
        status = "CAUTION"
    elif asserted:
        res.notes.append("[ORIGINALITY] originality attested.")
    return status


def _row_honest_coverage(text: str, meta: dict[str, Any], res: EditorialGateResult) -> str:
    status = "PASS"
    for pattern, msg in COVERAGE_OVERCLAIM:
        if re.search(pattern, text, re.I):
            res.warnings.append(f"[COVERAGE] {msg}")
            status = "CAUTION"
    has_sources = bool(meta.get("sources")) or bool(SOURCE_PRESENT.search(text))
    if COMPLETENESS_CLAIM.search(text) and not has_sources:
        res.warnings.append("[COVERAGE] completeness claim (comprehensive/fully researched) without a source list")
        status = "CAUTION"
    if status == "PASS":
        res.notes.append("[COVERAGE] no inflated promises; coverage reads as honest.")
    return status


def _row_no_defamation(text: str, meta: dict[str, Any], res: EditorialGateResult) -> str:
    status = "PASS"
    for match in DEFAMATION_TERMS.finditer(text):
        window = text[max(0, match.start() - 120): match.end() + 40]
        if DEFAMATION_HEDGE.search(window):
            continue  # attributed/alleged — not asserted as fact
        # Only a risk if it sits near a named (real-looking) person.
        if PROPER_NAME.search(window) or _truthy(meta.get("names_real_people")):
            snippet = re.sub(r"\s+", " ", match.group(0)).strip()
            res.warnings.append(f"[DEFAMATION] unhedged derogatory factual claim near a named person: '{snippet}' — verify or attribute")
            res.counsel_flags.append("Defamation review: derogatory factual claim about a real person")
            status = "CAUTION"
            break
    if status == "PASS":
        res.notes.append("[DEFAMATION] no unhedged derogatory factual claims about real persons detected.")
    return status


def _row_format(text: str, meta: dict[str, Any], res: EditorialGateResult) -> str:
    body = text.strip()
    if not body:
        res.hard_stops.append("[FORMAT] empty document")
        return "FAIL"
    status = "PASS"
    has_title = bool(re.search(r"^#\s+\S", text, re.M)) or _truthy(meta.get("title"))
    if not has_title:
        res.warnings.append("[FORMAT] no title / top-level heading found")
        status = "CAUTION"
    required = meta.get("required_sections") or []
    low = text.lower()
    missing = [s for s in required if s.lower() not in low]
    if missing:
        res.warnings.append(f"[FORMAT] missing required section(s): {', '.join(missing)}")
        status = "CAUTION"
    return status


def _row_structure(text: str, meta: dict[str, Any], res: EditorialGateResult) -> str:
    divisions = len(STRUCTURE_MARKER.findall(text))
    words = len(text.split())
    if words >= 1500 and divisions < 2:
        res.warnings.append(f"[STRUCTURE] long document ({words} words) with <2 structural divisions — add chapters/sections/scenes")
        return "CAUTION"
    if divisions == 0 and words >= 400:
        res.warnings.append("[STRUCTURE] no structural divisions detected")
        return "CAUTION"
    res.notes.append(f"[STRUCTURE] {divisions} structural division(s) over {words} words.")
    return "PASS"


def _row_genre(text: str, meta: dict[str, Any], res: EditorialGateResult) -> str:
    if _truthy(meta.get("genre")) or GENRE_DECLARATION.search(text):
        return "PASS"
    res.warnings.append("[GENRE] no genre / category declared — state the genre so format & tone checks can scope")
    return "CAUTION"


# --------------------------------------------------------------------------- evaluate
_ROWS = [
    ("row_1_client_ip", _row_client_ip),
    ("row_2_originality", _row_originality),
    ("row_3_honest_coverage", _row_honest_coverage),
    ("row_4_no_defamation", _row_no_defamation),
    ("row_5_format", _row_format),
    ("row_6_structure", _row_structure),
    ("row_7_genre", _row_genre),
]


def evaluate_editorial_gate(text: str, meta: Optional[dict[str, Any]] = None) -> EditorialGateResult:
    """Evaluate the Editorial Gate. No-op when content is not editorial-scoped."""
    text = text or ""
    if not _is_editorial(text, meta):
        return EditorialGateResult(applies=False, status="N/A")

    meta = meta or {}
    res = EditorialGateResult(applies=True)
    res.notes.append("Editorial Gate: client-deliverable editorial rails apply.")

    for row_key, row_fn in _ROWS:
        res.checklist[row_key] = row_fn(text, meta, res)

    if res.hard_stops:
        res.verdict, res.status, res.blocked = "RED", "BLOCKED", True
    elif res.warnings or res.counsel_flags:
        res.verdict, res.status, res.requires_human_signoff = "YELLOW", "CAUTION", True
    else:
        res.verdict, res.status = "GREEN", "PASS"
        res.notes.append("Editorial Gate: all seven rails clear.")

    res.human_signoff = _truthy(meta.get("human_signoff"))
    return res


# --------------------------------------------------------------------------- report sink
def save_editorial_report(
    gate: Any,
    project: str = "Untitled",
    *,
    source_text: str = "",
    stage: Optional[str] = None,
) -> Optional[dict[str, Path]]:
    """Route the Editorial Gate report to the shared ``Studio/Legal/Gate_Reports`` sink.

    Mirrors ``legal_gate.LegalGate.save_report`` so editorial forms auto-route exactly
    like every other lane: a ``GATE_<verdict>_<slug>_<stamp>_editorial.md`` lands in the
    shared sink, with a JSON companion in ``Producers_Office/Editorial_Gate``.

    ``gate`` may be an :class:`EditorialGateResult` or its ``to_dict()`` form. Returns
    ``{"md": Path, "json": Path}``, or ``None`` if the workspace path helpers are
    unavailable (e.g. the gate is exercised standalone in a bare checkout).
    """
    g = gate.to_dict() if hasattr(gate, "to_dict") else dict(gate)

    artifacts = Path(__file__).resolve().parents[1]  # .../artifacts
    import sys

    if str(artifacts) not in sys.path:
        sys.path.insert(0, str(artifacts))
    try:
        from lib.bootstrap import ensure_paths

        ensure_paths()
        from lib.studio_paths import producers_path, studio_path
    except Exception:
        return None

    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe = re.sub(r"[^a-zA-Z0-9_]", "_", str(project))[:40] or "untitled"
    verdict = g.get("verdict", "GREEN")

    md_path = studio_path("Legal", "Gate_Reports", f"GATE_{verdict}_{safe}_{stamp}_editorial.md")
    json_path = producers_path("Editorial_Gate", f"GATE_{verdict}_{safe}_{stamp}.json")

    signoff = (
        "yes" if g.get("human_signoff")
        else ("required" if g.get("requires_human_signoff") else "not required")
    )
    lines = [
        f"# Editorial Gate — {verdict}",
        f"**Project:** {project}",
        "**Gate:** editorial (issue #212)",
        f"**Stage:** {stage or 'n/a'}",
        f"**Status:** {g.get('status')}",
        f"**Human sign-off:** {signoff}",
        f"**Time:** {stamp}",
        "",
        "## Editorial Rails",
    ]
    for row, val in (g.get("checklist") or {}).items():
        icon = {"PASS": "✅", "CAUTION": "⚠️", "FAIL": "🛑"}.get(val, "•")
        lines.append(f"- {icon} `{row}` → {val}")
    lines.append("")
    for header, key, mark in (
        ("HARD STOPS (NO OVERRIDE)", "hard_stops", "🛑"),
        ("COUNSEL REQUIRED", "counsel_flags", "⚖️"),
        ("WARNINGS", "warnings", "⚠️"),
        ("NOTES", "notes", "•"),
    ):
        items = g.get(key) or []
        if items:
            lines.append(f"## {header}")
            lines.extend(f"- {mark} {x}" for x in items)
            lines.append("")
    md_path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")

    payload = dict(g)
    payload.update(
        {
            "project": project,
            "stage": stage,
            "timestamp": stamp,
            "source_excerpt": (source_text or "")[:500],
            "shared_report": str(md_path),
        }
    )
    json_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    return {"md": md_path, "json": json_path}


if __name__ == "__main__":  # pragma: no cover - smoke
    import json
    import sys

    src = sys.stdin.read() if not sys.argv[1:] else " ".join(sys.argv[1:])
    print(json.dumps(evaluate_editorial_gate(src, {"client_deliverable": True}).to_dict(), indent=2))
