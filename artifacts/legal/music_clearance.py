#!/usr/bin/env python3
"""Music clearance manifest — Gate 0 row 2 helper (owned / royalty-free / CC0 beds)."""

from __future__ import annotations

import json
import re
from functools import lru_cache
from pathlib import Path
from typing import Any

from lib.studio_paths import studio_path

MANIFEST_REL = "Music_Sound/clearance_manifest.json"
TRACK_ID_PATTERN = re.compile(r"\b(BED-[A-Z]+-\d{3})\b", re.I)
MUSIC_BED_DECL_PATTERN = re.compile(
    r"\b(?:music[_ ]bed(?:_id)?|bed_id)\s*[:=]\s*([A-Z0-9_-]+)\b",
    re.I,
)


@lru_cache(maxsize=1)
def manifest_path() -> Path:
    return studio_path("Music_Sound", "clearance_manifest.json")


@lru_cache(maxsize=1)
def load_manifest() -> dict[str, Any]:
    path = manifest_path()
    if not path.is_file():
        return {"version": "0", "tracks": {}}
    return json.loads(path.read_text(encoding="utf-8"))


def reload_manifest() -> dict[str, Any]:
    load_manifest.cache_clear()
    manifest_path.cache_clear()
    return load_manifest()


def track_catalog() -> dict[str, dict[str, Any]]:
    return dict(load_manifest().get("tracks") or {})


def extract_track_refs(text: str) -> list[str]:
    """Return manifest-style BED-* IDs referenced in brief text (deduped, order preserved)."""
    seen: set[str] = set()
    ordered: list[str] = []
    for pattern in (MUSIC_BED_DECL_PATTERN, TRACK_ID_PATTERN):
        for match in pattern.finditer(text):
            tid = match.group(1).upper()
            if tid not in seen:
                seen.add(tid)
                ordered.append(tid)
    return ordered


def validate_tracks(
    track_ids: list[str],
    channels: list[str],
    *,
    manifest: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Classify track refs as cleared, unlisted, or channel-blocked."""
    manifest = manifest or load_manifest()
    catalog = manifest.get("tracks") or {}
    norm_channels = [c.lower().strip() for c in channels if c.strip()]

    cleared: list[str] = []
    unlisted: list[str] = []
    channel_blocked: list[dict[str, Any]] = []

    for tid in track_ids:
        key = tid.upper()
        if key not in catalog:
            unlisted.append(key)
            continue
        allowed = [c.lower() for c in catalog[key].get("allowed_channels") or []]
        blocked = [c for c in norm_channels if c not in allowed]
        if blocked:
            channel_blocked.append({"track_id": key, "channels": blocked})
        else:
            cleared.append(key)

    return {
        "cleared": cleared,
        "unlisted": unlisted,
        "channel_blocked": channel_blocked,
        "all_cleared": bool(track_ids) and not unlisted and not channel_blocked,
    }


def format_bed_declaration(track_id: str, *, manifest: dict[str, Any] | None = None) -> str:
    """Standard Gate 0 brief line referencing clearance_manifest.json."""
    manifest = manifest or load_manifest()
    catalog = manifest.get("tracks") or {}
    key = track_id.upper()
    if key not in catalog:
        raise KeyError(f"Music bed '{track_id}' not in clearance_manifest.json")

    track = catalog[key]
    attr = (
        "attribution required"
        if track.get("attribution_required")
        else "no attribution required"
    )
    channels = ", ".join(track.get("allowed_channels") or [])
    return (
        f"Music bed: {key} — {track.get('title', '')} ({track.get('lane', '')}); "
        f"cleared per STUDIO/Music_Sound/clearance_manifest.json "
        f"(source: {track.get('source', '')}; license: {track.get('license', '')}; "
        f"{attr}); allowed channels: {channels}"
    )


def resolve_music_from_concept(concept: dict[str, Any]) -> str | None:
    """Build music line for Gate 0 brief from concept gate_0 / music_bed_id."""
    gate = concept.get("gate_0") or {}
    bed_id = gate.get("music_bed_id") or concept.get("music_bed_id")
    if bed_id:
        return format_bed_declaration(str(bed_id))
    music_plan = gate.get("music_plan") or concept.get("music_plan")
    if music_plan:
        return f"Music plan: {music_plan}"
    return None


def music_row2_status(text: str, channels: list[str]) -> dict[str, Any]:
    """Evaluate manifest-backed clearance for Gate 0 row 2."""
    refs = extract_track_refs(text)
    if not refs:
        return {
            "refs": [],
            "manifest_cleared": False,
            "unlisted": [],
            "channel_blocked": [],
        }
    result = validate_tracks(refs, channels)
    return {
        "refs": refs,
        "manifest_cleared": result["all_cleared"],
        "cleared": result["cleared"],
        "unlisted": result["unlisted"],
        "channel_blocked": result["channel_blocked"],
    }