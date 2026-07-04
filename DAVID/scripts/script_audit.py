"""script_audit.py — Pre-render pipeline analysis suite (Oliver-pattern read-only verbs).

Five analysis verbs, all read-only against script JSON + catalog:

  1. scout()       — Oliver scouting report: entity coverage, modifier completeness,
                     orphan detection, style transition flags, underspecified shots.
  2. drift()       — Longitudinal consistency: detect entity state divergence across
                     shots without a version bump (Oliver velocity-drop alert).
  3. project_cost() — Render complexity projection: estimated API calls, modifier
                     layer count, continuation chain depth, priority ordering.
  4. coherence()   — Audio-visual DNA coherence: flag mismatched modifier combos
                     that aren't explicitly marked as intentional artistic contrast.
  5. heatmap()     — Modifier coverage grid: per-shot explicit/default/unset status
                     for every modifier field.

Usage:
    from script_audit import scout, drift, project_cost, coherence, heatmap

    report = scout(script, catalog)
    drift_report = drift(script, catalog)
    cost = project_cost(script)
    flags = coherence(script)
    grid = heatmap(script)

CLI:
    python script_audit.py <script.json> [--catalog <master_catalog.json>] [--verb all|scout|drift|cost|coherence|heatmap]
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

from _paths import DAVID_ROOT

# Lazy imports to avoid circular deps — resolved at call time
_catalog_mod = None
_style_mod = None


def _get_catalog_mod():
    global _catalog_mod
    if _catalog_mod is None:
        import production_catalog as _pc
        _catalog_mod = _pc
    return _catalog_mod


def _get_style_mod():
    global _style_mod
    if _style_mod is None:
        import style_modifiers as _sm
        _style_mod = _sm
    return _style_mod


# ── Shared helpers ───────────────────────────────────────────────────────────

def _shots(script: dict[str, Any]) -> list[dict[str, Any]]:
    return script.get("shots") or []


def _shot_id(shot: dict[str, Any]) -> str:
    return str(shot.get("id") or "?")


def _extract_ids_from_prompt(prompt: str, pattern: re.Pattern) -> list[str]:
    return [f"@{m.group(1)}_{m.group(2)}" for m in pattern.finditer(prompt)]


def _is_barebones(script: dict[str, Any]) -> bool:
    """True when script uses barebones prompt mode (inline direction, no structured modifiers)."""
    return (script.get("config") or {}).get("prompt_mode") == "barebones"


# Maps barebones sub-fields to the structured modifier fields they replace.
_BAREBONES_FIELD_MAP: dict[str, list[str]] = {
    "style": ["style_dna_tag"],
    "audio": ["audio_dna_tag", "audio_dna_combo"],
    "camera": ["director_persona_id"],
    "scene": ["pacing_dna_tag"],
}


def _barebones_coverage(shot: dict[str, Any]) -> dict[str, str]:
    """Check which modifier-equivalent barebones sub-fields have content.

    Returns: {modifier_field: "inline"} for each field covered by barebones text.
    Language is checked from barebones.dialogue.language directly.
    """
    bb = shot.get("barebones") or {}
    covered: dict[str, str] = {}
    for bb_key, mod_fields in _BAREBONES_FIELD_MAP.items():
        val = bb.get(bb_key, "")
        # Also check voice_direction, voice_direction_DE, ambient as audio sub-fields
        if bb_key == "audio":
            val = val or bb.get("voice_direction", "") or bb.get("ambient", "")
        if val and len(str(val)) > 5:  # non-trivial content
            for fld in mod_fields:
                covered[fld] = "inline"
    # Music: check if scene/audio mentions music keywords
    audio_text = str(bb.get("audio", "")) + str(bb.get("scene", ""))
    if any(kw in audio_text.lower() for kw in ("music", "score", "soundtrack", "underscore")):
        covered["music_dna_tag"] = "inline"
        covered["music_dna_combo"] = "inline"
    # Language from dialogue block
    lang = (bb.get("dialogue") or {}).get("language")
    if lang:
        covered["language"] = "inline"
    return covered


def _barebones_prompt_text(shot: dict[str, Any]) -> str:
    """Extract all prompt text from a barebones shot for entity/context scanning."""
    bb = shot.get("barebones") or {}
    parts = []
    for key in ("command", "style", "audio", "camera", "scene",
                "voice_direction", "voice_direction_DE", "ambient"):
        val = bb.get(key)
        if isinstance(val, str):
            parts.append(val)
    # @1, @2 description blocks
    for ref_key in ("@1", "@2", "@3", "@4"):
        ref = bb.get(ref_key)
        if isinstance(ref, dict):
            parts.append(ref.get("description", ""))
    # dialogue
    dlg = bb.get("dialogue")
    if isinstance(dlg, dict):
        parts.append(dlg.get("speech_text", ""))
    return " ".join(parts)


# ═══════════════════════════════════════════════════════════════════════════════
# 1. SCOUT — Oliver scouting report
# ═══════════════════════════════════════════════════════════════════════════════

def scout(
    script: dict[str, Any],
    catalog: Any | None = None,
) -> dict[str, Any]:
    """Pre-render scouting report. Catches problems before expensive renders.

    Returns:
        {
            "shot_count": int,
            "entity_summary": {type: count},
            "modifier_completeness": {field: {"set": n, "unset": n}},
            "underspecified_shots": [...],    # shots missing key modifiers
            "orphan_entities": [...],         # catalog entries never referenced
            "style_transitions": [...],       # style changes between consecutive shots
            "missing_references": [...],      # @IDs in script not in catalog
            "single_appearance": [...],       # entities that appear in only 1 shot
            "grade": "A"|"B"|"C"|"F",
            "risk_summary": str,
        }
    """
    pc = _get_catalog_mod()
    sm = _get_style_mod()
    shots = _shots(script)

    if catalog is None:
        catalog_path = DAVID_ROOT / "productions" / "master_catalog.json"
        if catalog_path.is_file():
            catalog = pc.Catalog.load(catalog_path)

    id_pattern = catalog.id_pattern() if catalog else pc.build_id_pattern(pc.movie_types())

    barebones = _is_barebones(script)

    # ── Entity extraction ────────────────────────────────────────────────
    entity_to_shots: dict[str, list[str]] = defaultdict(list)
    type_counter: Counter = Counter()

    for shot in shots:
        sid = _shot_id(shot)
        # Barebones scripts embed @IDs in barebones sub-fields, not video_prompt
        prompt = _barebones_prompt_text(shot) if barebones else shot.get("video_prompt", "")
        ids = _extract_ids_from_prompt(prompt, id_pattern)
        for eid in ids:
            entity_to_shots[eid].append(sid)
            etype = eid.split("_")[0].lstrip("@")
            type_counter[etype] += 1

    # ── Modifier completeness ────────────────────────────────────────────
    MODIFIER_FIELDS = [
        "director_persona_id", "style_dna_tag", "audio_dna_tag",
        "music_dna_tag", "pacing_dna_tag", "language",
    ]
    field_stats: dict[str, dict[str, int]] = {f: {"set": 0, "unset": 0} for f in MODIFIER_FIELDS}
    underspecified: list[dict[str, Any]] = []

    for shot in shots:
        sid = _shot_id(shot)
        bb_cover = _barebones_coverage(shot) if barebones else {}
        resolved = sm.resolve_modifier_ids(script, shot)
        missing_fields = []
        for fld in MODIFIER_FIELDS:
            val = resolved.get(fld) or bb_cover.get(fld)
            if val:
                field_stats[fld]["set"] += 1
            else:
                field_stats[fld]["unset"] += 1
                missing_fields.append(fld)
        if len(missing_fields) >= 3:
            underspecified.append({
                "shot_id": sid,
                "missing_fields": missing_fields,
                "missing_count": len(missing_fields),
            })

    # ── Orphan entities (in catalog but never referenced) ────────────────
    orphans = []
    if catalog:
        referenced_ids = set(entity_to_shots.keys())
        for entry in catalog.active_entries():
            if entry.id not in referenced_ids:
                orphans.append({
                    "entity_id": entry.id,
                    "name": entry.name,
                    "type": entry.type,
                })

    # ── Missing references (@IDs in script but not in catalog) ───────────
    missing_refs = []
    if catalog:
        for eid, shot_ids in entity_to_shots.items():
            entry = catalog.resolve(eid)
            if entry is None:
                missing_refs.append({
                    "entity_id": eid,
                    "referenced_in": shot_ids,
                    "action": "Register entity or fix typo",
                })

    # ── Single-appearance entities (potential orphan risk) ────────────────
    singles = [
        {"entity_id": eid, "shot_id": sids[0]}
        for eid, sids in entity_to_shots.items()
        if len(sids) == 1 and not eid.startswith("@SET") and not eid.startswith("@LOC")
    ]

    # ── Style transitions (consecutive shots with different style_dna_tag) ─
    transitions = []
    prev_style = None
    prev_sid = None
    for shot in shots:
        sid = _shot_id(shot)
        resolved = sm.resolve_modifier_ids(script, shot)
        style = resolved.get("style_dna_tag")
        # Barebones: fall back to inline style text for transition detection
        if not style and barebones:
            style = (shot.get("barebones") or {}).get("style")
        if prev_style and style and style != prev_style:
            transitions.append({
                "from_shot": prev_sid,
                "to_shot": sid,
                "from_style": prev_style,
                "to_style": style,
            })
        prev_style = style
        prev_sid = sid

    # ── Grade ────────────────────────────────────────────────────────────
    risk_points = 0
    risk_points += len(missing_refs) * 15
    risk_points += len(underspecified) * 5
    risk_points += len(transitions) * 2  # transitions aren't bad, just noteworthy

    score = max(0, 100 - risk_points)
    grade = "A" if score >= 85 else "B" if score >= 70 else "C" if score >= 50 else "F"

    risks = []
    if missing_refs:
        risks.append(f"{len(missing_refs)} unregistered @ID reference(s)")
    if underspecified:
        risks.append(f"{len(underspecified)} underspecified shot(s) (3+ missing modifiers)")
    if transitions:
        risks.append(f"{len(transitions)} style transition(s) to verify")
    if not risks:
        risks.append("Clean — no issues detected")

    return {
        "shot_count": len(shots),
        "entity_summary": dict(type_counter),
        "unique_entities": len(entity_to_shots),
        "modifier_completeness": field_stats,
        "underspecified_shots": underspecified,
        "orphan_entities": orphans,
        "missing_references": missing_refs,
        "single_appearance": singles,
        "style_transitions": transitions,
        "score": score,
        "grade": grade,
        "risk_summary": "; ".join(risks),
    }


# ═══════════════════════════════════════════════════════════════════════════════
# 2. DRIFT — Longitudinal consistency (Oliver velocity-drop)
# ═══════════════════════════════════════════════════════════════════════════════

def drift(
    script: dict[str, Any],
    catalog: Any | None = None,
) -> dict[str, Any]:
    """Detect entity state drift across shots without version bumps.

    For each entity that appears in multiple shots, checks whether the
    surrounding prompt context diverges enough to suggest the entity's
    visual/state has changed — but the catalog version hasn't been bumped.

    Returns:
        {
            "entities_checked": int,
            "drift_flags": [
                {
                    "entity_id": str,
                    "name": str,
                    "first_shot": str,
                    "last_shot": str,
                    "appearances": int,
                    "catalog_version": int,
                    "context_keywords_first": [...],
                    "context_keywords_last": [...],
                    "divergent_keywords": [...],  # in last but not first
                    "drift_score": float,         # 0.0 = identical, 1.0 = total divergence
                    "action": str,
                }
            ],
            "clean_entities": int,
        }
    """
    pc = _get_catalog_mod()
    shots = _shots(script)

    if catalog is None:
        catalog_path = DAVID_ROOT / "productions" / "master_catalog.json"
        if catalog_path.is_file():
            catalog = pc.Catalog.load(catalog_path)

    id_pattern = catalog.id_pattern() if catalog else pc.build_id_pattern(pc.movie_types())

    barebones = _is_barebones(script)

    # Build entity → ordered list of (shot_id, surrounding_context)
    entity_contexts: dict[str, list[tuple[str, str]]] = defaultdict(list)

    for shot in shots:
        sid = _shot_id(shot)
        prompt = _barebones_prompt_text(shot) if barebones else shot.get("video_prompt", "")
        ids = _extract_ids_from_prompt(prompt, id_pattern)
        for eid in ids:
            entity_contexts[eid].append((sid, prompt))

    # Only check entities with 2+ appearances
    multi = {eid: ctx for eid, ctx in entity_contexts.items() if len(ctx) >= 2}
    drift_flags = []

    for eid, contexts in multi.items():
        first_sid, first_prompt = contexts[0]
        last_sid, last_prompt = contexts[-1]

        # Extract context keywords (simple word-level comparison)
        first_words = _context_keywords(first_prompt, eid)
        last_words = _context_keywords(last_prompt, eid)

        divergent = last_words - first_words
        shared = first_words & last_words
        total = first_words | last_words

        drift_score = round(len(divergent) / max(1, len(total)), 2)

        # Only flag significant drift (>30% keyword divergence)
        if drift_score > 0.3:
            entry = catalog.resolve(eid) if catalog else None
            drift_flags.append({
                "entity_id": eid,
                "name": entry.name if entry else "?",
                "first_shot": first_sid,
                "last_shot": last_sid,
                "appearances": len(contexts),
                "catalog_version": entry.version if entry else 0,
                "context_keywords_first": sorted(first_words)[:10],
                "context_keywords_last": sorted(last_words)[:10],
                "divergent_keywords": sorted(divergent)[:10],
                "drift_score": drift_score,
                "action": "Review — entity context changed significantly; consider version bump",
            })

    return {
        "entities_checked": len(multi),
        "drift_flags": drift_flags,
        "clean_entities": len(multi) - len(drift_flags),
    }


def _context_keywords(prompt: str, entity_id: str) -> set[str]:
    """Extract meaningful context words near an entity reference."""
    # Find the entity position and take a ±50 char window
    idx = prompt.find(entity_id)
    if idx < 0:
        idx = 0
    start = max(0, idx - 80)
    end = min(len(prompt), idx + len(entity_id) + 80)
    window = prompt[start:end].lower()

    # Extract words, filter stopwords and short tokens
    words = set(re.findall(r"[a-z]{3,}", window))
    stopwords = {"the", "and", "for", "with", "from", "this", "that", "into", "over",
                 "shot", "scene", "camera", "angle", "close", "wide", "medium"}
    return words - stopwords


# ═══════════════════════════════════════════════════════════════════════════════
# 3. PROJECT_COST — Render complexity projection (Oliver contract valuation)
# ═══════════════════════════════════════════════════════════════════════════════

def project_cost(
    script: dict[str, Any],
) -> dict[str, Any]:
    """Estimate render complexity and API cost per shot.

    Returns:
        {
            "total_shots": int,
            "estimated_api_calls": int,
            "total_complexity_score": int,
            "shots": [
                {
                    "shot_id": str,
                    "complexity_score": int,      # 0-100
                    "modifier_layers": int,        # how many modifiers active
                    "is_chain_continuation": bool,
                    "has_speech": bool,
                    "estimated_duration_s": float,
                    "priority_tier": "high"|"medium"|"low",
                }
            ],
            "priority_order": [...],  # shot_ids sorted by complexity (render hardest first for early failure)
            "chain_depth": int,       # longest continuation chain
            "summary": str,
        }
    """
    sm = _get_style_mod()
    shots = _shots(script)
    cfg = script.get("config") or {}

    shot_reports = []
    chain_count = 0
    max_chain_depth = 0
    current_chain = 0
    total_api = 0

    barebones = _is_barebones(script)

    for shot in shots:
        sid = _shot_id(shot)
        resolved = sm.resolve_modifier_ids(script, shot)

        # Count active modifier layers
        MODIFIER_FIELDS = [
            "director_persona_id", "style_dna_tag", "audio_dna_tag", "audio_dna_combo",
            "music_dna_tag", "music_dna_combo", "pacing_dna_tag", "language",
            "anim_style_id", "camera_move", "anti_generic_armor",
        ]
        active_mods = sum(1 for f in MODIFIER_FIELDS if resolved.get(f))
        # Barebones: inline direction counts as modifier layers
        if barebones:
            bb_cover = _barebones_coverage(shot)
            active_mods = max(active_mods, len(bb_cover))

        is_chain = sm.shot_is_chain_continuation(script, shot)
        if is_chain:
            current_chain += 1
            chain_count += 1
        else:
            max_chain_depth = max(max_chain_depth, current_chain)
            current_chain = 0

        has_speech = bool(shot.get("speech_text") or shot.get("dialogue"))
        duration = float(shot.get("duration_s") or shot.get("duration") or 5.0)

        # Complexity scoring
        complexity = 10  # base
        complexity += active_mods * 5
        complexity += 15 if has_speech else 0
        complexity += 10 if is_chain else 0
        complexity += min(20, int(duration))
        complexity = min(100, complexity)

        # API calls: 1 base + 1 if extend (chain) + 1 if speech overlay
        api_calls = 1
        if is_chain:
            api_calls += 1
        total_api += api_calls

        tier = "high" if complexity >= 60 else "medium" if complexity >= 35 else "low"

        shot_reports.append({
            "shot_id": sid,
            "complexity_score": complexity,
            "modifier_layers": active_mods,
            "is_chain_continuation": is_chain,
            "has_speech": has_speech,
            "estimated_duration_s": duration,
            "estimated_api_calls": api_calls,
            "priority_tier": tier,
        })

    max_chain_depth = max(max_chain_depth, current_chain)
    total_complexity = sum(s["complexity_score"] for s in shot_reports)

    # Priority order: render hardest shots first (fail-fast strategy)
    priority = sorted(shot_reports, key=lambda s: s["complexity_score"], reverse=True)

    high = sum(1 for s in shot_reports if s["priority_tier"] == "high")
    med = sum(1 for s in shot_reports if s["priority_tier"] == "medium")
    low = sum(1 for s in shot_reports if s["priority_tier"] == "low")

    return {
        "total_shots": len(shots),
        "estimated_api_calls": total_api,
        "total_complexity_score": total_complexity,
        "avg_complexity": round(total_complexity / max(1, len(shots)), 1),
        "chain_shots": chain_count,
        "max_chain_depth": max_chain_depth,
        "tier_breakdown": {"high": high, "medium": med, "low": low},
        "shots": shot_reports,
        "priority_order": [s["shot_id"] for s in priority],
        "summary": (
            f"{len(shots)} shots, ~{total_api} API calls, "
            f"{high} high / {med} medium / {low} low complexity, "
            f"longest chain: {max_chain_depth}"
        ),
    }


# ═══════════════════════════════════════════════════════════════════════════════
# 4. COHERENCE — Audio-visual DNA coherence check
# ═══════════════════════════════════════════════════════════════════════════════

# Aesthetic family groupings — modifiers that naturally pair together.
# Cross-family combos get flagged (not blocked — could be intentional contrast).
_AESTHETIC_FAMILIES = {
    "dark_tension": {
        "styles": {"style_fincher_khondji", "style_bergman_nykvist", "anim_fincher_khondji", "anim_bergman_nykvist"},
        "sounds": {"sound_fincher_khondji", "sound_bergman_nykvist", "sound_gudnadottir_dread", "sound_king_nolan"},
        "music": {"music_herrmann_suspense", "music_greenwood_dissonant"},
        "pacing": {"pacing_fincher_tension_accel", "pacing_murch_subtractive"},
    },
    "warm_symmetry": {
        "styles": {"style_anderson_yeoman", "anim_anderson_yeoman"},
        "sounds": {"sound_anderson_yeoman"},
        "music": {"music_desplat_impressionist", "music_rota_storyteller", "music_hisaishi_dreamer"},
        "pacing": {"pacing_mid_tempo_dialogue"},
    },
    "operatic_epic": {
        "styles": {"style_coppola_willis", "style_bertolucci_storaro", "anim_coppola_willis", "anim_bertolucci_storaro"},
        "sounds": {"sound_coppola_willis", "sound_storaro_bertolucci"},
        "music": {"music_morricone_melodist", "music_horner_epic", "music_poledouris_warrior", "music_williams_leitmotif"},
        "pacing": {"pacing_slow_build_setup", "pacing_schoonmaker_momentum"},
    },
    "naturalist_flow": {
        "styles": {"style_deakins_villeneuve", "style_cuaron_lubezki", "anim_deakins_villeneuve", "anim_cuaron_lubezki"},
        "sounds": {"sound_deakins", "sound_cuaron_lubezki", "sound_rydstrom_emotional"},
        "music": {"music_zimmer_architect", "music_sakamoto_crosscultural", "music_goransson_fusion"},
        "pacing": {"pacing_lubezki_long_take_flow"},
    },
}


def _family_for_slug(slug: str | None) -> str | None:
    if not slug:
        return None
    for family, groups in _AESTHETIC_FAMILIES.items():
        for group_slugs in groups.values():
            if slug in group_slugs:
                return family
    return None


def coherence(
    script: dict[str, Any],
) -> dict[str, Any]:
    """Flag audio-visual-pacing DNA mismatches per shot.

    Returns:
        {
            "shots_checked": int,
            "coherent": int,
            "mismatches": [
                {
                    "shot_id": str,
                    "style_family": str|null,
                    "audio_family": str|null,
                    "music_family": str|null,
                    "pacing_family": str|null,
                    "conflicting_families": [str, str],
                    "severity": "INFO"|"WARN",
                    "note": str,
                }
            ],
        }
    """
    sm = _get_style_mod()
    shots = _shots(script)
    barebones = _is_barebones(script)
    mismatches = []

    # Barebones scripts use inline free-text direction — can't classify into families
    if barebones:
        return {
            "shots_checked": len(shots),
            "coherent": len(shots),
            "mismatches": [],
            "note": "barebones prompt_mode — style/audio/pacing direction is inline text, "
                    "not structured modifier slugs. Family coherence check not applicable.",
        }

    for shot in shots:
        sid = _shot_id(shot)
        resolved = sm.resolve_modifier_ids(script, shot)

        families = {
            "style": _family_for_slug(resolved.get("style_dna_tag")),
            "audio": _family_for_slug(resolved.get("audio_dna_tag")),
            "music": _family_for_slug(resolved.get("music_dna_tag")),
            "pacing": _family_for_slug(resolved.get("pacing_dna_tag")),
        }

        active = {k: v for k, v in families.items() if v is not None}
        unique_families = set(active.values())

        if len(unique_families) > 1:
            # Check if shot.modifiers has an explicit override (intentional contrast)
            mods = shot.get("modifiers") if isinstance(shot.get("modifiers"), dict) else {}
            is_explicit = bool(mods)
            mismatches.append({
                "shot_id": sid,
                "style_family": families["style"],
                "audio_family": families["audio"],
                "music_family": families["music"],
                "pacing_family": families["pacing"],
                "conflicting_families": sorted(unique_families),
                "severity": "INFO" if is_explicit else "WARN",
                "note": (
                    "Intentional contrast (explicit shot modifiers)"
                    if is_explicit
                    else "Cross-family modifier mix — verify artistic intent"
                ),
            })

    return {
        "shots_checked": len(shots),
        "coherent": len(shots) - len(mismatches),
        "mismatches": mismatches,
    }


# ═══════════════════════════════════════════════════════════════════════════════
# 5. HEATMAP — Modifier coverage grid
# ═══════════════════════════════════════════════════════════════════════════════

def heatmap(
    script: dict[str, Any],
) -> dict[str, Any]:
    """Per-shot modifier coverage: explicit / default / unset for each field.

    Returns:
        {
            "fields": [str],
            "shots": [
                {
                    "shot_id": str,
                    "coverage": {
                        field: {"status": "explicit"|"default"|"unset", "value": str|null, "source": str}
                    },
                    "coverage_pct": float,
                }
            ],
            "field_coverage": {field: {"explicit": n, "default": n, "unset": n}},
            "overall_coverage_pct": float,
        }
    """
    sm = _get_style_mod()
    shots = _shots(script)
    barebones_mode = _is_barebones(script)

    FIELDS = [
        "director_persona_id", "style_dna_tag", "audio_dna_tag", "audio_dna_combo",
        "music_dna_tag", "music_dna_combo", "pacing_dna_tag", "language",
    ]

    # Barebones uses "inline" as a fourth status alongside explicit/default/unset
    statuses = ["explicit", "default", "inline", "unset"]
    field_totals: dict[str, dict[str, int]] = {f: {s: 0 for s in statuses} for f in FIELDS}
    shot_rows = []
    total_set = 0
    total_cells = 0

    for shot in shots:
        sid = _shot_id(shot)
        resolved = sm.resolve_modifier_ids(script, shot)
        bb_cover = _barebones_coverage(shot) if barebones_mode else {}
        coverage: dict[str, dict[str, Any]] = {}
        set_count = 0

        for fld in FIELDS:
            val = resolved.get(fld)
            source = resolved.get(f"_{fld}_source", "")
            bb_val = bb_cover.get(fld)
            total_cells += 1

            if val:
                set_count += 1
                total_set += 1
                if source and any(s in str(source) for s in ("shot", "barebones")):
                    status = "explicit"
                    field_totals[fld]["explicit"] += 1
                else:
                    status = "default"
                    field_totals[fld]["default"] += 1
            elif bb_val:
                # Inline barebones direction — direction IS present, just not structured
                set_count += 1
                total_set += 1
                status = "inline"
                val = bb_val
                source = "barebones_inline"
                field_totals[fld]["inline"] += 1
            else:
                status = "unset"
                field_totals[fld]["unset"] += 1

            coverage[fld] = {"status": status, "value": val, "source": str(source)}

        shot_rows.append({
            "shot_id": sid,
            "coverage": coverage,
            "coverage_pct": round(100 * set_count / max(1, len(FIELDS)), 1),
        })

    return {
        "fields": FIELDS,
        "shots": shot_rows,
        "field_coverage": field_totals,
        "overall_coverage_pct": round(100 * total_set / max(1, total_cells), 1),
    }


# ═══════════════════════════════════════════════════════════════════════════════
# Full report (all five verbs)
# ═══════════════════════════════════════════════════════════════════════════════

def full_report(
    script: dict[str, Any],
    catalog: Any | None = None,
) -> dict[str, Any]:
    """Run all five audit verbs and return combined report."""
    return {
        "scout": scout(script, catalog),
        "drift": drift(script, catalog),
        "cost": project_cost(script),
        "coherence": coherence(script),
        "heatmap": heatmap(script),
    }


# ═══════════════════════════════════════════════════════════════════════════════
# CLI
# ═══════════════════════════════════════════════════════════════════════════════

def _cli():
    parser = argparse.ArgumentParser(
        description="Pre-render script audit (Oliver-pattern analysis verbs)",
    )
    parser.add_argument("script", help="Path to script JSON")
    parser.add_argument(
        "--catalog", "-c",
        help="Path to master_catalog.json (auto-detected if omitted)",
        default=None,
    )
    parser.add_argument(
        "--verb", "-v",
        choices=["all", "scout", "drift", "cost", "coherence", "heatmap"],
        default="all",
        help="Which analysis verb to run (default: all)",
    )
    parser.add_argument(
        "--compact",
        action="store_true",
        help="Compact JSON output (no indentation)",
    )
    args = parser.parse_args()

    script_path = Path(args.script)
    if not script_path.is_file():
        print(f"ERROR: Script not found: {script_path}", file=sys.stderr)
        sys.exit(1)

    script = json.loads(script_path.read_text(encoding="utf-8"))

    catalog = None
    if args.catalog:
        pc = _get_catalog_mod()
        catalog = pc.Catalog.load(Path(args.catalog))

    verbs = {
        "scout": lambda: scout(script, catalog),
        "drift": lambda: drift(script, catalog),
        "cost": lambda: project_cost(script),
        "coherence": lambda: coherence(script),
        "heatmap": lambda: heatmap(script),
    }

    if args.verb == "all":
        result = full_report(script, catalog)
    else:
        result = verbs[args.verb]()

    indent = None if args.compact else 2
    print(json.dumps(result, indent=indent, ensure_ascii=False))


if __name__ == "__main__":
    _cli()
