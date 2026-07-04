"""brief_narrator.py — MERIDIAN Layer 3 Oliver-pattern narration engine.

Reads structured box score rows (Layer 2) → plain-English briefs (Layer 3).
Vertical-specific templates, shared 5-section engine. LLM-ready via llm_prompt field.

Every brief follows:
  1. What changed (facts)
  2. How it compares to expected (residual)
  3. What's approaching threshold (predictive)
  4. Recommended action (optional, never mandatory)
  5. Confidence and caveats

Usage:
    from brief_narrator import BriefNarrator, narrate_vertical

    narrator = BriefNarrator()
    brief = narrator.narrate("airport", "obstruction_change_report", rows)
    print(brief.body_text)
"""
from __future__ import annotations

import json
import sys
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

from _paths import WORKSPACE
from box_score_db import BoxScoreDB, BoxScoreRow
from epoch_manager import load_meridian_config
from production_catalog import parse_meridian_id

MERIDIAN_ROOT = WORKSPACE / "Stonebridge" / "Products" / "MERIDIAN"

# EU compliance (mandatory on all output)
_ELEANOR_MW = WORKSPACE / "AI" / "ELEANOR" / "middleware"
if str(_ELEANOR_MW) not in sys.path:
    sys.path.insert(0, str(_ELEANOR_MW))
try:
    from eu_compliance import compliance_output_metadata_unified  # noqa: E402
    _HAS_COMPLIANCE = True
except ImportError:
    _HAS_COMPLIANCE = False


BRIEF_SECTIONS = (
    "what_changed",
    "vs_expected",
    "approaching_threshold",
    "recommended_action",
    "confidence_caveats",
)

DELIVERABLE_TYPES: dict[str, list[str]] = {
    "rally": ["stage_brief", "change_alert", "season_digest"],
    "real_estate": ["property_subsidence_report", "portfolio_alert_digest", "municipal_risk_brief"],
    "infrastructure": ["corridor_condition_report", "maintenance_queue", "annual_asset_report"],
    "airport": ["obstruction_change_report", "planning_horizon_brief", "ai_flyby_narration"],
}


@dataclass
class MeridianBrief:
    """One narrated deliverable — audit-ready structured + plain text."""
    vertical: str
    deliverable_type: str
    title: str
    sections: dict[str, str]
    body_text: str
    feature_ids: list[str] = field(default_factory=list)
    epoch_dates: list[str] = field(default_factory=list)
    compiler_confidence: float | None = None
    llm_prompt: str = ""
    compliance: dict[str, Any] = field(default_factory=dict)
    generated_at: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    def save(self, path: Path | str) -> None:
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(self.to_dict(), indent=2, ensure_ascii=False), encoding="utf-8")


# ── Section builders (deterministic — LLM narrates from these facts) ──────────

def _fmt_id(fid: str) -> str:
    return fid if fid.startswith("@") else f"@{fid}"


def _confidence_caveat(rows: list[BoxScoreRow], gap_note: str = "") -> str:
    confs = [r.compiler_confidence for r in rows if r.compiler_confidence is not None]
    avg = sum(confs) / len(confs) if confs else 0.45
    epochs = max((r.epoch_count for r in rows), default=1)
    parts = [
        f"Compiler confidence: {avg:.0%} (mean across referenced features).",
        f"Longitudinal depth: {epochs} epoch(s) on record.",
    ]
    if avg < 0.60:
        parts.append("Below publish threshold — dad QA review recommended before client delivery.")
    if gap_note:
        parts.append(gap_note)
    parts.append("All measurements from Layer 2 deterministic geomatics — narration does not alter values.")
    return " ".join(parts)


def _rally_stage_brief(rows: list[BoxScoreRow]) -> dict[str, str]:
    latest = rows[-1] if rows else None
    if not latest:
        return {s: "No box score data available." for s in BRIEF_SECTIONS}

    m = latest.measurements
    fid = latest.feature_id
    what = (
        f"{fid}: road width {m.get('road_width_m', '?')}m, "
        f"roughness σ {m.get('dsm_roughness_std', '?')}, "
        f"vegetation encroachment {m.get('vegetation_encroachment_pct', '?')}%. "
    )
    if len(rows) >= 2:
        prev = rows[-2]
        pm = prev.measurements
        what += (
            f"Since {prev.epoch_date}: cut volume Δ {m.get('cut_volume_delta_m3', 0)} m³, "
            f"edge shift L/R {m.get('edge_shift_left_m', 0)}/{m.get('edge_shift_right_m', 0)} m."
        )

    residual = latest.residual_vs_expected or 0
    vs_exp = (
        f"Residual vs expected deterioration model: {residual:+.2f}. "
        + ("Above baseline — surface change exceeds substrate × climate expectation." if residual > 0.15
           else "Within expected range for substrate class and season.")
    )

    approaching = ""
    encroach = m.get("vegetation_encroachment_pct", 0) or 0
    if encroach > 3:
        approaching = f"Vegetation encroachment at {encroach}% — monitor for grip-affecting edge closure."
    water = m.get("water_holding_proxy", 0) or 0
    if water > 0.35:
        approaching += f" Drainage proxy elevated ({water}) — wet-stage holding risk."

    action = ""
    if residual > 0.2:
        action = "Consider recce verification of edge geometry before next event. Not mandatory — team judgment."

    return {
        "what_changed": what,
        "vs_expected": vs_exp,
        "approaching_threshold": approaching or "No threshold alerts on current metrics.",
        "recommended_action": action or "No action indicated from current epoch data.",
        "confidence_caveats": _confidence_caveat(rows),
    }


def _airport_obstruction_report(rows: list[BoxScoreRow]) -> dict[str, str]:
    by_id: dict[str, list[BoxScoreRow]] = {}
    for r in rows:
        by_id.setdefault(r.feature_id, []).append(r)
    for fid in by_id:
        by_id[fid].sort(key=lambda x: x.epoch_date)

    new_obstructions: list[str] = []
    approaching: list[str] = []
    changed: list[str] = []

    for fid, history in by_id.items():
        latest = history[-1]
        m = latest.measurements
        pen = m.get("penetration_m", 0) or 0
        name = m.get("object_name", fid)
        obj_type = m.get("object_type", "object")

        if len(history) >= 2:
            prev = history[-2]
            prev_pen = prev.measurements.get("penetration_m", 0) or 0
            delta = pen - prev_pen
            if pen > 0 and prev_pen == 0:
                new_obstructions.append(
                    f"{fid} ({name}) now penetrates approach surface by {pen:.1f}m — "
                    f"not present in {prev.epoch_date} epoch."
                )
            elif delta > 0:
                changed.append(f"{fid} ({name}): penetration increased {delta:+.1f}m since {prev.epoch_date}.")
        elif pen > 0:
            new_obstructions.append(f"{fid} ({name}) penetrates by {pen:.1f}m on first recorded epoch.")

        ytp = m.get("years_to_penetration")
        if pen == 0 and ytp is not None and ytp <= 2.0:
            approaching.append(
                f"{fid} ({obj_type}): ~{ytp:.1f} years to penetration at {m.get('growth_rate_m_yr', '?')} m/yr growth."
            )

    what = " ".join(new_obstructions + changed) if (new_obstructions or changed) else "No new obstructions since prior epoch."
    vs_exp_parts = []
    for fid, history in by_id.items():
        latest = history[-1]
        res = latest.residual_vs_expected
        if res and res > 0:
            vs_exp_parts.append(f"{fid} residual vs growth model: {res:+.1f}m.")
    vs_exp = " ".join(vs_exp_parts) if vs_exp_parts else "All objects within expected growth/construction baseline."

    approach_txt = " ".join(approaching) if approaching else "No objects within 2-year penetration horizon."
    action = ""
    if new_obstructions:
        action = "Recommend FAA Form 7460-1 review for new penetrations. Vegetation management program for approaching objects."
    elif approaching:
        action = "Recommend annual trimming cycle for vegetation objects flagged in approach corridor."

    return {
        "what_changed": what,
        "vs_expected": vs_exp,
        "approaching_threshold": approach_txt,
        "recommended_action": action or "Continue scheduled monitoring — no immediate intervention indicated.",
        "confidence_caveats": _confidence_caveat(rows),
    }


def _airport_flyby_narration(rows: list[BoxScoreRow], context: dict[str, Any]) -> dict[str, str]:
    """Voiceover beats for AI approach-path video — paired with waypoints."""
    base = _airport_obstruction_report(rows)
    waypoints = context.get("waypoints", [])
    beats: list[str] = []
    for wp in waypoints:
        label = wp.get("label", "")
        ids = wp.get("highlight_ids", [])
        if not ids:
            beats.append(f"[{label}] Continue approach — glide slope nominal.")
            continue
        highlights = [r for r in rows if r.feature_id in ids]
        for r in highlights:
            m = r.measurements
            pen = m.get("penetration_m", 0) or 0
            if pen > 0:
                beats.append(
                    f"[{label}] Obstruction {r.feature_id}: {m.get('object_name', '')} — "
                    f"penetrates {pen:.1f}m. Highlight overlay active."
                )
            else:
                ytp = m.get("years_to_penetration", "?")
                beats.append(
                    f"[{label}] {r.feature_id}: {m.get('object_name', '')} — "
                    f"clear today, ~{ytp} years to surface at current growth."
                )
    base["what_changed"] = " ".join(beats) if beats else base["what_changed"]
    return base


def _real_estate_property_report(rows: list[BoxScoreRow]) -> dict[str, str]:
    latest = rows[-1] if rows else None
    if not latest:
        return {s: "No property data." for s in BRIEF_SECTIONS}
    m = latest.measurements
    fid = latest.feature_id
    delta = m.get("dsm_elev_delta", 0) or 0
    annual = m.get("dsm_elev_delta_annualized", 0) or 0
    what = f"{fid}: settlement {delta:.0f}mm since prior epoch ({annual:.1f} mm/yr annualized)."
    residual = latest.residual_vs_expected or 0
    soil = m.get("soil_class", "unknown")
    vs_exp = (
        f"Residual vs expected ({soil} soil model): {residual:+.1f}mm. "
        + ("Exceeds expected settlement rate." if abs(residual) > 5 else "Within expected range.")
    )
    tilt = m.get("tilt_vector_deg", 0) or 0
    approaching = f"Tilt {tilt}° {m.get('tilt_direction', '')}." if tilt > 0.2 else ""
    drain = m.get("drainage_risk", 0) or 0
    if drain > 0.5:
        approaching += f" Drainage risk elevated ({drain:.0%})."
    action = "Recommend geotechnical investigation before purchase." if residual > 5 else ""
    return {
        "what_changed": what,
        "vs_expected": vs_exp,
        "approaching_threshold": approaching or "No threshold alerts.",
        "recommended_action": action or "No action required from current data.",
        "confidence_caveats": _confidence_caveat(rows),
    }


def _infrastructure_corridor_report(rows: list[BoxScoreRow]) -> dict[str, str]:
    flagged = [r for r in rows if (r.residual_vs_expected or 0) > 1.0]
    what_parts = []
    for r in rows:
        m = r.measurements
        seg = r.segment_id or r.feature_id
        what_parts.append(
            f"{seg}: IRI proxy {m.get('surface_roughness_iri', '?')}, "
            f"rutting {m.get('rutting_depth_mm', '?')}mm, "
            f"cracks {m.get('crack_density_pct', '?')}%."
        )
    what = " ".join(what_parts[:5])
    if len(what_parts) > 5:
        what += f" (+{len(what_parts) - 5} more segments)"
    vs_exp = (
        f"{len(flagged)} of {len(rows)} segments exceed expected deterioration."
        if flagged else "All segments within expected deterioration model."
    )
    approaching = " ".join(
        f"{r.feature_id}: residual {r.residual_vs_expected:+.1f}."
        for r in flagged[:3]
    )
    action = ""
    if flagged:
        top = flagged[0]
        action = f"Top priority: {top.feature_id} — core sample or mill/overlay assessment recommended."
    return {
        "what_changed": what,
        "vs_expected": vs_exp,
        "approaching_threshold": approaching or "No segments above residual threshold.",
        "recommended_action": action or "Defer maintenance — within tolerance.",
        "confidence_caveats": _confidence_caveat(rows),
    }


def _portfolio_digest(rows: list[BoxScoreRow], vertical: str) -> dict[str, str]:
    alerts = [r for r in rows if (r.residual_vs_expected or 0) >= 1.0
              or (r.compiler_confidence or 1) < 0.60]
    what = f"{len(alerts)} of {len(rows)} monitored features exceed threshold."
    details = "; ".join(
        f"{r.feature_id} (residual {r.residual_vs_expected:+.1f})"
        for r in alerts[:10]
    )
    return {
        "what_changed": what + (" " + details if details else ""),
        "vs_expected": "Portfolio residual analysis across latest epoch per feature.",
        "approaching_threshold": details,
        "recommended_action": "Review flagged features in exception queue.",
        "confidence_caveats": _confidence_caveat(rows),
    }


# Deliverable → builder routing
_SECTION_BUILDERS: dict[str, Callable[..., dict[str, str]]] = {
    "stage_brief": _rally_stage_brief,
    "change_alert": _rally_stage_brief,
    "property_subsidence_report": _real_estate_property_report,
    "corridor_condition_report": _infrastructure_corridor_report,
    "maintenance_queue": _infrastructure_corridor_report,
    "obstruction_change_report": _airport_obstruction_report,
    "planning_horizon_brief": _airport_obstruction_report,
    "ai_flyby_narration": _airport_flyby_narration,
    "portfolio_alert_digest": lambda rows, **_: _portfolio_digest(rows, "real_estate"),
    "season_digest": lambda rows, **_: _portfolio_digest(rows, "rally"),
    "annual_asset_report": lambda rows, **_: _portfolio_digest(rows, "infrastructure"),
    "municipal_risk_brief": lambda rows, **_: _portfolio_digest(rows, "real_estate"),
}


def _compose_body(sections: dict[str, str]) -> str:
    labels = {
        "what_changed": "What changed",
        "vs_expected": "Compared to expected",
        "approaching_threshold": "Approaching threshold",
        "recommended_action": "Recommended action",
        "confidence_caveats": "Confidence & caveats",
    }
    parts = []
    for key in BRIEF_SECTIONS:
        text = sections.get(key, "")
        if text:
            parts.append(f"{labels[key]}: {text}")
    return "\n\n".join(parts)


def _build_llm_prompt(
    vertical: str,
    deliverable_type: str,
    sections: dict[str, str],
    rows: list[BoxScoreRow],
) -> str:
    """Structured prompt for MATILDA/ELEANOR — facts locked, LLM writes prose."""
    facts = json.dumps([r.to_dict() for r in rows], indent=2)
    section_block = "\n".join(f"{k}: {v}" for k, v in sections.items())
    return (
        f"MERIDIAN {vertical} brief — {deliverable_type}\n"
        f"Write plain-English client brief. Use exact @IDs and numbers from facts. "
        f"Never invent measurements. Section structure mandatory.\n\n"
        f"FACTS (Layer 2 — do not alter):\n{facts}\n\n"
        f"SECTION DRAFT:\n{section_block}\n\n"
        f"Tone: professional, auditable, never prescriptive on safety-critical actions."
    )


def _compliance_meta(deliverable_type: str) -> dict[str, Any]:
    if _HAS_COMPLIANCE:
        return compliance_output_metadata_unified(
            performer="matilda_8b",
            component=f"meridian_brief_{deliverable_type}",
        )
    return {
        "eu_ai_act": {"article_50_compliant": True, "ai_generated": True},
        "us_disclosure": {"synthetic_performer": True},
        "component": f"meridian_brief_{deliverable_type}",
    }


def _title_for(vertical: str, deliverable_type: str, rows: list[BoxScoreRow]) -> str:
    titles = {
        "stage_brief": "Stage Sector Brief",
        "obstruction_change_report": "Obstruction Change Report",
        "ai_flyby_narration": "Approach Path Narration",
        "property_subsidence_report": "Property Subsidence Report",
        "corridor_condition_report": "Corridor Condition Report",
        "portfolio_alert_digest": "Portfolio Alert Digest",
    }
    base = titles.get(deliverable_type, deliverable_type.replace("_", " ").title())
    if rows:
        return f"MERIDIAN {base} — {rows[0].feature_id}"
    return f"MERIDIAN {base}"


class BriefNarrator:
    """Oliver-pattern narration — structured data → derived brief → LLM prose."""

    def __init__(self, config: dict[str, Any] | None = None, db: BoxScoreDB | None = None) -> None:
        self.config = config or load_meridian_config()
        self.db = db or BoxScoreDB.load()

    def narrate(
        self,
        vertical: str,
        deliverable_type: str,
        rows: list[BoxScoreRow] | None = None,
        *,
        feature_id: str = "",
        context: dict[str, Any] | None = None,
    ) -> MeridianBrief:
        """Generate a brief from box score rows or DB query."""
        allowed = DELIVERABLE_TYPES.get(vertical, [])
        if deliverable_type not in allowed and deliverable_type not in _SECTION_BUILDERS:
            raise ValueError(
                f"Unknown deliverable {deliverable_type!r} for vertical {vertical!r}. "
                f"Expected one of: {allowed}"
            )

        if rows is None:
            rows = self.db.query(vertical, feature_id=feature_id)
        if not rows:
            raise ValueError(f"No box score rows for vertical={vertical} feature_id={feature_id!r}")

        builder = _SECTION_BUILDERS.get(deliverable_type, _portfolio_digest)
        ctx = context or {}
        if deliverable_type in ("ai_flyby_narration",):
            sections = builder(rows, context=ctx)
        else:
            sections = builder(rows)

        confs = [r.compiler_confidence for r in rows if r.compiler_confidence is not None]
        avg_conf = sum(confs) / len(confs) if confs else None

        brief = MeridianBrief(
            vertical=vertical,
            deliverable_type=deliverable_type,
            title=_title_for(vertical, deliverable_type, rows),
            sections=sections,
            body_text=_compose_body(sections),
            feature_ids=sorted({r.feature_id for r in rows}),
            epoch_dates=sorted({r.epoch_date for r in rows}),
            compiler_confidence=avg_conf,
            llm_prompt=_build_llm_prompt(vertical, deliverable_type, sections, rows),
            compliance=_compliance_meta(deliverable_type),
            generated_at=_now(),
        )
        return brief

    def narrate_from_db(
        self,
        vertical: str,
        deliverable_type: str,
        *,
        feature_id: str = "",
        alerts_only: bool = False,
        context: dict[str, Any] | None = None,
    ) -> MeridianBrief:
        if alerts_only:
            rows = self.db.alerts(vertical)
        else:
            rows = self.db.query(vertical, feature_id=feature_id)
        return self.narrate(vertical, deliverable_type, rows, context=context)


def narrate_vertical(
    vertical: str,
    deliverable_type: str,
    *,
    feature_id: str = "",
    load_fixtures: bool = False,
    context: dict[str, Any] | None = None,
) -> MeridianBrief:
    """Convenience: load DB (+ optional fixtures) → narrate."""
    db = BoxScoreDB.load()
    if load_fixtures:
        try:
            db.load_fixture(vertical)
        except FileNotFoundError:
            pass
    narrator = BriefNarrator(db=db)
    return narrator.narrate_from_db(
        vertical, deliverable_type, feature_id=feature_id, context=context,
    )


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


if __name__ == "__main__":
    db = BoxScoreDB.load()
    db.load_fixture("rally")
    db.load_fixture("airport")

    narrator = BriefNarrator(db=db)

    rally = narrator.narrate_from_db("rally", "stage_brief", feature_id="@ST-SS4-S3")
    print(f"rally: {rally.title}")
    print(rally.body_text[:200], "...")

    airport = narrator.narrate_from_db("airport", "obstruction_change_report")
    print(f"\nairport: {airport.title}")
    print(airport.sections["what_changed"][:200], "...")

    path_data = json.loads(
        (MERIDIAN_ROOT / "airport" / "demo" / "approach_path_fixture.json").read_text(encoding="utf-8")
    )
    flyby = narrator.narrate_from_db(
        "airport", "ai_flyby_narration",
        context={"waypoints": path_data.get("waypoints", [])},
    )
    print(f"\nflyby narration beats: {len(flyby.sections['what_changed'])} chars")
    print("smoke OK")