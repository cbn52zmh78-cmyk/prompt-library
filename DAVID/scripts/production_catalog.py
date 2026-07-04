"""production_catalog.py — Permanent ID registry + continuity evaluate for movie pipeline.

Oliver permanent-ID pattern → @TYPE_NNN IDs (opaque, permanent, never deleted).
Catalog + ingest + exception queue before render.

Supports product-specific entity types:
  - movie (default): CHAR, LOC, PROP, STYLE, SET, SHOT
  - atreides: CASE, SUBJECT, NETWORK, VEHICLE, LOCATION, EVENT
  - meridian: STAGE, SECTOR, DRIVER, VEHICLE, EPOCH, SURFACE (legacy)
              ST, RE, INF, APT vertical prefixes (@ST-SS4-S3, @RE-4472, …)

Master catalog paths (one per product):
  - DAVID/productions/master_catalog.json
  - Stonebridge/Products/ATREIDES/master_catalog.json
  - Stonebridge/Products/MERIDIAN/master_catalog.json

Usage:
    from production_catalog import Catalog, continuity_evaluate, catalog_for_product

    catalog = catalog_for_product("movie")
    report = continuity_evaluate(catalog, script)
"""
from __future__ import annotations

import csv
import json
import re
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from _paths import DAVID_ROOT, WORKSPACE

# Stonebridge personnel re-exports (own module to stay within mount limits).
try:
    from sb_registry import (  # noqa: F401
        SBPersonnel,
        SBRegistry,
        SB_ID_PATTERN as SB_ID_PATTERN,
        resolve_any_id,
        sb_registry_path,
    )
except ImportError:
    pass  # sb_registry.py not yet deployed — catalog still works standalone


# ── ID format ─────────────────────────────────────────────────────────────────
# @TYPE_NNN — opaque, permanent, never deleted (archived after "retirement").
# Same religion as Oliver's @223443: one entity = one ID forever.

_NEXT_ID_KEY = "_next_ids"

MOVIE_TYPES = ["CHAR", "LOC", "PROP", "STYLE", "SET", "SHOT",
               "DIR", "VIS", "ANI", "HYB", "SND", "MUS", "PAC", "LNG"]
ATREIDES_TYPES = ["CASE", "SUBJECT", "NETWORK", "VEHICLE", "LOCATION", "EVENT"]
MERIDIAN_TYPES = ["STAGE", "SECTOR", "DRIVER", "VEHICLE", "EPOCH", "SURFACE"]
# Unified Architecture vertical prefixes — @ST-SS4-S3, @RE-4472, @INF-2847, @APT-2847
MERIDIAN_VERTICAL_PREFIXES: dict[str, str] = {
    "ST": "rally",
    "RE": "real_estate",
    "INF": "infrastructure",
    "APT": "airport",
}
MERIDIAN_PREFIX_TYPES = list(MERIDIAN_VERTICAL_PREFIXES.keys())

PRODUCT_CATALOG_PATHS: dict[str, Path] = {
    "movie": DAVID_ROOT / "productions" / "master_catalog.json",
    "atreides": WORKSPACE / "Stonebridge" / "Products" / "ATREIDES" / "master_catalog.json",
    "meridian": WORKSPACE / "Stonebridge" / "Products" / "MERIDIAN" / "master_catalog.json",
}

# ── Creative asset ID mapping ────────────────────────────────────────────────
# Maps new @TYPE prefixes → modifier_type key in style_modifier_registry_v1.json.
# The registry's _registry_files dict maps modifier_type → source JSON filename.
CREATIVE_ASSET_PREFIX_TO_MODIFIER: dict[str, str] = {
    "DIR": "director",
    "VIS": "style",
    "ANI": "anim",
    "HYB": "hybrid",
    "SND": "sound",       # includes sound_combo (same source)
    "MUS": "music",       # includes music_combo (same source)
    "PAC": "pacing",
    "LNG": "language",
}

# Reverse lookup: modifier_type → prefix
MODIFIER_TO_PREFIX: dict[str, str] = {v: k for k, v in CREATIVE_ASSET_PREFIX_TO_MODIFIER.items()}
# Combos share the parent prefix
MODIFIER_TO_PREFIX["sound_combo"] = "SND"
MODIFIER_TO_PREFIX["music_combo"] = "MUS"


def movie_types() -> list[str]:
    """Default entity types for the movie / DAVID render pipeline."""
    return list(MOVIE_TYPES)


def atreides_types() -> list[str]:
    """Entity types for ATREIDES LE-analytics catalog."""
    return list(ATREIDES_TYPES)


def meridian_types() -> list[str]:
    """Entity types for MERIDIAN — legacy motorsport + unified vertical prefixes."""
    return list(MERIDIAN_TYPES) + list(MERIDIAN_PREFIX_TYPES)


def meridian_vertical_prefixes() -> dict[str, str]:
    """Map ID prefix → vertical slug (ST→rally, RE→real_estate, …)."""
    return dict(MERIDIAN_VERTICAL_PREFIXES)


def vertical_for_prefix(prefix: str) -> str:
    """Resolve vertical slug from @PREFIX- ID."""
    return MERIDIAN_VERTICAL_PREFIXES.get(prefix.upper(), "")


def types_for_product(product: str) -> list[str]:
    """Resolve entity type preset for a Stonebridge product slug."""
    key = product.strip().lower()
    if key in ("movie", "david", "studio"):
        return movie_types()
    if key == "atreides":
        return atreides_types()
    if key == "meridian":
        return meridian_types()
    raise ValueError(f"Unknown product for catalog types: {product}")


def build_id_pattern(entity_types: list[str]) -> re.Pattern[str]:
    """Build @TYPE_NNN matcher for a product's entity type set."""
    if not entity_types:
        entity_types = movie_types()
    type_alt = "|".join(re.escape(t.upper()) for t in entity_types)
    return re.compile(rf"@({type_alt})[-_](\w+)")


def build_meridian_prefix_pattern() -> re.Pattern[str]:
    """Match unified vertical IDs: @ST-SS4-S3, @RE-4472, @INF-2847, @APT-2847."""
    prefix_alt = "|".join(re.escape(p) for p in MERIDIAN_VERTICAL_PREFIXES)
    return re.compile(rf"@({prefix_alt})-([\w.-]+)")


def parse_meridian_id(entity_id: str) -> dict[str, str] | None:
    """Parse @PREFIX-slug into {prefix, slug, vertical} or None."""
    m = build_meridian_prefix_pattern().match(entity_id)
    if not m:
        return None
    prefix = m.group(1).upper()
    return {
        "prefix": prefix,
        "slug": m.group(2),
        "vertical": vertical_for_prefix(prefix),
        "full_id": entity_id,
    }


# Backward-compatible default pattern for movie pipeline imports.
ID_PATTERN = build_id_pattern(MOVIE_TYPES)


# ── Utilities (must precede classes that call _now) ──────────────────────────

def _product_from_path(path: Path) -> str:
    parts = {p.lower() for p in path.parts}
    if "atreides" in parts:
        return "atreides"
    if "meridian" in parts:
        return "meridian"
    if "productions" in parts:
        return "movie"
    return ""


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


# ── Catalog entry ─────────────────────────────────────────────────────────────

@dataclass
class CatalogEntry:
    """One permanent entity in the production universe."""
    id: str                          # @CHAR_001, @LOC_012, etc.
    type: str                        # CHAR, LOC, PROP, STYLE, SET, SHOT
    name: str                        # Human-readable canonical name
    created: str = ""                # ISO timestamp
    status: str = "active"           # active | archived | merged
    version: int = 1                 # Increments on state change (wardrobe, set dress)
    aliases: list[str] = field(default_factory=list)   # Previous names / merged IDs
    merged_into: str | None = None   # If merged, target ID
    state: dict[str, Any] = field(default_factory=dict)  # Current versioned state
    history: list[dict[str, Any]] = field(default_factory=list)  # State changelog
    notes: str = ""

    def archive(self, reason: str = "") -> None:
        """Oliver career-archive: ID preserved for flashbacks/prequels."""
        self.status = "archived"
        self.history.append({
            "action": "archived",
            "at": _now(),
            "reason": reason,
            "version": self.version,
        })

    def merge_into(self, target_id: str, reason: str = "") -> None:
        """Two José Garcías → one ID. Source becomes alias of target."""
        self.status = "merged"
        self.merged_into = target_id
        self.history.append({
            "action": "merged",
            "at": _now(),
            "target": target_id,
            "reason": reason,
        })

    def bump_version(self, new_state: dict[str, Any], reason: str = "") -> None:
        """Wardrobe change, set redress, location epoch shift."""
        self.history.append({
            "action": "version_bump",
            "at": _now(),
            "from_version": self.version,
            "old_state": dict(self.state),
            "reason": reason,
        })
        self.version += 1
        self.state.update(new_state)


# ── Catalog ───────────────────────────────────────────────────────────────────

class Catalog:
    """Oliver-pattern permanent ID registry — movie, ATREIDES, or MERIDIAN."""

    def __init__(
        self,
        entity_types: list[str] | None = None,
        *,
        franchise: str = "",
        product: str = "movie",
    ) -> None:
        types = [t.upper() for t in (entity_types or movie_types())]
        self.product = product
        self._entity_types = types
        self.entries: dict[str, CatalogEntry] = {}
        self._next_ids: dict[str, int] = {t: 1 for t in types}
        self.created: str = _now()
        self.franchise = franchise

    def id_pattern(self) -> re.Pattern[str]:
        """@TYPE_NNN regex for this catalog's entity types."""
        types = list(self._next_ids.keys()) or self._entity_types
        return build_id_pattern(types)

    def meridian_prefix_pattern(self) -> re.Pattern[str]:
        """@PREFIX-slug regex for MERIDIAN unified vertical IDs."""
        return build_meridian_prefix_pattern()

    # ── Persistence ───────────────────────────────────────────────────────

    def save(self, path: Path | str) -> None:
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        data = {
            "catalog_version": "1.1",
            "product": self.product,
            "entity_types": self._entity_types,
            "franchise": self.franchise,
            "created": self.created,
            "saved_at": _now(),
            "entry_count": len(self.entries),
            _NEXT_ID_KEY: self._next_ids,
            "entries": {eid: asdict(e) for eid, e in self.entries.items()},
        }
        path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")

    @classmethod
    def load(
        cls,
        path: Path | str,
        entity_types: list[str] | None = None,
        *,
        product: str = "",
    ) -> "Catalog":
        path = Path(path)
        if not path.is_file():
            inferred = product or _product_from_path(path)
            types = entity_types or types_for_product(inferred)
            c = cls(types, franchise="", product=inferred or "movie")
            c.save(path)
            return c
        data = json.loads(path.read_text(encoding="utf-8"))
        saved_types = data.get("entity_types") or list(data.get(_NEXT_ID_KEY, {}).keys())
        saved_product = data.get("product") or product or _product_from_path(path) or "movie"
        types = entity_types or saved_types or types_for_product(saved_product)
        c = cls(types, franchise=data.get("franchise", ""), product=saved_product)
        c.created = data.get("created", _now())
        saved_next = data.get(_NEXT_ID_KEY, {})
        for t in types:
            c._next_ids.setdefault(t.upper(), 1)
        for t, n in saved_next.items():
            c._next_ids[t.upper()] = max(c._next_ids.get(t.upper(), 1), int(n))
        for eid, edata in data.get("entries", {}).items():
            c.entries[eid] = CatalogEntry(**edata)
        return c

    # ── ID operations ─────────────────────────────────────────────────────

    def register(
        self,
        entity_type: str,
        name: str,
        state: dict[str, Any] | None = None,
        notes: str = "",
    ) -> CatalogEntry:
        """Mint a new permanent ID. Never call for existing entities — resolve first."""
        entity_type = entity_type.upper()
        if entity_type not in self._next_ids:
            raise ValueError(f"Unknown entity type: {entity_type}")
        num = self._next_ids[entity_type]
        self._next_ids[entity_type] = num + 1
        eid = f"@{entity_type}_{num:03d}"
        entry = CatalogEntry(
            id=eid,
            type=entity_type,
            name=name,
            created=_now(),
            state=state or {},
            notes=notes,
        )
        self.entries[eid] = entry
        return entry

    def register_prefixed(
        self,
        prefix: str,
        slug: str,
        name: str,
        state: dict[str, Any] | None = None,
        notes: str = "",
    ) -> CatalogEntry:
        """Mint a MERIDIAN vertical permanent ID: @PREFIX-slug (never deleted).

        Examples: @ST-SS4-S3, @RE-4472, @INF-2847, @APT-2847
        Slug is opaque and permanent — survives renaming and admin changes.
        """
        prefix = prefix.upper()
        if prefix not in MERIDIAN_VERTICAL_PREFIXES:
            raise ValueError(
                f"Unknown MERIDIAN prefix: {prefix}. "
                f"Expected one of {list(MERIDIAN_VERTICAL_PREFIXES)}"
            )
        slug = slug.strip().replace(" ", "-")
        if not slug or not re.match(r"^[\w.-]+$", slug):
            raise ValueError(f"Invalid slug for @{prefix}-: {slug!r}")
        eid = f"@{prefix}-{slug}"
        if eid in self.entries:
            existing = self.resolve(eid)
            if existing and existing.status != "merged":
                raise ValueError(f"Permanent ID already registered: {eid}")
        vertical = MERIDIAN_VERTICAL_PREFIXES[prefix]
        entry = CatalogEntry(
            id=eid,
            type=prefix,
            name=name,
            created=_now(),
            state={"vertical": vertical, "slug": slug, **(state or {})},
            notes=notes,
        )
        self.entries[eid] = entry
        if prefix not in self._next_ids:
            self._next_ids[prefix] = 1
        return entry

    def resolve(self, entity_id: str) -> CatalogEntry | None:
        """Look up by ID. Follows merge chains."""
        entry = self.entries.get(entity_id)
        if entry and entry.status == "merged" and entry.merged_into:
            return self.resolve(entry.merged_into)
        return entry

    def find_by_name(self, name: str, entity_type: str = "") -> list[CatalogEntry]:
        """Find entries by name (case-insensitive). The 'two José Garcías' check."""
        name_lower = name.lower()
        matches = []
        for e in self.entries.values():
            if e.status == "merged":
                continue
            if entity_type and e.type != entity_type.upper():
                continue
            if e.name.lower() == name_lower or name_lower in [a.lower() for a in e.aliases]:
                matches.append(e)
        return matches

    def active_entries(self, entity_type: str = "") -> list[CatalogEntry]:
        """All non-merged entries of a type."""
        return [
            e for e in self.entries.values()
            if e.status != "merged"
            and (not entity_type or e.type == entity_type.upper())
        ]

    # ── Ingest from script ────────────────────────────────────────────────

    def ingest_script(self, script: dict[str, Any]) -> list[dict[str, Any]]:
        """Scan a script JSON for @ID references. Return exceptions for unknowns.

        Oliver pattern: ingest the newest box score → find what's new or changed.
        """
        exceptions: list[dict[str, Any]] = []
        seen_ids: set[str] = set()
        id_pattern = self.id_pattern()

        for shot in script.get("shots", []):
            prompt = shot.get("video_prompt", "")
            for match in id_pattern.finditer(prompt):
                full_id = f"@{match.group(1)}_{match.group(2)}"
                seen_ids.add(full_id)

                entry = self.resolve(full_id)
                if entry is None:
                    # Unknown @ID in script — needs registration or is a typo
                    exceptions.append({
                        "type": "UNKNOWN_ID",
                        "id": full_id,
                        "shot_id": shot.get("id", "?"),
                        "context": prompt[:120],
                        "action_needed": "Register new entity or fix typo",
                    })
                elif entry.status == "archived":
                    # Archived entity referenced — might be intentional (flashback)
                    exceptions.append({
                        "type": "ARCHIVED_REF",
                        "id": full_id,
                        "name": entry.name,
                        "shot_id": shot.get("id", "?"),
                        "action_needed": "Confirm intentional (flashback/prequel) or update script",
                    })

        return exceptions


# ── Continuity evaluate (Oliver evaluate verb) ────────────────────────────────

@dataclass
class ContinuityException:
    """One flagged issue — goes to the exception queue, not auto-fixed."""
    severity: str          # BLOCK | WARN | INFO
    category: str          # id_unknown, id_collision, state_mismatch, etc.
    shot_id: str
    entity_id: str
    detail: str
    action_needed: str


def continuity_evaluate(
    catalog: Catalog,
    script: dict[str, Any],
) -> dict[str, Any]:
    """Oliver evaluate verb for film: grade every shot reference against catalog truth.

    Returns:
        {
            "pass": bool,
            "score": int (0-100),
            "confidence": float,
            "exceptions": [...],
            "resolved": [...],
            "dimensions": {continuity, identity, state_version, coverage, compliance},
        }
    """
    exceptions: list[dict[str, Any]] = []
    resolved: list[dict[str, Any]] = []
    shots = script.get("shots", [])

    dim_continuity = 100
    dim_identity = 100
    dim_state = 100
    dim_coverage = 100
    dim_compliance = 100

    all_ids_in_script: set[str] = set()
    id_pattern = catalog.id_pattern()

    for shot in shots:
        prompt = shot.get("video_prompt", "")
        shot_id = shot.get("id", "?")

        # Extract all @IDs from this shot
        ids_in_shot = []
        for match in id_pattern.finditer(prompt):
            full_id = f"@{match.group(1)}_{match.group(2)}"
            ids_in_shot.append(full_id)
            all_ids_in_script.add(full_id)

        # Also check for legacy @Name-NNN patterns (e.g. @David-001, @Set-Archive-001)
        legacy_pattern = re.compile(
            r"@([A-Z][a-z]+-\d+|"
            r"[A-Z][A-Za-z0-9]*(?:-[A-Za-z][A-Za-z0-9]*)+-\d{3})"
        )
        for lm in legacy_pattern.finditer(prompt):
            legacy_id = f"@{lm.group(1)}"
            all_ids_in_script.add(legacy_id)
            # Legacy IDs get WARN — migration should have caught these at authoring
            exceptions.append({
                "severity": "WARN",
                "category": "legacy_id_format",
                "shot_id": shot_id,
                "entity_id": legacy_id,
                "detail": "Legacy ID format — should be @TYPE_NNN",
                "action_needed": "Run catalog_refs.resolve_script_refs() or register in catalog",
            })

        for eid in ids_in_shot:
            entry = catalog.resolve(eid)

            if entry is None:
                exceptions.append({
                    "severity": "BLOCK",
                    "category": "id_unknown",
                    "shot_id": shot_id,
                    "entity_id": eid,
                    "detail": f"Referenced {eid} not in catalog",
                    "action_needed": "Register entity or fix ID reference",
                })
                dim_identity -= 15

            elif entry.status == "archived":
                exceptions.append({
                    "severity": "WARN",
                    "category": "archived_reference",
                    "shot_id": shot_id,
                    "entity_id": eid,
                    "detail": f"{eid} ({entry.name}) is archived — flashback?",
                    "action_needed": "Confirm intentional or update reference",
                })
                dim_state -= 10

            else:
                resolved.append({
                    "shot_id": shot_id,
                    "entity_id": eid,
                    "name": entry.name,
                    "version": entry.version,
                    "status": "OK",
                })

        # Check for name collisions (the "two José Garcías" problem)
        speech = shot.get("speech_text", "")
        if speech:
            # Look for character names mentioned in speech that might collide
            for entry in catalog.active_entries("CHAR"):
                if entry.name.lower() in speech.lower():
                    dupes = catalog.find_by_name(entry.name, "CHAR")
                    if len(dupes) > 1:
                        exceptions.append({
                            "severity": "WARN",
                            "category": "name_collision",
                            "shot_id": shot_id,
                            "entity_id": entry.id,
                            "detail": f"Name '{entry.name}' matches {len(dupes)} catalog entries: "
                                      f"{[d.id for d in dupes]}",
                            "action_needed": "Merge duplicates or disambiguate",
                        })
                        dim_continuity -= 20

    # Coverage: are all catalog entities actually used?
    active_ids = {e.id for e in catalog.active_entries()}
    unused = active_ids - all_ids_in_script
    if unused and len(catalog.entries) > 0:
        # Not a block — just informational
        coverage_pct = (len(all_ids_in_script & active_ids) / max(1, len(active_ids))) * 100
        dim_coverage = min(100, round(coverage_pct))

    # Compliance: check for shots missing any @ID reference at all
    shots_without_ids = [
        s["id"] for s in shots
        if not id_pattern.search(s.get("video_prompt", ""))
        and not legacy_pattern.search(s.get("video_prompt", ""))
    ]
    if shots_without_ids:
        dim_compliance -= len(shots_without_ids) * 10
        for sid in shots_without_ids:
            exceptions.append({
                "severity": "INFO",
                "category": "no_catalog_reference",
                "shot_id": sid,
                "entity_id": "",
                "detail": "Shot has no @ID references — not catalog-tracked",
                "action_needed": "Add @CHAR/@LOC/@STYLE references to video_prompt",
            })

    # Clamp dimensions
    dims = {
        "continuity": max(0, dim_continuity),
        "identity": max(0, dim_identity),
        "state_version": max(0, dim_state),
        "coverage": max(0, dim_coverage),
        "compliance": max(0, dim_compliance),
    }
    dim_vals = list(dims.values())
    composite = round(sum(dim_vals) / len(dim_vals))
    variance = sum((d - composite) ** 2 for d in dim_vals) / len(dim_vals)
    confidence = round(max(0.1, 1.0 - (variance / 2500)), 2)

    blocks = [e for e in exceptions if e.get("severity") == "BLOCK"]

    return {
        "pass": len(blocks) == 0,
        "continuity_score": composite,
        "continuity_tier": (
            "A" if composite >= 85 else
            "B" if composite >= 70 else
            "C" if composite >= 50 else "F"
        ),
        "confidence": confidence,
        "dimensions": dims,
        "total_ids_referenced": len(all_ids_in_script),
        "resolved_count": len(resolved),
        "exception_count": len(exceptions),
        "block_count": len(blocks),
        "exceptions": exceptions,
        "resolved": resolved,
    }


# ── Exception queue export (Oliver's Excel desk) ──────────────────────────────

def write_exception_csv(
    exceptions: list[dict[str, Any]],
    path: Path | str,
) -> None:
    """Write exceptions to CSV for human review — Oliver's Excel report pattern.

    Dad reviews when he can: merge/split/assign. Same workflow for movie canon.
    """
    path = Path(path)
    if not exceptions:
        return
    fields = ["severity", "category", "shot_id", "entity_id", "detail", "action_needed"]
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(exceptions)


# ── Project verb (Oliver project → look-ahead) ───────────────────────────────

def continuity_project(
    catalog: Catalog,
    script: dict[str, Any],
    shot_id: str,
) -> list[dict[str, Any]]:
    """Oliver project verb: if we lock state X here, what downstream shots are affected?

    "Scene 12 locks @LOC_5 night rain → Scene 18 must match."
    """
    shots = script.get("shots", [])
    target_idx = None
    target_ids: set[str] = set()

    id_pattern = catalog.id_pattern()
    for i, shot in enumerate(shots):
        if shot.get("id") == shot_id:
            target_idx = i
            for m in id_pattern.finditer(shot.get("video_prompt", "")):
                target_ids.add(f"@{m.group(1)}_{m.group(2)}")
            break

    if target_idx is None:
        return []

    downstream_impacts: list[dict[str, Any]] = []
    for shot in shots[target_idx + 1:]:
        prompt = shot.get("video_prompt", "")
        shared = set()
        for m in id_pattern.finditer(prompt):
            eid = f"@{m.group(1)}_{m.group(2)}"
            if eid in target_ids:
                shared.add(eid)
        if shared:
            downstream_impacts.append({
                "shot_id": shot["id"],
                "shared_ids": sorted(shared),
                "must_match": True,
                "note": f"Shares {len(shared)} entity(ies) with {shot_id} — state must be consistent",
            })

    return downstream_impacts


# ── Compare verb (Oliver compare → take A vs take B) ─────────────────────────

def continuity_compare(
    catalog: Catalog,
    script_a: dict[str, Any],
    script_b: dict[str, Any],
) -> dict[str, Any]:
    """Oliver compare: episode 3 vs episode 1 for same @CHAR aging.

    Also: take A vs take B for same scene.
    """
    id_pattern = catalog.id_pattern()

    def _extract_ids(script: dict[str, Any]) -> dict[str, set[str]]:
        id_to_shots: dict[str, set[str]] = {}
        for shot in script.get("shots", []):
            for m in id_pattern.finditer(shot.get("video_prompt", "")):
                eid = f"@{m.group(1)}_{m.group(2)}"
                id_to_shots.setdefault(eid, set()).add(shot.get("id", "?"))
        return id_to_shots

    ids_a = _extract_ids(script_a)
    ids_b = _extract_ids(script_b)

    shared = set(ids_a.keys()) & set(ids_b.keys())
    only_a = set(ids_a.keys()) - set(ids_b.keys())
    only_b = set(ids_b.keys()) - set(ids_a.keys())

    entity_diffs: list[dict[str, Any]] = []
    for eid in sorted(shared):
        entry = catalog.resolve(eid)
        entity_diffs.append({
            "entity_id": eid,
            "name": entry.name if entry else "?",
            "in_a_shots": sorted(ids_a[eid]),
            "in_b_shots": sorted(ids_b[eid]),
            "version": entry.version if entry else 0,
            "status": "consistent" if entry else "unregistered",
        })

    return {
        "shared_entities": len(shared),
        "only_in_a": sorted(only_a),
        "only_in_b": sorted(only_b),
        "entity_comparison": entity_diffs,
        "slug_a": script_a.get("slug", "?"),
        "slug_b": script_b.get("slug", "?"),
    }


# ── Bootstrap: auto-register from existing identity lock ──────────────────────

def bootstrap_from_identity_lock(
    catalog: Catalog,
    lock: dict[str, Any],
) -> list[CatalogEntry]:
    """Seed catalog from existing identity lock JSON (migration helper)."""
    registered: list[CatalogEntry] = []
    char = lock.get("character", {})

    if char.get("name"):
        existing = catalog.find_by_name(char["name"], "CHAR")
        if not existing:
            entry = catalog.register(
                "CHAR",
                char["name"],
                state={
                    "role": char.get("role", ""),
                    "age_read": char.get("age_read", ""),
                    "wardrobe": char.get("wardrobe", ""),
                },
                notes=f"Bootstrapped from identity lock (status={lock.get('status')})",
            )
            registered.append(entry)

    refs = lock.get("references", {})
    set_ref = refs.get("set_plate") or refs.get("archive_set") or {}
    if set_ref:
        set_name = char.get("set_name", "Unknown Set")
        existing = catalog.find_by_name(set_name, "SET")
        if not existing:
            entry = catalog.register(
                "SET",
                set_name,
                state={
                    "file": set_ref.get("file", ""),
                    "url": set_ref.get("url", ""),
                },
                notes="Bootstrapped from identity lock set_plate reference",
            )
            registered.append(entry)

    return registered


# ── Creative asset seeding + resolution ──────────────────────────────────────

def seed_creative_assets(
    catalog: Catalog,
    registry_path: Path | str,
) -> list[CatalogEntry]:
    """Populate catalog with @ID entries for every modifier slug in the registry.

    Reads style_modifier_registry_v1.json → id_index, mints @DIR_001, @HYB_003, etc.
    Skips slugs that already have a catalog entry (idempotent).
    Stores the slug in entry.state["slug"] so resolve can map @ID → slug.
    """
    path = Path(registry_path)
    if not path.is_file():
        return []
    data = json.loads(path.read_text(encoding="utf-8"))
    id_index = data.get("id_index", {})
    registry_files = data.get("_registry_files", {})
    registered: list[CatalogEntry] = []

    for modifier_type, slugs in id_index.items():
        prefix = MODIFIER_TO_PREFIX.get(modifier_type)
        if not prefix:
            continue  # unknown modifier type — skip safely
        if prefix not in catalog._next_ids:
            catalog._next_ids[prefix] = 1
        for slug in slugs:
            # Check if this slug is already registered under this prefix
            existing = [
                e for e in catalog.entries.values()
                if e.type == prefix
                and e.status != "merged"
                and e.state.get("slug") == slug
            ]
            if existing:
                continue
            entry = catalog.register(
                prefix,
                slug,  # name = slug for now; human-readable names are in source JSONs
                state={
                    "slug": slug,
                    "modifier_type": modifier_type,
                    "source_file": registry_files.get(
                        _modifier_type_to_registry_key(modifier_type), ""
                    ),
                },
                notes=f"Seeded from style_modifier_registry_v1.json id_index.{modifier_type}",
            )
            registered.append(entry)

    return registered


def _modifier_type_to_registry_key(modifier_type: str) -> str:
    """Map id_index key → _registry_files key."""
    mapping = {
        "director": "director_persona",
        "style": "visual_live_action",
        "anim": "visual_animation",
        "hybrid": "visual_hybrid",
        "sound": "audio",
        "sound_combo": "audio",
        "music": "music",
        "music_combo": "music",
        "pacing": "pacing",
        "language": "language",
    }
    return mapping.get(modifier_type, modifier_type)


def resolve_creative_id(
    catalog: Catalog,
    entity_id: str,
) -> dict[str, Any] | None:
    """Resolve @TYPE_NNN creative asset ID → slug + source file + full entry.

    Returns dict with slug, modifier_type, source_file, and the CatalogEntry,
    or None if the ID is not a creative asset or not found.
    """
    entry = catalog.resolve(entity_id)
    if entry is None:
        return None
    prefix = entry.type
    if prefix not in CREATIVE_ASSET_PREFIX_TO_MODIFIER:
        return None  # not a creative asset ID (CHAR, SET, etc.)
    return {
        "entity_id": entry.id,
        "slug": entry.state.get("slug", ""),
        "modifier_type": entry.state.get("modifier_type", ""),
        "source_file": entry.state.get("source_file", ""),
        "name": entry.name,
        "status": entry.status,
        "entry": entry,
    }


def build_creative_id_lookup(catalog: Catalog) -> dict[str, str]:
    """Build a slug → @ID reverse-lookup dict for all creative asset entries.

    Used by style_modifiers.py to translate slugs back to IDs for logging.
    """
    lookup: dict[str, str] = {}
    for entry in catalog.entries.values():
        if entry.type in CREATIVE_ASSET_PREFIX_TO_MODIFIER and entry.status != "merged":
            slug = entry.state.get("slug", "")
            if slug:
                lookup[slug] = entry.id
    return lookup


# ── Product catalog helpers ───────────────────────────────────────────────────

def catalog_path_for_product(product: str) -> Path:
    """Standard master_catalog.json path for a product slug."""
    key = product.strip().lower()
    if key not in PRODUCT_CATALOG_PATHS:
        raise ValueError(f"Unknown product: {product}")
    return PRODUCT_CATALOG_PATHS[key]


def catalog_for_product(product: str) -> Catalog:
    """Load or bootstrap the master catalog for a product."""
    key = product.strip().lower()
    return Catalog.load(catalog_path_for_product(key), product=key)


def bootstrap_product_catalog(product: str, *, franchise: str = "") -> Catalog:
    """Create a fresh product catalog with the correct entity types."""
    key = product.strip().lower()
    catalog = Catalog(types_for_product(key), franchise=franchise, product=key)
    catalog.save(catalog_path_for_product(key))
    return catalog


def bootstrap_from_atreides_registry(
    catalog: Catalog,
    registry_path: Path | str,
) -> list[CatalogEntry]:
    """Seed ATREIDES catalog metadata from fleet registry (no CASE/SUBJECT auto-mint)."""
    path = Path(registry_path)
    if not path.is_file():
        return []
    data = json.loads(path.read_text(encoding="utf-8"))
    catalog.franchise = data.get("product_id", catalog.franchise or "stonebridge.atreides.le_analysis")
    catalog.product = "atreides"
    return []


def bootstrap_from_meridian_scaffold(
    catalog: Catalog,
    scaffold_path: Path | str | None = None,
) -> list[CatalogEntry]:
    """Initialize MERIDIAN catalog product metadata (parked — types only, no entities)."""
    catalog.franchise = catalog.franchise or "stonebridge.meridian"
    catalog.product = "meridian"
    if scaffold_path and Path(scaffold_path).is_file():
        catalog.franchise = f"{catalog.franchise}:scaffold"
    return []


def register_ingest_sources_for_product(
    registry: Any,
    product: str,
) -> list[Any]:
    """Register ingest_registry presets for a product slug."""
    from ingest_registry import (
        atreides_sources,
        meridian_sources,
        movie_sources,
        oliver_sources,
    )

    presets = {
        "movie": movie_sources,
        "david": movie_sources,
        "oliver": oliver_sources,
        "meridian": meridian_sources,
        "atreides": atreides_sources,
    }
    key = product.strip().lower()
    fn = presets.get(key)
    if not fn:
        raise ValueError(f"No ingest presets for product: {product}")
    registered = []
    for spec in fn():
        registered.append(registry.register_source(**spec))
    return registered


# ── CLI smoke ─────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    for product in ("movie", "atreides", "meridian"):
        types = types_for_product(product)
        cat = Catalog(types, product=product)
        entry = cat.register(types[0], f"smoke_{product}")
        pat = cat.id_pattern().pattern
        print(f"{product}: {entry.id} types={types} pattern_ok={types[0] in pat}")
    default = Catalog()
    default_keys = list(default._next_ids.keys())
    assert set(default_keys) == set(movie_types()), f"mismatch: {default_keys}"
    print("backward_compat: default movie types OK")

    # creative asset prefix sanity
    for prefix, mtype in CREATIVE_ASSET_PREFIX_TO_MODIFIER.items():
        assert prefix in default._next_ids, f"prefix {prefix} missing from movie_types"
    print(f"creative_asset_prefixes: {list(CREATIVE_ASSET_PREFIX_TO_MODIFIER.keys())} OK")

    mcat = Catalog(meridian_types(), product="meridian")
    st = mcat.register_prefixed("ST", "SS4-S3", "Stage 4 Sector 3")
    re_ = mcat.register_prefixed("RE", "4472", "Lot 4472 Main St")
    assert st.id == "@ST-SS4-S3"
    assert re_.id == "@RE-4472"
    assert parse_meridian_id("@INF-2847")["vertical"] == "infrastructure"
    print(f"meridian_prefixes: {st.id} {re_.id} pattern={mcat.meridian_prefix_pattern().pattern}")
