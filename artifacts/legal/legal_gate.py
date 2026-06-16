#!/usr/bin/env python3
"""
Legal Gate v1.1 — Producer Hard Stop
Gate 0: FIRST action on every scene, video, brief, or client ask.

Reviews TWO legal stacks before anything else:
  1. AI Content law (replica, deepfake, synthetic performer, likeness)
  2. Mass Dissemination law (CARA/rating bodies, social, streaming, theatrical, festival)

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

VALID_RATINGS = ("G", "PG", "PG-13", "R")
VALID_CHANNELS = ("social", "streaming", "theatrical", "festival", "client")

# ── HARD STOP — AI Content ────────────────────────────────────────────────
HARD_STOP_PATTERNS: list[tuple[str, str]] = [
    (r"\b(minor|child|underage|preteen|pedo|loli)\b.*\b(sex|nude|erotic|intimate|nsfw)", "Sexual content involving minors — FEDERAL CRIME"),
    (r"\b(teen|teenager|young.?looking|schoolgirl|schoolboy)\b.*\b(sex|nude|erotic|intimate|topless)", "Ambiguous youth + sexual content — HARD STOP"),
    (r"\b(hardcore|xxx|unsimulated|pornographic|porn)\b", "Explicit adult industry content — outside studio mandate"),
    (r"\bdeepfake\b.*\b(non.?consent|revenge|ex.?girlfriend|ex.?boyfriend)", "Non-consensual deepfake — HARD STOP"),
    (r"\b(generate|create|make)\b.*\b(nude|naked)\b.*\b(celebrity|famous|real person)", "Non-consensual celebrity likeness nudity — HARD STOP"),
    (r"\bwithout (consent|permission)\b.*\b(likeness|face|voice)", "Explicit non-consent likeness use"),
    (r"\bimpersonat(e|ion)\b.*\b(fraud|scam|deceive|endorse)", "Deceptive impersonation for fraud"),
]

# ── HARD STOP — Rating / dissemination ceiling ────────────────────────────
RATING_HARD_STOP_PATTERNS: list[tuple[str, str]] = [
    (r"\bNC-?17\b", "NC-17 is not a studio production target — HARD STOP"),
    (r"\b(graphic sex|unsimulated sex|explicit penetration|porn shoot)\b", "Content exceeds theatrical cinema mandate — HARD STOP"),
]

# Content that exceeds common rating ceilings when target is lower
RATING_CEILING_VIOLATIONS: dict[str, list[tuple[str, str]]] = {
    "G": [
        (r"\b(fuck|shit|bitch|nude|naked|topless|sex|drug|cocaine|heroin)\b", "Language/nudity/drugs exceed G ceiling"),
    ],
    "PG": [
        (r"\b(fuck|motherfucker|topless|nude|graphic sex|cocaine|heroin)\b", "Content exceeds PG ceiling"),
    ],
    "PG-13": [
        (r"\b(graphic sex|unsimulated|hardcore|full.?frontal|genitalia|penetration)\b", "Sexual explicitness exceeds PG-13 ceiling"),
        (r"\b(fuck)\b.*\b(repeated|constant|every line)\b", "Repeated strong language may exceed PG-13 — review"),
    ],
    "R": [
        (r"\b(hardcore|xxx|unsimulated sex act|pornographic)\b", "Content exceeds R theatrical ceiling — NC-17 territory"),
    ],
}

COUNSEL_PATTERNS: list[tuple[str, str]] = [
    (r"\b(sag|union|taft.?hartley|signatory)\b", "Union/signatory — verify with entertainment counsel"),
    (r"\b(e&o|errors.?and.?omissions|insurance)\b", "E&O/insurance — broker + counsel"),
    (r"\b(deepfake|digital replica|synthetic performer|de.?aging|ai.?generated.?actor)\b", "Digital replica — AB 2602 / SAG replica consent required"),
    (r"\b(licensed music|sync license|master use|beatles|taylor swift)\b", "Music clearance — two-sided licenses required"),
    (r"\b(real person|living person|celebrity)\b.*\b(likeness|face|voice|portrait)", "Living person likeness on screen — counsel + consent"),
    (r"\b(deceased|post.?mortem)\b.*\b(replica|deepfake|likeness)", "Deceased replica — AB 1836 / counsel"),
    (r"\b(broadcast|fcc|ofcom|tv.?ma|watershed)\b", "Broadcast standards — territory-specific counsel"),
]

YELLOW_PATTERNS: list[tuple[str, str]] = [
    (r"\b(brand|logo|nike|apple|coca.?cola|disney)\b.*\b(prominent|featured|endorse)", "Trademark in frame — clearance or nominative text only"),
    (r"\b(true story|based on actual|real events)\b.*\b(defame|accuse|guilty)", "Real-person story — defamation review"),
    (r"\bno age\b|\bage not stated\b", "Performer age not stated — Intimacy Protocol requires numerical age first"),
]

# Per-channel dissemination flags (warnings / counsel triggers)
CHANNEL_CHECKS: dict[str, list[tuple[str, str]]] = {
    "social": [
        (r"\b(ai|synthetic|generated)\b", "Social platforms require AI disclosure labels — verify current ToS"),
        (r"\b(nude|topless|sexual|nsfw)\b", "Sexual content on social — age-gate + platform policy review"),
        (r"\b(copyright|dmca|stolen|ripped)\b", "Copyright risk on social — takedown exposure"),
    ],
    "streaming": [
        (r"\b(licensed music|popular song|chart hit)\b", "Streaming deliverable — music cue sheet + sync required"),
        (r"\b(tv.?ma|mature audiences)\b", "Streaming rating — verify platform content descriptor requirements"),
    ],
    "theatrical": [
        (r"\b(self.?rate|no rating|unrated release)\b", "Theatrical requires CARA/MPA or regional board — no self-rating"),
        (r"\b(intimate|nude|sexual|gfe)\b", "Theatrical intimacy — CARA + Intimacy Protocol v1.3"),
    ],
    "festival": [
        (r"\b(likeness|celebrity|real person)\b", "Festival submission — likeness release packet required"),
    ],
    "client": [
        (r"\b(brand|endorse|sponsored|ad)\b", "Client work — brand safety + indemnity + extra clearance"),
        (r"\b(work.?for.?hire|wfh)\b", "Client deliverable — chain-of-title + contract review"),
    ],
}

REQUIRED_AGE_PATTERN = re.compile(
    r"\b\d{2}-year-old\b|\b\d{2} year old\b|\bage[:\s]+\d{2}\b",
    re.I,
)


@dataclass
class GateResult:
    project: str
    verdict: str  # GREEN | YELLOW | COUNSEL | RED
    target_rating: str = ""
    channels: list[str] = field(default_factory=list)
    hard_stops: list[str] = field(default_factory=list)
    counsel_flags: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    distribution_flags: list[str] = field(default_factory=list)
    rating_flags: list[str] = field(default_factory=list)
    cara_status: str = ""
    notes: list[str] = field(default_factory=list)

    def blocked(self) -> bool:
        return self.verdict == "RED"

    def to_dict(self) -> dict:
        return {
            "project": self.project,
            "verdict": self.verdict,
            "target_rating": self.target_rating,
            "channels": self.channels,
            "hard_stops": self.hard_stops,
            "counsel_flags": self.counsel_flags,
            "warnings": self.warnings,
            "distribution_flags": self.distribution_flags,
            "rating_flags": self.rating_flags,
            "cara_status": self.cara_status,
            "notes": self.notes,
            "timestamp": datetime.now().isoformat(),
        }


class LegalGate:
    def __init__(self) -> None:
        self.gate_dir = producers_path("Legal_Gate")
        self.legal_reports = studio_path("Legal", "Gate_Reports")
        self.gate_dir.mkdir(parents=True, exist_ok=True)
        self.legal_reports.mkdir(parents=True, exist_ok=True)

    def _run_cara(self, text: str, target_rating: str, project: str) -> tuple[str, list[str]]:
        try:
            from compliance.content_rating_compliance_guard import ContentRatingGuard

            guard = ContentRatingGuard()
            report = guard.analyze_prompt(text, target_rating=target_rating, name=project)
            return report["status"], list(report.get("issues", []))
        except Exception as exc:
            return "SKIPPED", [f"CARA guard unavailable: {exc}"]

    def review(
        self,
        text: str,
        project: str = "Untitled",
        *,
        target_rating: str = "",
        channels: list[str] | None = None,
        has_performers: bool = True,
    ) -> GateResult:
        lower = text.lower()
        channels = [c.lower().strip() for c in (channels or []) if c.strip()]
        result = GateResult(
            project=project,
            verdict="GREEN",
            target_rating=target_rating.upper() if target_rating else "",
            channels=channels,
        )

        # ── Stack 1: AI Content hard stops ────────────────────────────────
        for pattern, msg in HARD_STOP_PATTERNS:
            if re.search(pattern, lower, re.I):
                result.hard_stops.append(f"[AI] {msg}")

        # ── Stack 2: Rating / dissemination hard stops ────────────────────
        for pattern, msg in RATING_HARD_STOP_PATTERNS:
            if re.search(pattern, lower, re.I):
                result.hard_stops.append(f"[RATING] {msg}")

        for pattern, msg in COUNSEL_PATTERNS:
            if re.search(pattern, lower, re.I):
                result.counsel_flags.append(msg)

        for pattern, msg in YELLOW_PATTERNS:
            if re.search(pattern, lower, re.I):
                result.warnings.append(msg)

        # ── Rating ceiling vs declared target ─────────────────────────────
        if target_rating and target_rating.upper() in RATING_CEILING_VIOLATIONS:
            rating = target_rating.upper()
            for pattern, msg in RATING_CEILING_VIOLATIONS[rating]:
                if re.search(pattern, lower, re.I):
                    result.rating_flags.append(f"[{rating}] {msg}")

        # ── CARA theatrical analysis ──────────────────────────────────────
        if target_rating and target_rating.upper() in VALID_RATINGS:
            cara_status, cara_issues = self._run_cara(text, target_rating.upper(), project)
            result.cara_status = cara_status
            for issue in cara_issues:
                if "CRITICAL" in issue or "Prohibited" in issue:
                    result.hard_stops.append(f"[CARA] {issue}")
                else:
                    result.rating_flags.append(f"[CARA] {issue}")
        elif target_rating:
            result.warnings.append(f"Unknown target rating '{target_rating}' — use G/PG/PG-13/R")

        # ── Mass dissemination per declared channel ─────────────────────
        if not channels:
            result.distribution_flags.append(
                "No distribution channel declared — Gate 0 requires social/streaming/theatrical/festival/client intent"
            )
        for channel in channels:
            if channel not in VALID_CHANNELS:
                result.warnings.append(f"Unknown channel '{channel}' — valid: {', '.join(VALID_CHANNELS)}")
                continue
            for pattern, msg in CHANNEL_CHECKS.get(channel, []):
                if re.search(pattern, lower, re.I):
                    result.distribution_flags.append(f"[{channel.upper()}] {msg}")

        if "theatrical" in channels and not target_rating:
            result.distribution_flags.append("[THEATRICAL] Target rating required for CARA ceiling check")

        if "social" in channels:
            result.notes.append("Social = mass dissemination. Platform AI-label + community guidelines apply.")

        # ── Performer age (Intimacy Protocol) ───────────────────────────
        if has_performers and not REQUIRED_AGE_PATTERN.search(text):
            intimate = any(w in lower for w in ("intimate", "nude", "sensual", "erotic", "gfe", "topless", "sexual"))
            if intimate or "performer" in lower or "actress" in lower or "actor" in lower:
                result.warnings.append("Numerical performer age not stated — required per Age Policy + Intimacy Protocol v1.3")

        # ── Verdict ───────────────────────────────────────────────────────
        if result.hard_stops:
            result.verdict = "RED"
            result.notes.append("PRODUCER HARD STOP — Gate 0 failed. Do not generate. Do not shoot. Do not publish.")
        elif result.counsel_flags:
            result.verdict = "COUNSEL"
            result.notes.append("Escalate to entertainment counsel before proceeding.")
        elif result.warnings or result.rating_flags or result.distribution_flags:
            result.verdict = "YELLOW"
            result.notes.append("Revise and re-submit to Legal Gate (Gate 0).")
        else:
            result.notes.append("Gate 0 cleared for Development/Pre-Production subject to ongoing review.")

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
            f"# Legal Gate 0 — {result.verdict}",
            f"**Project:** {result.project}",
            f"**Target Rating:** {result.target_rating or 'not declared'}",
            f"**Channels:** {', '.join(result.channels) or 'not declared'}",
            f"**CARA:** {result.cara_status or 'n/a'}",
            f"**Time:** {stamp}",
            "",
            "## Legal Stacks Reviewed",
            "- AI Content (replica, deepfake, likeness, synthetic performer)",
            "- Mass Dissemination (rating bodies, social, streaming, theatrical, festival, client)",
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
        if result.rating_flags:
            lines.append("## RATING FLAGS")
            lines.extend(f"- {x}" for x in result.rating_flags)
            lines.append("")
        if result.distribution_flags:
            lines.append("## DISTRIBUTION FLAGS")
            lines.extend(f"- {x}" for x in result.distribution_flags)
            lines.append("")
        if result.warnings:
            lines.append("## WARNINGS")
            lines.extend(f"- {x}" for x in result.warnings)
            lines.append("")
        lines.append("## Producer Notes")
        lines.extend(f"- {n}" for n in result.notes)
        md_path.write_text("\n".join(lines), encoding="utf-8")
        return path


def main() -> int:
    import argparse

    parser = argparse.ArgumentParser(
        description="Legal Gate v1.1 — Gate 0: AI + mass dissemination compliance (RUN FIRST)"
    )
    parser.add_argument("--project", required=True, help="Project / slate ID")
    parser.add_argument("--text", help="Inline brief, prompt, or scene description")
    parser.add_argument("--file", help="Path to brief/prompt/screenplay excerpt")
    parser.add_argument("--rating", choices=["G", "PG", "PG-13", "R"], help="Target CARA/rating ceiling")
    parser.add_argument(
        "--channels",
        help="Comma-separated distribution intent: social,streaming,theatrical,festival,client",
    )
    parser.add_argument("--no-performers", action="store_true")
    args = parser.parse_args()

    if args.file:
        text = Path(args.file).read_text(encoding="utf-8", errors="replace")
    elif args.text:
        text = args.text
    else:
        print("❌ Provide --text or --file")
        return 1

    channels = [c.strip() for c in args.channels.split(",")] if args.channels else []

    gate = LegalGate()
    result = gate.review(
        text,
        args.project,
        target_rating=args.rating or "",
        channels=channels,
        has_performers=not args.no_performers,
    )
    path = gate.save_report(result, text)

    icon = {"GREEN": "✅", "YELLOW": "⚠️", "COUNSEL": "⚖️", "RED": "🛑"}.get(result.verdict, "?")
    print(f"\n{icon} GATE 0 VERDICT: {result.verdict}")
    if result.target_rating:
        print(f"   Rating ceiling: {result.target_rating} | CARA: {result.cara_status or 'n/a'}")
    if result.channels:
        print(f"   Channels: {', '.join(result.channels)}")
    for msg in result.hard_stops:
        print(f"  🛑 HARD STOP: {msg}")
    for msg in result.counsel_flags:
        print(f"  ⚖️  COUNSEL: {msg}")
    for msg in result.rating_flags:
        print(f"  📋 RATING: {msg}")
    for msg in result.distribution_flags:
        print(f"  📡 DISTRIBUTION: {msg}")
    for msg in result.warnings:
        print(f"  ⚠️  WARN: {msg}")
    print(f"\nReport: {path}")
    if result.blocked():
        print("\nPRODUCER: Gate 0 failed. Legal no. Hard fucking no. We are not making this.")
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())