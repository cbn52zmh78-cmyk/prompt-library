#!/usr/bin/env python3
"""
Legal Gate v1.0 — Producer Hard Stop
Reviews project ideas, prompts, and briefs BEFORE production.
RED = hard fucking no. No override without licensed counsel on file.
"""

from __future__ import annotations

import json
import re
import sys
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from lib.bootstrap import ensure_paths

ensure_paths()
from lib.studio_paths import producers_path, studio_path

# ── HARD STOP patterns (Producer locked) ──────────────────────────────────
HARD_STOP_PATTERNS: list[tuple[str, str]] = [
    (r"\b(minor|child|underage|preteen|pedo|loli)\b.*\b(sex|nude|erotic|intimate|nsfw)", "Sexual content involving minors — FEDERAL CRIME"),
    (r"\b(teen|teenager|young.?looking|schoolgirl|schoolboy)\b.*\b(sex|nude|erotic|intimate|topless)", "Ambiguous youth + sexual content — HARD STOP"),
    (r"\b(hardcore|xxx|unsimulated|pornographic|porn)\b", "Explicit adult industry content — outside studio mandate"),
    (r"\bdeepfake\b.*\b(non.?consent|revenge|ex.?girlfriend|ex.?boyfriend)", "Non-consensual deepfake — HARD STOP"),
    (r"\b(generate|create|make)\b.*\b(nude|naked)\b.*\b(celebrity|famous|real person)", "Non-consensual celebrity likeness nudity — HARD STOP"),
    (r"\bwithout (consent|permission)\b.*\b(likeness|face|voice)", "Explicit non-consent likeness use"),
    (r"\bimpersonat(e|ion)\b.*\b(fraud|scam|deceive|endorse)", "Deceptive impersonation for fraud"),
]

COUNSEL_PATTERNS: list[tuple[str, str]] = [
    (r"\b(sag|union|taft.?hartley|signatory)\b", "Union/signatory — verify with entertainment counsel"),
    (r"\b(e&o|errors.?and.?omissions|insurance)\b", "E&O/insurance — broker + counsel"),
    (r"\b(deepfake|digital replica|synthetic performer|de.?aging)\b", "Digital replica — AB 2602 / SAG replica consent required"),
    (r"\b(licensed music|sync license|master use|beatles|taylor swift)\b", "Music clearance — two-sided licenses required"),
    (r"\b(real person|living person|celebrity)\b.*\b(likeness|face|voice|portrait)", "Living person likeness on screen — counsel + consent"),
    (r"\b(deceased|post.?mortem)\b.*\b(replica|deepfake|likeness)", "Deceased replica — AB 1836 / counsel"),
]

YELLOW_PATTERNS: list[tuple[str, str]] = [
    (r"\b(brand|logo|nike|apple|coca.?cola|disney)\b.*\b(prominent|featured|endorse)", "Trademark in frame — clearance or nominative text only"),
    (r"\b(true story|based on actual|real events)\b.*\b(defame|accuse|guilty)", "Real-person story — defamation review"),
    (r"\bno age\b|\bage not stated\b", "Performer age not stated — Intimacy Protocol requires numerical age first"),
]

REQUIRED_AGE_PATTERN = re.compile(
    r"\b\d{2}-year-old\b|\b\d{2} year old\b|\bage[:\s]+\d{2}\b",
    re.I,
)


@dataclass
class GateResult:
    project: str
    verdict: str  # GREEN | YELLOW | COUNSEL | RED
    hard_stops: list[str] = field(default_factory=list)
    counsel_flags: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)

    def blocked(self) -> bool:
        return self.verdict == "RED"

    def to_dict(self) -> dict:
        return {
            "project": self.project,
            "verdict": self.verdict,
            "hard_stops": self.hard_stops,
            "counsel_flags": self.counsel_flags,
            "warnings": self.warnings,
            "notes": self.notes,
            "timestamp": datetime.now().isoformat(),
        }


class LegalGate:
    def __init__(self) -> None:
        self.gate_dir = producers_path("Legal_Gate")
        self.legal_reports = studio_path("Legal", "Gate_Reports")
        self.gate_dir.mkdir(parents=True, exist_ok=True)
        self.legal_reports.mkdir(parents=True, exist_ok=True)

    def review(self, text: str, project: str = "Untitled", *, has_performers: bool = True) -> GateResult:
        lower = text.lower()
        result = GateResult(project=project, verdict="GREEN")

        for pattern, msg in HARD_STOP_PATTERNS:
            if re.search(pattern, lower, re.I):
                result.hard_stops.append(msg)

        for pattern, msg in COUNSEL_PATTERNS:
            if re.search(pattern, lower, re.I):
                result.counsel_flags.append(msg)

        for pattern, msg in YELLOW_PATTERNS:
            if re.search(pattern, lower, re.I):
                result.warnings.append(msg)

        if has_performers and not REQUIRED_AGE_PATTERN.search(text):
            intimate = any(w in lower for w in ("intimate", "nude", "sensual", "erotic", "gfe", "topless", "sexual"))
            if intimate or "performer" in lower or "actress" in lower or "actor" in lower:
                result.warnings.append("Numerical performer age not stated — required per Age Policy + Intimacy Protocol v1.3")

        if result.hard_stops:
            result.verdict = "RED"
            result.notes.append("PRODUCER HARD STOP — Do not generate. Do not shoot. Legal no means no.")
        elif result.counsel_flags:
            result.verdict = "COUNSEL"
            result.notes.append("Escalate to entertainment counsel before proceeding.")
        elif result.warnings:
            result.verdict = "YELLOW"
            result.notes.append("Revise and re-submit to Legal Gate.")
        else:
            result.notes.append("Cleared for Development/Pre-Production subject to ongoing review.")

        return result

    def save_report(self, result: GateResult, source_text: str = "") -> Path:
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe = re.sub(r"[^a-zA-Z0-9_]", "_", result.project)[:40]
        path = self.gate_dir / f"GATE_{result.verdict}_{safe}_{stamp}.json"
        payload = result.to_dict()
        payload["source_excerpt"] = source_text[:500]
        path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

        md_path = self.legal_reports / f"GATE_{result.verdict}_{safe}_{stamp}.md"
        lines = [
            f"# Legal Gate — {result.verdict}",
            f"**Project:** {result.project}",
            f"**Time:** {stamp}",
            "",
        ]
        if result.hard_stops:
            lines.append("## HARD STOPS (NO OVERRIDE)")
            lines.extend(f"- {x}" for x in result.hard_stops)
            lines.append("")
        if result.counsel_flags:
            lines.append("## COUNSEL REQUIRED")
            lines.extend(f"- {x}" for x in result.counsel_flags)
            lines.append("")
        if result.warnings:
            lines.append("## WARNINGS")
            lines.extend(f"- {x}" for x in result.warnings)
            lines.append("")
        lines.extend(f"- {n}" for n in result.notes)
        md_path.write_text("\n".join(lines), encoding="utf-8")
        return path


def main() -> int:
    import argparse

    parser = argparse.ArgumentParser(description="Legal Gate v1.0 — Producer hard stop")
    parser.add_argument("--project", required=True, help="Project name")
    parser.add_argument("--text", help="Inline text to review")
    parser.add_argument("--file", help="Path to brief/prompt/screenplay excerpt")
    parser.add_argument("--no-performers", action="store_true")
    args = parser.parse_args()

    if args.file:
        text = Path(args.file).read_text(encoding="utf-8", errors="replace")
    elif args.text:
        text = args.text
    else:
        print("❌ Provide --text or --file")
        return 1

    gate = LegalGate()
    result = gate.review(text, args.project, has_performers=not args.no_performers)
    path = gate.save_report(result, text)

    icon = {"GREEN": "✅", "YELLOW": "⚠️", "COUNSEL": "⚖️", "RED": "🛑"}.get(result.verdict, "?")
    print(f"\n{icon} VERDICT: {result.verdict}")
    for msg in result.hard_stops:
        print(f"  🛑 HARD STOP: {msg}")
    for msg in result.counsel_flags:
        print(f"  ⚖️  COUNSEL: {msg}")
    for msg in result.warnings:
        print(f"  ⚠️  WARN: {msg}")
    print(f"\nReport: {path}")
    if result.blocked():
        print("\nPRODUCER: Legal no. Hard fucking no. We are not making this.")
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())