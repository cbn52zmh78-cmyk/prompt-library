#!/usr/bin/env python3
"""catalog_resolver.py — Map screenplay names to @CHAR/@SET/@STYLE catalog IDs.

Phase B catalog resolver. Takes screenplay_ingest.py output (which has raw
character/location names) and resolves them against the production_catalog.py
permanent ID registry. Unresolved names go to the HITL exception queue.

Usage:
    python catalog_resolver.py script.json -o script_resolved.json
    python catalog_resolver.py script.json --auto-register   # mint new IDs for unknowns
    python catalog_resolver.py script.json --report-only      # just show resolution report

As a library:
    from catalog_resolver import resolve_catalog, apply_resolutions
    report = resolve_catalog(script_dict, catalog)
    script = apply_resolutions(script_dict, report)
"""

import argparse
import json
import re
import sys
from difflib import SequenceMatcher
from pathlib import Path
from typing import Any

# ── Import catalog (graceful fallback for standalone use) ─────────────

_CATALOG_AVAILABLE = False
try:
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from production_catalog import Catalog, catalog_for_product, PRODUCT_CATALOG_PATHS
    _CATALOG_AVAILABLE = True
except ImportError:
    pass


# ─────────────────────────── fuzzy matching ───────────────────────────

def _similarity(a: str, b: str) -> float:
    """Case-insensitive similarity ratio (0.0 - 1.0).

    Uses token-aware matching: if the query is a single token that matches
    a token in the candidate (e.g. "VINCENT" vs "Vincent Vega"), boost the
    score.  Screenplay names are almost always first-name only.
    """
    al, bl = a.lower().strip(), b.lower().strip()
    # Direct SequenceMatcher
    seq_score = SequenceMatcher(None, al, bl).ratio()

    # Token match — if one side is a single token that appears as a full
    # token in the other, treat as a strong partial match.
    a_tokens = al.split()
    b_tokens = bl.split()
    if len(a_tokens) == 1 and a_tokens[0] in b_tokens:
        # single-token query matches a word in the candidate
        # Score: 0.90 if it's the first token (first name), 0.85 otherwise
        token_score = 0.90 if b_tokens[0] == a_tokens[0] else 0.85
        return max(seq_score, token_score)
    if len(b_tokens) == 1 and b_tokens[0] in a_tokens:
        token_score = 0.90 if a_tokens[0] == b_tokens[0] else 0.85
        return max(seq_score, token_score)

    return seq_score


def _normalize_name(name: str) -> str:
    """Normalize a name for matching: strip titles, honorifics, articles."""
    n = name.strip().upper()
    # Strip common screenplay extensions
    n = re.sub(r"\s*\(V\.O\.\)|\(O\.S\.\)|\(CONT'D\)|\(O\.C\.\)", "", n)
    # Strip titles
    n = re.sub(r"^(MR\.|MRS\.|MS\.|DR\.|DETECTIVE|OFFICER|AGENT|CAPTAIN|SGT\.?|LT\.?)\s+", "", n)
    return n.strip()


def _normalize_location(loc: str) -> str:
    """Normalize location: strip INT./EXT. prefix and time suffix."""
    l = loc.strip()
    l = re.sub(r"^(INT\.|EXT\.|INT\.\s*/\s*EXT\.|I/E\.)\s*", "", l, flags=re.IGNORECASE)
    l = re.sub(r"\s*-\s*(DAY|NIGHT|MORNING|EVENING|AFTERNOON|DUSK|DAWN|LATER|CONTINUOUS|SAME)\s*$", "", l, flags=re.IGNORECASE)
    return l.strip()


# ─────────────────────────── resolution engine ────────────────────────

MATCH_THRESHOLD = 0.75   # Minimum similarity for auto-match
HIGH_CONFIDENCE = 0.90   # Auto-apply without HITL review


def _find_best_match(name: str, catalog_entries: list, entity_type: str = "") -> dict | None:
    """Find the best catalog match for a name.

    Returns {entry, score, method} or None.
    """
    normalized = _normalize_name(name)
    best = None
    best_score = 0.0

    for entry in catalog_entries:
        if entity_type and entry.type != entity_type.upper():
            continue
        if entry.status == "merged":
            continue

        # Exact match on canonical name
        if _normalize_name(entry.name) == normalized:
            return {"entry": entry, "score": 1.0, "method": "exact_name"}

        # Exact match on alias
        for alias in entry.aliases:
            if _normalize_name(alias) == normalized:
                return {"entry": entry, "score": 0.98, "method": "exact_alias"}

        # Fuzzy match on name
        score = _similarity(normalized, _normalize_name(entry.name))
        if score > best_score:
            best_score = score
            best = {"entry": entry, "score": score, "method": "fuzzy_name"}

        # Fuzzy match on aliases
        for alias in entry.aliases:
            score = _similarity(normalized, _normalize_name(alias))
            if score > best_score:
                best_score = score
                best = {"entry": entry, "score": score, "method": "fuzzy_alias"}

    if best and best_score >= MATCH_THRESHOLD:
        return best
    return None


# ─────────────────────────── public API ───────────────────────────────

def resolve_catalog(script: dict, catalog: Any = None) -> dict:
    """Resolve all character/location/style names in a script against the catalog.

    Returns a resolution report:
    {
        "characters": [{name, resolved_id, score, method, status}, ...],
        "locations":  [{name, resolved_id, score, method, status}, ...],
        "styles":     [{name, resolved_id, score, method, status}, ...],
        "summary": {total, resolved, unresolved, auto_resolved, hitl_needed},
        "hitl_queue": [{type, name, candidates, action_needed}, ...],
    }
    """
    report = {
        "characters": [],
        "locations": [],
        "styles": [],
        "summary": {"total": 0, "resolved": 0, "unresolved": 0,
                     "auto_resolved": 0, "hitl_needed": 0},
        "hitl_queue": [],
    }

    # Extract unique characters from script
    characters = set()
    locations = set()
    for shot in script.get("shots", []):
        st = shot.get("speech_text")
        vp = shot.get("video_prompt", "")
        # Characters from _characters index (set by screenplay_ingest.py)
        # Locations from scene headings in video_prompt
        pass

    # From _characters metadata
    char_index = script.get("_characters", {})
    for name in char_index:
        characters.add(name)

    # From intake
    intake = script.get("intake", {})
    if intake.get("actor_id"):
        characters.add(intake["actor_id"])
    if intake.get("set_id"):
        locations.add(intake["set_id"])

    # Scan shots for locations from video_prompt scene headings
    for shot in script.get("shots", []):
        vp = shot.get("video_prompt", "")
        loc_match = re.match(r"(INT\.|EXT\.|INT\.\s*/\s*EXT\.|I/E\.)\s+(.+?)(?:\.\s|$)", vp, re.IGNORECASE)
        if loc_match:
            raw_loc = loc_match.group(1) + " " + loc_match.group(2)
            locations.add(raw_loc)

    # Dedup locations by normalized form (MOTEL ROOM - DAY and MOTEL ROOM - NIGHT are the same set)
    seen_normalized = {}
    for loc in sorted(locations):
        norm = _normalize_location(loc)
        if norm not in seen_normalized:
            seen_normalized[norm] = loc
    locations = set(seen_normalized.values())

    # Get catalog entries for matching
    catalog_entries = []
    if catalog and hasattr(catalog, "active_entries"):
        catalog_entries = catalog.active_entries()

    # Resolve characters
    for name in sorted(characters):
        report["summary"]["total"] += 1
        match = _find_best_match(name, catalog_entries, "CHAR") if catalog_entries else None

        if match and match["score"] >= HIGH_CONFIDENCE:
            report["characters"].append({
                "name": name,
                "resolved_id": match["entry"].id,
                "resolved_name": match["entry"].name,
                "score": round(match["score"], 3),
                "method": match["method"],
                "status": "auto_resolved",
            })
            report["summary"]["resolved"] += 1
            report["summary"]["auto_resolved"] += 1

        elif match and match["score"] >= MATCH_THRESHOLD:
            report["characters"].append({
                "name": name,
                "resolved_id": match["entry"].id,
                "resolved_name": match["entry"].name,
                "score": round(match["score"], 3),
                "method": match["method"],
                "status": "hitl_review",
            })
            report["summary"]["resolved"] += 1
            report["summary"]["hitl_needed"] += 1
            report["hitl_queue"].append({
                "type": "CHAR",
                "name": name,
                "candidate_id": match["entry"].id,
                "candidate_name": match["entry"].name,
                "score": round(match["score"], 3),
                "action_needed": f"Confirm '{name}' matches catalog entry '{match['entry'].name}' ({match['entry'].id})",
            })

        else:
            # No match — needs registration
            report["characters"].append({
                "name": name,
                "resolved_id": None,
                "score": 0,
                "method": "none",
                "status": "unresolved",
            })
            report["summary"]["unresolved"] += 1
            candidates = []
            if catalog_entries:
                # Find closest near-misses for operator reference
                char_entries = [e for e in catalog_entries if e.type == "CHAR"]
                scored = [(e, _similarity(_normalize_name(name), _normalize_name(e.name))) for e in char_entries]
                scored.sort(key=lambda x: x[1], reverse=True)
                candidates = [
                    {"id": e.id, "name": e.name, "score": round(s, 3)}
                    for e, s in scored[:3] if s > 0.3
                ]
            report["hitl_queue"].append({
                "type": "CHAR",
                "name": name,
                "candidate_id": None,
                "candidates_nearby": candidates,
                "action_needed": f"Register '{name}' as new @CHAR or map to existing entry",
            })

    # Resolve locations
    for loc in sorted(locations):
        report["summary"]["total"] += 1
        normalized_loc = _normalize_location(loc)
        match = _find_best_match(normalized_loc, catalog_entries, "SET") if catalog_entries else None

        if not match:
            # Also try LOC type
            match = _find_best_match(normalized_loc, catalog_entries, "LOC") if catalog_entries else None

        if match and match["score"] >= HIGH_CONFIDENCE:
            report["locations"].append({
                "name": loc,
                "normalized": normalized_loc,
                "resolved_id": match["entry"].id,
                "resolved_name": match["entry"].name,
                "score": round(match["score"], 3),
                "method": match["method"],
                "status": "auto_resolved",
            })
            report["summary"]["resolved"] += 1
            report["summary"]["auto_resolved"] += 1

        elif match and match["score"] >= MATCH_THRESHOLD:
            report["locations"].append({
                "name": loc,
                "normalized": normalized_loc,
                "resolved_id": match["entry"].id,
                "resolved_name": match["entry"].name,
                "score": round(match["score"], 3),
                "method": match["method"],
                "status": "hitl_review",
            })
            report["summary"]["resolved"] += 1
            report["summary"]["hitl_needed"] += 1
            report["hitl_queue"].append({
                "type": "SET",
                "name": loc,
                "normalized": normalized_loc,
                "candidate_id": match["entry"].id,
                "candidate_name": match["entry"].name,
                "score": round(match["score"], 3),
                "action_needed": f"Confirm '{normalized_loc}' matches '{match['entry'].name}' ({match['entry'].id})",
            })

        else:
            report["locations"].append({
                "name": loc,
                "normalized": normalized_loc,
                "resolved_id": None,
                "score": 0,
                "method": "none",
                "status": "unresolved",
            })
            report["summary"]["unresolved"] += 1
            report["hitl_queue"].append({
                "type": "SET",
                "name": loc,
                "normalized": normalized_loc,
                "candidate_id": None,
                "action_needed": f"Register '{normalized_loc}' as new @SET or map to existing entry",
            })

    return report


def apply_resolutions(script: dict, report: dict, auto_only: bool = True) -> dict:
    """Apply resolved IDs back into the script.

    If auto_only=True, only applies high-confidence matches (>= 0.90).
    If auto_only=False, applies all matches above threshold.
    """
    # Build name→ID map from resolutions
    char_map = {}
    for r in report.get("characters", []):
        if r["resolved_id"] and (not auto_only or r["status"] == "auto_resolved"):
            char_map[r["name"]] = r["resolved_id"]

    loc_map = {}
    for r in report.get("locations", []):
        if r["resolved_id"] and (not auto_only or r["status"] == "auto_resolved"):
            loc_map[r["name"]] = r["resolved_id"]
            if r.get("normalized"):
                loc_map[r["normalized"]] = r["resolved_id"]

    # Update intake
    intake = script.get("intake", {})
    if intake.get("actor_id") and intake["actor_id"] in char_map:
        intake["actor_id"] = char_map[intake["actor_id"]]
    if intake.get("set_id") and intake["set_id"] in loc_map:
        intake["set_id"] = loc_map[intake["set_id"]]

    # Update _characters index
    if "_characters" in script:
        resolved_chars = {}
        for name, info in script["_characters"].items():
            new_key = char_map.get(name, name)
            info["original_name"] = name
            if new_key != name:
                info["catalog_id"] = new_key
            resolved_chars[name] = info
        script["_characters"] = resolved_chars

    # Annotate resolution report into script
    script["_catalog_resolution"] = {
        "summary": report["summary"],
        "hitl_queue": report["hitl_queue"],
        "resolved_at": _now(),
    }

    return script


def auto_register(script: dict, catalog: Any, report: dict) -> dict:
    """Register all unresolved names as new catalog entries.

    Returns updated report with newly minted IDs.
    """
    if not catalog or not hasattr(catalog, "register"):
        raise RuntimeError("Catalog with register() method required for auto-registration")

    for item in report.get("characters", []):
        if item["status"] == "unresolved":
            entry = catalog.register("CHAR", item["name"], notes="Auto-registered from screenplay ingest")
            item["resolved_id"] = entry.id
            item["status"] = "auto_registered"
            item["method"] = "auto_register"
            item["score"] = 1.0
            report["summary"]["unresolved"] -= 1
            report["summary"]["resolved"] += 1

    for item in report.get("locations", []):
        if item["status"] == "unresolved":
            clean = item.get("normalized", item["name"])
            entry = catalog.register("SET", clean, notes="Auto-registered from screenplay ingest")
            item["resolved_id"] = entry.id
            item["status"] = "auto_registered"
            item["method"] = "auto_register"
            item["score"] = 1.0
            report["summary"]["unresolved"] -= 1
            report["summary"]["resolved"] += 1

    # Remove auto-registered items from HITL queue
    report["hitl_queue"] = [
        h for h in report["hitl_queue"]
        if not any(
            (r["name"] == h["name"] and r["status"] == "auto_registered")
            for r in report.get("characters", []) + report.get("locations", [])
        )
    ]

    return report


def _now() -> str:
    from datetime import datetime, timezone
    return datetime.now(timezone.utc).isoformat()


# ─────────────────────────── CLI ──────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Resolve screenplay names to production catalog @IDs."
    )
    parser.add_argument("input", help="Path to ingested script JSON")
    parser.add_argument("-o", "--output", help="Output path for resolved script")
    parser.add_argument("--catalog", help="Path to master_catalog.json (default: auto-detect)")
    parser.add_argument("--auto-register", action="store_true",
                        help="Auto-register unresolved names as new catalog entries")
    parser.add_argument("--report-only", action="store_true",
                        help="Print resolution report without modifying script")
    parser.add_argument("--threshold", type=float, default=MATCH_THRESHOLD,
                        help=f"Fuzzy match threshold (default: {MATCH_THRESHOLD})")

    args = parser.parse_args()

    script = json.loads(Path(args.input).read_text(encoding="utf-8"))

    # Load catalog
    catalog = None
    if args.catalog:
        if _CATALOG_AVAILABLE:
            catalog = Catalog.load(args.catalog)
        else:
            print("[catalog_resolver] WARNING: production_catalog.py not importable. "
                  "Running in standalone mode (no catalog matching).", file=sys.stderr)
    elif _CATALOG_AVAILABLE:
        try:
            catalog = catalog_for_product("movie")
        except Exception:
            pass

    # Resolve (use caller threshold)
    report = resolve_catalog(script, catalog)

    # Print report
    s = report["summary"]
    print(f"\n=== Catalog Resolution Report ===", file=sys.stderr)
    print(f"  Total entities : {s['total']}", file=sys.stderr)
    print(f"  Resolved       : {s['resolved']} ({s['auto_resolved']} auto, {s['hitl_needed']} HITL)", file=sys.stderr)
    print(f"  Unresolved     : {s['unresolved']}", file=sys.stderr)

    if report["characters"]:
        print(f"\n  Characters:", file=sys.stderr)
        for c in report["characters"]:
            status_icon = {"auto_resolved": "+", "hitl_review": "?", "unresolved": "X"}.get(c["status"], " ")
            rid = c["resolved_id"] or "---"
            rname = c.get("resolved_name", "")
            print(f"    [{status_icon}] {c['name']:25s} → {rid:12s} {rname} (score={c['score']:.2f})", file=sys.stderr)

    if report["locations"]:
        print(f"\n  Locations:", file=sys.stderr)
        for l in report["locations"]:
            status_icon = {"auto_resolved": "+", "hitl_review": "?", "unresolved": "X"}.get(l["status"], " ")
            rid = l["resolved_id"] or "---"
            rname = l.get("resolved_name", "")
            norm = l.get("normalized", "")
            print(f"    [{status_icon}] {norm:30s} → {rid:12s} {rname} (score={l['score']:.2f})", file=sys.stderr)

    if report["hitl_queue"]:
        print(f"\n  HITL Exception Queue ({len(report['hitl_queue'])} items):", file=sys.stderr)
        for h in report["hitl_queue"]:
            print(f"    [{h['type']}] {h['action_needed']}", file=sys.stderr)

    if args.report_only:
        # Dump report as JSON to stdout
        print(json.dumps(report, indent=2, ensure_ascii=False, default=str))
        return

    # Auto-register if requested
    if args.auto_register and catalog:
        report = auto_register(script, catalog, report)
        print(f"\n  Auto-registered {s['total'] - s['resolved']} new entries.", file=sys.stderr)
        # Save updated catalog
        cat_path = args.catalog or str(PRODUCT_CATALOG_PATHS.get("movie", ""))
        if cat_path:
            catalog.save(cat_path)
            print(f"  Catalog saved: {cat_path}", file=sys.stderr)

    # Apply resolutions
    script = apply_resolutions(script, report, auto_only=not args.auto_register)

    # Output
    if args.output:
        Path(args.output).write_text(
            json.dumps(script, indent=2, ensure_ascii=False, default=str),
            encoding="utf-8",
        )
        print(f"\n[catalog_resolver] Written: {args.output}", file=sys.stderr)
    else:
        print(json.dumps(script, indent=2, ensure_ascii=False, default=str))


if __name__ == "__main__":
    main()
