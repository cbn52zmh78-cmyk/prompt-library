"""catalog_refs.py — Resolve informal @Name-NNN script refs to catalog @TYPE_NNN IDs.

Script generators call resolve_script_refs() at authoring time so video_prompts
emit permanent catalog IDs instead of legacy informal refs like @David-001.

Usage:
    from catalog_refs import resolve_script_refs

    script = resolve_script_refs(script, catalog_path="productions/master_catalog.json")
"""
from __future__ import annotations

import copy
import json
import logging
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from _paths import DAVID_ROOT, WORKSPACE
from production_catalog import Catalog, CatalogEntry, bootstrap_from_identity_lock

log = logging.getLogger(__name__)

DEFAULT_CATALOG_PATH = DAVID_ROOT / "productions" / "master_catalog.json"
CASTING_REGISTRY = WORKSPACE / "STUDIO" / "Cast" / "Casting_Bible" / "registry" / "casting_registry.json"
SET_LIBRARY = WORKSPACE / "STUDIO" / "Pipeline" / "Set_Library_v1.json"
STYLE_LIBRARY = WORKSPACE / "STUDIO" / "Pipeline" / "Style_Library_v1.json"
DAVID_IDENTITY_LOCK = DAVID_ROOT / "productions" / "host_identity_v1" / "david_identity_lock.json"

# Simple legacy: @David-001. Compound legacy: @Set-Archive-001, @Style-Cool-Clinical-001.
LEGACY_ID_PATTERN = re.compile(
    r"@([A-Z][a-z]+-\d+|"  # @David-001
    r"[A-Z][A-Za-z0-9]*(?:-[A-Za-z][A-Za-z0-9]*)+-\d{3})"  # @Set-Archive-001
)


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _informal_stem(informal_id: str) -> str:
    """Strip @ and numeric suffix: @Set-Archive-001 → Set-Archive."""
    bare = informal_id.lstrip("@")
    if "-" not in bare:
        return bare
    stem, suffix = bare.rsplit("-", 1)
    return stem if suffix.isdigit() else bare


def _infer_entity_type(informal_id: str) -> str:
    stem = _informal_stem(informal_id)
    if stem.startswith("Set-"):
        return "SET"
    if stem.startswith("Style-"):
        return "STYLE"
    if stem.startswith("Sci-"):
        return "PROP"
    return "CHAR"


def _find_by_informal_id(catalog: Catalog, informal_id: str) -> list[CatalogEntry]:
    """Match catalog entry by informal @ID stored in aliases or canonical name."""
    bare = informal_id.lstrip("@")
    stem = _informal_stem(informal_id)
    entity_type = _infer_entity_type(informal_id)
    matches: list[CatalogEntry] = []

    for entry in catalog.entries.values():
        if entry.status == "merged":
            continue
        alias_keys = {a.lower() for a in entry.aliases}
        alias_keys.add(entry.name.lower())
        alias_keys.add(entry.id.lower())
        if bare.lower() in alias_keys or informal_id.lower() in alias_keys:
            matches.append(entry)

    if matches:
        return matches

    by_name = catalog.find_by_name(stem, entity_type)
    if by_name:
        return by_name

    # First-token fallback for simple actor IDs: David-001 → David
    if "-" in stem:
        first_token = stem.split("-", 1)[0]
        if first_token != stem:
            return catalog.find_by_name(first_token, entity_type)
    return catalog.find_by_name(stem, "")


def resolve_legacy_ref(catalog: Catalog, informal_id: str) -> CatalogEntry | None:
    """Resolve one informal @ID to a catalog entry. None if ambiguous or missing."""
    matches = _find_by_informal_id(catalog, informal_id)
    if len(matches) == 1:
        return matches[0]
    if len(matches) > 1:
        log.warning(
            "Ambiguous informal ID %s — matches %s; needs HITL review",
            informal_id,
            [m.id for m in matches],
        )
    return None


def _replace_in_prompt(prompt: str, informal_id: str, catalog_id: str) -> str:
    return prompt.replace(informal_id, catalog_id)


def resolve_script_refs(
    script: dict[str, Any],
    catalog_path: Path | str | None = None,
    *,
    ensure_catalog: bool = True,
) -> dict[str, Any]:
    """Replace informal @Name-NNN refs in video_prompt fields with catalog @TYPE_NNN IDs.

    Unresolved refs are left as-is and logged. Ambiguous name collisions are not
    auto-resolved. Original informal IDs are recorded in script['catalog_ref_audit'].
    """
    path = Path(catalog_path) if catalog_path else DEFAULT_CATALOG_PATH
    if ensure_catalog and not path.is_file():
        ensure_movie_catalog(path)

    catalog = Catalog.load(path)
    script = copy.deepcopy(script)
    audit: dict[str, str] = dict(script.get("catalog_ref_audit", {}).get("mappings", {}))
    warnings: list[str] = []

    for shot in script.get("shots", []):
        prompt = shot.get("video_prompt", "")
        if not prompt:
            continue

        for match in LEGACY_ID_PATTERN.finditer(prompt):
            informal_id = f"@{match.group(1)}"
            if informal_id in audit:
                prompt = _replace_in_prompt(prompt, informal_id, audit[informal_id])
                continue

            entry = resolve_legacy_ref(catalog, informal_id)
            if entry is None:
                warnings.append(f"{informal_id} in shot {shot.get('id', '?')}")
                continue

            prompt = _replace_in_prompt(prompt, informal_id, entry.id)
            audit[informal_id] = entry.id

        shot["video_prompt"] = prompt

    _migrate_intake_refs(script, audit, catalog, warnings)

    if audit:
        script["catalog_ref_audit"] = {
            "migrated_at": _now(),
            "mappings": dict(sorted(audit.items())),
            "unresolved": warnings,
        }

    for msg in warnings:
        log.warning("Unresolved legacy catalog ref: %s", msg)

    return script


def _migrate_intake_refs(
    script: dict[str, Any],
    audit: dict[str, str],
    catalog: Catalog,
    warnings: list[str],
) -> None:
    """Update intake actor_id / set_id / style_id when mappings are known."""
    intake = script.get("intake")
    if not isinstance(intake, dict):
        return

    field_map = {
        "actor_id": ("CHAR", False),
        "set_id": ("SET", True),
        "style_id": ("STYLE", True),
    }
    for field, (entity_type, has_at_prefix) in field_map.items():
        raw = intake.get(field)
        if not raw:
            continue
        informal = raw if raw.startswith("@") else f"@{raw}" if has_at_prefix else raw
        lookup_key = informal if has_at_prefix else raw

        if lookup_key in audit:
            new_val = audit[lookup_key].lstrip("@") if not has_at_prefix else audit[lookup_key]
            intake[field] = new_val
            continue

        if has_at_prefix:
            entry = resolve_legacy_ref(catalog, informal)
            if entry:
                intake[field] = entry.id
                audit[informal] = entry.id
            else:
                warnings.append(f"{informal} in intake.{field}")
        else:
            # actor_id without @ prefix: David-001
            entry = resolve_legacy_ref(catalog, f"@{raw}")
            if entry:
                intake[field] = entry.id.lstrip("@")
                audit[f"@{raw}"] = entry.id
            else:
                warnings.append(f"@{raw} in intake.{field}")


def _register_if_missing(
    catalog: Catalog,
    entity_type: str,
    name: str,
    aliases: list[str],
    state: dict[str, Any] | None = None,
    notes: str = "",
) -> CatalogEntry:
    for alias in aliases:
        existing = _find_by_informal_id(catalog, alias if alias.startswith("@") else f"@{alias}")
        if len(existing) == 1:
            entry = existing[0]
            for a in aliases:
                if a not in entry.aliases:
                    entry.aliases.append(a)
            return entry

    by_name = catalog.find_by_name(name, entity_type)
    if len(by_name) == 1:
        entry = by_name[0]
        for a in aliases:
            if a not in entry.aliases:
                entry.aliases.append(a)
        return entry

    entry = catalog.register(entity_type, name, state=state or {}, notes=notes)
    entry.aliases = list(dict.fromkeys(aliases))
    return entry


def ensure_movie_catalog(catalog_path: Path | str | None = None) -> Catalog:
    """Bootstrap master_catalog.json from identity lock + STUDIO libraries."""
    path = Path(catalog_path) if catalog_path else DEFAULT_CATALOG_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    catalog = Catalog.load(path)
    if not catalog.franchise:
        catalog.franchise = "DAVID_Productions"

    if DAVID_IDENTITY_LOCK.is_file():
        lock = json.loads(DAVID_IDENTITY_LOCK.read_text(encoding="utf-8"))
        bootstrap_from_identity_lock(catalog, lock)
        char = lock.get("character", {})
        if char.get("name"):
            _register_if_missing(
                catalog,
                "CHAR",
                char["name"],
                aliases=["David-001", "@David-001", char["name"]],
                state={
                    "role": char.get("role", ""),
                    "age_read": char.get("age_read", ""),
                    "wardrobe": char.get("wardrobe", ""),
                },
                notes="DAVID host — identity lock",
            )
        set_name = char.get("set_name", "The Archive")
        _register_if_missing(
            catalog,
            "SET",
            set_name,
            aliases=["Set-Archive-001", "@Set-Archive-001", set_name, "The Archive"],
            notes="Archive set — identity lock",
        )

    if CASTING_REGISTRY.is_file():
        registry = json.loads(CASTING_REGISTRY.read_text(encoding="utf-8"))
        for actor in registry.get("actors", []):
            actor_id = actor.get("actor_id", "")
            if not actor_id:
                continue
            first_name = actor_id.split("-", 1)[0]
            _register_if_missing(
                catalog,
                "CHAR",
                actor.get("stage_name", first_name),
                aliases=[actor_id, f"@{actor_id}", first_name, actor.get("talent_id", "")],
                state={"actor_id": actor_id, "synthetic": actor.get("synthetic", True)},
                notes=f"Casting registry — {actor_id}",
            )

    if SET_LIBRARY.is_file():
        lib = json.loads(SET_LIBRARY.read_text(encoding="utf-8"))
        for set_key, spec in lib.get("sets", {}).items():
            bare = set_key.lstrip("@")
            stem = _informal_stem(set_key)
            entry = _register_if_missing(
                catalog,
                "SET",
                spec.get("name", stem),
                aliases=[bare, set_key, stem, spec.get("name", "")],
                state={"reference_file": spec.get("reference_file", "")},
                notes=f"Set library — {set_key}",
            )
            # Reconcile ingest-watcher SET IDs (e.g. Archive Chamber) with library informal IDs.
            if "archive" in set_key.lower() or "archive" in spec.get("name", "").lower():
                for e in catalog.active_entries("SET"):
                    if "archive" in e.name.lower() and e.id != entry.id:
                        for alias in (bare, set_key, stem, spec.get("name", "")):
                            if alias and alias not in e.aliases:
                                e.aliases.append(alias)

    if STYLE_LIBRARY.is_file():
        lib = json.loads(STYLE_LIBRARY.read_text(encoding="utf-8"))
        for style_key, spec in lib.get("styles", {}).items():
            bare = style_key.lstrip("@")
            stem = _informal_stem(style_key)
            _register_if_missing(
                catalog,
                "STYLE",
                spec.get("name", stem),
                aliases=[bare, style_key, stem],
                notes=f"Style library — {style_key}",
            )

    catalog.save(path)
    return catalog


def migrate_scripts(
    scripts_dir: Path | str | None = None,
    catalog_path: Path | str | None = None,
) -> dict[str, Any]:
    """One-time migration pass over longform_scripts/*.json."""
    scripts_dir = Path(scripts_dir) if scripts_dir else DAVID_ROOT / "scripts" / "longform_scripts"
    cat_path = Path(catalog_path) if catalog_path else DEFAULT_CATALOG_PATH

    ensure_movie_catalog(cat_path)

    summary: dict[str, Any] = {
        "files_scanned": 0,
        "files_updated": 0,
        "total_replacements": 0,
        "per_file": {},
        "unresolved": [],
    }

    for script_path in sorted(scripts_dir.glob("*.json")):
        summary["files_scanned"] += 1
        original = json.loads(script_path.read_text(encoding="utf-8"))
        migrated = resolve_script_refs(original, cat_path, ensure_catalog=False)

        mappings = migrated.get("catalog_ref_audit", {}).get("mappings", {})
        unresolved = migrated.get("catalog_ref_audit", {}).get("unresolved", [])

        if mappings:
            script_path.write_text(
                json.dumps(migrated, indent=2, ensure_ascii=False) + "\n",
                encoding="utf-8",
            )
            summary["files_updated"] += 1
            summary["total_replacements"] += len(mappings)
            summary["per_file"][script_path.name] = mappings

        if unresolved:
            summary["unresolved"].extend(
                {"file": script_path.name, "issue": u} for u in unresolved
            )

    return summary


def _print_migration_summary(summary: dict[str, Any]) -> None:
    print(f"Scanned: {summary['files_scanned']} scripts")
    print(f"Updated: {summary['files_updated']} scripts")
    print(f"Total ID mappings applied: {summary['total_replacements']}")
    if summary["per_file"]:
        print("\nPer-file mappings:")
        for fname, mappings in summary["per_file"].items():
            print(f"  {fname}:")
            for old, new in sorted(mappings.items()):
                print(f"    {old} → {new}")
    if summary["unresolved"]:
        print(f"\nUnresolved ({len(summary['unresolved'])}):")
        for item in summary["unresolved"]:
            print(f"  {item['file']}: {item['issue']}")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    result = migrate_scripts()
    _print_migration_summary(result)