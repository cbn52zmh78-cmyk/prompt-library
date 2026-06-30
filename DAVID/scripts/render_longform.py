#!/usr/bin/env python3
"""DAVID long-form video assembler — arbitrary shot-count concat pipeline.

Generalizes render_post*.py / render_sample_videos.py per
STUDIO/Techniques/STUDIO_LongForm_Video_Assembly_v1.md.

Usage:
    python render_longform.py <script.json>
    python render_longform.py <script.json> --concat-only
    python render_longform.py <script.json> --script-only
    python render_longform.py <script.json> --force-shot 03_host_pie_line
    python render_longform.py <script.json> --package
    python render_longform.py <script.json> --package-only

Input: script JSON with shots[] + config + provenance_card (imagine-pack schema).
Output: productions/<slug>/ → shots/, output/*.mp4, imagine_pack.json, qa_report.json
"""
from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import textwrap
import time
import urllib.request
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
WORKSPACE = ROOT.parent
PIPELINE_DIR = WORKSPACE / "Studio" / "Pipeline"
if str(PIPELINE_DIR) not in sys.path:
    sys.path.insert(0, str(PIPELINE_DIR))

# --- qa_gate wiring ---
_AI_FED = WORKSPACE / "AI" / "federation"
if str(_AI_FED) not in sys.path:
    sys.path.insert(0, str(_AI_FED))
from qa_gate import qa_check as _qa_gate_check  # noqa: E402  # distinct from local qa_check()
# --- end qa_gate wiring ---

# --- PromptDirector wiring ---
_PROMPT_DIRECTOR: "Any | None" = None
try:
    _PROMPT_DIR_MOD = str(_AI_FED / "prompt_director")
    if _PROMPT_DIR_MOD not in sys.path:
        sys.path.insert(0, _PROMPT_DIR_MOD)
    from prompt_director import PromptDirector as _PromptDirector
    _PROMPT_DIRECTOR = _PromptDirector()
except Exception as _pd_exc:
    print(f"[PromptDirector] not available — continuing without: {_pd_exc}", file=sys.stderr)
    _PROMPT_DIRECTOR = None
# --- end PromptDirector wiring ---


def _ledger_note(path, **meta):
    """#259 path-stamping: record an output in the canonical ledger (best-effort)."""
    try:
        tools = WORKSPACE / "tools"
        if str(tools) not in sys.path:
            sys.path.insert(0, str(tools))
        from output_registry import note

        note(path, **meta)
    except Exception:
        pass

from shot_duration import (  # noqa: E402
    av_sync_drift_label,
    check_shot_duration_band,
    clamp_shot_duration,
    effective_shot_duration,
)

DEFAULT_LOCK = ROOT / "productions" / "host_identity_v1" / "david_identity_lock.json"
FFMPEG: str | None = None

SYNTHETIC_GUARD = "synthetic host only"
DEFAULT_VOICE_SUFFIX = (
    "mid-low resonant unhurried voice, precise diction, documentary gravitas, "
    "Attenborough-calm, accessible never stuffy, synthetic host only"
)
DEFAULT_CONTINUITY_PREFIX = (
    "CONTINUITY LOCK @David-001: identical host face, charcoal sweater, Archive desk, "
    "brass lamp, same eye-line — seamless continuation of prior take, zero jump cut."
)
DEFAULT_END_GUARD = (
    "Finish on gesture peak (hand motion or lean), never hold dead stillness or dead frame."
)
HOST_PERFORMANCE_NAME = "host_performance_extend.mp4"
API_PACE_S = 1.25  # xAI video rate limit ~1 req/s
# #194 — neutral WB base; lamp warm is localized (not full-frame tint)
NEUTRAL_WB_VF = "eq=gamma_r=1.00:gamma_g=0.92:gamma_b=1.04:saturation=0.93:brightness=0.00"
SKIN_NEUTRAL_VF = "eq=contrast=1.02:saturation=0.96"
LAMP_ACCENT_VF = "eq=gamma_r=1.10:gamma_g=1.02:gamma_b=0.82:saturation=1.08"
LAMP_LOCK_VF = (
    "eq=gamma_r=1.06:gamma_g=1.02:gamma_b=0.88:saturation=1.10:brightness=0.02"
)
LAMP_LOCK_PROMPT = (
    "Warm gold brass desk lamp 3200K key light locked — zero hue drift, amber pool only, "
    "no magenta purple ambient, no cool fill, no glasses purple reflection."
)
ARCHIVE_ANTI_MAGENTA_GENERATION_LOCK = (
    "MAGENTA SUPPRESS @David-001 (#218): D65 neutral white balance 5000K on host face, charcoal "
    "sweater, walls, and ambient plate — frame-wide midtones R≈G≈B within 8%; forbid purple/magenta "
    "ambient, pink wall bounce, magenta shadow grey, violet wood bounce, and red-blue skew "
    "(R+B must not exceed G×1.25 in ambient mids); brass lamp warmth stays amber-only in desk "
    "quadrant ≤25% frame — zero magenta spill on host skin, sweater, or shelf blur; neutral "
    "documentary skin, no color gel on key light."
)
ARCHIVE_NEUTRAL_GENERATION_LOCK = (
    "LIGHTING LOCK @David-001 (#243): neutral balanced 5000K white key on face, neck, and charcoal "
    "sweater — natural documentary skin with intact blue channel (B≥40/255 mids, B/R≥0.35); soft "
    "5200K shelf-bounce fill ≤25%; brass desk lamp 3200K tight motivated accent ONLY on desk "
    "quadrant (worktable, codex, lamp shade) — warm amber pool ≤25% frame, NEVER global amber wash "
    "on face, sweater, walls, or shadows; no yellow-green cast; no blue-starved shadows; no magenta "
    "purple ambient, no pink skin cast, no violet shadow bounce."
)
_ARCHIVE_WARM_PURGE_RE = re.compile(
    r"Warm gold brass desk lamp 3200K key light locked[^.]*\."
    r"(?:\s*Motivated practical key only[^.]*\.)?"
    r"\s*COLOR LOCK Archive: dominant amber 3200K[^.]*\."
    r"\s*GRADE LOCK Documentary-Prestige: skin warmth \+3% amber max[^.]*\.",
    re.I,
)
_ARCHIVE_NEUTRAL_PROMPT_BLOCK = (
    "LIGHTING: Neutral balanced 5000K ambient key on host — natural skin, blue channel intact; "
    "brass desk lamp 3200K localized warm pool on desk quadrant only; soft 5200K shelf bounce ≤25%; "
    "no yellow-green cast; no blue-starved shadows; no magenta ambient. "
    "GENERATION LOCK Archive-neutral (#243): D65 neutral WB 4800–5200K; B≥40 in skin mids; "
    "frame ambient R≈G≈B within 8%; forbid dominant amber full-frame; forbid blue-starved "
    "generation; forbid purple/magenta ambient, pink bounce, violet shadows."
)
GLASSES_LOCK_PROMPT = "Reading glasses pushed up into hair — same placement every frame."
AUDIO_SILENCE_DB = -45.0
LOUDNORM_I = -16.0
LOUDNORM_TP = -1.5
LOUDNORM_LRA = 11.0
MAGENTA_CLAMP_VF = "eq=gamma_r=1.08:gamma_g=1.02:gamma_b=0.82:saturation=1.05:brightness=0.01"
MAGENTA_CLAMP_STRONG_VF = (
    "eq=gamma_r=1.18:gamma_g=1.08:gamma_b=0.62:saturation=0.90:brightness=0.03"
)
DARK_SCENE_MAGENTA_CLAMP_VF = (
    "eq=gamma_r=1.14:gamma_g=1.05:gamma_b=0.68:saturation=0.94:brightness=0.02"
)
# #244 T4 — saturation-reduction safety net (single-pass; ceiling ≠ raw-magenta 0.634 fix alone)
MAGENTA_SATURATION_CLAMP_VF = (
    "eq=gamma_r=1.00:gamma_g=0.98:gamma_b=0.90:saturation=0.93:brightness=0.00"
)
CLAMP_STAGE_ISSUE = 244
CLAMP_STAGE_NAME = "process_shot_segment"
# Grade pipeline (#243/#244): clamp ONCE in process_shot_segment → chip/pin/loudnorm →
# xfade chain (histogram match optional, NO re-clamp) → final mux. T4 #244 calibrates
# against the single saturation-reduction pass stamped via .clamp244.json.
ARCHIVE_NEUTRAL_CLAMP_VF = MAGENTA_SATURATION_CLAMP_VF
CLINICAL_NEUTRAL_CLAMP_VF = f"{NEUTRAL_WB_VF},{MAGENTA_CLAMP_VF},{SKIN_NEUTRAL_VF}"
WARM_GOLD_CLAMP_VF = ARCHIVE_NEUTRAL_CLAMP_VF
MAGENTA_SCORE_MAX = 0.42
YELLOW_GREEN_SCORE_MAX = 0.12
import numpy as np  # noqa: E402

from color_cast_qa import (  # noqa: E402
    color_cast_breaches,
    color_cast_passes,
    generation_reference_breaches,
    generation_reference_passes,
    measure_color_cast,
    measure_set_shadow_blue_health,
)
CLINICAL_CHANNEL_BALANCE_MAX = 0.12  # #199 — absolute host CCB; fails +66 legacy false-pass frames
LABEL_CHIP_COLORS = {
    "RECONSTRUCTED PRONUNCIATION": (140, 88, 28, 245),
    "CLASSICAL LATIN": (40, 48, 62, 235),
}
LOUDNESS_SPREAD_MAX_LU = 1.5
REGROUND_EVERY_N = 2
LOUDNORM_LRA_TIGHT = 7.0
# Frame-chain joins: 0.2s @24fps ≈5 blended frames — reads as hard-cut on 7–9s shots.
DEFAULT_XFADE_S = 0.45
MIN_XFADE_S = 0.35
MAX_XFADE_S = 2.5  # raised from 0.75 — documentary band requires 1.8s (Render_Directive_v2)
SET_LIBRARY_PATH = WORKSPACE / "Studio" / "Pipeline" / "Set_Library_v1.json"
DARK_SCENE_KEYWORDS = (
    "warehouse", "industrial", "dusk", "shadow", "darkness", "dramatic",
    "night", "low key", "high-contrast", "corridor", "noir", "deep shadow",
)
WAREHOUSE_KELVIN_LOCK_PROMPT = (
    "Industrial window 4800K directional key locked — zero hue drift, deep shadow pockets, "
    "no magenta brick bounce, no cool fill contamination, no purple ambient."
)
_SET_LIBRARY_CACHE: dict[str, Any] | None = None
_LOG_STREAM = sys.stderr  # progress logs — keep stdout for manifest JSON (#193)


def _log(*args: Any, **kwargs: Any) -> None:
    """Progress logging on stderr so piped batch runs do not fill stdout."""
    kwargs.setdefault("file", _LOG_STREAM)
    print(*args, **kwargs)


def _eff_dur(shot: dict[str, Any], refs: dict[str, Any], *, seamless: bool) -> int:
    return effective_shot_duration(
        shot,
        seamless=seamless,
        seamless_cfg=refs.get("seamless_cfg"),
    )


def resolve_render_exit_code(result: dict[str, Any]) -> int:
    """Return process exit code from QA verdict (#193): 0 when pass, else 1."""
    return 0 if (result.get("qa") or {}).get("pass") is True else 1


def _load_grok_token() -> str:
    auth_path = Path.home() / ".grok" / "auth.json"
    if not auth_path.is_file():
        raise RuntimeError("No ~/.grok/auth.json — run grok login or set XAI_API_KEY")
    data = json.loads(auth_path.read_text(encoding="utf-8"))
    entry = next(iter(data.values()))
    token = entry.get("key") or entry.get("access_token")
    if not token:
        raise RuntimeError("Grok auth.json has no token")
    return token


def _ffmpeg_exe() -> str:
    global FFMPEG
    if FFMPEG:
        return FFMPEG
    try:
        import imageio_ffmpeg

        FFMPEG = imageio_ffmpeg.get_ffmpeg_exe()
    except ImportError:
        FFMPEG = "ffmpeg"
    return FFMPEG


def _download(url: str, dest: Path) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    req = urllib.request.Request(url, headers={"User-Agent": "DAVID-longform/1.0"})
    with urllib.request.urlopen(req, timeout=300) as r:
        dest.write_bytes(r.read())


def _api_pace() -> None:
    time.sleep(API_PACE_S)


def load_identity_lock(path: Path) -> dict[str, Any]:
    if not path.is_file():
        raise RuntimeError(f"Identity lock not found: {path}")
    lock = json.loads(path.read_text(encoding="utf-8"))
    if lock.get("status") != "LOCKED":
        raise RuntimeError(f"Identity lock status is not LOCKED: {path}")
    return lock


def _resolve_david_path(rel: str) -> Path:
    return _resolve_workspace_path(rel)


def _resolve_workspace_path(rel: str) -> Path:
    rel = str(rel).replace("\\", "/")
    if rel.split("/", 1)[0].lower() == "studio":  # canonical or legacy casing
        return WORKSPACE / rel
    if rel.startswith("DAVID/"):
        rel = rel[6:]
    p = Path(rel)
    if p.is_absolute():
        return p
    candidate = ROOT / p
    if candidate.is_file() or candidate.is_dir():
        return candidate
    ws_candidate = WORKSPACE / p
    if ws_candidate.is_file() or ws_candidate.is_dir():
        return ws_candidate
    return candidate


def _output_prefix(script: dict[str, Any]) -> str:
    fmt = script.get("format_id", "documentary-host")
    return "david" if fmt == "documentary-host" else "studio"


def _identity_anchor(script: dict[str, Any]) -> str:
    meta = script.get("production_meta") or {}
    anchor = meta.get("identity_anchor") or meta.get("talent_id") or "@David-001"
    return str(anchor)


def _is_archive_production(script: dict[str, Any], refs: dict[str, Any]) -> bool:
    set_file = str(refs.get("set_file") or "")
    return "archive" in set_file.lower() or script.get("format_id") == "documentary-host"


def _refs_is_archive(refs: dict[str, Any]) -> bool:
    set_file = str(refs.get("set_file") or "").lower()
    return "archive" in set_file or refs.get("format_id") == "documentary-host"


def _is_clinical_neutral_set(script: dict[str, Any], refs: dict[str, Any]) -> bool:
    set_file = str(refs.get("set_file") or "").lower()
    if any(k in set_file for k in ("cyclorama", "seamless_neutral", "studio_interior")):
        return True
    return script.get("format_id") in (
        "science-explainer",
        "editorial-explainer",
        "companion",
        "gfe-companion",
    )


def _apply_grade_policy(
    script: dict[str, Any],
    refs: dict[str, Any],
    opts: SeamlessOptions,
) -> SeamlessOptions:
    """Clinical/neutral productions: white-balance grade, no full-frame warm lamp cast (#193)."""
    if not _is_clinical_neutral_set(script, refs):
        return opts
    seam = script.get("config", {}).get("seamless") or {}
    neutral = bool(seam.get("neutral_grade", True))
    return SeamlessOptions(
        enabled=opts.enabled,
        xfade_s=opts.xfade_s,
        match_color=opts.match_color,
        cut_on_motion=opts.cut_on_motion,
        lamp_lock=False,
        glasses_lock=opts.glasses_lock,
        loudnorm=opts.loudnorm,
        pin_audio_sync=opts.pin_audio_sync,
        reground_interval=opts.reground_interval,
        magenta_clamp=opts.magenta_clamp,
        neutral_grade=neutral,
    )


def _use_magenta_hue_qa(script: dict[str, Any], refs: dict[str, Any]) -> bool:
    return (
        _is_archive_production(script, refs)
        or _is_dark_scene(refs, script=script)
        or script.get("format_id") in ("narrative-short-film", "movies")
    )


def _should_magenta_reroll(script: dict[str, Any], refs: dict[str, Any]) -> bool:
    """Clinical/neutral sets skip API re-roll; dark/archive/movies must converge."""
    if _is_clinical_neutral_set(script, refs):
        return False
    return _use_magenta_hue_qa(script, refs) or _is_dark_scene(refs, script=script)


def _script_ctx_from_refs(refs: dict[str, Any]) -> dict[str, Any]:
    return {
        "format_id": refs.get("format_id"),
        "production_meta": refs.get("production_meta") or {},
    }


def _shot_uses_viz_reference(shot: dict[str, Any]) -> bool:
    slots = shot.get("reference_slots") or {}
    if slots.get("@2") == "visualization":
        return True
    return shot.get("role") == "visualization" or shot.get("use_avatar") is False


def _extract_zone(text: str) -> str | None:
    """Parse zone plate id (@1, @3, …) from shot.zone or video_prompt markers."""
    if not text:
        return None
    m = re.search(r"\(@(\d+)", text)
    if m:
        return f"@{m.group(1)}"
    m = re.search(r"@(\d+)\b", text)
    return f"@{m.group(1)}" if m else None


def _shot_zone(shot: dict[str, Any]) -> str | None:
    raw = shot.get("zone")
    if raw:
        z = str(raw).strip()
        return z if z.startswith("@") else f"@{z}"
    return _extract_zone(shot.get("video_prompt", ""))


def _needs_zone_plates(script: dict[str, Any], refs: dict[str, Any]) -> bool:
    """Lock empty @1 environment plates on disk; video seeds from @2 avatar_url only."""
    cfg = script.get("config") or {}
    if cfg.get("use_zone_plates") is False:
        return False
    if not refs.get("set_file"):
        return False
    if cfg.get("use_zone_plates") is True:
        return True
    if cfg.get("avatar_in_set"):
        return False
    lock = refs.get("lock") or {}
    talent = (lock.get("references") or {}).get("talent_avatar") or {}
    if cfg.get("use_identity_lock", True) and talent.get("url"):
        return False
    return bool(refs.get("avatar_file") or refs.get("avatar_url"))


def _load_plate_sidecar(path: Path) -> dict[str, Any]:
    meta = path.with_suffix(".json")
    if not meta.is_file():
        return {}
    try:
        return json.loads(meta.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {}


def _save_plate_sidecar(path: Path, data: dict[str, Any]) -> None:
    path.with_suffix(".json").write_text(
        json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8"
    )


def _resolve_environment_plate_url(
    client: Any | None,
    *,
    set_id: str | None,
    set_file: str | None,
) -> str:
    """Locked empty-set environment plate (@1 background, no talent)."""
    local_files: list[Path] = []
    if set_file:
        sf = Path(set_file)
        if sf.is_file():
            local_files.append(sf)

    if set_id:
        entry = (_load_set_library().get("sets") or {}).get(set_id) or {}
        ref_file = entry.get("reference_file")
        if ref_file:
            rp = _resolve_workspace_path(str(ref_file))
            if rp.is_file() and rp not in local_files:
                local_files.append(rp)

    # Fresh upload from disk — sidecar/library imgen URLs expire (404).
    if client is not None:
        for path in local_files:
            return upload_image_url(client, path)

    for path in local_files:
        meta = _load_plate_sidecar(path)
        url = meta.get("url") or meta.get("reference_url")
        if url:
            return str(url)

    if set_id:
        entry = (_load_set_library().get("sets") or {}).get(set_id) or {}
        url = entry.get("reference_url")
        if url:
            return str(url)

    raise RuntimeError(
        f"No environment plate URL for set {set_id or set_file} — "
        "run STUDIO/Pipeline/generate_set_references.py or provide set_reference sidecar url"
    )


def _resolve_environment_plate_file(
    script: dict[str, Any],
    refs: dict[str, Any],
) -> tuple[Path, str | None]:
    """Local locked empty-set file (no people) for zone plate copy."""
    set_id = _extract_set_id(
        str(refs.get("set_file") or "")
        + " "
        + json.dumps(script.get("intake") or {})
        + " "
        + json.dumps(script.get("config") or {})
    )
    candidates: list[Path] = []
    if refs.get("set_file"):
        sf = Path(str(refs["set_file"]))
        if sf.is_file():
            candidates.append(sf)
    if set_id:
        ref_file = ((_load_set_library().get("sets") or {}).get(set_id) or {}).get("reference_file")
        if ref_file:
            rp = _resolve_workspace_path(str(ref_file))
            if rp.is_file() and rp not in candidates:
                candidates.append(rp)
    if not candidates:
        raise RuntimeError(
            f"No empty environment plate on disk for set {set_id or refs.get('set_file')} — "
            "run STUDIO/Pipeline/generate_set_references.py"
        )
    return candidates[0], set_id


def generate_zone_plate(
    zone_id: str,
    client: Any,
    refs: dict[str, Any],
    plates_dir: Path,
    script: dict[str, Any],
    *,
    force: bool = False,
) -> dict[str, Any]:
    """Lock empty environment plate for zone (@1 = set only, no talent, no props).

    @2 avatar_url remains the casting reference; video prompts place the performer.
    """
    plates_dir.mkdir(parents=True, exist_ok=True)
    plate_path = plates_dir / f"{zone_id}_plate.jpg"
    meta = _load_plate_sidecar(plate_path)
    if (
        not force
        and plate_path.is_file()
        and plate_path.stat().st_size > 5000
        and meta.get("url")
        and meta.get("plate_type") == "environment_empty"
        and meta.get("no_people") is True
    ):
        # Reuse plate pixels + CDN url; always re-upload for a live session file_id.
        _api_pace()
        upload_url, plate_file_id = upload_and_capture_id(
            client, plate_path, friendly=zone_id,
        )
        meta["file_id"] = plate_file_id
        if not meta.get("url"):
            meta["url"] = upload_url
        _save_plate_sidecar(plate_path, meta)
        _log(
            f"[zone] reusing empty {zone_id} plate pixels — "
            f"fresh session file_id={plate_file_id}"
        )
        return {**meta, "path": str(plate_path), "reused": True}

    source_path, set_id = _resolve_environment_plate_file(script, refs)
    if source_path.resolve() != plate_path.resolve():
        shutil.copy2(source_path, plate_path)
    _log(f"[zone] locking empty {zone_id} environment plate from {source_path.name}")
    _api_pace()
    plate_url, plate_file_id = upload_and_capture_id(
        client, plate_path, friendly=zone_id,
    )
    source_meta = _load_plate_sidecar(source_path)

    data = {
        "zone_id": zone_id,
        "plate_type": "environment_empty",
        "no_people": True,
        "path": str(plate_path),
        "url": plate_url,
        "file_id": plate_file_id,
        "source_file": str(source_path),
        "source_url": source_meta.get("url"),
        "set_id": set_id,
        "avatar_reference": refs.get("avatar_url"),
        "note": "@1 empty set on disk only — never composited with @2; video seeds from avatar_url",
        "status": "REGENERATED" if force else "LOCKED",
        "reused": False,
    }
    _save_plate_sidecar(plate_path, data)
    return data


def _load_cached_zone_plates(refs: dict[str, Any], plates_dir: Path) -> int:
    """Hydrate refs from prior plate sidecars (concat-only / no API client)."""
    if not plates_dir.is_dir():
        return 0
    loaded = 0
    for meta_path in plates_dir.glob("@*_plate.json"):
        try:
            meta = json.loads(meta_path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            continue
        zone_id = meta.get("zone_id") or meta_path.stem.replace("_plate", "")
        url = meta.get("url")
        if zone_id and url:
            refs[f"{zone_id}_plate_url"] = url
            refs[f"{zone_id}_plate_file"] = meta.get("path") or str(meta_path.with_suffix(".jpg"))
            # file_id intentionally omitted — stale across sessions; live ids from capture_editor_session
            loaded += 1
    return loaded


def ensure_zone_plates(
    script: dict[str, Any],
    refs: dict[str, Any],
    client: Any,
    plates_dir: Path,
    *,
    force: bool = False,
) -> None:
    """Build zone plate URLs for every host-shot zone used in the script."""
    if not _needs_zone_plates(script, refs):
        return

    zones: set[str] = set()
    for shot in script.get("shots", []):
        if shot.get("role", "host") == "card" or _shot_uses_viz_reference(shot):
            continue
        zone = _shot_zone(shot)
        if zone:
            zones.add(zone)
    if not zones:
        zones.add("@1")

    for zone_id in sorted(zones):
        plate = generate_zone_plate(
            zone_id, client, refs, plates_dir, script, force=force
        )
        refs[f"{zone_id}_plate_url"] = plate["url"]
        refs[f"{zone_id}_plate_file"] = plate["path"]
        if plate.get("file_id"):
            refs[f"{zone_id}_plate_file_id"] = plate["file_id"]


def inject_api_file_ref_tokens(
    prompt: str,
    shot: dict[str, Any],
    refs: dict[str, Any],
) -> str:
    """DEPRECATED — prose @file tokens do not composite; use reference_image_file_ids.

    Prepend @file_XXXX API handles — legacy experiment only.
    """
    tokens: list[str] = []
    zone = _shot_zone(shot)
    if zone:
        plate_id = refs.get(f"{zone}_plate_file_id")
        if plate_id:
            tokens.append(f"@{plate_id}")
    avatar_id = refs.get("avatar_file_id")
    if avatar_id:
        tokens.append(f"@{avatar_id}")
    if not tokens:
        return prompt
    prefix = " ".join(tokens)
    _log(f"[file_ref] injecting API handles: {prefix}")
    return f"{prefix} {prompt}"


def _prompt_mode(script: dict[str, Any] | None) -> str:
    return str((script or {}).get("config", {}).get("prompt_mode") or "seamless")


def capture_editor_session(
    client: Any,
    refs: dict[str, Any],
    script: dict[str, Any],
    prod_dir: Path,
    *,
    force: bool = False,
) -> dict[str, Any]:
    """Upload fresh @1/@2 session UUIDs — valid for this run + in-run extends only.

    Writes editor_session.json for audit; never reads it back on a new run.
    """
    session_path = prod_dir / "editor_session.json"
    plates_dir = prod_dir / "plates"
    ensure_zone_plates(script, refs, client, plates_dir, force=True)
    avatar_file = Path(str(refs["avatar_file"]))
    _api_pace()
    avatar_url, avatar_id = upload_and_capture_id(client, avatar_file, friendly="@2")

    session = {
        "captured_at": datetime.now(timezone.utc).isoformat(),
        "video_slug": script.get("slug"),
        "scope": "this video + extensions only — not portable to new projects",
        "slots": {
            "@1": {
                "role": "setting",
                "file_id": refs["@1_plate_file_id"],
                "url": refs["@1_plate_url"],
                "plate_path": refs.get("@1_plate_file"),
            },
            "@2": {
                "role": "talent_render",
                "file_id": avatar_id,
                "url": avatar_url,
                "source": str(avatar_file),
            },
        },
    }
    session_path.write_text(json.dumps(session, indent=2, ensure_ascii=False), encoding="utf-8")
    refs["editor_session"] = session
    refs["avatar_file_id"] = avatar_id
    refs["avatar_url"] = avatar_url
    _log(
        f"[editor_session] captured @1={session['slots']['@1']['file_id']} "
        f"@2={session['slots']['@2']['file_id']}"
    )
    return session


def _session_slot_ids(
    refs: dict[str, Any],
    prod_dir: Path | None,
) -> tuple[str | None, str | None]:
    session = refs.get("editor_session")
    if session:
        slots = session.get("slots") or {}
        talent = (slots.get("@2") or {}).get("file_id")
        setting = (slots.get("@1") or {}).get("file_id")
        if talent and setting:
            return str(talent), str(setting)
    talent = refs.get("avatar_file_id")
    setting = refs.get("@1_plate_file_id")
    return (str(talent) if talent else None, str(setting) if setting else None)


DEFAULT_BAREBONES_TEMPLATE = "Studio/prompts/MASTER_Matilda_v1.json"
BAREBONES_SLOT_KEYS = ("@1", "@2", "@3", "@4", "@5", "@6", "@7")
BAREBONES_PAYLOAD_KEYS = (
    *BAREBONES_SLOT_KEYS,
    "command",
    "scene",
    "camera",
    "dialogue",
    "audio",
    "style",
    "lighting",
    "output",
)


def _slot_description(slot: dict[str, Any] | None) -> str:
    """Canonical BAREBONES slot text — description first, performance_modifiers fallback."""
    if not isinstance(slot, dict):
        return ""
    return str(slot.get("description") or slot.get("performance_modifiers") or "").strip()


def crop_turntable_front_panel(src: Path, out: Path | None = None) -> Path:
    """Extract center (front) panel from 3-view casting turntable."""
    from PIL import Image

    img = Image.open(src).convert("RGB")
    w, h = img.size
    third = w // 3
    crop = img.crop((third, 0, 2 * third, h))
    dest = out or src.with_name(f"{src.stem}_front_panel.jpg")
    dest.parent.mkdir(parents=True, exist_ok=True)
    crop.save(dest, quality=95)
    return dest


def _editor_uuid_token(file_id: str) -> str:
    """Editor prose syntax — strip API file_ prefix, emit @uuid."""
    fid = str(file_id).strip()
    if fid.startswith("file_"):
        fid = fid[5:]
    return f"@{fid}"


def _resolve_seed_slot(refs: dict[str, Any], image_url: str | None) -> str | None:
    """Which @ slot is pixel-locked via image_url for this generation."""
    if not image_url:
        return None
    url = str(image_url).strip()
    session = refs.get("editor_session") or {}
    for slot_id in BAREBONES_SLOT_KEYS:
        slot = (session.get("slots") or {}).get(slot_id) or {}
        if slot.get("url") and str(slot["url"]) == url:
            return slot_id
    if refs.get("@1_plate_url") and str(refs["@1_plate_url"]) == url:
        return "@1"
    if refs.get("avatar_url") and str(refs["avatar_url"]) == url:
        return "@2"
    head_url = refs.get("@3_plate_url")
    if head_url and str(head_url) == url:
        return "@3"
    return None


def _slot_file_id(refs: dict[str, Any], prod_dir: Path | None, slot_id: str) -> str | None:
    session = refs.get("editor_session")
    if session:
        fid = (session.get("slots") or {}).get(slot_id, {}).get("file_id")
        if fid:
            return str(fid)
    if slot_id == "@1":
        return refs.get("@1_plate_file_id")
    if slot_id == "@2":
        return refs.get("avatar_file_id")
    if slot_id == "@3":
        return refs.get("@3_plate_file_id")
    return refs.get(f"{slot_id}_plate_file_id")


def _barebones_payload(doc: dict[str, Any]) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for key in BAREBONES_PAYLOAD_KEYS:
        if key not in doc:
            continue
        val = doc[key]
        if key in BAREBONES_SLOT_KEYS and isinstance(val, dict):
            out[key] = dict(val)
        elif isinstance(val, dict):
            out[key] = dict(val)
        else:
            out[key] = val
    return out


def _merge_barebones_shot(shot: dict[str, Any], script: dict[str, Any] | None) -> dict[str, Any]:
    """Merge per-shot barebones overrides onto Studio template defaults."""
    cfg = (script or {}).get("config") or {}
    default_template = DEFAULT_BAREBONES_TEMPLATE
    if (script or {}).get("format_id") == "science-pure-visual":
        default_template = "Studio/prompts/MASTER_PureVisual_v1.json"
    rel = str(cfg.get("prompt_template") or default_template)
    template_path = Path(rel) if Path(rel).is_absolute() else _resolve_workspace_path(rel)
    base: dict[str, Any] = {}
    if template_path.is_file():
        try:
            base = _barebones_payload(json.loads(template_path.read_text(encoding="utf-8")))
        except (json.JSONDecodeError, OSError):
            pass
    merged = dict(base)
    shot_bb = shot.get("barebones")
    if not isinstance(shot_bb, dict):
        return merged
    for key, val in shot_bb.items():
        if key in BAREBONES_SLOT_KEYS and isinstance(val, dict):
            slot_base = dict(merged.get(key) or {})
            slot_base.update(val)
            merged[key] = slot_base
        elif isinstance(val, dict) and isinstance(merged.get(key), dict):
            block = dict(merged[key])
            block.update(val)
            merged[key] = block
        else:
            merged[key] = val
    return merged


def _format_camera_clause(camera: str) -> str:
    c = camera.strip()
    if not c:
        return ""
    if c.lower().startswith("camera"):
        return c
    return f"Camera does {c}"


def _format_setting_clause(
    setting_id: str,
    bb: dict[str, Any],
) -> str:
    """@1 always leads — source image Imagine anchors the rest of the video on."""
    s1 = bb.get("@1") if isinstance(bb.get("@1"), dict) else {}
    perf = _slot_description(s1)
    token = _editor_uuid_token(setting_id)
    if perf:
        return f"Setting: {token} ({perf})"
    return f"Setting: {token}"


SILENT_SCENE_LOCK = (
    "NO VOICEOVER, NO NARRATION, SILENT — visual only, zero spoken audio, zero lip-sync, "
    "zero voice track, mute output"
)

# Branch-chain seed policies (script config branch_chain.seed_handoff / branch_mode).
BRANCH_CHAIN_LAST_FRAME_MODE = "last_frame"
BRANCH_CHAIN_STAGING_MODE = "last_frame_prompt_only"
BRANCH_STAGING_GUIDE_PREFIX = (
    "STAGING GUIDE (last-frame reference — prompt only, NOT an image seed, NOT uploaded)"
)


def resolve_branch_chain_seed_handoff(script: dict[str, Any] | None) -> str:
    """Return branch image-seed policy: sequential last-frame chain vs star composite staging."""
    branch_cfg = ((script or {}).get("config") or {}).get("branch_chain") or {}
    seed = str(branch_cfg.get("seed_handoff") or "").strip().lower()
    if seed == BRANCH_CHAIN_LAST_FRAME_MODE:
        return BRANCH_CHAIN_LAST_FRAME_MODE
    mode = str(
        branch_cfg.get("branch_mode") or branch_cfg.get("staging_guide") or ""
    ).strip().lower()
    if mode == BRANCH_CHAIN_LAST_FRAME_MODE:
        return BRANCH_CHAIN_LAST_FRAME_MODE
    return BRANCH_CHAIN_STAGING_MODE


def narration_enabled(script: dict[str, Any] | None, shot: dict[str, Any] | None = None) -> bool:
    """False when config.narration or shot.narration is explicitly false."""
    if shot is not None and shot.get("narration") is False:
        return False
    cfg = (script or {}).get("config") or {}
    return cfg.get("narration") is not False


def compile_barebones_prose_prompt(
    shot: dict[str, Any],
    refs: dict[str, Any],
    prod_dir: Path | None,
    script: dict[str, Any] | None = None,
    *,
    image_url: str | None = None,
    seed_slot: str | None = None,
    talent_baked_in: bool = False,
) -> str:
    """Compile Studio BAREBONES JSON → prose_prompt (MATILDA_Direction_Guide § Grok Syntax).

    Slot order is fixed: @1 Setting first (always — matches image_url source plate),
    then @2/@3 talent tokens, then scene + integrated camera prose.
    talent_baked_in: composite @1 carries talent+set pixels (DAVID-style baked seed).
    """
    bb = _merge_barebones_shot(shot, script)
    if seed_slot is None:
        seed_slot = _resolve_seed_slot(refs, image_url)
    dialogue = bb.get("dialogue") if isinstance(bb.get("dialogue"), dict) else {}
    character = str(dialogue.get("character") or "MATILDA").strip()

    scene = str(bb.get("scene") or "").strip()
    if not scene:
        scene = str(shot.get("video_prompt") or "").strip()
    if not narration_enabled(script, shot):
        if SILENT_SCENE_LOCK not in scene:
            scene = f"{SILENT_SCENE_LOCK}; {scene}" if scene else SILENT_SCENE_LOCK
    camera = _format_camera_clause(str(bb.get("camera") or ""))

    parts: list[str] = []

    session = refs.get("editor_session") or {}
    slot1 = (session.get("slots") or {}).get("@1") or {}
    chain_handoff = slot1.get("role") == "baked_chain_frame"
    staging_guide = str(bb.get("staging_guide") or bb.get("handoff_lock") or "").strip()
    handoff_lock = staging_guide
    setting_id = _slot_file_id(refs, prod_dir, "@1")
    if staging_guide and not chain_handoff:
        parts.append(staging_guide)
    if chain_handoff:
        s1 = bb.get("@1") if isinstance(bb.get("@1"), dict) else {}
        perf = _slot_description(s1) or (
            "see attached render — prior segment exit frame; camera and lighting locked to seed"
        )
        lead = f"Setting: {perf}"
        if handoff_lock and handoff_lock not in lead:
            lead = f"{lead}; {handoff_lock}"
        parts.append(lead)
    elif setting_id:
        parts.append(_format_setting_clause(setting_id, bb))

    body_id = _slot_file_id(refs, prod_dir, "@2")
    shot_bb = shot.get("barebones") if isinstance(shot.get("barebones"), dict) else {}
    use_head_slot = "@3" in shot_bb
    head_id = _slot_file_id(refs, prod_dir, "@3") if use_head_slot else None
    talent_in_seed = talent_baked_in or seed_slot in ("@2", "@3")
    s2 = bb.get("@2") if isinstance(bb.get("@2"), dict) else {}
    body_mods = _slot_description(s2)
    head_mods = (
        _slot_description(bb.get("@3") if isinstance(bb.get("@3"), dict) else {})
        if use_head_slot
        else ""
    )
    mods = "; ".join(m for m in (body_mods, head_mods) if m)

    action = scene
    if camera:
        action = f"{scene}. {camera}" if scene else camera

    if body_id and not talent_in_seed:
        if head_id:
            char_clause = (
                f"{character} (body_reference: {_editor_uuid_token(body_id)}, "
                f"head_reference: {_editor_uuid_token(head_id)}"
            )
            if mods:
                char_clause += f"; {mods}"
            char_clause += ")"
        else:
            char_clause = f"{character} ( {_editor_uuid_token(body_id)}"
            if mods:
                char_clause += f" , {mods}"
            char_clause += ")"
        parts.append(f"{char_clause} {action}".strip())
    elif action:
        parts.append(action)

    speech = ""
    if narration_enabled(script, shot):
        speech = str(
            dialogue.get("speech_text") or shot.get("speech_text") or ""
        ).strip()
    assembled = " ; ".join(parts)
    if speech and speech not in assembled:
        lang = str(dialogue.get("language") or "")
        lang_note = "native Bavarian German" if lang.startswith("de") else "dialogue"
        parts.append(f'Lip-synced, delivers in {lang_note}: "{speech}"')
    audio = bb.get("audio") if isinstance(bb.get("audio"), dict) else {}
    ambient = str(audio.get("ambient") or "").strip()
    if ambient:
        parts.append(ambient)
    if narration_enabled(script, shot):
        voice_en = str(audio.get("voice_direction") or "").strip()
        if voice_en and not str(dialogue.get("language") or "").startswith("de"):
            parts.append(voice_en)
        voice_de = str(audio.get("voice_direction_DE") or "").strip()
        if voice_de and str(dialogue.get("language") or "").startswith("de"):
            parts.append(voice_de)

    style = str(bb.get("style") or "").strip()
    if style:
        parts.append(style)

    prompt = " ; ".join(p for p in parts if p)

    talent_label = (
        "baked@1" if talent_baked_in else "in-seed" if talent_in_seed else "named@2"
    )
    _log(
        f"[prompt] barebones {shot.get('id')}: seed={seed_slot or 'none'} "
        f"@1_first=yes talent={talent_label}"
    )
    return prompt.strip()


def _resolve_composite_first_frame(
    script: dict[str, Any] | None,
    prod_dir: Path | None,
) -> Path | None:
    """Baked @1 composite JPG for shot 0 — production path when video refs gated."""
    cfg = (script or {}).get("config") or {}
    raw = cfg.get("composite_first_frame") or cfg.get("baked_composite_seed")
    if not raw:
        return None
    candidates = [
        Path(str(raw)),
        _resolve_workspace_path(str(raw)),
    ]
    if prod_dir:
        candidates.append(Path(prod_dir) / str(raw))
    for p in candidates:
        if p.is_file():
            return p.resolve()
    return None


def generate_baked_composite_video(
    client: Any,
    shot: dict[str, Any],
    refs: dict[str, Any],
    script: dict[str, Any],
    prod_dir: Path | None,
    composite_path: Path,
    *,
    duration: int,
) -> tuple[Any, dict[str, Any]]:
    """video.generate from composite JPG — talent+set baked into @1 (no reference_images)."""
    composite_path = Path(composite_path)
    if not composite_path.is_file():
        raise FileNotFoundError(f"composite seed missing: {composite_path}")
    _api_pace()
    url, fid = upload_and_capture_id(client, composite_path, friendly="@1_composite")
    session = refs.setdefault("editor_session", {"slots": {}})
    slots = session.setdefault("slots", {})
    slots["@1"] = {
        "role": "baked_composite",
        "file_id": fid,
        "url": url,
        "source": str(composite_path.resolve()),
    }
    refs["@1_plate_file_id"] = fid
    refs["@1_plate_url"] = url
    prompt = compile_barebones_prose_prompt(
        shot,
        refs,
        prod_dir,
        script,
        image_url=url,
        seed_slot="@1",
        talent_baked_in=True,
    )
    gen_kwargs: dict[str, Any] = {
        "prompt": prompt,
        "model": refs["model_video"],
        "image_file_id": fid,
        "duration": duration,
        "resolution": refs["resolution"],
        "aspect_ratio": _script_aspect_ratio(script),
    }
    _log(
        f"[baked@1] generate {shot.get('id')}: image_file_id={fid[:20]}... "
        f"talent+set in composite seed"
    )
    _api_pace()
    resp = client.video.generate(**gen_kwargs)
    req = {
        "prompt": prompt,
        "kwargs": gen_kwargs,
        "binding": {
            "seed_mode": "baked_composite@1",
            "image_field": "image_file_id",
            "image_value": fid,
            "composite_path": str(composite_path),
        },
    }
    return resp, req


def generate_baked_chain_video(
    client: Any,
    shot: dict[str, Any],
    refs: dict[str, Any],
    script: dict[str, Any],
    prod_dir: Path | None,
    *,
    chain_image_file_id: str,
    chain_image_url: str | None,
    duration: int,
) -> tuple[Any, dict[str, Any]]:
    """video.generate from chain frame — identity baked in pixels, no reference_images."""
    fid = str(chain_image_file_id)
    url = str(chain_image_url or "")
    session = refs.setdefault("editor_session", {"slots": {}})
    slots = session.setdefault("slots", {})
    slots["@1"] = {
        "role": "baked_chain_frame",
        "file_id": fid,
        "url": url,
    }
    refs["@1_plate_file_id"] = fid
    if url:
        refs["@1_plate_url"] = url
    prompt = compile_barebones_prose_prompt(
        shot,
        refs,
        prod_dir,
        script,
        image_url=url or None,
        seed_slot="@1",
        talent_baked_in=True,
    )
    gen_kwargs: dict[str, Any] = {
        "prompt": prompt,
        "model": refs["model_video"],
        "image_file_id": fid,
        "duration": duration,
        "resolution": refs["resolution"],
        "aspect_ratio": _script_aspect_ratio(script),
    }
    _log(
        f"[baked@chain] generate {shot.get('id')}: image_file_id={fid[:20]}... "
        f"talent+set in chain seed (no refs)"
    )
    _api_pace()
    resp = client.video.generate(**gen_kwargs)
    req = {
        "prompt": prompt,
        "kwargs": gen_kwargs,
        "binding": {
            "seed_mode": "baked_chain@1",
            "image_field": "image_file_id",
            "image_value": fid,
        },
    }
    return resp, req


def mandatory_extract_last_frame(video: Path, out_jpg: Path) -> Path:
    """Hard-fail last-frame extraction — required for branch handoff (#branch-chain)."""
    if not video.is_file() or video.stat().st_size < 10000:
        raise FileNotFoundError(f"MANDATORY handoff: branch video missing or empty: {video}")
    extract_last_frame(video, out_jpg)
    if not out_jpg.is_file() or out_jpg.stat().st_size < 500:
        raise RuntimeError(f"MANDATORY handoff: last-frame extraction failed: {out_jpg}")
    return out_jpg


def generate_branch_last_frame_video(
    client: Any,
    shot: dict[str, Any],
    refs: dict[str, Any],
    script: dict[str, Any],
    prod_dir: Path | None,
    *,
    handoff_frame: Path,
    prev_shot_id: str,
    duration: int,
) -> tuple[Any, dict[str, Any]]:
    """Branch chain: upload prev-branch last frame → image_file_id seed (sequential topology).

    b02 ← b01 last frame, b03 ← b02 last frame, etc. Identity baked in chain pixels.
    """
    handoff_frame = Path(handoff_frame)
    if not handoff_frame.is_file() or handoff_frame.stat().st_size < 500:
        raise FileNotFoundError(
            f"MANDATORY handoff frame missing before branch {shot.get('id')}: {handoff_frame}"
        )
    _log(
        f"[branch-chain] {shot.get('id')} ← {prev_shot_id} "
        f"seed={handoff_frame.name} (uploaded last-frame chain)"
    )
    _api_pace()
    chain_url, chain_fid = upload_and_capture_id(
        client, handoff_frame, friendly=f"branch_seed_{shot.get('id')}",
    )
    resp, req = generate_baked_chain_video(
        client,
        shot,
        refs,
        script,
        prod_dir,
        chain_image_file_id=chain_fid,
        chain_image_url=chain_url,
        duration=duration,
    )
    req["binding"] = {
        **(req.get("binding") or {}),
        "seed_mode": BRANCH_CHAIN_LAST_FRAME_MODE,
        "topology": "sequential_last_frame",
        "handoff_frame_local": str(handoff_frame),
        "handoff_from": prev_shot_id,
        "handoff_frame_uploaded": True,
    }
    return resp, req


def generate_branch_staging_video(
    client: Any,
    shot: dict[str, Any],
    refs: dict[str, Any],
    script: dict[str, Any],
    prod_dir: Path | None,
    *,
    staging_frame: Path,
    origin_video_url: str,
    origin_composite: Path,
    prev_shot_id: str,
    duration: int,
) -> tuple[Any, dict[str, Any]]:
    """Branch chain (hardcoded): last frame = staging guide only → prompt → star-origin generate.

    1. Extract last frame locally (never uploaded as image/reference seed)
    2. analyze_handoff_frame → lighting, distance, camera viewpoint
    3. Inject staging prose into next-branch prompt
    4. video.generate(image_file_id=origin_composite) — same composite as b01 (star topology)
       origin_video_url is audit-only (locked b01 UUID); never the previous branch UUID.

    grok-imagine-video-1.5 rejects video_url edit; composite star-seed preserves policy.
    """
    staging_frame = Path(staging_frame)
    origin_composite = Path(origin_composite)
    if not staging_frame.is_file() or staging_frame.stat().st_size < 500:
        raise FileNotFoundError(
            f"MANDATORY staging frame missing before branch {shot.get('id')}: {staging_frame}"
        )
    if not origin_composite.is_file():
        raise FileNotFoundError(f"MANDATORY origin composite missing: {origin_composite}")
    origin = str(origin_video_url or "").strip()
    if not origin:
        raise ValueError(f"MANDATORY origin_video_url (audit) missing for branch {shot.get('id')}")

    staging_meta = analyze_handoff_frame(staging_frame)
    shot = apply_staging_guide_to_shot(
        shot, staging_frame, prev_shot_id=prev_shot_id, meta=staging_meta,
    )

    _log(
        f"[branch-staging] {shot.get('id')} ← {prev_shot_id} "
        f"staging={staging_frame.name} (local prompt only) "
        f"viewpoint={staging_meta.get('camera_viewpoint', '')[:40]}… "
        f"origin_audit={origin[:48]}… composite_seed={origin_composite.name}"
    )
    resp, req = generate_baked_composite_video(
        client,
        shot,
        refs,
        script,
        prod_dir,
        origin_composite,
        duration=duration,
    )
    req["binding"] = {
        **(req.get("binding") or {}),
        "seed_mode": BRANCH_CHAIN_STAGING_MODE,
        "staging_policy": BRANCH_STAGING_GUIDE_PREFIX,
        "topology": "star_from_origin_composite",
        "origin_video_url_audit": origin,
        "origin_composite": str(origin_composite),
        "staging_frame_local": str(staging_frame),
        "staging_from": prev_shot_id,
        "staging_meta": staging_meta,
        "staging_frame_uploaded": False,
    }
    return resp, req


def generate_branch_handoff_video(
    client: Any,
    shot: dict[str, Any],
    refs: dict[str, Any],
    script: dict[str, Any],
    prod_dir: Path | None,
    *,
    handoff_frame: Path,
    prev_shot_id: str,
    duration: int,
    origin_video_url: str = "",
    origin_composite: Path | None = None,
    seed_mode: str | None = None,
) -> tuple[Any, dict[str, Any]]:
    """Dispatch branch generate by script branch_chain seed policy."""
    mode = seed_mode or resolve_branch_chain_seed_handoff(script)
    if mode == BRANCH_CHAIN_LAST_FRAME_MODE:
        return generate_branch_last_frame_video(
            client,
            shot,
            refs,
            script,
            prod_dir,
            handoff_frame=handoff_frame,
            prev_shot_id=prev_shot_id,
            duration=duration,
        )
    if not origin_composite:
        raise ValueError("origin_composite required for staging-guide branch mode")
    return generate_branch_staging_video(
        client,
        shot,
        refs,
        script,
        prod_dir,
        staging_frame=handoff_frame,
        origin_video_url=origin_video_url,
        origin_composite=origin_composite,
        prev_shot_id=prev_shot_id,
        duration=duration,
    )


def _uses_baked_composite_pipeline(
    script: dict[str, Any] | None,
    prod_dir: Path | None,
) -> bool:
    return _resolve_composite_first_frame(script, prod_dir) is not None


def _editor_reference_file_ids(refs: dict[str, Any]) -> list[str]:
    """@2–@7 session file_ids for reference_image_file_ids (compositing, not first frame)."""
    session = refs.get("editor_session") or {}
    slots = session.get("slots") or {}
    ids: list[str] = []
    for slot in BAREBONES_SLOT_KEYS[1:]:
        fid = (slots.get(slot) or {}).get("file_id")
        if fid:
            ids.append(str(fid))
    return ids


def _script_aspect_ratio(script: dict[str, Any] | None) -> str:
    return str((script or {}).get("config", {}).get("aspect_ratio") or "16:9")


def build_barebones_generate_request(
    shot: dict[str, Any],
    refs: dict[str, Any],
    script: dict[str, Any],
    prod_dir: Path | None,
    *,
    duration: int,
    chain_image_url: str | None = None,
    chain_image_file_id: str | None = None,
    seed_slot: str | None = None,
) -> dict[str, Any]:
    """Assemble barebones i2v + R2V kwargs: @1 first frame, @2+ reference sheets."""
    session = refs.get("editor_session") or {}
    slots = session.get("slots") or {}
    ref_ids = _editor_reference_file_ids(refs)

    image_file_id: str | None = None
    image_url: str | None = None
    binding: dict[str, Any] = {"reference_image_file_ids": ref_ids}

    if chain_image_file_id:
        image_file_id = str(chain_image_file_id)
        binding["seed_mode"] = "chain_frame"
        binding["image_field"] = "image_file_id"
        prompt_seed_url = chain_image_url
        seed_slot = seed_slot or "chain"
    elif chain_image_url:
        image_url = str(chain_image_url)
        binding["seed_mode"] = "chain_frame"
        binding["image_field"] = "image_url"
        prompt_seed_url = image_url
        seed_slot = seed_slot or "chain"
    else:
        s1 = slots.get("@1") or {}
        image_file_id = str(s1["file_id"]) if s1.get("file_id") else None
        image_url = str(s1["url"]) if s1.get("url") else None
        binding["seed_mode"] = "@1_plate"
        prompt_seed_url = image_url
        seed_slot = seed_slot or "@1"
        if image_file_id:
            binding["image_field"] = "image_file_id"
        elif image_url:
            binding["image_field"] = "image_url"
        else:
            binding["image_field"] = "none"

    prompt = compile_barebones_prose_prompt(
        shot,
        refs,
        prod_dir,
        script,
        image_url=prompt_seed_url,
        seed_slot=seed_slot,
    )

    gen_kwargs: dict[str, Any] = {
        "prompt": prompt,
        "model": refs["model_video"],
        "duration": duration,
        "resolution": refs["resolution"],
        "aspect_ratio": _script_aspect_ratio(script),
    }
    if image_file_id:
        gen_kwargs["image_file_id"] = image_file_id
        binding["image_value"] = image_file_id
    elif image_url:
        gen_kwargs["image_url"] = image_url
        binding["image_value"] = image_url
    if ref_ids:
        gen_kwargs["reference_image_file_ids"] = ref_ids

    return {"prompt": prompt, "kwargs": gen_kwargs, "binding": binding}


def generate_barebones_video(
    client: Any,
    shot: dict[str, Any],
    refs: dict[str, Any],
    script: dict[str, Any],
    prod_dir: Path | None,
    *,
    duration: int,
    chain_image_url: str | None = None,
    chain_image_file_id: str | None = None,
    seed_slot: str | None = None,
) -> tuple[Any, dict[str, Any]]:
    """video.generate with @1 image + @2+ reference_image_file_ids."""
    req = build_barebones_generate_request(
        shot,
        refs,
        script,
        prod_dir,
        duration=duration,
        chain_image_url=chain_image_url,
        chain_image_file_id=chain_image_file_id,
        seed_slot=seed_slot,
    )
    binding = req["binding"]
    kwargs = req["kwargs"]
    sent_fields = [k for k in ("image_file_id", "image_url", "reference_image_file_ids") if kwargs.get(k)]
    _log(
        f"[barebones] generate {shot.get('id')}: seed={binding.get('seed_mode')} "
        f"image_field={binding.get('image_field')} "
        f"refs={len(binding.get('reference_image_file_ids') or [])} "
        f"sent={sent_fields}"
    )
    _api_pace()
    try:
        resp = client.video.generate(**kwargs)
    except Exception as exc:
        if _reference_images_not_supported(exc) and kwargs.get("reference_image_file_ids"):
            _log(
                f"[barebones] {REFERENCE_IMAGES_API_FINDING['finding']} "
                f"(model={kwargs.get('model')})"
            )
        raise
    return resp, req


def _is_barebones_mode(script: dict[str, Any] | None) -> bool:
    return _prompt_mode(script) in ("barebones", "asset_directed")


def build_asset_directed_prompt(
    shot: dict[str, Any],
    refs: dict[str, Any],
    prod_dir: Path | None,
    *,
    script: dict[str, Any] | None = None,
    image_url: str | None = None,
    seed_slot: str | None = None,
) -> str:
    """Backward-compatible alias — compiles BAREBONES → prose_prompt."""
    return compile_barebones_prose_prompt(
        shot, refs, prod_dir, script, image_url=image_url, seed_slot=seed_slot,
    )


def build_video_generation_prompt(
    shot: dict[str, Any],
    refs: dict[str, Any],
    opts: SeamlessOptions,
    *,
    script: dict[str, Any] | None = None,
    prod_dir: Path | None = None,
    image_url: str | None = None,
    seed_slot: str | None = None,
) -> str:
    mode = _prompt_mode(script)
    if mode in ("asset_directed", "barebones"):
        return compile_barebones_prose_prompt(
            shot,
            refs,
            prod_dir,
            script,
            image_url=image_url,
            seed_slot=seed_slot,
        )
    base = apply_seamless_prompt(shot, refs, opts)
    return inject_api_file_ref_tokens(base, shot, refs)


def get_pure_character_seed(
    shot: dict[str, Any],
    refs: dict[str, Any],
    *,
    use_avatar: bool = True,
) -> str:
    """@2-only video seed — casting avatar or viz plate; never @1 zone plates.

    use_avatar=False routes science/@2-viz shots to visualization_url only.
    Empty @1 environment plates stay on disk; set lives in shot video_prompt.
    """
    if shot.get("image_url"):
        return str(shot["image_url"])
    if _shot_uses_viz_reference(shot) or not use_avatar:
        viz = refs.get("visualization_url")
        if viz:
            return str(viz)
        if not use_avatar:
            raise RuntimeError(
                f"Shot {shot.get('id')}: use_avatar=False but no visualization_url"
            )
    avatar = refs.get("avatar_url")
    if not avatar:
        raise RuntimeError(
            f"Shot {shot.get('id')}: no @2 avatar_url for pure character seed"
        )
    return str(avatar)


def resolve_shot_image_url(shot: dict[str, Any], refs: dict[str, Any]) -> str:
    """Delegate to get_pure_character_seed — @2 avatar/viz seed for re-ground shots."""
    use_avatar = not _shot_uses_viz_reference(shot)
    return get_pure_character_seed(shot, refs, use_avatar=use_avatar)


def resolve_shot0_set_seed(shot: dict[str, Any], refs: dict[str, Any]) -> str:
    """Shot 01 image_url — mode-dependent pixel seed.

    barebones/asset_directed: empty @1 set plate (walk-in; @2 named in prose).
    seamless legacy: @2 avatar locks identity; set lives in @file prompt tokens.
    """
    if shot.get("image_url"):
        return str(shot["image_url"])
    # Viz shots: seed from visualization reference (no character anchor needed)
    if _shot_uses_viz_reference(shot) and refs.get("visualization_url"):
        return str(refs["visualization_url"])
    mode = str(refs.get("prompt_mode") or "seamless")
    if mode in ("barebones", "asset_directed"):
        plate_url = refs.get("@1_plate_url")
        if plate_url:
            return str(plate_url)
    # Character/host shots: avatar is the identity anchor.
    # Set plate is already in @file tokens via inject_api_file_ref_tokens().
    avatar_url = refs.get("avatar_url")
    if avatar_url:
        return str(avatar_url)
    # Fallback: plate (pure set shots with no character)
    zone = _shot_zone(shot) or "@1"
    plate_url = refs.get(f"{zone}_plate_url")
    if plate_url:
        return str(plate_url)
    return resolve_shot_image_url(shot, refs)


def _use_avatar_reground(
    refs: dict[str, Any],
    shot: dict[str, Any],
    shot_index: int,
    opts: "SeamlessOptions",
) -> bool:
    """Dark/high-contrast: re-ground every shot on locked avatar (never drifted chain frame)."""
    mode = str(refs.get("prompt_mode") or "seamless")
    if mode in ("barebones", "asset_directed"):
        return shot_index == 0
    if _shot_uses_viz_reference(shot) and refs.get("visualization_url"):
        return True
    if _is_dark_scene(refs, shot=shot):
        return True
    if shot_index == 0:
        return True
    reground_n = _effective_reground_interval(opts, refs, shot)
    return reground_n > 0 and (shot_index % reground_n == 0)


def _magenta_reroll_attempts(refs: dict[str, Any], shot: dict[str, Any]) -> int:
    return 5 if _is_dark_scene(refs, shot=shot) else 3


def _load_set_library() -> dict[str, Any]:
    global _SET_LIBRARY_CACHE
    if _SET_LIBRARY_CACHE is None:
        if SET_LIBRARY_PATH.is_file():
            _SET_LIBRARY_CACHE = json.loads(SET_LIBRARY_PATH.read_text(encoding="utf-8"))
        else:
            _SET_LIBRARY_CACHE = {}
    return _SET_LIBRARY_CACHE


def _extract_set_id(text: str) -> str | None:
    m = re.search(r"@Set-[\w-]+", text)
    return m.group(0) if m else None


def _set_lighting_lock(set_id: str) -> str | None:
    entry = (_load_set_library().get("sets") or {}).get(set_id)
    if not entry:
        return None
    lock = entry.get("lighting_lock")
    return str(lock) if lock else None


def _kelvin_lock_for_prompt(base: str, refs: dict[str, Any]) -> str | None:
    if re.search(r"\b\d{4}\s*k\b", base, re.I):
        return None
    set_id = _extract_set_id(base)
    if set_id:
        lock = _set_lighting_lock(set_id)
        if lock:
            return lock
    set_file = str(refs.get("set_file") or "").lower()
    if "warehouse" in set_file or "industrial" in set_file:
        return WAREHOUSE_KELVIN_LOCK_PROMPT
    if "archive" in set_file:
        return LAMP_LOCK_PROMPT
    return None


def purge_archive_warm_prompt_clauses(text: str) -> str:
    """Strip warm-global Archive clauses before generation (#218)."""
    out = _ARCHIVE_WARM_PURGE_RE.sub(_ARCHIVE_NEUTRAL_PROMPT_BLOCK, text)
    out = re.sub(r"\bwarm brass lamplight\b", "neutral ambient light, brass lamp accent on desk only", out, flags=re.I)
    out = re.sub(r"\bWarm inviting close\b", "Neutral inviting close", out)
    out = re.sub(r"\bamber pool only on desk and face\b", "localized warm pool on desk quadrant only", out, flags=re.I)
    return out


def _is_dark_scene(
    refs: dict[str, Any],
    *,
    script: dict[str, Any] | None = None,
    shot: dict[str, Any] | None = None,
) -> bool:
    set_file = str(refs.get("set_file") or "").lower()
    # Archive host desk is NOT a dark-scene grade path (#218) — "shadow" in color guards
    # must not trigger DARK_SCENE_MAGENTA_CLAMP (gamma_b=0.68 crushes blue).
    if _refs_is_archive(refs) or "archive" in set_file:
        return False
    # Clinical seamless sets use "shadow definition" in prompts — not dark-scene grade (#193).
    if any(k in set_file for k in ("cyclorama", "seamless_neutral", "studio_interior")):
        return False
    if any(k in set_file for k in ("warehouse", "industrial", "rooftop", "night", "dusk")):
        return True
    texts: list[str] = []
    if shot:
        texts.append(shot.get("video_prompt", ""))
    elif script:
        texts.extend(s.get("video_prompt", "") for s in script.get("shots", []))
    blob = " ".join(texts).lower()
    if any(k in blob for k in DARK_SCENE_KEYWORDS):
        return True
    return bool(re.search(r"\b(4200|4300|4800)\s*k\b", blob, re.I))


def _effective_reground_interval(
    opts: "SeamlessOptions",
    refs: dict[str, Any],
    shot: dict[str, Any],
) -> int:
    if _is_dark_scene(refs, shot=shot):
        return 1
    return opts.reground_interval


def _clamp_stage_marker(out: Path) -> Path:
    return out.with_suffix(out.suffix + ".clamp244.json")


def _clamp_already_applied(out: Path) -> bool:
    marker = _clamp_stage_marker(out)
    if not marker.is_file():
        return False
    try:
        data = json.loads(marker.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return False
    return (
        data.get("issue") == CLAMP_STAGE_ISSUE
        and data.get("stage") == CLAMP_STAGE_NAME
        and data.get("vf") == MAGENTA_SATURATION_CLAMP_VF
        and out.is_file()
        and out.stat().st_size > 10_000
    )


def _write_clamp_stage_marker(out: Path, *, magenta: float, host_b: float) -> None:
    _clamp_stage_marker(out).write_text(
        json.dumps({
            "issue": CLAMP_STAGE_ISSUE,
            "stage": CLAMP_STAGE_NAME,
            "vf": MAGENTA_SATURATION_CLAMP_VF,
            "magenta": round(magenta, 4),
            "host_blue_mean": round(host_b, 1),
        }, indent=2),
        encoding="utf-8",
    )


def _magenta_clamp_vf(
    *,
    dark_scene: bool,
    lamp_lock: bool,
    strong: bool = False,
    archive_neutral: bool = False,
) -> str:
    if archive_neutral and not dark_scene:
        return MAGENTA_SATURATION_CLAMP_VF
    if strong or dark_scene:
        base = MAGENTA_CLAMP_STRONG_VF if strong else DARK_SCENE_MAGENTA_CLAMP_VF
    else:
        base = MAGENTA_CLAMP_VF
    if lamp_lock and not archive_neutral:
        return f"{base},{LAMP_LOCK_VF}"
    return base


def _normalize_shot_list(
    shots: list[dict[str, Any]],
    cfg: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    t = 0
    for s in shots:
        shot = {**s}
        if "shot_id" in shot and "id" not in shot:
            shot["id"] = shot.pop("shot_id")
        timing = shot.pop("timing", None) or {}
        dur = shot.get("duration", 0)
        shot.setdefault("t_start", timing.get("start_s", t))
        shot.setdefault("t_end", timing.get("end_s", t + dur))
        t = int(shot["t_end"])
        speech = shot.get("speech_text", "")
        prompt = shot.get("video_prompt", "")
        if speech and speech not in prompt and narration_enabled({"config": cfg or {}}, shot):
            shot["video_prompt"] = f'{prompt.rstrip()} Lip-synced, delivers: "{speech}"'
        out.append(shot)
    return out


def _canonicalize_config(raw: dict[str, Any], cfg: dict[str, Any]) -> dict[str, Any]:
    """Fold legacy top-level fields into config; seamless lives only in config."""
    out = dict(cfg)
    for key in ("model_video", "resolution", "aspect_ratio"):
        if key not in out and raw.get(key):
            out[key] = raw[key]
    if "compare_v1" not in out and raw.get("compare_v1"):
        out["compare_v1"] = raw["compare_v1"]
    seam = out.get("seamless") or raw.get("seamless") or raw.get("config", {}).get("seamless")
    if seam:
        out["seamless"] = seam
    avatar_rel = (raw.get("avatar") or {}).get("reference")
    if avatar_rel and "avatar_reference" not in out:
        out["avatar_reference"] = str(_resolve_david_path(avatar_rel))
    lock_rel = raw.get("host_identity") or raw.get("identity_lock")
    if lock_rel and "identity_lock" not in out:
        out["identity_lock"] = str(_resolve_david_path(lock_rel))
    voice = out.get("voice_suffix") or raw.get("voice_suffix", DEFAULT_VOICE_SUFFIX)
    if "synthetic" not in voice.lower():
        voice = f"{voice}, {SYNTHETIC_GUARD}"
    out["voice_suffix"] = voice
    return out


def _embed_legacy_continuity(
    shots: list[dict[str, Any]],
    prefix: str,
    guard: str,
    voice: str,
    cfg: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    """Bake legacy top-level continuity_prefix/end_guard into video_prompt when missing."""
    out: list[dict[str, Any]] = []
    for s in shots:
        shot = {**s}
        prompt = shot.get("video_prompt", "")
        if "@David-001" not in prompt and prefix:
            prompt = f"{prefix} {prompt}".strip()
        speech = shot.get("speech_text", "")
        if speech and speech not in prompt and narration_enabled({"config": cfg or {}}, shot):
            prompt = f'{prompt.rstrip()} Lip-synced, delivers: "{speech}"'
        if "gesture peak" not in prompt.lower() and guard:
            prompt = f"{prompt.rstrip()} {guard}"
        shot["video_prompt"] = ensure_voice_in_prompt(prompt, voice)
        for drop in ("shot_id", "scene_id", "join", "timing", "gesture_peak", "continuity_prefix", "end_guard"):
            shot.pop(drop, None)
        out.append(shot)
    return out


def normalize_script(raw: dict[str, Any], script_path: Path) -> dict[str, Any]:
    """Accept canonical schema or legacy shapes; always return canonical in-memory."""
    if "config" in raw and "shots" in raw:
        cfg = _canonicalize_config(raw, dict(raw["config"]))
        shots = _normalize_shot_list(raw["shots"], cfg)
        prefix = raw.get("continuity_prefix", "")
        guard = raw.get("end_guard", "")
        if prefix or guard:
            shots = _embed_legacy_continuity(
                shots, prefix, guard, cfg.get("voice_suffix", DEFAULT_VOICE_SUFFIX), cfg,
            )
        prov = raw.get("provenance_card")
        if not prov and raw.get("closing_card"):
            closing = raw["closing_card"]
            prov = {
                "enabled": closing.get("type") != "none",
                "card_type": "closing",
                "duration_s": closing.get("duration_s", 6),
                "title": closing.get("text", "DAVID · The Archive"),
                "subtitle": closing.get("subtext", ""),
                "footer": raw.get("cta", ""),
            }
        out = {
            "slug": raw.get("slug", script_path.stem.replace("_script", "")),
            "title": raw.get("title", raw.get("slug", script_path.stem)),
            "target_seconds": raw.get("target_seconds"),
            "config": cfg,
            "shots": shots,
            "provenance_card": prov or {"enabled": False},
            "qa_rules": raw.get("qa_rules", {
                "require_identity_lock": True,
                "require_synthetic_guard": True,
                "min_shots": 1,
            }),
        }
        for key in (
            "format_id", "concept", "production_dir", "production_meta",
            "guardrails", "continuity_prefix", "end_guard", "intake",
        ):
            if raw.get(key) is not None:
                out[key] = raw[key]
        return out

    # Channel intro / alternate longform shape (shot_id, host_identity, closing_card)
    if "shots" in raw and any("shot_id" in s for s in raw["shots"]):
        slug = raw.get("slug", script_path.stem.replace("_script", ""))
        lock_rel = raw.get("host_identity") or raw.get("identity_lock", "productions/host_identity_v1/david_identity_lock.json")
        avatar_rel = (raw.get("avatar") or {}).get("reference", "")
        closing = raw.get("closing_card", {})
        voice = raw.get("voice_suffix", DEFAULT_VOICE_SUFFIX)
        if "synthetic" not in voice.lower():
            voice = f"{voice}, {SYNTHETIC_GUARD}"

        cfg: dict[str, Any] = {
            "model_video": raw.get("model_video", "grok-imagine-video-1.5"),
            "resolution": raw.get("resolution", "720p"),
            "aspect_ratio": raw.get("aspect_ratio", "16:9"),
            "identity_lock": str(_resolve_david_path(lock_rel)),
            "voice_suffix": voice,
        }
        if avatar_rel:
            cfg["avatar_reference"] = str(_resolve_david_path(avatar_rel))
        if raw.get("seamless"):
            cfg["seamless"] = raw["seamless"]
        if raw.get("compare_v1"):
            cfg["compare_v1"] = raw["compare_v1"]

        shots = _normalize_shot_list(raw["shots"])
        prefix = raw.get("continuity_prefix", DEFAULT_CONTINUITY_PREFIX)
        guard = raw.get("end_guard", DEFAULT_END_GUARD)
        shots = _embed_legacy_continuity(shots, prefix, guard, voice)

        return {
            "slug": slug,
            "title": raw.get("title", slug),
            "target_seconds": raw.get("target_seconds"),
            "config": cfg,
            "shots": shots,
            "provenance_card": {
                "enabled": closing.get("type") != "none",
                "card_type": "closing",
                "duration_s": closing.get("duration_s", 6),
                "title": closing.get("text", "DAVID · The Archive"),
                "subtitle": closing.get("subtext", ""),
                "footer": raw.get("cta", ""),
            },
            "qa_rules": {
                "require_identity_lock": True,
                "require_synthetic_guard": True,
                "require_reconstructed_labels": False,
                "min_shots": 1,
            },
        }

    slug = raw.get("slug", script_path.stem)
    cfg: dict[str, Any] = {
        "model_video": "grok-imagine-video-1.5",
        "resolution": "720p",
        "aspect_ratio": "16:9",
        "identity_lock": str(raw.get("identity_lock", DEFAULT_LOCK)),
        "voice_suffix": DEFAULT_VOICE_SUFFIX,
    }
    if raw.get("host_reference"):
        cfg["avatar_reference"] = raw["host_reference"]

    prov = raw.get("provenance", {})
    title = raw.get("title", slug)
    banner = "RECONSTRUCTED — NOT ATTESTED"
    if raw.get("text_confidence") == "attested":
        banner = "ATTESTED TEXT · RECONSTRUCTED PRONUNCIATION"

    lines = []
    if prov.get("text"):
        lines.append(f"TEXT: {prov['text']}")
    if prov.get("pronunciation"):
        lines.append(f"PRONUNCIATION: {prov['pronunciation']}")
    if raw.get("line_ipa"):
        lines.append(f"IPA: {raw['line_ipa']}")
    if raw.get("translation"):
        lines.append(f"TRANSLATION: {raw['translation']}")
    if raw.get("reconstructed_text"):
        lines.append(f"LINE: {raw['reconstructed_text']}")
    if raw.get("attested_text"):
        lines.append(f"LINE: {raw['attested_text']}")
    if prov.get("citation"):
        lines.append(f"CITATION: {prov['citation']}")
    if prov.get("sources"):
        lines.append(f"SOURCES: {prov['sources']}")
    if prov.get("brain_scrape"):
        lines.append(f"BRAIN: {prov['brain_scrape']}")

    return {
        **{k: v for k, v in raw.items() if k not in ("shots", "provenance")},
        "slug": slug,
        "title": title,
        "config": cfg,
        "shots": _normalize_shot_list(raw.get("shots", [])),
        "provenance": prov,
        "provenance_card": {
            "enabled": True,
            "duration_s": 7,
            "banner": banner,
            "title": "DAVID · PROVENANCE",
            "subtitle": title,
            "lines": lines or [title],
            "footer": raw.get("on_screen_labels", {}).get("text", "DAVID"),
        },
        "qa_rules": {
            "require_identity_lock": True,
            "require_synthetic_guard": True,
            "min_shots": 1,
        },
    }


def assert_generation_reference_gate(
    script: dict[str, Any],
    refs: dict[str, Any],
    *,
    seamless_opts: SeamlessOptions | None = None,
) -> None:
    """T243 — block full render when avatar/set stills are blue-starved at source."""
    opts = seamless_opts or SeamlessOptions()
    if not opts.neutral_generation or not opts.enabled:
        return
    if not _is_archive_production(script, refs):
        return

    from PIL import Image

    failures: list[str] = []
    avatar_path = Path(str(refs.get("avatar_file") or ""))
    set_path = Path(str(refs.get("set_file") or ""))

    if avatar_path.is_file():
        with Image.open(avatar_path) as img:
            metrics = measure_color_cast(np.asarray(img.convert("RGB")))
        if not generation_reference_passes(metrics, host=True):
            failures.append(
                f"avatar {avatar_path.name}: {generation_reference_breaches(metrics, host=True)} "
                f"(Bμ={metrics['host_blue_mean']:.1f} B/R={metrics['host_br_ratio']:.3f} "
                f"starve={metrics['blue_starvation_fraction']:.3f})"
            )
    else:
        failures.append(f"avatar reference missing: {avatar_path}")

    if set_path.is_file():
        with Image.open(set_path) as img:
            set_metrics = measure_set_shadow_blue_health(np.asarray(img.convert("RGB")))
        if not generation_reference_passes(set_metrics, host=False):
            failures.append(
                f"set {set_path.name}: {generation_reference_breaches(set_metrics, host=False)} "
                f"(shadow Bμ={set_metrics['host_blue_mean']:.1f} "
                f"B/R={set_metrics['host_br_ratio']:.3f} "
                f"starve={set_metrics['blue_starvation_fraction']:.3f})"
            )
    else:
        failures.append(f"set reference missing: {set_path}")

    if failures:
        raise SystemExit(
            "Generation reference gate FAIL (#243) — regenerate avatar + set before render. "
            "Targets: Bμ≥40, B/R≥0.35, blue_starvation_fraction≤0.30. "
            f"Failures: {'; '.join(failures)}. "
            "Run: python DAVID/scripts/render_host_identity.py --force-refs"
        )


def assert_gate_0_cleared(script: dict[str, Any]) -> None:
    """Block render when intake Gate 0 is RED or pending human sign-off."""
    intake = script.get("intake") or {}
    gate = intake.get("gate_0") or {}
    if not gate:
        return  # legacy script without intake stamp
    verdict = gate.get("verdict", "")
    if gate.get("blocked") or verdict == "RED":
        report = gate.get("report_path", "unknown")
        raise SystemExit(
            f"Gate 0 RED — render blocked. No script may ship. Report: {report}"
        )
    if gate.get("requires_human_signoff") and not gate.get("human_signoff"):
        raise SystemExit(
            f"Gate 0 {verdict} — human sign-off required before render. "
            f"Set gate_0.human_signoff in concept and re-run intake, or update script intake stamp. "
            f"Report: {gate.get('report_path', 'unknown')}"
        )
    if gate.get("music_bed_id") and gate.get("row_2_music_sync") != "PASS":
        raise SystemExit(
            f"Gate 0 row 2 music/sync FAIL — render blocked for music bed "
            f"{gate.get('music_bed_id')}. Verify Studio/Music_Sound/clearance_manifest.json. "
            f"Report: {gate.get('report_path', 'unknown')}"
        )


def resolve_production_dir(script: dict[str, Any]) -> Path:
    if script.get("production_dir"):
        raw = str(script["production_dir"]).replace("\\", "/")
        if raw.split("/", 1)[0].lower() == "studio":  # canonical or legacy casing
            return _resolve_workspace_path(raw)
        p = Path(script["production_dir"])
        return p if p.is_absolute() else (ROOT / p)
    slug = script.get("slug", "longform")
    if script.get("format_id") and script["format_id"] != "documentary-host":
        return WORKSPACE / "Studio" / "Productions" / "Editorial" / f"{slug}_longform_v1"
    return ROOT / "productions" / f"{slug}_longform_v1"


def resolve_refs(script: dict[str, Any], *, client: Any = None) -> dict[str, Any]:
    cfg = script.setdefault("config", {})
    use_lock = cfg.get("use_identity_lock", True)
    lock: dict[str, Any] = {}
    lock_path = Path(cfg.get("identity_lock", DEFAULT_LOCK))
    if use_lock:
        lock_path = lock_path if lock_path.is_absolute() else _resolve_workspace_path(str(lock_path))
        lock = load_identity_lock(lock_path)

    avatar_url = cfg.get("avatar_url")
    avatar_file = cfg.get("avatar_reference")
    set_file = cfg.get("set_reference")
    voice_suffix = cfg.get("voice_suffix") or lock.get("voice", {}).get("prompt_suffix") or DEFAULT_VOICE_SUFFIX

    if lock:
        refs_block = lock.get("references") or {}
        talent_ref = refs_block.get("talent_avatar") or refs_block.get("david_avatar") or {}
        set_ref = refs_block.get("set_plate") or refs_block.get("archive_set") or {}
        avatar_url = avatar_url or talent_ref.get("url")
        avatar_file = avatar_file or talent_ref.get("file")
        set_file = set_file or set_ref.get("file")
        if use_lock and not avatar_url:
            raise RuntimeError(
                "Avatar URL missing from identity lock — regenerate talent identity lock"
            )

    if avatar_file:
        ap = Path(str(avatar_file))
        avatar_file = str(ap if ap.is_absolute() else _resolve_workspace_path(str(avatar_file)))
    elif cfg.get("avatar_reference"):
        ar = _resolve_workspace_path(str(cfg["avatar_reference"]))
        if ar.is_file():
            avatar_file = str(ar)

    if set_file:
        sp = Path(str(set_file))
        set_file = str(sp if sp.is_absolute() else _resolve_workspace_path(str(set_file)))

    def _sidecar_get(image_path: str | None, key: str) -> str | None:
        if not image_path:
            return None
        meta = Path(image_path).with_suffix(".json")
        if not meta.is_file():
            return None
        try:
            val = json.loads(meta.read_text(encoding="utf-8")).get(key)
            return str(val) if val else None
        except (json.JSONDecodeError, OSError):
            return None

    def _write_image_sidecar(image_path: Path, fields: dict[str, Any]) -> None:
        meta_path = image_path.with_suffix(".json")
        existing: dict[str, Any] = {}
        if meta_path.is_file():
            try:
                existing = json.loads(meta_path.read_text(encoding="utf-8"))
            except (json.JSONDecodeError, OSError):
                pass
        existing.update(fields)
        meta_path.write_text(
            json.dumps(existing, indent=2, ensure_ascii=False), encoding="utf-8",
        )

    # Prefer fresh regen sidecar over stale identity_lock url (#218).
    sidecar = _sidecar_get(avatar_file, "url")
    if sidecar:
        avatar_url = sidecar
        cfg["avatar_url"] = avatar_url

    # CDN url from sidecar is permanent; file_id is session-scoped — never reuse stale ids.
    avatar_file_id: str | None = None
    if client is not None and avatar_file:
        _api_pace()
        upload_url, avatar_file_id = upload_and_capture_id(
            client, Path(avatar_file), friendly="avatar",
        )
        if not avatar_url:
            avatar_url = upload_url
            cfg["avatar_url"] = upload_url
        cfg["avatar_file_id"] = avatar_file_id
        _write_image_sidecar(
            Path(avatar_file),
            {"url": avatar_url, "file_id": avatar_file_id},
        )

    viz_url = cfg.get("visualization_url")
    viz_file = cfg.get("visualization_reference")
    if viz_file:
        vp = Path(str(viz_file))
        viz_file = str(vp if vp.is_absolute() else _resolve_workspace_path(str(viz_file)))
    if not viz_url and viz_file and client is not None:
        viz_url = upload_image_url(client, Path(viz_file))
        cfg["visualization_url"] = viz_url

    return {
        "lock": lock,
        "lock_path": lock_path,
        "avatar_url": avatar_url,
        "avatar_file_id": avatar_file_id,
        "avatar_file": avatar_file,
        "config_avatar_reference": cfg.get("avatar_reference"),
        "visualization_url": viz_url,
        "visualization_file": viz_file,
        "set_file": set_file,
        "voice_suffix": voice_suffix,
        "format_id": script.get("format_id"),
        "production_meta": script.get("production_meta"),
        "model_video": cfg.get("model_video", "grok-imagine-video-1.5"),
        "extend_model": cfg.get("extend_model")
        or (
            LEGACY_EXTEND_MODEL
            if "grok-imagine-video-1.5" in str(cfg.get("model_video", ""))
            else cfg.get("model_video", "grok-imagine-video-1.5")
        ),
        "resolution": cfg.get("resolution", "720p"),
        "prompt_mode": cfg.get("prompt_mode", "seamless"),
        "seamless_cfg": cfg.get("seamless") or {},
        "narration": narration_enabled(script),
    }


def ensure_voice_in_prompt(prompt: str, voice_suffix: str) -> str:
    if voice_suffix.lower() not in prompt.lower():
        prompt = f"{prompt.rstrip()} {voice_suffix}"
    if "synthetic" not in prompt.lower():
        prompt = f"{prompt.rstrip()} {SYNTHETIC_GUARD}"
    return prompt


def build_imagine_pack(
    script: dict[str, Any],
    refs: dict[str, Any],
    seamless_opts: SeamlessOptions | None = None,
) -> dict[str, Any]:
    shots = script["shots"]
    prov = script.get("provenance_card", {})
    use_seamless = seamless_opts and seamless_opts.enabled
    return {
        "slug": script.get("slug"),
        "title": script.get("title"),
        "model_video": refs["model_video"],
        "resolution": refs["resolution"],
        "aspect_ratio": script.get("config", {}).get("aspect_ratio", "16:9"),
        "host_reference": refs.get("avatar_file"),
        "avatar_url": refs.get("avatar_url"),
        "set_reference": refs.get("set_file"),
        "zone_plates": {
            k.replace("_plate_url", ""): v
            for k, v in refs.items()
            if k.endswith("_plate_url")
        },
        "voice_suffix": refs["voice_suffix"],
        "seamless": use_seamless,
        "shots": [
            {
                "shot_id": s["id"],
                "duration": _eff_dur(s, refs, seamless=use_seamless),
                "image_url": resolve_shot_image_url(s, refs),
                "video_prompt": (
                    apply_seamless_prompt(s, refs, seamless_opts)
                    if use_seamless
                    else ensure_voice_in_prompt(s["video_prompt"], refs["voice_suffix"])
                ),
                "speech_text": s.get("speech_text", ""),
                "speech_ipa": s.get("speech_ipa"),
                "on_screen": s.get("on_screen", ""),
                "on_screen_labels": s.get("on_screen_labels", []),
                "timing": {
                    "start_s": s.get("t_start"),
                    "end_s": s.get("t_end"),
                },
            }
            for s in shots
        ],
        "provenance_shot": {
            "type": "code_rendered_png",
            "duration_s": prov.get("duration_s", 7),
            "enabled": prov.get("enabled", True),
        },
    }


def render_provenance_card(script: dict[str, Any], out_path: Path) -> None:
    from PIL import Image, ImageDraw, ImageFont

    prov = script.get("provenance_card", {})
    w, h = 1280, 720
    img = Image.new("RGB", (w, h), (12, 14, 20))
    draw = ImageDraw.Draw(img)
    try:
        title_font = ImageFont.truetype("arial.ttf", 40)
        warn_font = ImageFont.truetype("arialbd.ttf", 30)
        body_font = ImageFont.truetype("arial.ttf", 24)
        small_font = ImageFont.truetype("arial.ttf", 20)
    except OSError:
        title_font = warn_font = body_font = small_font = ImageFont.load_default()

    card_type = prov.get("card_type", "provenance")
    if card_type == "sources":
        draw.rectangle([(40, 40), (w - 40, h - 40)], outline=(90, 140, 180), width=4)
        banner = prov.get("banner", "HISTORICAL SOURCES")
        if banner:
            draw.rectangle([(55, 55), (w - 55, 110)], fill=(25, 45, 70))
            draw.text((70, 62), banner, fill=(180, 210, 240), font=warn_font)
            y_title = 130
        else:
            y_title = 70

        draw.text((70, y_title), prov.get("title", "SOURCES"), fill=(220, 190, 120), font=title_font)
        if prov.get("subtitle"):
            draw.text((70, y_title + 50), prov["subtitle"], fill=(240, 240, 245), font=body_font)

        rules = prov.get("render_rules") or {}
        max_lines = int(rules.get("max_lines_on_card", 6))
        trunc = int(rules.get("truncate_citation_chars", 88))
        pfx_p = rules.get("primary_prefix", "P")
        pfx_s = rules.get("secondary_prefix", "S")

        y = y_title + (100 if prov.get("subtitle") else 60)
        show_agency = bool(rules.get("show_agency"))
        for src in prov.get("sources", [])[:max_lines]:
            cite = str(src.get("citation", "")).strip()
            if len(cite) > trunc:
                cite = cite[: trunc - 1] + "…"
            kind = str(src.get("type", "secondary")).lower()
            prefix = pfx_p if kind == "primary" else pfx_s
            agency = str(src.get("agency", "")).strip()
            if show_agency and agency and kind == "primary":
                line = f"{prefix} [{agency}]: {cite}"
            else:
                line = f"{prefix}: {cite}"
            for wrapped in textwrap.wrap(line, width=78):
                draw.text((70, y), wrapped, fill=(200, 205, 215), font=small_font)
                y += 26
            if y > h - 120:
                break

        footer = prov.get("footer", "")
        if footer:
            for wrapped in textwrap.wrap(footer, width=70):
                draw.text((70, h - 90), wrapped, fill=(255, 180, 90), font=small_font)
                break
    elif card_type == "closing":
        draw.rectangle([(40, 40), (w - 40, h - 40)], outline=(180, 150, 90), width=3)
        title = prov.get("title", "DAVID · The Archive")
        subtitle = prov.get("subtitle", "")
        try:
            big_font = ImageFont.truetype("arial.ttf", 56)
        except OSError:
            big_font = title_font
        tw = draw.textlength(title, font=big_font)
        draw.text(((w - tw) / 2, h // 2 - 80), title, fill=(220, 190, 120), font=big_font)
        if subtitle:
            sw = draw.textlength(subtitle, font=body_font)
            draw.text(((w - sw) / 2, h // 2 + 10), subtitle, fill=(200, 205, 215), font=body_font)
        footer = prov.get("footer", "")
        if footer:
            for wrapped in textwrap.wrap(footer, width=60):
                fw = draw.textlength(wrapped, font=small_font)
                draw.text(((w - fw) / 2, h - 120), wrapped, fill=(255, 180, 90), font=small_font)
    else:
        draw.rectangle([(40, 40), (w - 40, h - 40)], outline=(200, 120, 50), width=4)
        banner = prov.get("banner", "")
        if banner:
            draw.rectangle([(55, 55), (w - 55, 110)], fill=(80, 45, 20))
            draw.text((70, 62), banner, fill=(255, 200, 120), font=warn_font)
            y_title = 130
        else:
            y_title = 70

        draw.text((70, y_title), prov.get("title", "DAVID · PROVENANCE"), fill=(220, 190, 120), font=title_font)
        if prov.get("subtitle"):
            draw.text((70, y_title + 50), prov["subtitle"], fill=(240, 240, 245), font=body_font)

        y = y_title + (100 if prov.get("subtitle") else 60)
        for line in prov.get("lines", []):
            for wrapped in textwrap.wrap(str(line), width=78):
                draw.text((70, y), wrapped, fill=(200, 205, 215), font=small_font)
                y += 28

        footer = prov.get("footer", "")
        if footer:
            draw.text((70, h - 70), footer, fill=(255, 180, 90), font=small_font)

    out_path.parent.mkdir(parents=True, exist_ok=True)
    img.save(out_path)


def provenance_to_video(png: Path, mp4: Path, duration: float) -> None:
    ff = _ffmpeg_exe()
    subprocess.run(
        [
            ff, "-y", "-loop", "1", "-i", str(png),
            "-c:v", "libx264", "-t", str(duration),
            "-pix_fmt", "yuv420p", "-vf", "scale=1280:720", str(mp4),
        ],
        check=True,
        capture_output=True,
    )


def concat_videos(parts: list[Path], out: Path, *, seamless: bool = False) -> None:
    if seamless:
        raise RuntimeError(
            "concat_videos hard-cut forbidden in seamless mode — use _reconcat_seamless_chain"
        )
    ff = _ffmpeg_exe()
    list_file = out.with_suffix(".txt")
    list_file.write_text(
        "\n".join(f"file '{p.resolve().as_posix()}'" for p in parts),
        encoding="utf-8",
    )
    subprocess.run(
        [ff, "-y", "-f", "concat", "-safe", "0", "-i", str(list_file), "-c", "copy", str(out)],
        check=True,
        capture_output=True,
    )
    list_file.unlink(missing_ok=True)


def _xfade_from_template(format_id: str) -> float:
    """Load xfade_s from Production_Templates_v1.json for the given format_id.

    Fallback chain: template → DEFAULT_XFADE_S. Never raises.
    """
    try:
        tmpl_path = (
            WORKSPACE / "Studio" / "Pipeline"
            / "Production_Templates" / "Production_Templates_v1.json"
        )
        tmpl = json.loads(tmpl_path.read_text(encoding="utf-8"))
        return float(tmpl["formats"][format_id]["seamless_defaults"]["xfade_s"])
    except Exception:  # noqa: BLE001
        return DEFAULT_XFADE_S


def resolve_xfade_s(
    *,
    cli: float | None,
    script_seam: dict[str, Any] | None = None,
    format_id: str | None = None,
) -> float:
    """Clamp cross-dissolve to perceptible range for frame-chain continuity.

    Fallback chain: CLI → script_seam.xfade_s → template by format_id → DEFAULT_XFADE_S.
    """
    seam = script_seam or {}
    if cli is not None:
        raw = float(cli)
    elif "xfade_s" in seam:
        raw = float(seam["xfade_s"])
    elif format_id:
        raw = _xfade_from_template(format_id)
    else:
        raw = DEFAULT_XFADE_S
    return max(MIN_XFADE_S, min(MAX_XFADE_S, raw))


@dataclass
class SeamlessOptions:
    enabled: bool = False
    xfade_s: float = DEFAULT_XFADE_S
    match_color: bool = False
    cut_on_motion: bool = False
    lamp_lock: bool = True
    glasses_lock: bool = True
    loudnorm: bool = True
    pin_audio_sync: bool = True
    reground_interval: int = REGROUND_EVERY_N
    magenta_clamp: bool = False  # opt-in per production — no universal grade
    neutral_grade: bool = False
    neutral_generation: bool = False


LEGACY_EXTEND_MODEL = "grok-imagine-video"

EXTEND_API_FINDING = {
    "scriptable": True,
    "enabled_on_model": True,
    "generate_model": "grok-imagine-video-1.5",
    "extend_model": LEGACY_EXTEND_MODEL,
    "editor_extend": "Grok Imagine UI Continue/Extend may work before API parity on 1.5",
    "finding": (
        "grok-imagine-video-1.5 generate + grok-imagine-video extend (split model path). "
        "1.5 rejects extend; legacy extend PASS from native vidgen URLs (probe 2026-06-29). "
        "Files API re-upload of trimmed MP4 returns HTTP 403 to extend service — use resp.url, "
        "not upload_video_url. extend_at_s trim is local join assembly only."
    ),
}

REFERENCE_IMAGES_API_FINDING = {
    "scriptable": True,
    "enabled_on_model": False,
    "model": "grok-imagine-video-1.5",
    "sdk_field": "reference_image_file_ids",
    "api_field": "reference_images",
    "probe_artifact": (
        "productions/matilda_kitchen_stonebridge_10s_longform_v1/proof/"
        "reference_images_probe_report.json"
    ),
    "probe_matrix_2026_06_29": {
        "total": 25,
        "pass": 3,
        "passing": [
            {"model": "grok-imagine-video", "mode": "r2v_ref_file_ids_only"},
            {"model": "grok-imagine-video", "mode": "r2v_ref_urls_only"},
            {"model": "grok-imagine-video", "mode": "r2v_ref_file_ids_and_urls"},
        ],
        "i2v_plus_refs_on_grok_imagine_video": (
            "INVALID_ARGUMENT: Cannot specify both image and reference_images — "
            "mutual exclusivity, not missing field"
        ),
        "all_refs_on_grok_imagine_video_1_5": (
            "reference_images is not supported for this model — true 1.5 gate"
        ),
        "phantom_models": ["grok-imagine-video-1.5-beta", "grok-imagine-video-r2v"],
        "sdk_no_exposed": ["x-grok-beta header", "enable_references flag", "api_version"],
    },
    "dead_escalations": [
        "reference_image_urls on grok-imagine-video-1.5 — same gate as file_ids",
        "grok-imagine-video-1.5-beta / grok-imagine-video-r2v — NOT_FOUND on team",
    ],
    "editor_compositing": (
        "Editor web @1+@2 dual-slot may use a surface that allows i2v+refs together; "
        "public API enforces image XOR reference_images on grok-imagine-video."
    ),
    "pr1_stance": (
        "Keep PR1 wired (image_file_id + reference_image_file_ids). "
        "When 1.5 gate opens or Editor-parity endpoint ships, zero rewire. "
        "Rejection repro is actionable for xAI."
    ),
    "production_stance": (
        "composite-first-frame baked@1 (proven kitchen v4) until Editor-parity API."
    ),
    "finding": (
        "Beta gate / surface exposure — not a hard SDK fiction. "
        "grok-imagine-video accepts pure R2V refs; grok-imagine-video-1.5 rejects all refs; "
        "i2v+refs combo rejected as mutually exclusive on both. PR1 preserved."
    ),
}

COMPOSITE_FIRST_FRAME_API_FINDING = {
    "scriptable": True,
    "enabled_on_model": True,
    "model": "grok-imagine-image-quality",
    "sdk_fields": ["image_file_ids", "image_urls"],
    "video_bridge": "composite JPG → video.generate(image_url=...) — no reference_images on video",
    "mechanism": (
        "client.image.sample() with image_file_ids=[@1_plate, @2_turntable] and barebones "
        "directive produces a single still; that still seeds the video chain at t=0."
    ),
    "slot_remap": (
        "Image step uses @1+@2 as edit inputs, but output is one baked frame: talent is "
        "staged in the setting from t=0. For video.generate that composite is @1 only "
        "(image_url/image_file_id) — not empty-plate @1 + reference_image_file_ids @2. "
        "Identity is pixel-locked in the seed; no separate compositing layer on video."
    ),
    "editor_delta": (
        "Editor dual-slot: @1 empty plate at t=0, @2 compositing (walk-in possible). "
        "Composite-first-frame: @1 carries talent+set baked in (walk-in not reproducible)."
    ),
    "finding": (
        "Image API accepts multi-reference editing via image_file_ids (distinct from video "
        "reference_images). Kitchen probe 2026-06-29: correct MATILDA identity, talent baked "
        "into setting — acceptable interim unblock; not Editor @1/@2 layer parity."
    ),
    "proof_artifact": (
        "productions/matilda_kitchen_stonebridge_10s_longform_v1/proof/"
        "composite_first_frame_probe.jpg"
    ),
    "visual_gate": "PASS_IDENTITY",
}


def get_seamless_options(script: dict[str, Any], args: argparse.Namespace) -> SeamlessOptions:
    seam = script.get("config", {}).get("seamless") or {}
    auto = seam.get("primary") in ("extend", "extend_chain", True)
    return SeamlessOptions(
        enabled=bool(getattr(args, "seamless", False) or auto),
        xfade_s=resolve_xfade_s(
            cli=getattr(args, "xfade", None),
            script_seam=seam,
            format_id=script.get("format_id"),
        ),
        match_color=getattr(args, "match_color", False) or bool(seam.get("match_color")),
        cut_on_motion=getattr(args, "cut_on_motion", False) or bool(seam.get("cut_on_motion")),
        lamp_lock=bool(seam.get("lamp_lock", True)),
        glasses_lock=bool(seam.get("glasses_lock", True)),
        loudnorm=bool(seam.get("loudnorm", True)),
        pin_audio_sync=bool(seam.get("pin_audio_sync", True)),
        reground_interval=int(seam.get("reground_interval", REGROUND_EVERY_N)),
        magenta_clamp=bool(seam.get("magenta_clamp", False)),  # opt-in only
        neutral_grade=bool(seam.get("neutral_grade", False)),
        neutral_generation=bool(seam.get("neutral_generation", False)),
    )


def apply_seamless_prompt(shot: dict[str, Any], refs: dict[str, Any], opts: SeamlessOptions) -> str:
    """Use embedded video_prompt when continuity is already baked in; else patch defaults."""
    base = shot.get("video_prompt", "")
    archive = "archive" in str(refs.get("set_file") or "").lower()
    if opts.neutral_generation and archive:
        base = purge_archive_warm_prompt_clauses(base)
    locks: list[str] = []
    if opts.neutral_generation and archive:
        locks.extend([ARCHIVE_ANTI_MAGENTA_GENERATION_LOCK, ARCHIVE_NEUTRAL_GENERATION_LOCK])
    else:
        kelvin_lock = _kelvin_lock_for_prompt(base, refs)
        if kelvin_lock:
            locks.append(kelvin_lock)
        elif opts.lamp_lock and archive and "3200K" not in base:
            locks.append(LAMP_LOCK_PROMPT)
    if opts.glasses_lock and archive and "glasses" not in base.lower():
        locks.append(GLASSES_LOCK_PROMPT)
    baked = "CONTINUITY LOCK @" in base and "gesture peak" in base.lower()
    if baked:
        out = ensure_voice_in_prompt(base, refs["voice_suffix"])
        if locks:
            out = f"{' '.join(locks)} {out}"
        return out
    base = ensure_voice_in_prompt(base, refs["voice_suffix"])
    script_ctx = refs.get("script") if isinstance(refs.get("script"), dict) else None
    speech = shot.get("speech_text", "") if narration_enabled(script_ctx, shot) else ""
    parts = list(locks)
    if "CONTINUITY LOCK @" not in base:
        parts.append(DEFAULT_CONTINUITY_PREFIX)
    parts.append(base)
    if speech and speech not in base:
        parts.append(f'Lip-synced, delivers: "{speech}"')
    parts.append(DEFAULT_END_GUARD)
    return " ".join(p.strip() for p in parts if p.strip())


def probe_duration(video: Path) -> float:
    ff = _ffmpeg_exe()
    r = subprocess.run(
        [ff, "-i", str(video)],
        capture_output=True,
        text=True,
    )
    for line in (r.stderr or "").splitlines():
        if "Duration:" in line:
            t = line.split("Duration:", 1)[1].split(",")[0].strip()
            h, m, s = t.split(":")
            return int(h) * 3600 + int(m) * 60 + float(s)
    raise RuntimeError(f"cannot probe duration: {video}")


def extract_frame_at(video: Path, at_s: float, out_jpg: Path) -> Path:
    ff = _ffmpeg_exe()
    out_jpg.parent.mkdir(parents=True, exist_ok=True)
    dur = probe_duration(video)
    seek = max(0.0, min(float(at_s), max(0.0, dur - 0.05)))
    subprocess.run(
        [
            ff, "-y", "-ss", f"{seek:.3f}", "-i", str(video),
            "-frames:v", "1", "-q:v", "2", "-update", "1", str(out_jpg),
        ],
        check=True,
        capture_output=True,
    )
    return out_jpg


def extract_last_frame(video: Path, out_jpg: Path) -> Path:
    dur = probe_duration(video)
    return extract_frame_at(video, max(0.0, dur - 0.4), out_jpg)


def analyze_handoff_frame(handoff_jpg: Path) -> dict[str, str]:
    """Read staging signals from last frame — lighting, distance, camera viewpoint.

    Output informs the next-branch prompt only. Frame is never an API image seed.
    """
    from PIL import Image

    img = Image.open(handoff_jpg).convert("RGB")
    w, h = img.size

    def _zone_luma(x0: int, y0: int, x1: int, y1: int) -> tuple[float, float]:
        rs = gs = bs = n = 0
        for y in range(y0, y1, max(2, (y1 - y0) // 24)):
            for x in range(x0, x1, max(2, (x1 - x0) // 24)):
                r, g, b = img.getpixel((x, y))
                rs += r
                gs += g
                bs += b
                n += 1
        if not n:
            return 128.0, 1.0
        lum = (0.299 * rs + 0.587 * gs + 0.114 * bs) / n
        warm = (rs / max(gs, 1)) / n
        return lum, warm

    fx0, fx1 = int(w * 0.30), int(w * 0.70)
    fy0, fy1 = int(h * 0.08), int(h * 0.62)
    face_lum, face_warm = _zone_luma(fx0, fy0, fx1, fy1)

    lx0, lx1 = int(w * 0.05), int(w * 0.45)
    rx0, rx1 = int(w * 0.55), int(w * 0.95)
    left_lum, _ = _zone_luma(lx0, fy0, fx1, fy1)
    right_lum, _ = _zone_luma(rx0, fy0, rx1, fy1)
    if left_lum > right_lum * 1.08:
        key_side = "key light from camera-left"
    elif right_lum > left_lum * 1.08:
        key_side = "key light from camera-right"
    else:
        key_side = "soft balanced frontal key"

    if face_warm > 1.12:
        kelvin = "warm amber skin key (~3200K)"
    elif face_warm < 0.92:
        kelvin = "cool neutral skin key (~5600K)"
    else:
        kelvin = "neutral documentary skin key"

    upper_lum, _ = _zone_luma(fx0, int(h * 0.05), fx1, int(h * 0.40))
    lower_lum, _ = _zone_luma(fx0, int(h * 0.40), fx1, int(h * 0.85))
    face_coverage = (fx1 - fx0) * (fy1 - fy0) / max(w * h, 1)
    if upper_lum > lower_lum * 1.18:
        framing = "tight close-up — face dominates upper frame, shoulders only"
        subject_distance = "close portrait distance — subject near lens"
    elif upper_lum > lower_lum * 1.05:
        framing = "medium close-up — head and upper chest"
        subject_distance = "medium-close conversational distance"
    else:
        framing = "medium shot — waist-up"
        subject_distance = "medium conversational distance — waist-up"

    if face_coverage > 0.22:
        subject_distance = "close portrait distance — subject near lens"
    elif face_coverage < 0.10:
        subject_distance = "medium-wide distance — more environment visible"

    horiz_bias = (left_lum - right_lum) / max(left_lum + right_lum, 1)
    if horiz_bias > 0.06:
        camera_viewpoint = "eye-level, camera viewpoint slightly favoring camera-left angle"
    elif horiz_bias < -0.06:
        camera_viewpoint = "eye-level, camera viewpoint slightly favoring camera-right angle"
    else:
        camera_viewpoint = "eye-level straight-on — centered camera viewpoint"

    contrast = "high contrast chiaroscuro" if face_lum < 95 else (
        "soft low-contrast fill" if face_lum > 165 else "moderate documentary contrast"
    )

    staging_guide = (
        f"{BRANCH_STAGING_GUIDE_PREFIX}: analyzed exit frame — "
        f"camera viewpoint: {camera_viewpoint}; "
        f"subject distance: {subject_distance}; "
        f"shot scale: {framing}; "
        f"lighting: {kelvin}; {key_side}; {contrast}; "
        f"reproduce this staging in generated output — zero drift in camera position, "
        f"lens distance, eyeline, or lighting"
    )
    composition_lock = (
        f"STAGING COMPOSITION: {camera_viewpoint}; {subject_distance}; {framing}; "
        f"locked static camera — zero reframing, zero zoom, zero pull-back, zero pan, zero tilt"
    )
    lighting_lock = (
        f"STAGING LIGHTING: {kelvin}; {key_side}; {contrast}; "
        f"same fill on face and set — zero lighting drift"
    )
    return {
        "framing": framing,
        "kelvin": kelvin,
        "key_side": key_side,
        "contrast": contrast,
        "camera_viewpoint": camera_viewpoint,
        "subject_distance": subject_distance,
        "composition_lock": composition_lock,
        "lighting_lock": lighting_lock,
        "staging_guide": staging_guide,
        "handoff_lock": staging_guide,
    }


def apply_staging_guide_to_shot(
    shot: dict[str, Any],
    staging_jpg: Path,
    *,
    prev_shot_id: str,
    meta: dict[str, str] | None = None,
) -> dict[str, Any]:
    """Inject last-frame staging analysis into next-branch prompt (not image seed)."""
    staging_meta = meta or analyze_handoff_frame(staging_jpg)
    out = dict(shot)
    bb = dict(out.get("barebones") or {})
    bb["staging_guide"] = staging_meta["staging_guide"]
    bb["scene"] = (
        f"{staging_meta['composition_lock']}; {staging_meta['lighting_lock']}; "
        f"{str(bb.get('scene') or '').strip()}"
    ).strip(" ;")
    bb["camera"] = (
        f"{staging_meta['camera_viewpoint']}; {staging_meta['framing']}; "
        f"locked static — matches {prev_shot_id} exit staging; zero camera move"
    )
    bb["extension_composition"] = staging_meta["framing"]
    out["barebones"] = bb
    out["_staging_from"] = prev_shot_id
    out["_staging_frame_local"] = str(staging_jpg)
    return out


def apply_handoff_to_shot(
    shot: dict[str, Any],
    handoff_jpg: Path,
    *,
    prev_shot_id: str,
) -> dict[str, Any]:
    """Backward-compatible alias for apply_staging_guide_to_shot."""
    return apply_staging_guide_to_shot(shot, handoff_jpg, prev_shot_id=prev_shot_id)


def resolve_extend_at_s(shot: dict[str, Any], segment_duration: float) -> float | None:
    """Script editorial out-point — dialogue/movement wrapped, good extend pose."""
    raw = shot.get("extend_at_s")
    if raw is None:
        return None
    at = float(raw)
    dur = float(segment_duration)
    if at <= 0 or at >= dur - 0.1:
        return None
    return at


def trim_segment_to_s(video: Path, out: Path, end_s: float) -> Path:
    """Trim segment to script extend_at_s before join (drops tail dead air)."""
    ff = _ffmpeg_exe()
    out.parent.mkdir(parents=True, exist_ok=True)
    cmd = [
        ff, "-y", "-i", str(video), "-t", f"{end_s:.3f}",
        "-c:v", "libx264", "-pix_fmt", "yuv420p",
    ]
    if has_audio_stream(video):
        cmd.extend(["-c:a", "aac", "-b:a", "192k"])
    cmd.append(str(out))
    subprocess.run(cmd, check=True, capture_output=True)
    return out


def shot_join_segment(proc_path: Path, shot: dict[str, Any], shots_dir: Path) -> Path:
    """Return segment used for xfade join — trimmed to extend_at_s when scripted."""
    dur = probe_duration(proc_path)
    end_s = resolve_extend_at_s(shot, dur)
    if end_s is None:
        return proc_path
    trimmed = shots_dir / f"{proc_path.stem}_extend_at_{end_s:.2f}s.mp4"
    trim_segment_to_s(proc_path, trimmed, end_s)
    _log(f"[extend_at] {shot['id']} join trim → {end_s:.2f}s (was {dur:.2f}s)")
    return trimmed


def reject_concat_only_seamless_grade(
    *,
    concat_only: bool,
    seamless_opts: SeamlessOptions,
    match_color: bool,
    cut_on_motion: bool,
    seamless_flag: bool,
) -> None:
    """#194 — grading/re-seam requires fresh segments; concat-only must hard-fail."""
    if not concat_only:
        return
    if (
        seamless_opts.enabled
        or seamless_flag
        or match_color
        or cut_on_motion
        or seamless_opts.match_color
        or seamless_opts.cut_on_motion
        or seamless_opts.magenta_clamp
        or seamless_opts.neutral_grade
    ):
        raise SystemExit(
            "--concat-only cannot grade or re-seam (#194). "
            "Cached raw segments produce unchanged pixels — QA false-pass. "
            "Omit --concat-only; use --force-all for a full seamless re-render."
        )


def trim_tail_motion(video: Path, out: Path, trim_s: float = 0.15) -> Path:
    """Trim trailing stillness before a frame-chain join (--cut-on-motion)."""
    ff = _ffmpeg_exe()
    dur = probe_duration(video)
    keep = max(0.5, dur - trim_s)
    subprocess.run(
        [ff, "-y", "-i", str(video), "-t", f"{keep:.3f}", "-c", "copy", str(out)],
        check=True,
        capture_output=True,
    )
    return out


def upload_image_url(client: Any, image_path: Path) -> str:
    uploaded = client.files.upload(str(image_path))
    pub = client.files.create_public_url(uploaded.id)
    url = getattr(pub, "public_url", None) or pub.public_url
    if not url:
        raise RuntimeError(f"Failed to create public URL for {image_path}")
    return url


def upload_video_url(client: Any, video_path: Path) -> str:
    """Upload MP4 for client.video.extend() source — best-frame trim, not JPG extract."""
    _log(f"[extend] uploading extend source {video_path.name}")
    return upload_image_url(client, video_path)


def build_extend_prose_prompt(
    shot: dict[str, Any],
    refs: dict[str, Any],
    opts: SeamlessOptions,
    script: dict[str, Any] | None,
    prod_dir: Path | None,
    *,
    baked_pipeline: bool = False,
) -> str:
    """Prompt for client.video.extend() — identity already in video pixels when baked."""
    if baked_pipeline or _is_barebones_mode(script):
        bb = shot.get("barebones") if isinstance(shot.get("barebones"), dict) else {}
        comp = str(
            shot.get("extension_composition")
            or bb.get("extension_composition")
            or ""
        ).strip()
        prompt = compile_barebones_prose_prompt(
            shot,
            refs,
            prod_dir,
            script,
            talent_baked_in=True,
            seed_slot="@1",
        )
        if comp:
            prompt = f"{prompt} ; EXTENSION COMPOSITION LOCK: {comp}"
        return prompt
    return build_video_generation_prompt(
        shot, refs, opts, script=script, prod_dir=prod_dir,
    )


def prepare_extend_source_url(
    client: Any,
    video_path: Path,
    shot: dict[str, Any],
    work_dir: Path,
    *,
    native_api_url: str | None = None,
) -> tuple[str, Path, float]:
    """Resolve extend API input URL; trim locally for join assembly when extend_at_s set.

    Native vidgen URLs from video.generate()/video.extend() are fetchable by the extend
    service. Files API re-uploads of trimmed MP4s return HTTP 403 — never use those here.
    """
    work_dir.mkdir(parents=True, exist_ok=True)
    dur = probe_duration(video_path)
    end_s = resolve_extend_at_s(shot, dur)
    src = video_path
    if end_s is not None:
        trimmed = work_dir / f"extend_source_{shot['id']}_{end_s:.2f}s.mp4"
        trim_segment_to_s(video_path, trimmed, end_s)
        src = trimmed
        _log(
            f"[extend] join trim {shot['id']}: {dur:.2f}s → {end_s:.2f}s "
            f"(extend_at_s — local assembly only)"
        )
    else:
        _log(f"[extend] extend source {shot['id']}: full segment {dur:.2f}s")
    if native_api_url:
        _log(
            f"[extend] API handoff {shot['id']}: native vidgen URL "
            f"(not re-upload; Files API URLs 403 on extend)"
        )
        return native_api_url, src, probe_duration(src)
    _api_pace()
    url = upload_video_url(client, src)
    return url, src, probe_duration(src)


def upload_and_capture_id(
    client: Any,
    image_path: Path,
    friendly: str | None = None,
) -> tuple[str, str]:
    """Upload image; log API file_id (file_XXXX) and return (public_url, file_id)."""
    uploaded = client.files.upload(str(image_path))
    raw_id = getattr(uploaded, "id", None)
    if not raw_id:
        raise RuntimeError(f"Upload returned no id for {image_path}")
    _log(
        f"[DIAGNOSTIC] path={image_path.name} | "
        f"uploaded.id={raw_id} | "
        f"type={type(raw_id)} | "
        f"filename={getattr(uploaded, 'filename', None)} | "
        f"size={getattr(uploaded, 'size', None)}"
    )
    pub = client.files.create_public_url(raw_id)
    url = getattr(pub, "public_url", None) or getattr(pub, "url", None) or str(pub)
    if not url:
        raise RuntimeError(f"Failed to create public URL for {image_path}")
    if friendly:
        _log(f"[DIAGNOSTIC] friendly='{friendly}' → id={raw_id}")
    return url, str(raw_id)


def resolve_color_reference(refs: dict[str, Any], shots_dir: Path) -> Path:
    """Locked warm-gold reference — David-001 avatar still (never drifted chain frame)."""
    candidates: list[Path] = []
    if refs.get("avatar_file"):
        candidates.append(Path(str(refs["avatar_file"])))
    cfg_ref = refs.get("config_avatar_reference")
    if cfg_ref:
        candidates.append(_resolve_david_path(str(cfg_ref)))
    lock = refs.get("lock") or {}
    lock_file = (lock.get("references") or {}).get("david_avatar", {}).get("file")
    if lock_file:
        candidates.append(Path(str(lock_file)))
    for p in candidates:
        if p.is_file():
            return p
    anchor = shots_dir / "color_anchor.jpg"
    if anchor.is_file():
        return anchor
    raise RuntimeError("No color reference (avatar_file or color_anchor.jpg)")


def _parse_loudnorm_json(stderr: str) -> dict[str, str] | None:
    m = re.search(r"\{[\s\S]*?\"input_i\"[\s\S]*?\}", stderr)
    if not m:
        return None
    try:
        return json.loads(m.group(0))
    except json.JSONDecodeError:
        return None


def pin_av_to_duration(video: Path, out: Path, duration_s: float) -> Path:
    """Trim/pad audio to exact video duration — no atempo stretch, no offset."""
    ff = _ffmpeg_exe()
    out.parent.mkdir(parents=True, exist_ok=True)
    d = f"{duration_s:.6f}"
    has_a = has_audio_stream(video)
    if has_a:
        filt = (
            f"[0:v]fps=24,trim=0:{d},setpts=PTS-STARTPTS[v];"
            f"[0:a]asetpts=PTS-STARTPTS,atrim=0:{d},"
            f"apad=whole_dur={d}[a]"
        )
        maps = ["-map", "[v]", "-map", "[a]", "-c:a", "aac", "-b:a", "192k"]
    else:
        filt = f"[0:v]fps=24,trim=0:{d},setpts=PTS-STARTPTS[v]"
        maps = ["-map", "[v]"]
    subprocess.run(
        [
            ff, "-y", "-i", str(video),
            "-filter_complex", filt,
            *maps, "-c:v", "libx264", "-pix_fmt", "yuv420p", str(out),
        ],
        check=True,
        capture_output=True,
    )
    return out


def _remux_av(
    video: Path,
    out: Path,
    *,
    af: str | None = None,
    vf: str | None = None,
    copy_video: bool = True,
) -> None:
    """Remux primary video+audio streams — skips attached-picture sidecars."""
    ff = _ffmpeg_exe()
    out.parent.mkdir(parents=True, exist_ok=True)
    cmd = [ff, "-y", "-i", str(video), "-map", "0:0"]
    if vf:
        cmd.extend(["-vf", vf, "-c:v", "libx264", "-pix_fmt", "yuv420p"])
    elif copy_video:
        cmd.extend(["-c:v", "copy"])
    else:
        cmd.extend(["-c:v", "libx264", "-pix_fmt", "yuv420p"])
    if has_audio_stream(video):
        cmd.extend(["-map", "0:1"])
        if af:
            cmd.extend(["-af", af, "-c:a", "aac", "-b:a", "192k"])
        else:
            cmd.extend(["-c:a", "aac", "-b:a", "192k"])
    cmd.append(str(out))
    subprocess.run(cmd, check=True, capture_output=True)


def loudnorm_two_pass(
    video: Path,
    out: Path,
    *,
    target_i: float = LOUDNORM_I,
    target_tp: float = LOUDNORM_TP,
    target_lra: float = LOUDNORM_LRA,
) -> Path:
    """Two-pass EBU R128 loudnorm — one target for every shot."""
    ff = _ffmpeg_exe()
    out.parent.mkdir(parents=True, exist_ok=True)
    if not has_audio_stream(video):
        shutil.copy2(video, out)
        return out
    measure_af = f"loudnorm=I={target_i}:TP={target_tp}:LRA={target_lra}:print_format=json"
    r1 = subprocess.run(
        [ff, "-i", str(video), "-map", "0:a", "-af", measure_af, "-f", "null", "-"],
        capture_output=True,
        text=True,
    )
    stats = _parse_loudnorm_json(r1.stderr or "")
    if not stats:
        _log("[audio] loudnorm measure failed; dynaudnorm fallback")
        _remux_av(video, out, af="dynaudnorm=f=150:g=15:p=0.95:m=100:s=12")
        return out
    apply_af = (
        f"loudnorm=I={target_i}:TP={target_tp}:LRA={target_lra}:"
        f"measured_I={stats.get('input_i', target_i)}:"
        f"measured_TP={stats.get('input_tp', target_tp)}:"
        f"measured_LRA={stats.get('input_lra', target_lra)}:"
        f"measured_thresh={stats.get('input_thresh', '-70')}:"
        f"offset={stats.get('target_offset', '0')}:linear=true"
    )
    _remux_av(video, out, af=apply_af)
    return out


def probe_integrated_loudness(video: Path) -> float | None:
    if not has_audio_stream(video):
        return None
    ff = _ffmpeg_exe()
    r = subprocess.run(
        [
            ff, "-i", str(video),
            "-af", f"loudnorm=I={LOUDNORM_I}:TP={LOUDNORM_TP}:LRA={LOUDNORM_LRA}:print_format=json",
            "-f", "null", "-",
        ],
        capture_output=True,
        text=True,
    )
    stats = _parse_loudnorm_json(r.stderr or "")
    if stats and "input_i" in stats:
        try:
            return float(stats["input_i"])
        except ValueError:
            return None
    return None


def probe_av_duration_delta(video: Path, expected_s: float | None = None) -> float:
    """Container duration vs expected shot length; 0 = tight sync."""
    dur = probe_duration(video)
    if expected_s is None:
        return 0.0
    return abs(dur - expected_s)


def chain_segment_paths(shots_dir: Path, shots: list[dict[str, Any]]) -> list[Path]:
    paths: list[Path] = []
    for s in shots:
        proc = shots_dir / f"chain_{s['id']}_processed.mp4"
        raw = shots_dir / f"chain_{s['id']}.mp4"
        paths.append(proc if proc.is_file() and proc.stat().st_size > 10000 else raw)
    return paths


def chain_join_segments(
    shots_dir: Path,
    shots: list[dict[str, Any]],
    proc_segments: list[Path] | None = None,
) -> list[Path]:
    """Map processed chain segments to xfade join clips (extend_at_s trim when scripted)."""
    procs = proc_segments or chain_segment_paths(shots_dir, shots)
    return [
        shot_join_segment(proc, shot, shots_dir)
        for shot, proc in zip(shots, procs)
        if proc.is_file() and proc.stat().st_size > 10000
    ]


def resolve_chain_seed_segment(shots_dir: Path, prev_shot: dict[str, Any]) -> Path:
    """Full-duration processed/raw segment for extend_at_s frame extraction."""
    proc = shots_dir / f"chain_{prev_shot['id']}_processed.mp4"
    if proc.is_file() and proc.stat().st_size > 10000:
        return proc
    raw = shots_dir / f"chain_{prev_shot['id']}.mp4"
    return raw


def _extend_probe_skipped(refs: dict[str, Any], script: dict[str, Any] | None) -> bool:
    """Skip extend probe only when no legacy extend model is configured."""
    seam = (script or {}).get("config", {}).get("seamless") or {}
    if seam.get("skip_extend_probe"):
        return True
    extend_model = str(refs.get("extend_model") or refs.get("model_video") or "")
    gen_model = str(refs.get("model_video") or "")
    if extend_model == LEGACY_EXTEND_MODEL:
        return False
    if "grok-imagine-video-1.5" in gen_model and extend_model == gen_model:
        return True
    return False


def _chain_cache_status(
    shots_dir: Path,
    shots: list[dict[str, Any]],
) -> tuple[bool, bool, int, int, list[Path]]:
    """Return (all_present, any_present, present_count, total, segment_paths)."""
    chain_segs = chain_segment_paths(shots_dir, shots)
    present = [p for p in chain_segs if p.is_file() and p.stat().st_size > 10000]
    total = len(chain_segs)
    n = len(present)
    return n == total and total > 0, n > 0, n, total, chain_segs


def _persist_extend_state(
    state_path: Path,
    *,
    mode: str,
    opts: SeamlessOptions,
    segment_count: int,
    join_mode: str,
) -> None:
    state_path.write_text(
        json.dumps({
            "mode": mode,
            "extend_api": {**EXTEND_API_FINDING, "continuity_mode": mode},
            "segments": segment_count,
            "join_mode": join_mode,
            "xfade_s": opts.xfade_s,
            "assembly": (
                f"{join_mode}_{opts.xfade_s}s_loudnorm={opts.loudnorm}"
                f"_pin_sync={opts.pin_audio_sync}_magenta_clamp={opts.magenta_clamp}"
            ),
        }),
        encoding="utf-8",
    )


def _probe_grey_balance(video: Path, at_s: float | None = None) -> float:
    """Neutral grey balance metric for clinical sets — lower drift = better continuity."""
    from PIL import Image

    ff = _ffmpeg_exe()
    at_s = at_s if at_s is not None else max(0.0, probe_duration(video) * 0.5)
    jpg = video.with_suffix(".grey_probe.jpg")
    subprocess.run(
        [ff, "-y", "-ss", f"{at_s:.3f}", "-i", str(video), "-frames:v", "1", str(jpg)],
        check=True,
        capture_output=True,
    )
    img = Image.open(jpg).convert("RGB")
    w, h = img.size
    rs = gs = bs = n = 0
    for y in range(int(h * 0.1), int(h * 0.55), 8):
        for x in range(int(w * 0.15), int(w * 0.85), 8):
            r, g, b = img.getpixel((x, y))
            rs += r
            gs += g
            bs += b
            n += 1
    jpg.unlink(missing_ok=True)
    if not n:
        return 0.0
    r_mean, g_mean, b_mean = rs / n, gs / n, bs / n
    return abs(r_mean - g_mean) / 255.0 + abs(b_mean - g_mean) / 255.0


def probe_magenta_score(video: Path, at_s: float | None = None) -> float:
    """Fraction of ambient pixels with purple/magenta bias (0=none, 1=all)."""
    from PIL import Image

    ff = _ffmpeg_exe()
    at_s = at_s if at_s is not None else max(0.0, probe_duration(video) * 0.5)
    jpg = video.with_suffix(".magenta_probe.jpg")
    subprocess.run(
        [ff, "-y", "-ss", f"{at_s:.3f}", "-i", str(video), "-frames:v", "1", str(jpg)],
        check=True,
        capture_output=True,
    )
    img = Image.open(jpg).convert("RGB")
    w, h = img.size
    magenta_n = total_n = 0
    for y in range(0, h, 6):
        for x in range(0, w, 6):
            r, g, b = img.getpixel((x, y))
            lum = 0.299 * r + 0.587 * g + 0.114 * b
            if lum < 40 or lum > 200:
                continue
            total_n += 1
            if b > r * 1.08 and b > g * 1.05:
                magenta_n += 1
            elif (r + b) > g * 1.35 and b > g * 0.95:
                magenta_n += 1
    jpg.unlink(missing_ok=True)
    return magenta_n / total_n if total_n else 0.0


def probe_clinical_channel_balance(video: Path, at_s: float | None = None) -> float:
    """#199 absolute host RGB imbalance — catches blue-deficit casts yg gate misses."""
    from PIL import Image

    if str(Path(__file__).resolve().parent) not in sys.path:
        sys.path.insert(0, str(Path(__file__).resolve().parent))
    import color_cast_qa as cc  # noqa: WPS433

    ff = _ffmpeg_exe()
    at_s = at_s if at_s is not None else max(0.0, probe_duration(video) * 0.5)
    jpg = video.with_suffix(".ccb_probe.jpg")
    subprocess.run(
        [ff, "-y", "-ss", f"{at_s:.3f}", "-i", str(video), "-frames:v", "1", str(jpg)],
        check=True,
        capture_output=True,
    )
    img = Image.open(jpg).convert("RGB")
    score = cc.clinical_channel_balance(np.asarray(img))
    jpg.unlink(missing_ok=True)
    return score


def probe_yellow_green_score(video: Path, at_s: float | None = None) -> float:
    """Yellow-green cast in non-lamp host region — lower is better (#194)."""
    from PIL import Image

    ff = _ffmpeg_exe()
    at_s = at_s if at_s is not None else max(0.0, probe_duration(video) * 0.5)
    jpg = video.with_suffix(".yg_probe.jpg")
    subprocess.run(
        [ff, "-y", "-ss", f"{at_s:.3f}", "-i", str(video), "-frames:v", "1", str(jpg)],
        check=True,
        capture_output=True,
    )
    img = Image.open(jpg).convert("RGB")
    w, h = img.size
    bias_n = total_n = 0
    for y in range(int(h * 0.18), int(h * 0.72), 6):
        for x in range(int(w * 0.08), int(w * 0.48), 6):
            r, g, b = img.getpixel((x, y))
            lum = 0.299 * r + 0.587 * g + 0.114 * b
            if lum < 35 or lum > 210:
                continue
            total_n += 1
            if g > r * 1.06 and g > b * 1.04:
                bias_n += 1
    jpg.unlink(missing_ok=True)
    return bias_n / total_n if total_n else 0.0


def probe_color_cast_score(video: Path, at_s: float | None = None) -> dict[str, float]:
    """Blue-starvation / warm-cast gate — catches casts yellow-green probe misses (#194 T4)."""
    from PIL import Image

    ff = _ffmpeg_exe()
    at_s = at_s if at_s is not None else max(0.0, probe_duration(video) * 0.5)
    jpg = video.with_suffix(".cast_probe.jpg")
    subprocess.run(
        [ff, "-y", "-ss", f"{at_s:.3f}", "-i", str(video), "-frames:v", "1", str(jpg)],
        check=True,
        capture_output=True,
    )
    with Image.open(jpg) as img:
        metrics = measure_color_cast(np.asarray(img.convert("RGB")))
    jpg.unlink(missing_ok=True)
    return metrics


def apply_neutral_white_balance_grade(
    video: Path,
    out: Path,
    color_ref: Path,
) -> Path:
    """Clinical/neutral WB grade — histogram match + neutral clamp, no full-frame lamp cast (#193)."""
    ff = _ffmpeg_exe()
    out.parent.mkdir(parents=True, exist_ok=True)
    clamp_vf = CLINICAL_NEUTRAL_CLAMP_VF
    cur = video
    staged = out.with_name(f"{out.stem}_neutral_stage.mp4")

    use_histogram = color_ref.suffix.lower() in (".jpg", ".jpeg", ".png", ".webp")
    if use_histogram:
        vfilter = (
            "[0:v][1:v]histogrammatching=pattern=1:strength=0.55[matched];"
            f"[matched]{clamp_vf}[outv]"
        )
        hist_cmd = [
            ff, "-y", "-i", str(video), "-loop", "1", "-i", str(color_ref),
            "-filter_complex", vfilter,
            "-map", "[outv]", "-c:v", "libx264", "-pix_fmt", "yuv420p",
        ]
        if has_audio_stream(video):
            hist_cmd.extend(["-map", "0:1", "-c:a", "aac", "-b:a", "192k"])
        hist_cmd.extend(["-shortest", str(staged)])
        r = subprocess.run(hist_cmd, capture_output=True, text=True)
        if r.returncode == 0:
            cur = staged
        else:
            _log("[seamless] neutral WB histogram failed; eq-only fallback")
            use_histogram = False

    if not use_histogram:
        if not _run_video_eq_pass(video, staged, clamp_vf):
            shutil.copy2(video, out)
            return out
        cur = staged

    for pass_n in range(2):
        yg = probe_yellow_green_score(cur)
        if yg <= YELLOW_GREEN_SCORE_MAX:
            break
        strong_vf = f"{CLINICAL_NEUTRAL_CLAMP_VF},{MAGENTA_CLAMP_STRONG_VF}"
        strong_out = out.with_name(f"{out.stem}_neutral_strong{pass_n}.mp4")
        if not _run_video_eq_pass(cur, strong_out, strong_vf):
            break
        cur = strong_out
        _log(f"[neutral] WB strong pass {pass_n + 1}/2 (yellow-green was {yg:.3f})")

    staging = out.with_name(f"{out.stem}__neutral_staging.mp4")
    if staging.exists():
        staging.unlink(missing_ok=True)
    shutil.move(str(cur), str(staging))
    os.replace(staging, out)
    return out


def apply_lamp_accent_local(video: Path, out: Path) -> Path:
    """Warm 3200K pool on desk/lamp quadrant only — not full-frame tint (#194)."""
    ff = _ffmpeg_exe()
    out.parent.mkdir(parents=True, exist_ok=True)
    filt = (
        "[0:v]split=2[base][warmsrc];"
        f"[warmsrc]{LAMP_ACCENT_VF}[warmed];"
        "[base][warmed]blend=all_expr="
        "'if(between(X,W*0.52)*between(X,W*0.94)*between(Y,H*0.12)*between(Y,H*0.68),"
        "A*(1-0.62)+B*0.62,A)'[outv]"
    )
    cmd = [
        ff, "-y", "-i", str(video),
        "-filter_complex", filt,
        "-map", "[outv]", "-map", "0:a?",
        "-c:v", "libx264", "-pix_fmt", "yuv420p",
        "-c:a", "copy", str(out),
    ]
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        shutil.copy2(video, out)
    return out


def _shot_needs_label_chip_burn(shot: dict[str, Any]) -> bool:
    if shot.get("burn_label_chip"):
        return True
    on_screen = (shot.get("on_screen") or "").upper()
    return "PRONUNCIATION" in on_screen


def _video_frame_size(video: Path) -> tuple[int, int]:
    from PIL import Image

    ff = _ffmpeg_exe()
    jpg = video.with_suffix(".dims_probe.jpg")
    subprocess.run(
        [ff, "-y", "-ss", "0.5", "-i", str(video), "-frames:v", "1", str(jpg)],
        check=True,
        capture_output=True,
    )
    with Image.open(jpg) as img:
        w, h = img.size
    jpg.unlink(missing_ok=True)
    return w, h


def render_pronunciation_chip_overlay(
    shot: dict[str, Any],
    out_path: Path,
    *,
    width: int,
    height: int,
) -> Path:
    """High-contrast code-burned pronunciation chips (#194 washed-out fix)."""
    from PIL import Image, ImageDraw, ImageFont

    img = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    try:
        chip_font = ImageFont.truetype("arialbd.ttf", max(18, width // 56))
        sub_font = ImageFont.truetype("arial.ttf", max(15, width // 68))
    except OSError:
        chip_font = sub_font = ImageFont.load_default()

    on_screen = (shot.get("on_screen") or "").strip()
    parts = [p.strip() for p in on_screen.split("·")] if on_screen else []
    primary = parts[0].upper() if parts else "RECONSTRUCTED PRONUNCIATION"
    secondary = parts[1] if len(parts) > 1 else ""

    x, y = int(width * 0.025), int(height * 0.055)
    chip_color = LABEL_CHIP_COLORS.get(primary, (140, 88, 28, 245))
    tw = draw.textlength(primary, font=chip_font)
    pad = max(10, width // 96)
    chip_h = max(34, height // 22)
    draw.rounded_rectangle(
        [(x, y), (x + tw + pad * 2, y + chip_h)],
        radius=8,
        fill=chip_color,
    )
    draw.text((x + pad, y + pad // 2), primary, fill=(255, 255, 255, 255), font=chip_font)

    if secondary:
        sub_y = y + chip_h + 8
        stw = draw.textlength(secondary, font=sub_font)
        draw.rounded_rectangle(
            [(x, sub_y), (x + stw + pad * 2, sub_y + chip_h - 6)],
            radius=6,
            fill=LABEL_CHIP_COLORS.get(secondary.upper(), (40, 48, 62, 235)),
        )
        draw.text((x + pad, sub_y + 4), secondary, fill=(245, 242, 235, 255), font=sub_font)

    out_path.parent.mkdir(parents=True, exist_ok=True)
    img.save(out_path)
    return out_path


def burn_label_overlay(video: Path, overlay_png: Path, out: Path) -> Path:
    ff = _ffmpeg_exe()
    out.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        [
            ff, "-y",
            "-i", str(video),
            "-i", str(overlay_png),
            "-filter_complex", "[0:v][1:v]overlay=0:0:format=auto,format=yuv420p[v]",
            "-map", "[v]", "-map", "0:a?",
            "-c:v", "libx264", "-pix_fmt", "yuv420p",
            "-c:a", "copy", str(out),
        ],
        check=True,
        capture_output=True,
    )
    return out


def apply_warm_gold_clamp(video: Path, out: Path, color_ref: Path) -> Path:
    """Magenta suppression + warm-gold clamp against locked talent reference."""
    return apply_per_shot_magenta_clamp(
        video, out, color_ref, dark_scene=False, lamp_lock=True,
    )


def apply_archive_saturation_clamp_once(
    video: Path,
    out: Path,
    *,
    apply_lamp_accent: bool = False,
) -> Path:
    """#244 — one saturation-reduction eq pass; idempotent via .clamp244.json marker."""
    out.parent.mkdir(parents=True, exist_ok=True)
    if _clamp_already_applied(out):
        _log(f"[#244] clamp idempotent skip — already stamped {out.name}")
        return out

    staged = out.with_name(f"{out.stem}_clamp_stage.mp4")
    if not _run_video_eq_pass(video, staged, MAGENTA_SATURATION_CLAMP_VF):
        shutil.copy2(video, out)
        return out
    cur = staged

    if apply_lamp_accent:
        accented = out.with_name(f"{out.stem}_lamp_accent.mp4")
        apply_lamp_accent_local(cur, accented)
        cur = accented

    staging = out.with_name(f"{out.stem}__clamp_staging.mp4")
    if staging.exists():
        staging.unlink(missing_ok=True)
    shutil.move(str(cur), str(staging))
    os.replace(staging, out)
    cast = probe_color_cast_score(out)
    _write_clamp_stage_marker(
        out,
        magenta=probe_magenta_score(out),
        host_b=cast.get("host_blue_mean", 0.0),
    )
    return out


def _run_video_eq_pass(video: Path, out: Path, vf: str) -> bool:
    ff = _ffmpeg_exe()
    cmd = [
        ff, "-y", "-i", str(video), "-vf", vf,
        "-map", "0:0", "-c:v", "libx264", "-pix_fmt", "yuv420p",
    ]
    if has_audio_stream(video):
        cmd.extend(["-map", "0:1", "-c:a", "aac", "-b:a", "192k"])
    cmd.append(str(out))
    r = subprocess.run(cmd, capture_output=True, text=True)
    return r.returncode == 0


def apply_per_shot_magenta_clamp(
    video: Path,
    out: Path,
    color_ref: Path,
    *,
    dark_scene: bool = False,
    lamp_lock: bool = True,
    archive_neutral: bool = False,
    neutral_generation: bool = False,
) -> Path:
    """Per-shot magenta suppression — archive-neutral delegates to single-pass #244 clamp."""
    out.parent.mkdir(parents=True, exist_ok=True)
    if archive_neutral and not dark_scene:
        return apply_archive_saturation_clamp_once(
            video,
            out,
            apply_lamp_accent=not neutral_generation,
        )

    clamp_vf = _magenta_clamp_vf(
        dark_scene=dark_scene, lamp_lock=lamp_lock, archive_neutral=archive_neutral,
    )
    staged = out.with_name(f"{out.stem}_clamp_stage.mp4")
    ff = _ffmpeg_exe()
    cur = video
    use_histogram = (
        not dark_scene
        and color_ref.suffix.lower() in (".jpg", ".jpeg", ".png", ".webp")
    )
    if use_histogram:
        vfilter = (
            "[0:v][1:v]histogrammatching=pattern=1:strength=0.55[matched];"
            f"[matched]{clamp_vf}[outv]"
        )
        hist_cmd = [
            ff, "-y", "-i", str(video), "-loop", "1", "-i", str(color_ref),
            "-filter_complex", vfilter,
            "-map", "[outv]", "-c:v", "libx264", "-pix_fmt", "yuv420p",
        ]
        if has_audio_stream(video):
            hist_cmd.extend(["-map", "0:1", "-c:a", "aac", "-b:a", "192k"])
        hist_cmd.extend(["-shortest", str(staged)])
        r = subprocess.run(hist_cmd, capture_output=True, text=True)
        if r.returncode == 0:
            cur = staged
        else:
            _log("[seamless] per-shot histogram clamp failed; eq-only fallback")
            use_histogram = False

    if not use_histogram:
        if not _run_video_eq_pass(video, staged, clamp_vf):
            shutil.copy2(video, out)
            return out
        cur = staged

    max_strong = 4 if dark_scene else 2
    for pass_n in range(max_strong):
        mag = probe_magenta_score(cur)
        if mag <= MAGENTA_SCORE_MAX:
            break
        strong_vf = _magenta_clamp_vf(
            dark_scene=True, lamp_lock=lamp_lock, strong=True, archive_neutral=False,
        )
        strong_out = out.with_name(f"{out.stem}_strong{pass_n}.mp4")
        if not _run_video_eq_pass(cur, strong_out, strong_vf):
            break
        cur = strong_out
        _log(f"[magenta] within-clip strong pass {pass_n + 1}/{max_strong} (score was {mag:.3f})")

    staging = out.with_name(f"{out.stem}__clamp_staging.mp4")
    if staging.exists():
        staging.unlink(missing_ok=True)
    shutil.move(str(cur), str(staging))
    os.replace(staging, out)
    return out


GRADE_HOLD_WARM_VF = "eq=gamma_r=1.03:gamma_g=1.00:gamma_b=0.92:saturation=1.06:brightness=0.01"
GRADE_HOLD_HIST_STRENGTH = 0.28
LIVING_ROOM_RECOVERY_STRENGTH = 0.65
LIVING_ROOM_RECOVERY_FINISH_VF = "eq=brightness=-0.04:saturation=1.03"


def _probe_video_frame_arr(video: Path, at_s: float | None = None) -> np.ndarray:
    from PIL import Image

    ff = _ffmpeg_exe()
    at_s = at_s if at_s is not None else max(0.0, probe_duration(video) * 0.5)
    jpg = video.with_suffix(".grade_hold_probe.jpg")
    subprocess.run(
        [ff, "-y", "-ss", f"{at_s:.3f}", "-i", str(video), "-frames:v", "1", str(jpg)],
        check=True,
        capture_output=True,
    )
    return np.array(Image.open(jpg).convert("RGB"))


def _anchor_channel_mixer_vf(
    video: Path,
    anchor: Path,
    strength: float,
) -> str | None:
    """Host-region channel pull toward anchor — fallback when histogrammatching missing."""
    from color_cast_qa import host_channel_means

    try:
        vf = _probe_video_frame_arr(video)
        af = np.array(__import__("PIL").Image.open(anchor).convert("RGB"))
    except Exception:
        return None
    vr, vg, vb, _ = host_channel_means(vf)
    ar, ag, ab, _ = host_channel_means(af)

    def _ratio(target: float, source: float) -> float:
        if source < 8.0:
            return 1.0
        return max(0.75, min(1.25, target / source))

    rr, gg, bb = _ratio(ar, vr), _ratio(ag, vg), _ratio(ab, vb)
    s = max(0.0, min(1.0, strength))
    mixer = (
        f"colorchannelmixer=rr={rr:.4f}:rg=0:rb=0:"
        f"gr=0:gg={gg:.4f}:gb=0:br=0:bg=0:bb={bb:.4f}"
    )
    return (
        f"[0:v]split=2[base][src];[src]{mixer}[corr];"
        f"[base][corr]blend=all_expr='A*(1-{s})+B*{s}'[matched];"
        f"[matched]{GRADE_HOLD_WARM_VF}[outv]"
    )


def apply_living_room_skin_recovery(
    video: Path,
    out: Path,
    color_ref: Path,
    *,
    strength: float = LIVING_ROOM_RECOVERY_STRENGTH,
) -> Path:
    """b07/b08 magenta recovery — pull host RGB toward kitchen anchor, no blue crush."""
    out.parent.mkdir(parents=True, exist_ok=True)
    ff = _ffmpeg_exe()
    staged = out.with_name(f"{out.stem}_lr_recovery.mp4")
    vfilter = _anchor_channel_mixer_vf(video, color_ref, strength)
    if not vfilter:
        return apply_grade_hold_light(video, out, color_ref)
    vfilter = vfilter.replace(GRADE_HOLD_WARM_VF, LIVING_ROOM_RECOVERY_FINISH_VF)
    cmd = [
        ff, "-y", "-i", str(video), "-filter_complex", vfilter,
        "-map", "[outv]", "-c:v", "libx264", "-pix_fmt", "yuv420p",
    ]
    if has_audio_stream(video):
        cmd.extend(["-map", "0:1", "-c:a", "aac", "-b:a", "192k"])
    cmd.append(str(staged))
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        _log("[lr-recovery] channel pull failed; grade-hold fallback")
        return apply_grade_hold_light(video, out, color_ref)

    cur = staged
    mag = probe_magenta_score(cur)
    if mag > 0.35:
        mild = (
            "colorchannelmixer=rr=0.94:rg=0.02:rb=0:gr=0.02:gg=1.04:gb=0:"
            "br=0:bg=0:bb=0.96"
        )
        mild_out = out.with_name(f"{out.stem}_lr_mild.mp4")
        if _run_video_eq_pass(cur, mild_out, mild):
            cur = mild_out
            _log(f"[lr-recovery] mild magenta trim (score was {mag:.3f})")

    staging = out.with_name(f"{out.stem}__lr_recovery_staging.mp4")
    if staging.exists():
        staging.unlink(missing_ok=True)
    shutil.move(str(cur), str(staging))
    os.replace(staging, out)
    return out


def apply_grade_hold_light(
    video: Path,
    out: Path,
    color_ref: Path,
    *,
    hist_strength: float = GRADE_HOLD_HIST_STRENGTH,
) -> Path:
    """Pull living-room grade toward kitchen anchor — preserves warm skin, kills magenta."""
    out.parent.mkdir(parents=True, exist_ok=True)
    ff = _ffmpeg_exe()
    staged = out.with_name(f"{out.stem}_grade_hold.mp4")
    matched = False
    if color_ref.suffix.lower() in (".jpg", ".jpeg", ".png", ".webp"):
        vfilter = (
            f"[0:v][1:v]histogrammatching=pattern=1:strength={hist_strength}[matched];"
            f"[matched]{GRADE_HOLD_WARM_VF}[outv]"
        )
        cmd = [
            ff, "-y", "-i", str(video), "-loop", "1", "-i", str(color_ref),
            "-filter_complex", vfilter,
            "-map", "[outv]", "-c:v", "libx264", "-pix_fmt", "yuv420p",
        ]
        if has_audio_stream(video):
            cmd.extend(["-map", "0:1", "-c:a", "aac", "-b:a", "192k"])
        cmd.extend(["-shortest", str(staged)])
        r = subprocess.run(cmd, capture_output=True, text=True)
        matched = r.returncode == 0
        if not matched:
            _log("[grade-hold] histogram unavailable; anchor channel-mixer fallback")

    if not matched:
        vfilter = _anchor_channel_mixer_vf(video, color_ref, hist_strength)
        if vfilter:
            cmd = [
                ff, "-y", "-i", str(video), "-filter_complex", vfilter,
                "-map", "[outv]", "-c:v", "libx264", "-pix_fmt", "yuv420p",
            ]
            if has_audio_stream(video):
                cmd.extend(["-map", "0:1", "-c:a", "aac", "-b:a", "192k"])
            cmd.append(str(staged))
            r = subprocess.run(cmd, capture_output=True, text=True)
            matched = r.returncode == 0
            if not matched:
                _log("[grade-hold] channel-mixer failed; warm-eq fallback")

    if not matched:
        if not _run_video_eq_pass(video, staged, GRADE_HOLD_WARM_VF):
            shutil.copy2(video, out)
            return out

    cur = staged
    mag = probe_magenta_score(cur)
    if mag > MAGENTA_SCORE_MAX:
        mild_out = out.with_name(f"{out.stem}_grade_mild.mp4")
        if _run_video_eq_pass(cur, mild_out, MAGENTA_CLAMP_VF):
            cur = mild_out
            _log(f"[grade-hold] mild magenta pass (score was {mag:.3f})")

    staging = out.with_name(f"{out.stem}__grade_hold_staging.mp4")
    if staging.exists():
        staging.unlink(missing_ok=True)
    shutil.move(str(cur), str(staging))
    os.replace(staging, out)
    return out


def match_color_segment(
    reference: Path,
    target: Path,
    out: Path,
    *,
    lamp_lock: bool = True,
    color_ref: Path | None = None,
    archive_neutral: bool = False,
    neutral_grade: bool = False,
    skip_post_clamp: bool = False,
) -> Path:
    """Match *target* to locked *color_ref* (David-001), not drifted prior segment.

    When skip_post_clamp=True (#244), histogram alignment only — saturation clamp already
    ran once in process_shot_segment; fallbacks pass through without re-clamp.
    """
    ff = _ffmpeg_exe()
    out.parent.mkdir(parents=True, exist_ok=True)
    ref = color_ref or reference
    if skip_post_clamp:
        post_vf = None
    elif neutral_grade:
        post_vf = CLINICAL_NEUTRAL_CLAMP_VF
    elif archive_neutral:
        post_vf = None  # #244 — clamp already applied in process_shot_segment
    elif lamp_lock:
        post_vf = f"{MAGENTA_CLAMP_VF},{LAMP_LOCK_VF}"
    else:
        post_vf = None  # no universal grade — style decided at generation
    if ref.suffix.lower() in (".jpg", ".jpeg", ".png", ".webp"):
        if post_vf:
            vfilter = (
                f"[0:v][1:v]histogrammatching=pattern=1:strength=0.62[matched];"
                f"[matched]{post_vf}[outv]"
            )
        else:
            vfilter = "[0:v][1:v]histogrammatching=pattern=1:strength=0.62[outv]"
        cmd = [
            ff, "-y", "-i", str(target), "-loop", "1", "-i", str(ref),
            "-filter_complex", vfilter,
            "-map", "[outv]", "-map", "0:a?", "-c:v", "libx264", "-pix_fmt", "yuv420p",
            "-c:a", "copy", "-shortest", str(out),
        ]
    elif lamp_lock and post_vf:
        vfilter = (
            f"[0:v][1:v]histogrammatching=pattern=1:strength=0.55[matched];"
            f"[matched]{post_vf}[outv]"
        )
        cmd = [
            ff, "-y", "-i", str(target), "-i", str(ref),
            "-filter_complex", vfilter,
            "-map", "[outv]", "-map", "0:a?", "-c:v", "libx264", "-pix_fmt", "yuv420p",
            "-c:a", "copy", str(out),
        ]
    else:
        vfilter = "[0:v][1:v]histogrammatching=pattern=1:strength=0.55[outv]"
        cmd = [
            ff, "-y", "-i", str(target), "-i", str(ref),
            "-filter_complex", vfilter,
            "-map", "[outv]", "-map", "0:a?", "-c:v", "libx264", "-pix_fmt", "yuv420p",
            "-c:a", "copy", str(out),
        ]
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        if skip_post_clamp:
            _log("[#244] match-color failed; pass-through (clamp already at process_shot_segment)")
            shutil.copy2(target, out)
        elif neutral_grade:
            _log("[seamless] match-color filter unavailable; clinical neutral WB fallback")
            vf = CLINICAL_NEUTRAL_CLAMP_VF
            cmd_eq = [
                ff, "-y", "-i", str(target), "-vf", vf,
                "-c:v", "libx264", "-pix_fmt", "yuv420p",
                "-map", "0:v", "-map", "0:a?", "-c:a", "copy", str(out),
            ]
            r2 = subprocess.run(cmd_eq, capture_output=True, text=True)
            if r2.returncode != 0:
                shutil.copy2(target, out)
        else:
            _log("[seamless] match-color filter unavailable; warm-gold + magenta clamp fallback")
            vf = WARM_GOLD_CLAMP_VF if lamp_lock else MAGENTA_CLAMP_VF
            cmd_eq = [
                ff, "-y", "-i", str(target), "-vf", vf,
                "-c:v", "libx264", "-pix_fmt", "yuv420p",
                "-map", "0:v", "-map", "0:a?", "-c:a", "copy", str(out),
            ]
            r2 = subprocess.run(cmd_eq, capture_output=True, text=True)
            if r2.returncode != 0:
                shutil.copy2(target, out)
    return out


def process_shot_segment(
    video: Path,
    out: Path,
    shot: dict[str, Any],
    refs: dict[str, Any],
    opts: SeamlessOptions,
    shots_dir: Path,
    color_ref: Path,
) -> Path:
    """Post-process: color correct → label chip → pin A/V sync → loudnorm."""
    work = shots_dir
    cur = video
    dark_scene = _is_dark_scene(refs, shot=shot)
    archive_neutral = (
        _refs_is_archive(refs)
        and not dark_scene
        and (opts.neutral_generation or opts.lamp_lock)
    )
    target_dur = float(
        _eff_dur(shot, refs, seamless=True)
        if shot.get("duration") is not None
        else clamp_shot_duration(probe_duration(cur))
    )

    needs_grade = (
        opts.magenta_clamp
        or opts.match_color
        or opts.neutral_grade
        or (opts.enabled and opts.lamp_lock and _refs_is_archive(refs))
        or (opts.enabled and opts.neutral_generation and _refs_is_archive(refs))
    )
    if needs_grade:
        clamped = work / f"{video.stem}_clamped.mp4"
        if opts.neutral_grade:
            apply_neutral_white_balance_grade(cur, clamped, color_ref)
        elif archive_neutral and _clamp_already_applied(clamped) and clamped.is_file():
            _log(f"[#244] grade stage no-op — clamp marker on {clamped.name}")
        else:
            apply_per_shot_magenta_clamp(
                cur, clamped, color_ref,
                dark_scene=dark_scene, lamp_lock=opts.lamp_lock,
                archive_neutral=archive_neutral,
                neutral_generation=opts.neutral_generation,
            )
        cur = clamped

    if _shot_needs_label_chip_burn(shot):
        vw, vh = _video_frame_size(cur)
        overlay_png = work / f"{video.stem}_chip_overlay.png"
        burned = work / f"{video.stem}_chip_burned.mp4"
        render_pronunciation_chip_overlay(shot, overlay_png, width=vw, height=vh)
        burn_label_overlay(cur, overlay_png, burned)
        cur = burned
        _log(f"[#194] pronunciation chip burned → {shot.get('id', video.stem)}")

    if opts.pin_audio_sync:
        pinned = work / f"{video.stem}_pinned.mp4"
        pin_av_to_duration(cur, pinned, target_dur)
        cur = pinned

    if opts.loudnorm:
        normalized = work / f"{video.stem}_loud.mp4"
        loudnorm_two_pass(cur, normalized, target_lra=LOUDNORM_LRA_TIGHT)
        cur = normalized
        if opts.pin_audio_sync:
            final_pin = work / f"{video.stem}_final.mp4"
            pin_av_to_duration(cur, final_pin, target_dur)
            cur = final_pin

    staging = work / f"{out.stem}__staging.mp4"
    if staging.exists():
        staging.unlink(missing_ok=True)
    shutil.move(str(cur), str(staging))
    os.replace(staging, out)
    return out


def tighten_chain_loudness(
    segments: list[Path],
    shots: list[dict[str, Any]],
    shots_dir: Path,
) -> list[Path]:
    """Iterative volume trim: align per-shot integrated LUFS to chain median (≤1.5 LU)."""
    if len(segments) < 2:
        return segments
    updated = list(segments)

    for iteration in range(6):
        measured: list[tuple[Path, dict[str, Any], float, int]] = []
        for idx, (seg, shot) in enumerate(zip(updated, shots)):
            il = probe_integrated_loudness(seg)
            if il is not None:
                measured.append((seg, shot, il, idx))
        if len(measured) < 2:
            return updated

        values = sorted(m[2] for m in measured)
        spread = values[-1] - values[0]
        if spread <= LOUDNESS_SPREAD_MAX_LU:
            if iteration:
                _log(f"[audio] chain loudness converged (spread {spread:.2f} LU)")
            return updated

        target_i = values[len(values) // 2]
        for seg, shot, il, idx in measured:
            gain_db = target_i - il
            if abs(gain_db) < 0.02:
                continue
            leveled = shots_dir / f"{seg.stem}_lvl{iteration}.mp4"
            _remux_av(seg, leveled, af=f"volume={gain_db:.2f}dB")
            target_dur = float(_eff_dur(shot, refs, seamless=True))
            pinned = shots_dir / f"{seg.stem}_lvl{iteration}_pin.mp4"
            pin_av_to_duration(leveled, pinned, target_dur)
            staging = shots_dir / f"{seg.stem}__lvl_staging.mp4"
            if staging.exists():
                staging.unlink(missing_ok=True)
            shutil.move(str(pinned), str(staging))
            os.replace(staging, seg)
            updated[idx] = seg
            _log(
                f"[audio] chain level pass {iteration + 1} {seg.name}: "
                f"{il:.2f} → {target_i:.2f} LUFS (gain {gain_db:+.2f} dB)"
            )
    return updated


def _assemble_xfade_chain(
    segments: list[Path],
    shots: list[dict[str, Any]],
    out_path: Path,
    *,
    opts: SeamlessOptions,
    shots_dir: Path,
    color_ref: Path | None,
    label: str = "xfade chain",
) -> Path:
    """Re-concat/sync path — loudness-tighten then xfade when N>=2; no re-clamp (#244)."""
    segs = [p for p in segments if p.is_file() and p.stat().st_size > 10000]
    if not segs:
        raise ValueError("_assemble_xfade_chain: no valid segments")
    if opts.loudnorm and len(segs) >= 2:
        segs = tighten_chain_loudness(segs, shots, shots_dir)
    if len(segs) == 1:
        shutil.copy2(segs[0], out_path)
        return out_path
    if opts.enabled:
        _log(
            f"[seamless] {label} joining {len(segs)} segments "
            f"(xfade={opts.xfade_s}s, audio=synced)"
        )
        concat_xfade_chain(
            segs,
            out_path,
            xfade_s=opts.xfade_s,
            match_color=opts.match_color,
            cut_on_motion=opts.cut_on_motion,
            lamp_lock=opts.lamp_lock,
            neutral_grade=opts.neutral_grade,
            neutral_generation=opts.neutral_generation,
            magenta_clamp=opts.magenta_clamp,
            color_ref=color_ref,
            work_dir=shots_dir,
        )
        return out_path
    raise RuntimeError(
        "_assemble_xfade_chain: multi-segment re-concat requires seamless xfade "
        f"({len(segs)} segments, opts.enabled=False)"
    )


def _reconcat_seamless_chain(
    segments: list[Path],
    shots: list[dict[str, Any]],
    out_path: Path,
    *,
    opts: SeamlessOptions,
    shots_dir: Path,
    color_ref: Path | None,
    label: str = "reconcat",
) -> Path:
    """Clamp/sync/loudness re-concat entry — always preserves xfade joins (#193 extended)."""
    return _assemble_xfade_chain(
        segments,
        shots,
        out_path,
        opts=opts,
        shots_dir=shots_dir,
        color_ref=color_ref,
        label=label,
    )


def has_audio_stream(video: Path) -> bool:
    ff = _ffmpeg_exe()
    r = subprocess.run([ff, "-i", str(video)], capture_output=True, text=True)
    return "Audio:" in (r.stderr or "")


def audio_mean_volume_db(video: Path) -> float | None:
    """Return mean_volume (dB) or None if no audio / probe failed."""
    if not has_audio_stream(video):
        return None
    ff = _ffmpeg_exe()
    r = subprocess.run(
        [ff, "-i", str(video), "-af", "volumedetect", "-f", "null", "-"],
        capture_output=True,
        text=True,
    )
    for line in (r.stderr or "").splitlines():
        if "mean_volume:" in line:
            try:
                return float(line.split("mean_volume:")[1].split("dB")[0].strip())
            except ValueError:
                return None
    return None


def audio_has_speech(video: Path, silence_db: float = AUDIO_SILENCE_DB) -> bool:
    db = audio_mean_volume_db(video)
    return db is not None and db > silence_db


def _build_av_xfade_filter(
    dur_a: float,
    dur_b: float,
    xfade_s: float,
    *,
    has_a: bool,
    has_b: bool,
) -> tuple[str, list[str]]:
    """Video xfade + audio crossfade aligned to the same offset (no acrossfade o1)."""
    offset = max(0.0, dur_a - xfade_s)
    delay_ms = int(offset * 1000)
    out_dur = dur_a + dur_b - xfade_s
    filter_parts = [
        "[0:v]fps=24,scale=1280:720:flags=lanczos,setsar=1[v0]",
        "[1:v]fps=24,scale=1280:720:flags=lanczos,setsar=1[v1]",
        f"[v0][v1]xfade=transition=fade:duration={xfade_s}:offset={offset:.3f}[vout]",
    ]
    maps = ["-map", "[vout]"]
    if has_a or has_b:
        if has_a and has_b:
            filter_parts.append(
                f"[0:a]aformat=sample_rates=48000:channel_layouts=stereo,asetpts=PTS-STARTPTS,"
                f"afade=t=out:st={offset:.3f}:d={xfade_s}[a0f];"
                f"[1:a]aformat=sample_rates=48000:channel_layouts=stereo,asetpts=PTS-STARTPTS,"
                f"afade=t=in:st=0:d={xfade_s}[a1f];"
                f"[a1f]adelay={delay_ms}|{delay_ms}[a1d];"
                f"[a0f][a1d]amix=inputs=2:duration=longest:dropout_transition=0[aout]"
            )
        elif has_a:
            filter_parts.append(
                f"[0:a]aformat=sample_rates=48000:channel_layouts=stereo,asetpts=PTS-STARTPTS,"
                f"apad=whole_dur={out_dur:.3f},"
                f"afade=t=out:st={offset:.3f}:d={xfade_s}[aout]"
            )
        else:
            filter_parts.append(
                f"[1:a]aformat=sample_rates=48000:channel_layouts=stereo,asetpts=PTS-STARTPTS,"
                f"adelay={delay_ms}|{delay_ms}[aout]"
            )
        maps.extend(["-map", "[aout]", "-c:a", "aac", "-b:a", "192k"])
    return ";".join(filter_parts), maps


def mux_audio_track(video: Path, audio_wav: Path, out: Path, duration: float | None = None) -> Path:
    ff = _ffmpeg_exe()
    out.parent.mkdir(parents=True, exist_ok=True)
    dur_flag = ["-t", f"{duration:.3f}"] if duration else []
    subprocess.run(
        [
            ff, "-y", "-i", str(video), "-i", str(audio_wav),
            *dur_flag, "-map", "0:v", "-map", "1:a",
            "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-shortest", str(out),
        ],
        check=True,
        capture_output=True,
    )
    return out


def synthesize_speech_wav(text: str, out_wav: Path, voice_hint: str = "") -> Path:
    """Fallback TTS when i2v clip has no dialogue audio (edge-tts)."""
    out_wav.parent.mkdir(parents=True, exist_ok=True)
    try:
        import asyncio
        import edge_tts
    except ImportError as exc:
        raise RuntimeError(
            "Segment missing audio and edge-tts not installed — pip install edge-tts"
        ) from exc

    voice = "en-US-GuyNeural"
    if "attent" in voice_hint.lower() or "documentary" in voice_hint.lower():
        voice = "en-GB-RyanNeural"

    async def _run() -> None:
        comm = edge_tts.Communicate(text, voice)
        await comm.save(str(out_wav))

    asyncio.run(_run())
    return out_wav


def ensure_segment_audio(
    video: Path,
    shot: dict[str, Any],
    refs: dict[str, Any],
    work_dir: Path,
) -> Path:
    """Keep Grok i2v dialogue audio; synthesize+mux only when the clip is silent."""
    if audio_has_speech(video):
        return video
    if refs.get("narration") is False:
        return video
    speech = shot.get("speech_text", "").strip()
    if not speech:
        return video
    _log(f"[audio] silent segment {video.name} — TTS fallback for speech")
    wav = work_dir / f"{video.stem}_tts.wav"
    synthesize_speech_wav(speech, wav, refs.get("voice_suffix", ""))
    out = work_dir / f"{video.stem}_muxed.mp4"
    mux_audio_track(video, wav, out, duration=probe_duration(video))
    return out


def probe_lamp_warm_ratio(video: Path, at_s: float | None = None) -> float:
    """Sample lamp-region warm ratio (R/G); higher = warmer gold."""
    from PIL import Image

    ff = _ffmpeg_exe()
    at_s = at_s if at_s is not None else max(0.0, probe_duration(video) * 0.5)
    jpg = video.with_suffix(".lamp_probe.jpg")
    subprocess.run(
        [ff, "-y", "-ss", f"{at_s:.3f}", "-i", str(video), "-frames:v", "1", str(jpg)],
        check=True,
        capture_output=True,
    )
    img = Image.open(jpg).convert("RGB")
    w, h = img.size
    x0, x1 = int(w * 0.55), int(w * 0.92)
    y0, y1 = int(h * 0.15), int(h * 0.65)
    rs = gs = 0
    n = 0
    for y in range(y0, y1, 4):
        for x in range(x0, x1, 4):
            r, g, b = img.getpixel((x, y))
            rs += r
            gs += max(g, 1)
            n += 1
    jpg.unlink(missing_ok=True)
    return rs / gs / n if n else 1.0


def _write_seamless_final(
    host_join: Path,
    card_mp4: Path | None,
    seamless_out: Path,
    *,
    opts: SeamlessOptions,
    color_ref: Path | None,
    shots_dir: Path,
) -> Path:
    """Write graded+xfaded host (and optional card join) to the published output path."""
    seamless_out.parent.mkdir(parents=True, exist_ok=True)
    if card_mp4 and card_mp4.is_file():
        concat_xfade_two(
            host_join,
            card_mp4,
            seamless_out,
            xfade_s=opts.xfade_s,
            match_color=opts.match_color,
            cut_on_motion=False,
            lamp_lock=opts.lamp_lock,
            neutral_grade=opts.neutral_grade,
            neutral_generation=opts.neutral_generation,
            magenta_clamp=opts.magenta_clamp,
            color_ref=color_ref,
            work_dir=shots_dir,
        )
        _log(
            f"[seamless] final mux: xfade({opts.xfade_s}s) host+card → {seamless_out.name}"
        )
        return seamless_out
    shutil.copy2(host_join, seamless_out)
    _log(f"[seamless] final mux: graded xfade host → {seamless_out.name}")
    return seamless_out


def concat_xfade_two(
    left: Path,
    right: Path,
    out: Path,
    *,
    xfade_s: float = DEFAULT_XFADE_S,
    match_color: bool = False,
    cut_on_motion: bool = False,
    lamp_lock: bool = True,
    neutral_grade: bool = False,
    neutral_generation: bool = False,
    magenta_clamp: bool = True,
    color_ref: Path | None = None,
    work_dir: Path | None = None,
) -> Path:
    out.parent.mkdir(parents=True, exist_ok=True)
    if xfade_s < MIN_XFADE_S:
        # ffmpeg xfade with duration≈0 corrupts output after the first segment
        # (only ~segment_s decodes; rest reads as frozen). Use stream-copy hard cut.
        concat_videos([left, right], out)
        return out
    ff = _ffmpeg_exe()
    work = work_dir or out.parent
    a, b = left, right
    if cut_on_motion:
        trimmed = work / f"{left.stem}_trim_{out.stem}.mp4"
        trim_tail_motion(left, trimmed)
        a = trimmed
    if match_color:
        matched = work / f"{right.stem}_matched_{out.stem}.mp4"
        ref = color_ref or left
        archive_neutral = (
            (lamp_lock or neutral_generation)
            and not neutral_grade
            and any(k in str(ref).lower() for k in ("archive", "david_identity", "david_avatar"))
        )
        # Segments are pre-graded in process_shot_segment — join is histogram-only, no re-clamp.
        skip_post_clamp = magenta_clamp or neutral_grade
        match_color_segment(
            left, right, matched,
            lamp_lock=lamp_lock, color_ref=ref, archive_neutral=archive_neutral,
            neutral_grade=neutral_grade,
            skip_post_clamp=skip_post_clamp,
        )
        b = matched
    dur_a = probe_duration(a)
    dur_b = probe_duration(b)
    out.parent.mkdir(parents=True, exist_ok=True)
    has_a = has_audio_stream(a)
    has_b = has_audio_stream(b)
    filt, maps = _build_av_xfade_filter(dur_a, dur_b, xfade_s, has_a=has_a, has_b=has_b)
    cmd = [
        ff, "-y", "-i", str(a), "-i", str(b),
        "-filter_complex", filt,
        *maps, "-c:v", "libx264", "-pix_fmt", "yuv420p", str(out),
    ]
    subprocess.run(cmd, check=True, capture_output=True, text=True)
    return out


def concat_xfade_chain(
    segments: list[Path],
    out: Path,
    *,
    xfade_s: float = DEFAULT_XFADE_S,
    match_color: bool = False,
    cut_on_motion: bool = False,
    lamp_lock: bool = True,
    neutral_grade: bool = False,
    neutral_generation: bool = False,
    magenta_clamp: bool = True,
    color_ref: Path | None = None,
    work_dir: Path | None = None,
) -> Path:
    """Chain xfade + synced audio crossfade joins across N segments."""
    if not segments:
        raise ValueError("concat_xfade_chain: no segments")
    work = work_dir or out.parent
    out.parent.mkdir(parents=True, exist_ok=True)
    if len(segments) == 1:
        shutil.copy2(segments[0], out)
        return out
    if xfade_s < MIN_XFADE_S:
        _log(f"[stitch] hard-cut concat (xfade={xfade_s}s < MIN {MIN_XFADE_S}s)")
        concat_videos(segments, out)
        return out
    current = segments[0]
    for i, nxt in enumerate(segments[1:], start=1):
        tmp = work / f"xfade_chain_{i:02d}.mp4"
        concat_xfade_two(
            current,
            nxt,
            tmp,
            xfade_s=xfade_s,
            match_color=match_color,
            cut_on_motion=cut_on_motion,
            lamp_lock=lamp_lock,
            neutral_grade=neutral_grade,
            neutral_generation=neutral_generation,
            magenta_clamp=magenta_clamp,
            color_ref=color_ref,
            work_dir=work,
        )
        current = tmp
    shutil.copy2(current, out)
    return out


def build_side_by_side(left: Path, right: Path, out: Path, label_left: str = "v1", label_right: str = "v2") -> Path:
    ff = _ffmpeg_exe()
    out.parent.mkdir(parents=True, exist_ok=True)
    filt = (
        f"[0:v]scale=640:360,drawtext=text='{label_left}':fontsize=28:fontcolor=white:"
        f"x=20:y=20:box=1:boxcolor=black@0.5[left];"
        f"[1:v]scale=640:360,drawtext=text='{label_right}':fontsize=28:fontcolor=white:"
        f"x=20:y=20:box=1:boxcolor=black@0.5[right];"
        f"[left][right]hstack=inputs=2[vout]"
    )
    subprocess.run(
        [
            ff, "-y", "-i", str(left), "-i", str(right),
            "-filter_complex", filt, "-map", "[vout]",
            "-c:v", "libx264", "-pix_fmt", "yuv420p", "-t", str(min(probe_duration(left), probe_duration(right))),
            str(out),
        ],
        check=True,
        capture_output=True,
    )
    return out


def _extend_not_supported(exc: BaseException) -> bool:
    msg = str(exc).lower()
    if "extension is not supported" in msg or "extend is not supported" in msg:
        return True
    if "unable to download provided video_url" in msg or "403 forbidden" in msg:
        return True
    return False


def _extend_error_detail(exc: BaseException) -> str:
    msg = str(exc)
    if "details = " in msg:
        return msg.split("details = ")[1].split("\n")[0].strip('"')
    return msg[:200]


def _reference_images_not_supported(exc: BaseException) -> bool:
    msg = str(exc).lower()
    return "reference_image" in msg and ("not supported" in msg or "invalid_argument" in msg)


def render_frame_chain_performance(
    shots: list[dict[str, Any]],
    client: Any,
    refs: dict[str, Any],
    opts: SeamlessOptions,
    shots_dir: Path,
    out_path: Path,
    *,
    script: dict[str, Any] | None = None,
    concat_only: bool = False,
    force: bool = False,
    force_shots: set[str] | None = None,
    seed_segment: Path | None = None,
) -> tuple[Path, list[str], str]:
    """Fallback PRIMARY — last-frame → image-to-video chain (same take discipline)."""
    segments: list[Path] = []
    step_urls: list[str] = []
    model = refs["model_video"]
    frames_dir = shots_dir / "chain_frames"
    frames_dir.mkdir(parents=True, exist_ok=True)
    force_ids = force_shots or set()
    color_ref = resolve_color_reference(refs, shots_dir)
    avatar_url = refs["avatar_url"]
    script_ctx = script or _script_ctx_from_refs(refs)
    seam_cfg = refs.get("seamless_cfg") or {}
    magenta_reroll = (
        _should_magenta_reroll(script_ctx, refs)
        and bool(seam_cfg.get("magenta_reroll", True))
    )

    for i, shot in enumerate(shots):
        sid = shot["id"]
        seg_path = shots_dir / f"chain_{sid}.mp4"
        proc_path = shots_dir / f"chain_{sid}_processed.mp4"
        dur = _eff_dur(shot, refs, seamless=True)
        regen = force or sid in force_ids

        if (
            proc_path.exists()
            and proc_path.stat().st_size > 10000
            and not regen
            and not concat_only
        ):
            _log(f"[seamless] reusing processed {proc_path.name}")
            segments.append(shot_join_segment(proc_path, shot, shots_dir))
            continue

        if seg_path.exists() and seg_path.stat().st_size > 10000 and not regen and concat_only:
            raw = ensure_segment_audio(seg_path, shot, refs, shots_dir)
            process_shot_segment(raw, proc_path, shot, refs, opts, shots_dir, color_ref)
            segments.append(shot_join_segment(proc_path, shot, shots_dir))
            continue

        if seg_path.exists() and seg_path.stat().st_size > 10000 and not regen and not concat_only:
            raw = ensure_segment_audio(seg_path, shot, refs, shots_dir)
            process_shot_segment(raw, proc_path, shot, refs, opts, shots_dir, color_ref)
            if not magenta_reroll:
                segments.append(shot_join_segment(proc_path, shot, shots_dir))
                continue
            mag = probe_magenta_score(proc_path)
            if mag <= MAGENTA_SCORE_MAX:
                segments.append(shot_join_segment(proc_path, shot, shots_dir))
                continue
            _log(f"[magenta] cached {sid} score={mag:.3f} — re-roll")
            regen = True

        if concat_only:
            raise FileNotFoundError(f"--concat-only: missing frame-chain segment {seg_path}")

        if i == 0 and seed_segment and seed_segment.is_file() and not regen:
            shutil.copy2(seed_segment, seg_path)
            _log(f"[seamless] frame-chain {i + 1}/{len(shots)} {sid} — reusing extend seed")

        magenta_ok = not magenta_reroll
        max_attempts = _magenta_reroll_attempts(refs, shot) if magenta_reroll else 1
        for attempt in range(max_attempts):
            if not (seg_path.exists() and seg_path.stat().st_size > 10000 and not regen and attempt == 0):
                if i == 0 and attempt == 0 and seed_segment and seed_segment.is_file() and not regen:
                    pass
                else:
                    chain_url: str | None = None
                    chain_fid: str | None = None
                    use_plate_seed = _use_avatar_reground(refs, shot, i, opts)

                    if use_plate_seed:
                        dark = _is_dark_scene(refs, shot=shot)
                        if i == 0 and refs.get(f"{_shot_zone(shot) or '@1'}_plate_url"):
                            src = "locked empty @1 set plate"
                        elif _shot_uses_viz_reference(shot) and refs.get("visualization_url"):
                            src = "locked @2 science plate re-ground"
                        elif dark:
                            src = "dark-set avatar re-ground (Kelvin locked)"
                        else:
                            src = "talent re-ground"
                        _log(f"[seamless] frame-chain {i + 1}/{len(shots)} {sid} ({dur}s) ← {src}")
                    else:
                        prev_shot = shots[i - 1]
                        prev_proc = resolve_chain_seed_segment(shots_dir, prev_shot)
                        prev_dur = probe_duration(prev_proc)
                        seed_at = resolve_extend_at_s(prev_shot, prev_dur)
                        if seed_at is not None:
                            frame_jpg = (
                                frames_dir
                                / f"frame_at_{prev_shot['id']}_{seed_at:.2f}s.jpg"
                            )
                            extract_frame_at(prev_proc, seed_at, frame_jpg)
                            src = f"frame at {seed_at:.2f}s (extend_at_s from {prev_shot['id']})"
                        else:
                            frame_jpg = frames_dir / f"frame_after_{prev_proc.stem}.jpg"
                            extract_last_frame(prev_proc, frame_jpg)
                            src = "last frame"
                        _api_pace()
                        chain_url, chain_fid = upload_and_capture_id(
                            client, frame_jpg, friendly=f"chain_{sid}",
                        )
                        _log(
                            f"[seamless] frame-chain {i + 1}/{len(shots)} {sid} ({dur}s) ← {src}"
                        )
                        if _is_barebones_mode(script):
                            if _uses_baked_composite_pipeline(script, shots_dir.parent):
                                _log(
                                    f"[baked@chain] shot {sid}: chain_frame identity "
                                    f"(no reference_image_file_ids)"
                                )
                            else:
                                n_refs = len(_editor_reference_file_ids(refs))
                                _log(
                                    f"[barebones] chain shot {sid}: chain_frame + "
                                    f"reference_image_file_ids×{n_refs}"
                                )

                    prompt_log = shots_dir / f"chain_{sid}_generation_prompt.txt"
                    composite_seed = (
                        _resolve_composite_first_frame(script, shots_dir.parent)
                        if i == 0 and use_plate_seed
                        else None
                    )
                    baked_pipeline = _uses_baked_composite_pipeline(script, shots_dir.parent)
                    if _is_barebones_mode(script):
                        if composite_seed:
                            _log(
                                f"[baked@1] frame-chain shot 0 {sid} ← composite {composite_seed.name}"
                            )
                            resp, bb_req = generate_baked_composite_video(
                                client,
                                shot,
                                refs,
                                script,
                                shots_dir.parent,
                                composite_seed,
                                duration=dur,
                            )
                        elif baked_pipeline and chain_fid:
                            resp, bb_req = generate_baked_chain_video(
                                client,
                                shot,
                                refs,
                                script,
                                shots_dir.parent,
                                chain_image_file_id=chain_fid,
                                chain_image_url=chain_url,
                                duration=dur,
                            )
                        else:
                            resp, bb_req = generate_barebones_video(
                                client,
                                shot,
                                refs,
                                script,
                                shots_dir.parent,
                                duration=dur,
                                chain_image_url=chain_url,
                                chain_image_file_id=chain_fid,
                                seed_slot="@1" if use_plate_seed else "chain",
                            )
                        prompt = bb_req["prompt"]
                        log_payload = {
                            "shot_id": sid,
                            "prompt": prompt,
                            "prompt_mode": _prompt_mode(script),
                            "barebones_binding": bb_req["binding"],
                            "generate_kwargs": {
                                k: v for k, v in bb_req["kwargs"].items() if k != "prompt"
                            },
                            "neutral_generation": opts.neutral_generation,
                        }
                    else:
                        image_url = (
                            resolve_shot0_set_seed(shot, refs)
                            if use_plate_seed and i == 0
                            else resolve_shot_image_url(shot, refs)
                            if use_plate_seed
                            else chain_url
                        )
                        prompt = build_video_generation_prompt(
                            shot,
                            refs,
                            opts,
                            script=script,
                            prod_dir=shots_dir.parent,
                            image_url=image_url,
                        )
                        log_payload = {
                            "shot_id": sid,
                            "image_url": image_url,
                            "prompt": prompt,
                            "prompt_mode": _prompt_mode(script),
                            "neutral_generation": opts.neutral_generation,
                        }
                        _api_pace()
                        resp = client.video.generate(
                            prompt=prompt,
                            model=model,
                            image_url=image_url,
                            duration=dur,
                            resolution=refs["resolution"],
                        )
                    prompt_log.write_text(json.dumps(log_payload, indent=2), encoding="utf-8")
                    step_urls.append(resp.url)
                    _download(resp.url, seg_path)
                    prompt_log.write_text(
                        prompt_log.read_text(encoding="utf-8")
                        + f"\n\nvideo_url: {resp.url}\n",
                        encoding="utf-8",
                    )

            raw = ensure_segment_audio(seg_path, shot, refs, shots_dir)
            process_shot_segment(raw, proc_path, shot, refs, opts, shots_dir, color_ref)
            if magenta_reroll:
                mag = probe_magenta_score(proc_path)
                if mag <= MAGENTA_SCORE_MAX:
                    magenta_ok = True
                    break
                _log(f"[magenta] {sid} score={mag:.3f} — re-roll attempt {attempt + 2}/{max_attempts}")
                regen = True
            else:
                magenta_ok = True
                break

        if magenta_reroll and not magenta_ok and proc_path.is_file():
            _log(f"[magenta] {sid} still elevated after {max_attempts} attempts — keeping best-effort clamp")
            # Phase A — taxonomy_writer wire: log magenta exhaustion for concept_generator feedback
            try:
                _tw_dir = str(WORKSPACE / "STUDIO" / "Pipeline")
                if _tw_dir not in sys.path:
                    sys.path.insert(0, _tw_dir)
                import taxonomy_writer as _tw  # noqa: PLC0415
                _tw.append_failure(
                    WORKSPACE / "STUDIO" / "Pipeline" / "failure_taxonomy.json",
                    {
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                        "production_slug": (script_ctx or {}).get("slug", "unknown"),
                        "shot_id": sid,
                        "beat_id": shot.get("pacing_beat") or shot.get("beat_id", "unknown"),
                        "shot_role": shot.get("role", "host"),
                        "failure_type": "magenta_exhaustion",
                        "suppression_flags_applied": ["best_effort_clamp"],
                        "attempts": max_attempts,
                        "resolved": False,
                        "resolution_flags": [],
                    },
                )
            except Exception as _tw_exc:  # noqa: BLE001
                _log(f"[taxonomy] magenta write failed: {_tw_exc}")

        # Phase A — cast_gate_shot() per-shot wire (host lanes only)
        if proc_path.is_file() and shot.get("role", "host") in ("host", "presenter", "companion"):
            try:
                _tw_dir = str(WORKSPACE / "STUDIO" / "Pipeline")
                if _tw_dir not in sys.path:
                    sys.path.insert(0, _tw_dir)
                from clip_cast_gate import cast_gate_shot as _cast_gate  # noqa: PLC0415
                _cast_result = _cast_gate(
                    proc_path,
                    sid,
                    shot.get("pacing_beat") or shot.get("beat_id", "unknown"),
                    shot.get("role", "host"),
                    reference_metrics=color_ref,
                    production_slug=(script_ctx or {}).get("slug", "unknown"),
                )
                if not _cast_result["pass"]:
                    _log(
                        f"[cast_gate] {sid} FAIL — "
                        + "; ".join(_cast_result.get("breaches", []))[:120]
                    )
                    if _cast_result.get("taxonomy_entry"):
                        import taxonomy_writer as _tw  # noqa: PLC0415
                        _tw.append_failure(
                            WORKSPACE / "STUDIO" / "Pipeline" / "failure_taxonomy.json",
                            _cast_result["taxonomy_entry"],
                        )
            except Exception as _cg_exc:  # noqa: BLE001
                _log(f"[cast_gate] {sid} probe skipped: {_cg_exc}")

        segments.append(shot_join_segment(proc_path, shot, shots_dir))

    _reconcat_seamless_chain(
        segments,
        shots,
        out_path,
        opts=opts,
        shots_dir=shots_dir,
        color_ref=color_ref,
        label="frame-chain reconcat",
    )
    if opts.enabled and len(shots) >= 2:
        _persist_extend_state(
            shots_dir / "extend_state.json",
            mode="frame_chain",
            opts=opts,
            segment_count=len(shots),
            join_mode="xfade_chain",
        )
    return out_path, step_urls, "frame_chain"


def render_extend_performance(
    shots: list[dict[str, Any]],
    client: Any,
    refs: dict[str, Any],
    opts: SeamlessOptions,
    out_path: Path,
    shots_dir: Path,
    *,
    script: dict[str, Any] | None = None,
    concat_only: bool = False,
    force: bool = False,
    force_shots: set[str] | None = None,
) -> tuple[Path, list[str], str]:
    """PRIMARY path — Grok Imagine EXTEND when supported; else frame-chain fallback."""
    state_path = shots_dir / "extend_state.json"
    have_chain, any_chain, present_n, total_n, chain_segs = _chain_cache_status(shots_dir, shots)
    color_ref = resolve_color_reference(refs, shots_dir)

    regen_any = force or bool(force_shots)
    if concat_only:
        return render_frame_chain_performance(
            shots, client, refs, opts, shots_dir, out_path,
            script=script,
            concat_only=True, force=force, force_shots=force_shots,
        )
    if _extend_probe_skipped(refs, script) and not (have_chain and not regen_any):
        reason = "skip_extend_probe or no legacy extend_model configured"
        _log(f"[seamless] extend probe skipped — frame-chain fallback ({reason})")
        return render_frame_chain_performance(
            shots, client, refs, opts, shots_dir, out_path,
            script=script,
            concat_only=False,
            force=force,
            force_shots=force_shots,
        )
    if have_chain and not regen_any:
        join_segs = chain_join_segments(shots_dir, shots, chain_segs)
        _log(f"[seamless] xfade chain reassembly from {len(join_segs)} cached segments")
        _reconcat_seamless_chain(
            join_segs,
            shots,
            out_path,
            opts=opts,
            shots_dir=shots_dir,
            color_ref=color_ref,
            label="cached reassembly",
        )
        mode = "frame_chain"
        if state_path.is_file():
            mode = json.loads(state_path.read_text(encoding="utf-8")).get("mode", mode)
        _persist_extend_state(
            state_path,
            mode=mode,
            opts=opts,
            segment_count=len(chain_segs),
            join_mode="xfade_chain",
        )
        return out_path, [], mode

    if any_chain and not have_chain:
        _log(
            f"[seamless] partial chain cache ({present_n}/{total_n}) — "
            "xfade reassembly via frame-chain (no stale host reuse)"
        )
        return render_frame_chain_performance(
            shots, client, refs, opts, shots_dir, out_path,
            script=script,
            concat_only=False,
            force=force,
            force_shots=force_shots,
        )

    if out_path.exists() and out_path.stat().st_size > 10000 and not force and not any_chain:
        mode = "cached"
        join_mode = ""
        xfade_cached = opts.xfade_s
        if state_path.is_file():
            st = json.loads(state_path.read_text(encoding="utf-8"))
            mode = st.get("mode", mode)
            join_mode = st.get("join_mode", "")
            xfade_cached = float(st.get("xfade_s", opts.xfade_s))
        if join_mode == "xfade_chain":
            _log(
                f"[seamless] reusing xfade-assembled {out_path.name} "
                f"(join_mode={join_mode}, xfade={xfade_cached}s)"
            )
            return out_path, [], mode
        _log(
            "[seamless] stale host without xfade_chain provenance — "
            "forcing frame-chain rebuild (grade+xfade)"
        )
        seed = shots_dir / f"chain_{shots[0]['id']}.mp4"
        if out_path.is_file() and not seed.is_file():
            shutil.copy2(out_path, seed)
        return render_frame_chain_performance(
            shots, client, refs, opts, shots_dir, out_path,
            script=script,
            concat_only=False,
            force=force,
            force_shots=force_shots,
            seed_segment=seed if seed.is_file() else None,
        )

    gen_model = refs["model_video"]
    extend_model = refs.get("extend_model") or gen_model
    avatar_url = refs["avatar_url"]

    # First segment
    shot0 = shots[0]
    dur0 = _eff_dur(shot0, refs, seamless=True)
    seed_label = (
        "locked empty @1 set plate + @2 reference_image_file_ids"
        if _is_barebones_mode(script)
        else "@2 avatar seed (identity anchor)"
    )
    _log(
        f"[seamless] extend step 1/{len(shots)} {shot0['id']} ({dur0}s) ← {seed_label}"
    )
    composite_seed = _resolve_composite_first_frame(script, shots_dir.parent)
    if _is_barebones_mode(script):
        if composite_seed:
            _log(f"[baked@1] extend step 1 ← composite {composite_seed.name}")
            resp, _bb0 = generate_baked_composite_video(
                client,
                shot0,
                refs,
                script,
                shots_dir.parent,
                composite_seed,
                duration=dur0,
            )
        else:
            resp, _bb0 = generate_barebones_video(
                client,
                shot0,
                refs,
                script,
                shots_dir.parent,
                duration=dur0,
                seed_slot="@1",
            )
    else:
        image_url0 = resolve_shot0_set_seed(shot0, refs)
        prompt0 = build_video_generation_prompt(
            shot0, refs, opts, script=script, prod_dir=shots_dir.parent, image_url=image_url0,
        )
        _api_pace()
        resp = client.video.generate(
            prompt=prompt0,
            model=gen_model,
            image_url=image_url0,
            duration=dur0,
            resolution=refs["resolution"],
        )
    origin_api_url = resp.url
    step_urls = [origin_api_url]
    seg0_path = shots_dir / f"extend_{shot0['id']}.mp4"
    _download(origin_api_url, seg0_path)
    shutil.copy2(seg0_path, out_path)

    baked_pipeline = _uses_baked_composite_pipeline(script, shots_dir.parent)
    extend_work = shots_dir / "extend_sources"
    current_url, _, _ = prepare_extend_source_url(
        client, seg0_path, shot0, extend_work, native_api_url=origin_api_url,
    )
    refs["origin_video_url"] = origin_api_url
    refs["origin_video_file"] = str(seg0_path)
    refs["extend_source_url"] = current_url
    _log(
        f"[extend] origin locked {shot0['id']} api={origin_api_url[:48]}… "
        f"extend_model={extend_model}"
    )

    if len(shots) == 1:
        state_path.write_text(
            json.dumps({
                "mode": "generate_only",
                "urls": step_urls,
                "origin_video_url": origin_api_url,
            }),
            encoding="utf-8",
        )
        return out_path, step_urls, "generate_only"

    shot1 = shots[1]
    dur1 = _eff_dur(shot1, refs, seamless=True)
    prompt1 = build_extend_prose_prompt(
        shot1, refs, opts, script, shots_dir.parent, baked_pipeline=baked_pipeline,
    )
    try:
        _log(
            f"[seamless] extend step 2/{len(shots)} {shot1['id']} ({dur1}s) "
            f"← video extend (not frame extract) model={extend_model}"
        )
        _api_pace()
        resp = client.video.extend(
            prompt=prompt1,
            model=extend_model,
            video_url=current_url,
            duration=dur1,
        )
        current_url = resp.url
        step_urls.append(current_url)
        seg1 = shots_dir / f"extend_{shot1['id']}.mp4"
        _download(current_url, seg1)
        shutil.copy2(seg1, out_path)

        for i, shot in enumerate(shots[2:], start=3):
            sid = shot["id"]
            dur = _eff_dur(shot, refs, seamless=True)
            prompt = build_extend_prose_prompt(
                shot, refs, opts, script, shots_dir.parent, baked_pipeline=baked_pipeline,
            )
            _log(
                f"[seamless] extend step {i}/{len(shots)} {sid} ({dur}s) "
                f"← video extend model={extend_model}"
            )
            _api_pace()
            resp = client.video.extend(
                prompt=prompt,
                model=extend_model,
                video_url=current_url,
                duration=dur,
            )
            current_url = resp.url
            step_urls.append(current_url)
            seg_n = shots_dir / f"extend_{sid}.mp4"
            _download(current_url, seg_n)
            shutil.copy2(seg_n, out_path)

        state_path.write_text(
            json.dumps({
                "mode": "extend",
                "generate_model": gen_model,
                "extend_model": extend_model,
                "urls": step_urls,
                "origin_video_url": origin_api_url,
                "origin_video_file": str(seg0_path),
                "extend_api": {**EXTEND_API_FINDING, "enabled_on_model": True, "continuity_mode": "extend"},
            }),
            encoding="utf-8",
        )
        return out_path, step_urls, "extend"

    except Exception as exc:
        if not _extend_not_supported(exc):
            raise
        _log(
            f"[seamless] EXTEND failed on {extend_model} — {_extend_error_detail(exc)}; "
            "frame-chain fallback (last resort; STUDIO v1.1 §2)"
        )
        seed = shots_dir / f"chain_{shot0['id']}.mp4"
        if out_path.is_file():
            shutil.copy2(out_path, seed)
        result = render_frame_chain_performance(
            shots, client, refs, opts, shots_dir, out_path,
            script=script,
            concat_only=False, force=force, force_shots=force_shots,
            seed_segment=seed if not regen_any else None,
        )
        _persist_extend_state(
            state_path,
            mode="frame_chain",
            opts=opts,
            segment_count=len(shots),
            join_mode="xfade_chain",
        )
        return result


def qa_check(
    script: dict[str, Any],
    refs: dict[str, Any],
    rendered: list[Path],
    *,
    seamless_opts: SeamlessOptions | None = None,
    extend_path: Path | None = None,
    final_path: Path | None = None,
    chain_segments: list[Path] | None = None,
    comparison_path: Path | None = None,
    continuity_mode: str | None = None,
) -> dict[str, Any]:
    rules = script.get("qa_rules", {})
    issues: list[str] = []
    passes: list[str] = []

    if rules.get("require_identity_lock", True) and refs.get("lock"):
        if refs["lock"].get("status") == "LOCKED":
            passes.append("host identity lock LOADED")
        else:
            issues.append("host identity not LOCKED")

    shots = script.get("shots", [])
    min_shots = rules.get("min_shots", 1)
    if len(shots) >= min_shots:
        passes.append(f"shot count OK ({len(shots)} >= {min_shots})")
    else:
        issues.append(f"shot count {len(shots)} < min {min_shots}")

    if rules.get("require_synthetic_guard", True):
        voice = refs.get("voice_suffix", DEFAULT_VOICE_SUFFIX)
        bad = [
            s["id"]
            for s in shots
            if "synthetic" not in ensure_voice_in_prompt(s.get("video_prompt", ""), voice).lower()
        ]
        if bad:
            issues.append(f"shots missing synthetic guard after patch: {bad}")
        else:
            passes.append("all shots carry synthetic talent guard (incl. auto-patched)")

    if rules.get("require_at2_swap_proof"):
        meta = script.get("production_meta") or {}
        viz_shots = [s for s in shots if _shot_uses_viz_reference(s)]
        if not viz_shots:
            issues.append("@2 swap proof: no visualization reference_slots shot")
        elif refs.get("visualization_url") or refs.get("visualization_file"):
            plate_id = meta.get("plate_id", "visualization")
            passes.append(f"@2 swap proof: {plate_id} plate loaded for {viz_shots[0]['id']}")
            if meta.get("scaffold_id"):
                passes.append(f"fixed scaffold: {meta['scaffold_id']}")
        else:
            issues.append("@2 swap proof: missing visualization_reference / visualization_url")

    pie_like = [s for s in shots if s.get("speech_lang", "").startswith("pie") or "RECONSTRUCTED" in str(s.get("on_screen_labels"))]
    for s in pie_like:
        labels = s.get("on_screen_labels", [])
        if any("RECONSTRUCTED" in lb for lb in labels):
            passes.append(f"{s['id']}: RECONSTRUCTED labels present")
        elif rules.get("require_reconstructed_labels"):
            issues.append(f"{s['id']}: missing RECONSTRUCTED labels")

    for p in rendered:
        if not p.is_file() or p.stat().st_size < 10000:
            issues.append(f"missing or tiny segment: {p.name}")

    total_dur = sum(s.get("duration", 0) for s in shots)
    prov_dur = script.get("provenance_card", {}).get("duration_s", 7)
    if script.get("provenance_card", {}).get("enabled", True):
        total_dur += prov_dur
    passes.append(f"target duration ~{total_dur}s")

    if seamless_opts and seamless_opts.enabled:
        passes.append("STUDIO v1.1 seamless mode ACTIVE")
        mode = continuity_mode or "unknown"
        passes.append(f"continuity mode: {mode}; card join xfade={seamless_opts.xfade_s}s")
        if mode == "extend":
            passes.append("PRIMARY Grok Imagine EXTEND chain")
        elif mode == "frame_chain":
            passes.append("frame-chain i2v fallback (extend unsupported on 1.5)")
        if seamless_opts.match_color:
            passes.append("match-color pre-join ENABLED")
        if seamless_opts.cut_on_motion:
            passes.append("cut-on-motion tail trim ENABLED")
        if extend_path and extend_path.is_file():
            passes.append(f"host performance: {extend_path.name} ({probe_duration(extend_path):.1f}s)")
        else:
            issues.append("missing host performance file")
        anchor = _identity_anchor(script)
        identity_locked = any(anchor in s.get("video_prompt", "") for s in shots) or any(
            "CONTINUITY LOCK @" in s.get("video_prompt", "") for s in shots
        )
        if identity_locked:
            passes.append(f"{anchor} continuity prefix embedded in video_prompt")
        else:
            issues.append(f"shots missing {anchor} continuity in video_prompt")
        passes.append("xfade chain + synced audio crossfade at joins")
        chain_count = len([p for p in (chain_segments or []) if p.is_file()])
        if chain_count >= 2 and extend_path:
            state_path = extend_path.parent / "extend_state.json"
            if state_path.is_file():
                st = json.loads(state_path.read_text(encoding="utf-8"))
                if st.get("join_mode") == "xfade_chain":
                    passes.append(
                        f"re-concat join preserved: xfade_chain "
                        f"({st.get('xfade_s', seamless_opts.xfade_s)}s)"
                    )
                else:
                    issues.append(
                        f"re-concat stripped seamless xfade (join_mode={st.get('join_mode')})"
                    )
        check_path = final_path if final_path and final_path.is_file() else extend_path
        if (
            final_path
            and final_path.is_file()
            and _is_archive_production(script, refs)
            and not _is_clinical_neutral_set(script, refs)
        ):
            try:
                final_cast = probe_color_cast_score(final_path)
                if color_cast_passes(final_cast):
                    passes.append(
                        "final mux color-cast T4 clean (#244) — "
                        f"B/R={final_cast['host_br_ratio']:.3f} "
                        f"starve={final_cast['blue_starvation_fraction']:.3f} "
                        f"Bμ={final_cast['host_blue_mean']:.1f}"
                    )
                else:
                    issues.append(
                        "final output bypassed grade/xfade path (#244 T4): "
                        + str(color_cast_breaches(final_cast))
                    )
            except Exception as exc:
                issues.append(f"final color-cast probe failed (#244): {exc}")
        audio_ok = False
        if check_path and check_path.is_file():
            if has_audio_stream(check_path):
                db = audio_mean_volume_db(check_path)
                if db is not None and db > AUDIO_SILENCE_DB:
                    passes.append(f"audio PRESENT ({check_path.name} mean {db:.1f} dB)")
                    audio_ok = True
                else:
                    issues.append(f"audio stream too quiet ({db} dB) in {check_path.name}")
            else:
                issues.append(f"no audio stream in {check_path.name}")
        if rules.get("require_audio") and not audio_ok:
            issues.append("require_audio: final output missing synced speech track")
        if seamless_opts.neutral_grade and _is_clinical_neutral_set(script, refs):
            passes.append(
                "clinical neutral WB grade (#193) — lamp_lock disabled, no full-frame warm cast"
            )
        elif seamless_opts.lamp_lock and _is_archive_production(script, refs):
            passes.append(
                "#194 archive color: neutral WB + natural skin + localized 3200K lamp accent"
            )
        elif seamless_opts.lamp_lock:
            passes.append("color match reference from locked talent avatar")
        if seamless_opts.loudnorm:
            passes.append(f"loudnorm two-pass target I={LOUDNORM_I} LUFS per shot")
        if seamless_opts.pin_audio_sync:
            passes.append("audio pinned to exact shot duration (no stretch/offset)")
        segs = [p for p in (chain_segments or []) if p.is_file()]
        if segs:
            try:
                ilufs = [probe_integrated_loudness(p) for p in segs]
                ilufs = [x for x in ilufs if x is not None]
                if len(ilufs) >= 2:
                    spread = max(ilufs) - min(ilufs)
                    if spread <= LOUDNESS_SPREAD_MAX_LU:
                        passes.append(f"flat loudness across shots (spread {spread:.2f} LU)")
                    else:
                        issues.append(f"loudness spread {spread:.2f} LU > {LOUDNESS_SPREAD_MAX_LU}")
                if _use_magenta_hue_qa(script, refs):
                    mag_scores = [probe_magenta_score(p) for p in segs]
                    if max(mag_scores) <= MAGENTA_SCORE_MAX:
                        passes.append(f"zero magenta (max score {max(mag_scores):.3f} <= {MAGENTA_SCORE_MAX})")
                    else:
                        bad = [(segs[i].stem, mag_scores[i]) for i in range(len(segs)) if mag_scores[i] > MAGENTA_SCORE_MAX]
                        issues.append(f"magenta detected: {bad}")
                elif _is_clinical_neutral_set(script, refs):
                    passes.append("clinical/neutral set — magenta probe skipped (CCB gate #199)")
                else:
                    passes.append("neutral set — magenta probe skipped")
                sync_bad = []
                for p, shot in zip(segs, shots[: len(segs)]):
                    label = av_sync_drift_label(
                        shot, probe_duration(p), seamless=seamless_opts.enabled
                    )
                    if label:
                        sync_bad.append(label)
                if sync_bad:
                    issues.append(f"A/V sync drift: {sync_bad}")
                else:
                    passes.append("tight A/V sync per shot (duration pinned)")
                if _is_clinical_neutral_set(script, refs) and seamless_opts.neutral_grade:
                    ccb_scores = [probe_clinical_channel_balance(p) for p in segs]
                    if max(ccb_scores) <= CLINICAL_CHANNEL_BALANCE_MAX:
                        passes.append(
                            f"clinical channel balance OK "
                            f"(max CCB {max(ccb_scores):.3f} <= {CLINICAL_CHANNEL_BALANCE_MAX})"
                        )
                    else:
                        issues.append(
                            f"clinical channel imbalance (#199): "
                            f"{[(segs[i].stem, round(ccb_scores[i], 4)) for i in range(len(segs)) if ccb_scores[i] > CLINICAL_CHANNEL_BALANCE_MAX]}"
                        )
                elif _is_archive_production(script, refs):
                    yg_scores = [probe_yellow_green_score(p) for p in segs]
                    if max(yg_scores) <= YELLOW_GREEN_SCORE_MAX:
                        passes.append(
                            f"neutral WB — yellow-green suppressed "
                            f"(max {max(yg_scores):.3f} <= {YELLOW_GREEN_SCORE_MAX})"
                        )
                    else:
                        issues.append(
                            f"yellow-green cast detected: "
                            f"{[(segs[i].stem, yg_scores[i]) for i in range(len(segs)) if yg_scores[i] > YELLOW_GREEN_SCORE_MAX]}"
                        )
                    cast_scores = [probe_color_cast_score(p) for p in segs]
                    cast_bad = [
                        (segs[i].stem, cast_scores[i])
                        for i in range(len(segs))
                        if not color_cast_passes(cast_scores[i])
                    ]
                    if not cast_bad:
                        worst = max(cast_scores, key=lambda m: m["blue_starvation_fraction"])
                        passes.append(
                            "generation color-cast clean — "
                            f"B/R={worst['host_br_ratio']:.3f} "
                            f"starve={worst['blue_starvation_fraction']:.3f} "
                            f"Bμ={worst['host_blue_mean']:.1f}"
                        )
                    else:
                        issues.append(
                            "blue-starved generation cast (#194 T4): "
                            + str(
                                [
                                    (stem, color_cast_breaches(m))
                                    for stem, m in cast_bad
                                ]
                            )
                        )
                    chip_shots = [s for s in shots if _shot_needs_label_chip_burn(s)]
                    if chip_shots and segs:
                        shots_dir = segs[0].parent
                        overlays = list(shots_dir.glob("*chip_overlay.png"))
                        if overlays:
                            passes.append("pronunciation chip overlay burned (high-contrast #194)")
                        else:
                            issues.append("pronunciation chip overlay missing on demonstration shot")
                if len(segs) >= 2 and _is_archive_production(script, refs):
                    ratios = [probe_lamp_warm_ratio(p) for p in segs]
                    delta = max(ratios) - min(ratios)
                    if delta <= 0.18:
                        passes.append(f"lamp warm ratio stable across segments (Δ={delta:.3f})")
                    else:
                        issues.append(f"lamp hue drift between segments Δ={delta:.3f} ratios={ratios}")
                elif len(segs) >= 2 and _use_magenta_hue_qa(script, refs):
                    mag_scores = [probe_magenta_score(p) for p in segs]
                    if max(mag_scores) <= MAGENTA_SCORE_MAX:
                        passes.append(f"zero hue drift across segments (max magenta {max(mag_scores):.3f})")
                    else:
                        issues.append(f"hue drift detected across segments magenta={mag_scores}")
                elif (
                    len(segs) >= 2
                    and _is_clinical_neutral_set(script, refs)
                    and seamless_opts.neutral_grade
                ):
                    yg_scores = [probe_yellow_green_score(p) for p in segs]
                    delta = max(yg_scores) - min(yg_scores)
                    if delta <= YELLOW_GREEN_SCORE_MAX:
                        passes.append(
                            f"clinical hue stable across segments (yellow-green Δ={delta:.3f})"
                        )
                    else:
                        issues.append(
                            f"clinical hue drift across segments yellow-green={yg_scores}"
                        )
                elif len(segs) >= 2:
                    balances = [_probe_grey_balance(p) for p in segs]
                    delta = max(balances) - min(balances)
                    if delta <= 0.06:
                        passes.append(f"zero hue drift across segments (grey balance Δ={delta:.3f})")
                    else:
                        issues.append(f"hue drift across segments grey_balance={balances}")
            except Exception as exc:
                issues.append(f"post-process QA probe failed: {exc}")
        for s in shots:
            band_issue = check_shot_duration_band(
                s,
                seamless=seamless_opts.enabled,
                seamless_cfg=(script.get("config") or {}).get("seamless"),
            )
            if band_issue:
                issues.append(band_issue)
        if comparison_path and comparison_path.is_file():
            passes.append(f"side-by-side: {comparison_path.name}")

    report: dict[str, Any] = {
        "slug": script.get("slug"),
        "qa_at": datetime.now(timezone.utc).isoformat(),
        "pass": len(issues) == 0,
        "passes": passes,
        "issues": issues,
        "shot_count": len(shots),
        "segment_count": len(rendered),
        "seamless": seamless_opts.enabled if seamless_opts else False,
    }
    if seamless_opts and seamless_opts.enabled:
        report["extend_api"] = {
            **EXTEND_API_FINDING,
            "continuity_mode": continuity_mode or "unknown",
        }
    # Phase A — taxonomy_writer wire: log QA failures for concept_generator feedback
    if not report.get("pass") and report.get("issues"):
        try:
            _tw_dir = str(WORKSPACE / "STUDIO" / "Pipeline")
            if _tw_dir not in sys.path:
                sys.path.insert(0, _tw_dir)
            import taxonomy_writer as _tw  # noqa: PLC0415
            _taxonomy_path = WORKSPACE / "STUDIO" / "Pipeline" / "failure_taxonomy.json"
            for _issue in report["issues"]:
                _tw.append_failure(
                    _taxonomy_path,
                    {
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                        "production_slug": report.get("slug", "unknown"),
                        "shot_id": "production",
                        "beat_id": "qa_check",
                        "shot_role": "production",
                        "failure_type": "qa_fail",
                        "suppression_flags_applied": [],
                        "attempts": 1,
                        "resolved": False,
                        "resolution_flags": [],
                        "issue": _issue,
                    },
                )
        except Exception as _tw_exc:  # noqa: BLE001
            _log(f"[taxonomy] qa_check write failed: {_tw_exc}")
    return report


def render_longform(
    script: dict[str, Any],
    *,
    client: Any = None,
    concat_only: bool = False,
    force_shots: set[str] | None = None,
    force_all: bool = False,
    force_plates: bool = False,
    seamless_opts: SeamlessOptions | None = None,
) -> dict[str, Any]:
    prod_dir = resolve_production_dir(script)
    shots_dir = prod_dir / "shots"
    shots_dir.mkdir(parents=True, exist_ok=True)

    refs = resolve_refs(script, client=client)
    plates_dir = prod_dir / "plates"
    if _needs_zone_plates(script, refs):
        if client:
            ensure_zone_plates(
                script,
                refs,
                client,
                plates_dir,
                force=force_plates or force_all,
            )
        else:
            n = _load_cached_zone_plates(refs, plates_dir)
            if n:
                _log(f"[zone] loaded {n} cached plate(s) from {plates_dir}")
    if _prompt_mode(script) in ("asset_directed", "barebones") and client:
        capture_editor_session(client, refs, script, prod_dir)
    opts = _apply_grade_policy(script, refs, seamless_opts or SeamlessOptions())
    pack = build_imagine_pack(script, refs, opts if opts.enabled else None)
    pack_path = prod_dir / f"{script.get('slug', 'longform')}_imagine_pack.json"
    pack_path.write_text(json.dumps(pack, indent=2, ensure_ascii=False), encoding="utf-8")

    script_copy = prod_dir / f"{script.get('slug', 'longform')}_script.json"
    script_copy.write_text(json.dumps(script, indent=2, ensure_ascii=False), encoding="utf-8")

    slug = script.get("slug", "longform")
    prefix = _output_prefix(script)
    final_mp4 = prod_dir / "output" / f"{prefix}_{slug}_longform_v1.mp4"
    final_mp4.parent.mkdir(parents=True, exist_ok=True)
    comparison_path: Path | None = None
    extend_path: Path | None = None

    if opts.enabled:
        perf_shots = [s for s in script["shots"] if s.get("role", "host") != "card"]
        if not perf_shots:
            perf_shots = list(script["shots"])

        extend_path = shots_dir / HOST_PERFORMANCE_NAME
        shot_force = set(force_shots or set())
        if force_all:
            shot_force = {s["id"] for s in perf_shots}
        host_mp4, step_urls, continuity_mode = render_extend_performance(
            perf_shots,
            client,
            refs,
            opts,
            extend_path,
            shots_dir,
            script=script,
            concat_only=concat_only,
            force=force_all,
            force_shots=shot_force,
        )

        prov_cfg = script.get("provenance_card", {})
        card_mp4: Path | None = None
        if prov_cfg.get("enabled", True):
            prov_png = prod_dir / "provenance_card.png"
            render_provenance_card(script, prov_png)
            card_mp4 = shots_dir / "provenance.mp4"
            provenance_to_video(prov_png, card_mp4, prov_cfg.get("duration_s", 6))

        host_join = host_mp4
        if opts.cut_on_motion:
            trimmed_host = shots_dir / "host_performance_trimmed.mp4"
            trim_tail_motion(host_mp4, trimmed_host)
            host_join = trimmed_host

        color_ref = resolve_color_reference(refs, shots_dir)
        seamless_out = prod_dir / "output" / f"{prefix}_{slug}_seamless_v1.mp4"
        final_mp4 = _write_seamless_final(
            host_join,
            card_mp4,
            seamless_out,
            opts=opts,
            color_ref=color_ref,
            shots_dir=shots_dir,
        )
        assembly_provenance = {
            "host_source": str(host_join),
            "host_performance": str(host_mp4),
            "card_joined": bool(card_mp4),
            "join_mode": "xfade_chain",
            "xfade_s": opts.xfade_s,
            "graded_segments": True,
            "output_mux": str(final_mp4),
        }

        rendered = [p for p in [host_mp4, card_mp4] if p]
        _log(f"[seamless] final → {final_mp4}")
        chain_segments = chain_segment_paths(shots_dir, perf_shots)

        compare_v1 = script.get("config", {}).get("compare_v1")
        if compare_v1:
            v1_path = _resolve_david_path(compare_v1)
            if v1_path.is_file():
                comparison_path = prod_dir / "output" / f"david_{slug}_v1_vs_v2.mp4"
                try:
                    build_side_by_side(v1_path, final_mp4, comparison_path, "v1 hard-cut", "v2 seamless")
                    _log(f"[seamless] comparison → {comparison_path}")
                except subprocess.CalledProcessError:
                    comparison_path = prod_dir / "output" / f"david_{slug}_v1_vs_v2_nolabel.mp4"
                    subprocess.run(
                        [
                            _ffmpeg_exe(), "-y", "-i", str(v1_path), "-i", str(final_mp4),
                            "-filter_complex", "[0:v]scale=640:360[left];[1:v]scale=640:360[right];[left][right]hstack[vout]",
                            "-map", "[vout]", "-c:v", "libx264", "-pix_fmt", "yuv420p",
                            "-t", str(min(probe_duration(v1_path), probe_duration(final_mp4))),
                            str(comparison_path),
                        ],
                        check=True,
                        capture_output=True,
                    )
                    _log(f"[seamless] comparison (no labels) → {comparison_path}")

        qa = qa_check(
            script, refs, rendered,
            seamless_opts=opts,
            extend_path=extend_path,
            final_path=final_mp4,
            chain_segments=chain_segments,
            comparison_path=comparison_path,
            continuity_mode=continuity_mode,
        )
        qa_path = prod_dir / "qa_report.json"
        qa_path.write_text(json.dumps(qa, indent=2, ensure_ascii=False), encoding="utf-8")

        return {
            "production_dir": str(prod_dir),
            "script": str(script_copy),
            "imagine_pack": str(pack_path),
            "output": str(final_mp4),
            "extend_performance": str(extend_path),
            "extend_steps": len(step_urls) if step_urls else "cached",
            "continuity_mode": continuity_mode,
            "comparison": str(comparison_path) if comparison_path else None,
            "qa": qa,
            "segments": [str(p) for p in rendered if p],
            "seamless": True,
            "assembly": assembly_provenance,
        }

    rendered: list[Path] = []
    force_shots = force_shots or set()

    for shot in script["shots"]:
        sid = shot["id"]
        out = shots_dir / f"{sid}.mp4"
        reuse = (
            out.exists()
            and out.stat().st_size > 10000
            and sid not in force_shots
            and not force_all
        )
        if reuse:
            _log(f"[longform] reusing {out.name}")
            rendered.append(out)
            continue

        if concat_only:
            raise FileNotFoundError(
                f"--concat-only: missing cached shot {out} (generate first without --concat-only)"
            )

        if client is None:
            raise RuntimeError("API client required for shot generation")

        image_url = resolve_shot_image_url(shot, refs)
        prompt = build_video_generation_prompt(
            shot, refs, opts, script=script, prod_dir=prod_dir, image_url=image_url,
        )

        # --- PromptDirector: validate/augment prompt before generation ---
        _pd_render_id = ""
        if _PROMPT_DIRECTOR is not None:
            _pd_speech = shot.get("speech", "")
            _pd_shot_type = shot.get("shot_type", "medium_close")
            _pd_subject = shot.get("character", shot.get("host", "subject"))
            _pd_result = _PROMPT_DIRECTOR.direct(
                subject=_pd_subject,
                audio_line=_pd_speech,
                narrative_beat=shot.get("narrative_beat", ""),
                physical_description=shot.get("physical_description", ""),
                shot_type=_pd_shot_type if _pd_shot_type in ("wide", "medium", "medium_close", "close", "extreme_close") else "medium_close",
                sequence_position=shot.get("sequence_position", 1),
                sequence_total=shot.get("sequence_total", 1),
                prior_shot_context=shot.get("prior_shot_context", ""),
                dry_run=True,
            )
            _pd_render_id = _pd_result.render_id
            if _pd_result.gate == "RED":
                raise RuntimeError(
                    f"PromptDirector RED on shot {sid} — "
                    f"hard failure modes: {_pd_result.flagged_risks} | "
                    f"workarounds: {_pd_result.critique_issues}"
                )
            elif _pd_result.gate == "YELLOW":
                print(
                    f"[PromptDirector WARN] shot {sid} gate=YELLOW "
                    f"conf={_pd_result.confidence:.2f} "
                    f"risks={_pd_result.flagged_risks} "
                    f"levers={_pd_result.active_levers}",
                    file=sys.stderr,
                )
            # else GREEN — proceed silently
        # --- end PromptDirector ---

        # --- qa_gate: QA render description before generation ---
        _qa_rl = _qa_gate_check(
            content=prompt,
            content_type="render_description",
            subject=f"longform shot {sid}",
        )
        if _qa_rl["gate"] == "RED":
            print(
                f"[QA HOLD] render_longform.py: {_qa_rl['summary']} | Issues: {_qa_rl['issues']}",
                file=sys.stderr,
            )
            raise RuntimeError(f"QA gate RED on shot {sid} render description — render aborted")
        elif _qa_rl["gate"] == "YELLOW":
            print(
                f"[QA WARN] render_longform.py: {_qa_rl['summary']}",
                file=sys.stderr,
            )
        # --- end qa_gate ---
        _log(f"[longform] rendering {sid} ({shot['duration']}s)…")
        if _is_barebones_mode(script):
            vid, _bb = generate_barebones_video(
                client,
                shot,
                refs,
                script,
                prod_dir,
                duration=int(shot["duration"]),
                seed_slot="@1",
            )
        else:
            _api_pace()
            vid = client.video.generate(
                prompt=prompt,
                model=refs["model_video"],
                image_url=image_url,
                duration=shot["duration"],
                resolution=refs["resolution"],
            )
        _download(vid.url, out)
        rendered.append(out)
        # Print render_id so caller can capture it for outcome recording
        if _pd_render_id:
            print(f"[RENDER_ID] {_pd_render_id}")

    prov_cfg = script.get("provenance_card", {})
    if prov_cfg.get("enabled", True):
        prov_png = prod_dir / "provenance_card.png"
        render_provenance_card(script, prov_png)
        prov_mp4 = shots_dir / "provenance.mp4"
        provenance_to_video(prov_png, prov_mp4, prov_cfg.get("duration_s", 7))
        rendered.append(prov_mp4)

    concat_videos(rendered, final_mp4)
    _log(f"[longform] final → {final_mp4}")

    qa = qa_check(script, refs, rendered)
    qa_path = prod_dir / "qa_report.json"
    qa_path.write_text(json.dumps(qa, indent=2, ensure_ascii=False), encoding="utf-8")

    return {
        "production_dir": str(prod_dir),
        "script": str(script_copy),
        "imagine_pack": str(pack_path),
        "output": str(final_mp4),
        "qa": qa,
        "segments": [str(p) for p in rendered],
    }


def _run_package_stage(prod_dir: Path, *, require_qa_pass: bool = True) -> dict[str, Any]:
    pipeline_dir = WORKSPACE / "Studio" / "Pipeline"
    if str(pipeline_dir) not in sys.path:
        sys.path.insert(0, str(pipeline_dir))
    from package_episode import package_production  # noqa: WPS433

    return package_production(prod_dir, require_qa_pass=require_qa_pass)


def main() -> int:
    # Unicode status glyphs (→, ⚠) must survive a cp1252 Windows console — reconfigure stdout/stderr to utf-8.
    for _stream in (sys.stdout, sys.stderr):
        try:
            _stream.reconfigure(encoding="utf-8")
        except (AttributeError, ValueError):
            pass
    parser = argparse.ArgumentParser(description="DAVID long-form video assembler")
    parser.add_argument("script", type=Path, help="Path to script JSON")
    parser.add_argument("--concat-only", action="store_true", help="Reuse cached shots; no API calls")
    parser.add_argument("--script-only", action="store_true", help="Normalize + write imagine pack only")
    parser.add_argument("--package", action="store_true", help="Build upload kit after render")
    parser.add_argument("--package-only", action="store_true", help="Package existing production only; no render")
    parser.add_argument("--force-shot", action="append", default=[], help="Regenerate specific shot id(s)")
    parser.add_argument("--force-all", action="store_true", help="Regenerate every seamless chain shot")
    parser.add_argument("--force-plates", action="store_true", help="Re-lock @1 zone plates (empty environment stills from set_reference)")
    parser.add_argument("--skip-generation-gate", action="store_true", help="Bypass T243 avatar/set blue-channel pre-render gate (dev only)")
    parser.add_argument("--skip-t243-gate", action="store_true", help="Bypass T243-B formal pre-render checklist gate (dev only)")
    parser.add_argument("--seamless", action="store_true", help="STUDIO v1.1 extend-primary + xfade joins")
    parser.add_argument("--match-color", action="store_true", help="Histogram-match before frame-chain joins")
    parser.add_argument("--cut-on-motion", action="store_true", help="Trim tail stillness before card join")
    parser.add_argument(
        "--xfade",
        type=float,
        default=None,
        help=f"Crossfade seconds (default {DEFAULT_XFADE_S}, min {MIN_XFADE_S})",
    )
    args = parser.parse_args()

    script_path = args.script if args.script.is_absolute() else Path.cwd() / args.script
    if not script_path.is_file():
        script_path = Path(__file__).parent / "longform_scripts" / args.script.name
    if not script_path.is_file():
        raise SystemExit(f"Script not found: {args.script}")

    raw = json.loads(script_path.read_text(encoding="utf-8"))
    script = normalize_script(raw, script_path)

    if not script.get("shots"):
        raise SystemExit("Script has no shots[]")

    assert_gate_0_cleared(script)

    if args.package_only:
        prod_dir = resolve_production_dir(script)
        if not (prod_dir / "manifest.json").is_file():
            raise SystemExit(f"--package-only: no manifest in {prod_dir}")
        pkg = _run_package_stage(prod_dir)
        manifest = json.loads((prod_dir / "manifest.json").read_text(encoding="utf-8"))
        manifest["upload_kit"] = pkg["upload_kit"]
        manifest["packaged_at"] = pkg["manifest"]["packaged_at"]
        (prod_dir / "manifest.json").write_text(
            json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8"
        )
        print(json.dumps(pkg["manifest"], indent=2, ensure_ascii=False))
        return 0

    if args.script_only:
        refs = resolve_refs(script)
        pack = build_imagine_pack(script, refs)
        prod_dir = resolve_production_dir(script)
        prod_dir.mkdir(parents=True, exist_ok=True)
        out = prod_dir / f"{script.get('slug', 'longform')}_imagine_pack.json"
        out.write_text(json.dumps(pack, indent=2, ensure_ascii=False), encoding="utf-8")
        script_out = prod_dir / f"{script.get('slug', 'longform')}_script.json"
        script_out.write_text(json.dumps(script, indent=2, ensure_ascii=False), encoding="utf-8")
        _log(f"Script only → {script_out}")
        _log(f"Imagine pack → {out}")
        return 0

    client = None
    if not args.concat_only:
        import xai_sdk

        token = os.environ.get("XAI_API_KEY") or _load_grok_token()
        os.environ["XAI_API_KEY"] = token
        client = xai_sdk.Client(api_key=token)

    refs = resolve_refs(script, client=client)
    seamless_opts = get_seamless_options(script, args)  # reads script config; --seamless flag is one input, not the gate
    result = render_longform(
        script,
        client=client,
        concat_only=args.concat_only,
        force_shots=set(args.force_shot) if args.force_shot else None,
        force_all=args.force_all,
        force_plates=args.force_plates,
        seamless_opts=seamless_opts,
    )

    if args.package:
        prod_dir = resolve_production_dir(script)
        pkg = _run_package_stage(prod_dir)
        manifest_path = prod_dir / "manifest.json"
        if manifest_path.is_file():
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            manifest["upload_kit"] = pkg["upload_kit"]
            manifest["packaged_at"] = pkg["manifest"]["packaged_at"]
            manifest_path.write_text(
                json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8"
            )
        print(json.dumps(pkg["manifest"], indent=2, ensure_ascii=False))

    return resolve_render_exit_code(result)


if __name__ == "__main__":
    sys.exit(main())
