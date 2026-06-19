#!/usr/bin/env python3
"""
Legal Gate v1.5 — Producer Hard Stop (aligned to Gate_0_Checklist.md v1.1)

Gate 0: FIRST action on every scene, video, brief, or client ask.

Reviews TWO legal stacks + six checklist domains:
  1. AI Content law (replica, deepfake, synthetic performer, likeness)
  2. Mass Dissemination law (CARA/rating bodies, social, streaming, theatrical, festival)

Checklist rows mapped in GateResult.checklist_domains (row_1 … row_6).

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
from historical_figure_gate import evaluate_historical_figure_gate  # noqa: E402
from music_clearance import music_row2_status  # noqa: E402
from science_gate import evaluate_science_gate  # noqa: E402

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
    (
        r"\b(deepfake|digital replica|de.?aging|ai.?generated.?actor)\b",
        "Digital replica — AB 2602 / SAG replica consent required",
    ),
    (
        r"\b(licensed music|sync license|master use|beatles|taylor swift)\b",
        "Music clearance — two-sided licenses required",
    ),
    (
        r"\b(real person|living person|celebrity)\b.*\b(likeness|face|voice|portrait)",
        "Living person likeness on screen — counsel + consent",
    ),
    (r"\b(deceased|post.?mortem)\b.*\b(replica|deepfake|likeness)", "Deceased replica — AB 1836 / counsel"),
    (r"\b(broadcast|fcc|ofcom|tv.?ma|watershed)\b", "Broadcast standards — territory-specific counsel"),
]

# Gate 0 row 2 — uncleared music on client deliverable = RED (Music_Clearance CHARTER)
MUSIC_UNCLEARED_PATTERNS: list[tuple[str, str]] = [
    (r"\buncleared\b", "Uncleared music — HARD STOP on client deliverable (Gate 0 row 2)"),
    (r"\bunlicensed\b", "Unlicensed music — HARD STOP on client deliverable (Gate 0 row 2)"),
    (r"\bno sync license\b", "No sync license — HARD STOP on client deliverable (Gate 0 row 2)"),
    (r"\btemp music only\b", "Temp music only without clearance plan — HARD STOP on client deliverable (Gate 0 row 2)"),
    (r"\bno master use\b", "No master use clearance — HARD STOP on client deliverable (Gate 0 row 2)"),
    (r"\bmusic not cleared\b", "Music not cleared — HARD STOP on client deliverable (Gate 0 row 2)"),
]

DISCLOSURE_PLANNED_PATTERN = re.compile(
    r"ai disclosure|disclosure planned|synthetic.?performer disclosure|ai.?generated disclosure",
    re.I,
)
STUDIO_SYNTHETIC_CAST_PATTERN = re.compile(
    r"casting bible|synthetic:\s*true",
    re.I,
)
STUDIO_NO_LIKENESS_PATTERN = re.compile(
    r"real_person_likeness:\s*false|no real.?person likeness",
    re.I,
)
MUSIC_CLEARED_PATTERN = re.compile(
    r"music cleared|original score|cue sheet on file|cleared sync|master use cleared",
    re.I,
)
AGE_EXTRACT_PATTERN = re.compile(r"\b(\d{2})-year-old\b", re.I)
MIN_PERFORMER_AGE = 21

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
NEGATED_GUARD_PREFIX = re.compile(r"\bno[\s-]|non[\s-]|zero[\s-]|without[\s-]", re.I)


def _affirmed_pattern_match(pattern: str, text: str) -> bool:
    """True when pattern matches and match is not negated (e.g. 'no NSFW' is not an NSFW flag)."""
    for match in re.finditer(pattern, text, re.I):
        prefix = text[max(0, match.start() - 12) : match.start()]
        if NEGATED_GUARD_PREFIX.search(prefix):
            continue
        return True
    return False


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
    checklist_domains: dict[str, str] = field(default_factory=dict)
    historical_figure_gate: dict = field(default_factory=dict)
    science_gate: dict = field(default_factory=dict)

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
            "checklist_domains": self.checklist_domains,
            "historical_figure_gate": self.historical_figure_gate,
            "science_gate": self.science_gate,
            "timestamp": datetime.now().isoformat(),
        }


def _is_studio_synthetic_cast(text: str) -> bool:
    return bool(
        STUDIO_SYNTHETIC_CAST_PATTERN.search(text)
        and STUDIO_NO_LIKENESS_PATTERN.search(text)
    )


def _disclosure_planned(text: str) -> bool:
    return bool(DISCLOSURE_PLANNED_PATTERN.search(text))


def _music_cleared(text: str) -> bool:
    return bool(MUSIC_CLEARED_PATTERN.search(text))


def _evaluate_checklist_domains(result: GateResult, text: str, channels: list[str]) -> dict[str, str]:
    """Map machine findings to Gate_0_Checklist.md v1.1 rows 1–6."""
    lower = text.lower()
    domains: dict[str, str] = {}

    # Row 1 — synthetic-actor consent / ownership
    if any("[AI]" in h and "likeness" in h.lower() for h in result.hard_stops):
        domains["row_1_synthetic_ownership"] = "FAIL"
    elif _is_studio_synthetic_cast(text):
        domains["row_1_synthetic_ownership"] = "PASS"
    elif any("likeness" in f.lower() for f in result.counsel_flags):
        domains["row_1_synthetic_ownership"] = "COUNSEL"
    else:
        domains["row_1_synthetic_ownership"] = "MANUAL"

    # Row 2 — music / sync rights (manifest-backed beds + legacy cleared phrases)
    if any("[MUSIC]" in h for h in result.hard_stops):
        domains["row_2_music_sync"] = "FAIL"
    elif music_row2_status(text, channels).get("manifest_cleared"):
        domains["row_2_music_sync"] = "PASS"
    elif _music_cleared(text):
        domains["row_2_music_sync"] = "PASS"
    elif any("music" in f.lower() for f in result.counsel_flags):
        domains["row_2_music_sync"] = "COUNSEL"
    else:
        domains["row_2_music_sync"] = "MANUAL"

    # Row 3 — no-real-likeness sign-off
    if any("likeness" in h.lower() or "deepfake" in h.lower() for h in result.hard_stops):
        domains["row_3_no_real_likeness"] = "FAIL"
    elif any("likeness" in f.lower() for f in result.counsel_flags):
        domains["row_3_no_real_likeness"] = "COUNSEL"
    elif _is_studio_synthetic_cast(text) or "no real-person likeness" in lower:
        domains["row_3_no_real_likeness"] = "PASS"
    else:
        domains["row_3_no_real_likeness"] = "MANUAL"

    # Row 4 — target-channel legality
    if result.distribution_flags and result.verdict in ("YELLOW", "COUNSEL", "RED"):
        domains["row_4_target_channel"] = "REVIEW"
    elif result.distribution_flags:
        domains["row_4_target_channel"] = "REVIEW"
    elif channels:
        domains["row_4_target_channel"] = "PASS"
    else:
        domains["row_4_target_channel"] = "FAIL"

    # Row 5 — 2257-style age documentation
    ages = [int(m.group(1)) for m in AGE_EXTRACT_PATTERN.finditer(text)]
    if any(a < MIN_PERFORMER_AGE for a in ages):
        domains["row_5_age_documentation"] = "FAIL"
    elif ages and all(a >= MIN_PERFORMER_AGE for a in ages):
        domains["row_5_age_documentation"] = "PASS"
    elif "performer" in lower or "actress" in lower or "actor" in lower:
        domains["row_5_age_documentation"] = "MANUAL"
    else:
        domains["row_5_age_documentation"] = "N/A"

    # Row 6 — AI-disclosure obligation
    if _disclosure_planned(text):
        domains["row_6_ai_disclosure"] = "PASS"
    elif "social" in channels or "streaming" in channels:
        domains["row_6_ai_disclosure"] = "MANUAL"
    else:
        domains["row_6_ai_disclosure"] = "MANUAL"

    return domains


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
                if _affirmed_pattern_match(pattern, lower):
                    # Row 6: disclosure planned satisfies social AI-label obligation at Gate 0
                    if (
                        channel == "social"
                        and "AI disclosure" in msg
                        and _disclosure_planned(text)
                    ):
                        result.notes.append(
                            "Row 6: AI-disclosure obligation planned — verify presence at Pre-Publish."
                        )
                        continue
                    result.distribution_flags.append(f"[{channel.upper()}] {msg}")

        if "theatrical" in channels and not target_rating:
            result.distribution_flags.append("[THEATRICAL] Target rating required for CARA ceiling check")

        if "social" in channels:
            result.notes.append("Social = mass dissemination. Platform AI-label + community guidelines apply.")

        # ── Gate 0 row 2: clearance_manifest.json + uncleared music ─────
        mstatus = music_row2_status(text, channels)
        if mstatus["unlisted"]:
            result.hard_stops.append(
                "[MUSIC] Unlisted music bed(s) "
                f"{', '.join(mstatus['unlisted'])} — not in "
                "STUDIO/Music_Sound/clearance_manifest.json (Gate 0 row 2)"
            )
        for block in mstatus.get("channel_blocked") or []:
            result.hard_stops.append(
                f"[MUSIC] {block['track_id']} not cleared for channel(s): "
                f"{', '.join(block['channels'])} (Gate 0 row 2)"
            )
        if mstatus.get("manifest_cleared"):
            result.notes.append(
                "Row 2: Manifest-cleared music bed(s): "
                f"{', '.join(mstatus['cleared'])} "
                "(STUDIO/Music_Sound/clearance_manifest.json)"
            )

        client_delivery = "client" in channels or "client deliverable" in lower
        if client_delivery:
            for pattern, msg in MUSIC_UNCLEARED_PATTERNS:
                if re.search(pattern, lower, re.I):
                    result.hard_stops.append(f"[MUSIC] {msg}")
                    break

        # ── Gate 0 row 1: STUDIO Casting Bible synthetic cast note ───────
        if _is_studio_synthetic_cast(text):
            result.notes.append(
                "Row 1: STUDIO Casting Bible synthetic cast — Upon Tyne ownership; no third-party likeness license."
            )

        # ── Gate 0 row 5: 21+ age floor (2257-style) ─────────────────────
        for match in AGE_EXTRACT_PATTERN.finditer(text):
            age_val = int(match.group(1))
            if age_val < MIN_PERFORMER_AGE:
                result.hard_stops.append(
                    f"[AGE] Performer age {age_val} below {MIN_PERFORMER_AGE}+ floor — HARD STOP (Gate 0 row 5)"
                )

        # ── Performer age stated (Intimacy Protocol) ─────────────────────
        if has_performers and not REQUIRED_AGE_PATTERN.search(text):
            intimate = any(w in lower for w in ("intimate", "nude", "sensual", "erotic", "gfe", "topless", "sexual"))
            if intimate or "performer" in lower or "actress" in lower or "actor" in lower:
                result.warnings.append(
                    "Numerical performer age not stated — required per Age Policy + Intimacy Protocol v1.3"
                )

        # ── Historical Figure Gate (safety spine #147 / #154) ─────────────
        hist = evaluate_historical_figure_gate(text)
        result.historical_figure_gate = hist.to_dict()
        if hist.applies:
            result.hard_stops.extend(hist.hard_stops)
            result.warnings.extend(hist.warnings)
            result.notes.extend(hist.notes)

        # ── Science Gate (illustrative-not-simulation #154) ───────────────
        sci = evaluate_science_gate(text)
        result.science_gate = sci.to_dict()
        if sci.applies:
            result.hard_stops.extend(sci.hard_stops)
            result.warnings.extend(sci.warnings)
            result.notes.extend(sci.notes)

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

        result.checklist_domains = _evaluate_checklist_domains(result, text, channels)
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
        if result.historical_figure_gate.get("applies"):
            lines.append("## Historical Figure Gate (#147 / #154)")
            hfg = result.historical_figure_gate
            lines.append(f"- **status:** {hfg.get('status')}")
            if hfg.get("death_year") is not None:
                lines.append(f"- **death_year:** {hfg['death_year']}")
            for msg in hfg.get("hard_stops", []):
                lines.append(f"- 🛑 {msg}")
            for msg in hfg.get("warnings", []):
                lines.append(f"- ⚠️ {msg}")
            lines.append("")
        if result.science_gate.get("applies"):
            lines.append("## Science Gate (#154)")
            sg = result.science_gate
            lines.append(f"- **status:** {sg.get('status')}")
            for msg in sg.get("overclaims", []):
                lines.append(f"- ⚠️ {msg}")
            for msg in sg.get("warnings", []):
                if msg not in sg.get("overclaims", []):
                    lines.append(f"- ⚠️ {msg}")
            lines.append("")
        if result.checklist_domains:
            lines.append("## Checklist Domains (Gate 0 v1.1)")
            for key in (
                "row_1_synthetic_ownership",
                "row_2_music_sync",
                "row_3_no_real_likeness",
                "row_4_target_channel",
                "row_5_age_documentation",
                "row_6_ai_disclosure",
            ):
                if key in result.checklist_domains:
                    lines.append(f"- **{key}:** {result.checklist_domains[key]}")
            lines.append("")
        lines.append("## Producer Notes")
        lines.extend(f"- {n}" for n in result.notes)
        md_path.write_text("\n".join(lines), encoding="utf-8")
        return path


def main() -> int:
    import argparse

    parser = argparse.ArgumentParser(
        description="Legal Gate v1.5 — Gate 0: AI + dissemination + history + science spines (RUN FIRST)"
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
    if result.checklist_domains:
        print("\n  📋 CHECKLIST DOMAINS:")
        for key, status in result.checklist_domains.items():
            print(f"     {key}: {status}")
    print(f"\nReport: {path}")
    if result.blocked():
        print("\nPRODUCER: Gate 0 failed. Legal no. Hard fucking no. We are not making this.")
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())