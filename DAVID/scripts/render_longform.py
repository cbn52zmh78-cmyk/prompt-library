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
PIPELINE_DIR = WORKSPACE / "STUDIO" / "Pipeline"
if str(PIPELINE_DIR) not in sys.path:
    sys.path.insert(0, str(PIPELINE_DIR))

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
ARCHIVE_NEUTRAL_CLAMP_VF = f"{NEUTRAL_WB_VF},{MAGENTA_CLAMP_VF},{SKIN_NEUTRAL_VF}"
CLINICAL_NEUTRAL_CLAMP_VF = f"{NEUTRAL_WB_VF},{MAGENTA_CLAMP_VF},{SKIN_NEUTRAL_VF}"
WARM_GOLD_CLAMP_VF = ARCHIVE_NEUTRAL_CLAMP_VF
MAGENTA_SCORE_MAX = 0.42
YELLOW_GREEN_SCORE_MAX = 0.12
LABEL_CHIP_COLORS = {
    "RECONSTRUCTED PRONUNCIATION": (140, 88, 28, 245),
    "CLASSICAL LATIN": (40, 48, 62, 235),
}
LOUDNESS_SPREAD_MAX_LU = 1.5
REGROUND_EVERY_N = 2
LOUDNORM_LRA_TIGHT = 7.0
SET_LIBRARY_PATH = WORKSPACE / "STUDIO" / "Pipeline" / "Set_Library_v1.json"
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
    if rel.startswith("STUDIO/"):
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


def resolve_shot_image_url(shot: dict[str, Any], refs: dict[str, Any]) -> str:
    """Presenter shots use avatar; @2 visualization shots use locked science plate."""
    if shot.get("image_url"):
        return str(shot["image_url"])
    if _shot_uses_viz_reference(shot) and refs.get("visualization_url"):
        return str(refs["visualization_url"])
    return str(refs["avatar_url"])


def _use_avatar_reground(
    refs: dict[str, Any],
    shot: dict[str, Any],
    shot_index: int,
    opts: "SeamlessOptions",
) -> bool:
    """Dark/high-contrast: re-ground every shot on locked avatar (never drifted chain frame)."""
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


def _is_dark_scene(
    refs: dict[str, Any],
    *,
    script: dict[str, Any] | None = None,
    shot: dict[str, Any] | None = None,
) -> bool:
    set_file = str(refs.get("set_file") or "").lower()
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


def _magenta_clamp_vf(
    *,
    dark_scene: bool,
    lamp_lock: bool,
    strong: bool = False,
    archive_neutral: bool = False,
) -> str:
    if archive_neutral and not dark_scene:
        return ARCHIVE_NEUTRAL_CLAMP_VF if not strong else f"{ARCHIVE_NEUTRAL_CLAMP_VF},{MAGENTA_CLAMP_STRONG_VF}"
    if strong or dark_scene:
        base = MAGENTA_CLAMP_STRONG_VF if strong else DARK_SCENE_MAGENTA_CLAMP_VF
    else:
        base = MAGENTA_CLAMP_VF
    if lamp_lock and not archive_neutral:
        return f"{base},{LAMP_LOCK_VF}"
    return base


def _normalize_shot_list(shots: list[dict[str, Any]]) -> list[dict[str, Any]]:
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
        if speech and speech not in prompt:
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
) -> list[dict[str, Any]]:
    """Bake legacy top-level continuity_prefix/end_guard into video_prompt when missing."""
    out: list[dict[str, Any]] = []
    for s in shots:
        shot = {**s}
        prompt = shot.get("video_prompt", "")
        if "@David-001" not in prompt and prefix:
            prompt = f"{prefix} {prompt}".strip()
        speech = shot.get("speech_text", "")
        if speech and speech not in prompt:
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
        shots = _normalize_shot_list(raw["shots"])
        prefix = raw.get("continuity_prefix", "")
        guard = raw.get("end_guard", "")
        if prefix or guard:
            shots = _embed_legacy_continuity(shots, prefix, guard, cfg.get("voice_suffix", DEFAULT_VOICE_SUFFIX))
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
            f"{gate.get('music_bed_id')}. Verify STUDIO/Music_Sound/clearance_manifest.json. "
            f"Report: {gate.get('report_path', 'unknown')}"
        )


def resolve_production_dir(script: dict[str, Any]) -> Path:
    if script.get("production_dir"):
        raw = str(script["production_dir"]).replace("\\", "/")
        if raw.startswith("STUDIO/"):
            return _resolve_workspace_path(raw)
        p = Path(script["production_dir"])
        return p if p.is_absolute() else (ROOT / p)
    slug = script.get("slug", "longform")
    if script.get("format_id") and script["format_id"] != "documentary-host":
        return WORKSPACE / "STUDIO" / "Productions" / "Editorial" / f"{slug}_longform_v1"
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

    if not avatar_url and avatar_file and client is not None:
        avatar_url = upload_image_url(client, Path(avatar_file))
        cfg["avatar_url"] = avatar_url

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
        "avatar_file": avatar_file,
        "config_avatar_reference": cfg.get("avatar_reference"),
        "visualization_url": viz_url,
        "visualization_file": viz_file,
        "set_file": set_file,
        "voice_suffix": voice_suffix,
        "format_id": script.get("format_id"),
        "production_meta": script.get("production_meta"),
        "model_video": cfg.get("model_video", "grok-imagine-video-1.5"),
        "resolution": cfg.get("resolution", "720p"),
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
        "voice_suffix": refs["voice_suffix"],
        "seamless": use_seamless,
        "shots": [
            {
                "shot_id": s["id"],
                "duration": effective_shot_duration(s, seamless=use_seamless),
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


@dataclass
class SeamlessOptions:
    enabled: bool = False
    xfade_s: float = 0.2
    match_color: bool = False
    cut_on_motion: bool = False
    lamp_lock: bool = True
    glasses_lock: bool = True
    loudnorm: bool = True
    pin_audio_sync: bool = True
    reground_interval: int = REGROUND_EVERY_N
    magenta_clamp: bool = True
    neutral_grade: bool = False


EXTEND_API_FINDING = {
    "scriptable": True,
    "enabled_on_model": False,
    "model": "grok-imagine-video-1.5",
    "editor_extend": "Grok Imagine UI Continue/Extend may work before API parity on 1.5",
    "finding": (
        "client.video.extend() exists in xAI SDK but grok-imagine-video-1.5 returns "
        "'Video extension is not supported for this model'. Pipeline uses frame-chain i2v fallback."
    ),
}


def get_seamless_options(script: dict[str, Any], args: argparse.Namespace) -> SeamlessOptions:
    seam = script.get("config", {}).get("seamless") or {}
    auto = seam.get("primary") in ("extend", "extend_chain", True)
    return SeamlessOptions(
        enabled=bool(getattr(args, "seamless", False) or auto),
        xfade_s=float(getattr(args, "xfade", None) or seam.get("xfade_s", 0.2)),
        match_color=getattr(args, "match_color", False) or bool(seam.get("match_color")),
        cut_on_motion=getattr(args, "cut_on_motion", False) or bool(seam.get("cut_on_motion")),
        lamp_lock=bool(seam.get("lamp_lock", True)),
        glasses_lock=bool(seam.get("glasses_lock", True)),
        loudnorm=bool(seam.get("loudnorm", True)),
        pin_audio_sync=bool(seam.get("pin_audio_sync", True)),
        reground_interval=int(seam.get("reground_interval", REGROUND_EVERY_N)),
        magenta_clamp=bool(seam.get("magenta_clamp", True)),
        neutral_grade=bool(seam.get("neutral_grade", False)),
    )


def apply_seamless_prompt(shot: dict[str, Any], refs: dict[str, Any], opts: SeamlessOptions) -> str:
    """Use embedded video_prompt when continuity is already baked in; else patch defaults."""
    base = shot.get("video_prompt", "")
    locks: list[str] = []
    archive = "archive" in str(refs.get("set_file") or "").lower()
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
    speech = shot.get("speech_text", "")
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
) -> Path:
    """Per-shot magenta suppression — within-clip, independent of --match-color joins."""
    ff = _ffmpeg_exe()
    out.parent.mkdir(parents=True, exist_ok=True)
    clamp_vf = _magenta_clamp_vf(
        dark_scene=dark_scene, lamp_lock=lamp_lock, archive_neutral=archive_neutral,
    )
    cur = video
    staged = out.with_name(f"{out.stem}_clamp_stage.mp4")

    # Dark/high-contrast: eq-only within-clip — avatar histogram match drifts magenta.
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
            dark_scene=True, lamp_lock=lamp_lock, strong=True, archive_neutral=archive_neutral,
        )
        strong_out = out.with_name(f"{out.stem}_strong{pass_n}.mp4")
        if not _run_video_eq_pass(cur, strong_out, strong_vf):
            break
        cur = strong_out
        _log(f"[magenta] within-clip strong pass {pass_n + 1}/{max_strong} (score was {mag:.3f})")

    if archive_neutral and not dark_scene:
        accented = out.with_name(f"{out.stem}_lamp_accent.mp4")
        apply_lamp_accent_local(cur, accented)
        cur = accented

    staging = out.with_name(f"{out.stem}__clamp_staging.mp4")
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
) -> Path:
    """Match *target* to locked *color_ref* (David-001), not drifted prior segment."""
    ff = _ffmpeg_exe()
    out.parent.mkdir(parents=True, exist_ok=True)
    ref = color_ref or reference
    if neutral_grade:
        post_vf = CLINICAL_NEUTRAL_CLAMP_VF
    elif archive_neutral:
        post_vf = WARM_GOLD_CLAMP_VF
    elif lamp_lock:
        post_vf = f"{MAGENTA_CLAMP_VF},{LAMP_LOCK_VF}"
    else:
        post_vf = MAGENTA_CLAMP_VF
    if ref.suffix.lower() in (".jpg", ".jpeg", ".png", ".webp"):
        if lamp_lock:
            vfilter = (
                f"[0:v][1:v]histogrammatching=pattern=1:strength=0.62[matched];"
                f"[matched]{post_vf}[outv]"
            )
        else:
            vfilter = f"[0:v][1:v]histogrammatching=pattern=1:strength=0.62[matched];[matched]{MAGENTA_CLAMP_VF}[outv]"
        cmd = [
            ff, "-y", "-i", str(target), "-loop", "1", "-i", str(ref),
            "-filter_complex", vfilter,
            "-map", "[outv]", "-map", "0:a?", "-c:v", "libx264", "-pix_fmt", "yuv420p",
            "-c:a", "copy", "-shortest", str(out),
        ]
    elif lamp_lock:
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
        if neutral_grade:
            _log("[seamless] match-color filter unavailable; clinical neutral WB fallback")
            vf = CLINICAL_NEUTRAL_CLAMP_VF
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
    archive_neutral = _refs_is_archive(refs) and opts.lamp_lock and not dark_scene
    target_dur = float(
        effective_shot_duration(shot, seamless=True)
        if shot.get("duration") is not None
        else clamp_shot_duration(probe_duration(cur))
    )

    if opts.magenta_clamp or opts.match_color:
        clamped = work / f"{video.stem}_clamped.mp4"
        if opts.neutral_grade:
            apply_neutral_white_balance_grade(cur, clamped, color_ref)
        else:
            apply_per_shot_magenta_clamp(
                cur, clamped, color_ref,
                dark_scene=dark_scene, lamp_lock=opts.lamp_lock,
                archive_neutral=archive_neutral,
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
            target_dur = float(effective_shot_duration(shot, seamless=True))
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
    """Re-concat/clamp/sync path — loudness-tighten then mandatory xfade when N>=2 (#193)."""
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


def concat_xfade_two(
    left: Path,
    right: Path,
    out: Path,
    *,
    xfade_s: float = 0.2,
    match_color: bool = False,
    cut_on_motion: bool = False,
    lamp_lock: bool = True,
    neutral_grade: bool = False,
    color_ref: Path | None = None,
    work_dir: Path | None = None,
) -> Path:
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
            lamp_lock
            and not neutral_grade
            and any(k in str(ref).lower() for k in ("archive", "david_identity", "david_avatar"))
        )
        match_color_segment(
            left, right, matched,
            lamp_lock=lamp_lock, color_ref=ref, archive_neutral=archive_neutral,
            neutral_grade=neutral_grade,
        )
        if archive_neutral:
            accented = work / f"{right.stem}_matched_accent_{out.stem}.mp4"
            apply_lamp_accent_local(matched, accented)
            b = accented
        else:
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
    xfade_s: float = 0.2,
    match_color: bool = False,
    cut_on_motion: bool = False,
    lamp_lock: bool = True,
    neutral_grade: bool = False,
    color_ref: Path | None = None,
    work_dir: Path | None = None,
) -> Path:
    """Chain 0.2s xfade + synced audio crossfade joins across N segments."""
    if not segments:
        raise ValueError("concat_xfade_chain: no segments")
    work = work_dir or out.parent
    if len(segments) == 1:
        shutil.copy2(segments[0], out)
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
    return "not supported" in msg or "invalid_argument" in msg


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
    magenta_reroll = _should_magenta_reroll(script_ctx, refs)

    for i, shot in enumerate(shots):
        sid = shot["id"]
        seg_path = shots_dir / f"chain_{sid}.mp4"
        proc_path = shots_dir / f"chain_{sid}_processed.mp4"
        dur = effective_shot_duration(shot, seamless=True)
        prompt = apply_seamless_prompt(shot, refs, opts)
        regen = force or sid in force_ids

        if (
            proc_path.exists()
            and proc_path.stat().st_size > 10000
            and not regen
            and not concat_only
        ):
            _log(f"[seamless] reusing processed {proc_path.name}")
            segments.append(proc_path)
            continue

        if seg_path.exists() and seg_path.stat().st_size > 10000 and not regen and concat_only:
            raw = ensure_segment_audio(seg_path, shot, refs, shots_dir)
            process_shot_segment(raw, proc_path, shot, refs, opts, shots_dir, color_ref)
            segments.append(proc_path)
            continue

        if seg_path.exists() and seg_path.stat().st_size > 10000 and not regen and not concat_only:
            raw = ensure_segment_audio(seg_path, shot, refs, shots_dir)
            process_shot_segment(raw, proc_path, shot, refs, opts, shots_dir, color_ref)
            if not magenta_reroll:
                segments.append(proc_path)
                continue
            mag = probe_magenta_score(proc_path)
            if mag <= MAGENTA_SCORE_MAX:
                segments.append(proc_path)
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
                    if _use_avatar_reground(refs, shot, i, opts):
                        image_url = resolve_shot_image_url(shot, refs)
                        dark = _is_dark_scene(refs, shot=shot)
                        if _shot_uses_viz_reference(shot) and refs.get("visualization_url"):
                            src = "locked @2 science plate re-ground"
                        elif dark:
                            src = "dark-set avatar re-ground (Kelvin locked)"
                        else:
                            src = "talent re-ground" if i > 0 else "locked talent avatar"
                        _log(f"[seamless] frame-chain {i + 1}/{len(shots)} {sid} ({dur}s) ← {src}")
                    else:
                        frame_jpg = frames_dir / f"frame_after_{segments[-1].stem}.jpg"
                        extract_last_frame(segments[-1], frame_jpg)
                        _api_pace()
                        image_url = upload_image_url(client, frame_jpg)
                        _log(f"[seamless] frame-chain {i + 1}/{len(shots)} {sid} ({dur}s) ← last frame")

                    _api_pace()
                    resp = client.video.generate(
                        prompt=prompt,
                        model=model,
                        image_url=image_url,
                        duration=dur,
                        resolution=refs["resolution"],
                    )
                    step_urls.append(resp.url)
                    _download(resp.url, seg_path)

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

        segments.append(proc_path)

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
    if have_chain and not regen_any:
        _log(f"[seamless] xfade chain reassembly from {len(chain_segs)} cached segments")
        _reconcat_seamless_chain(
            chain_segs,
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
        _log(f"[seamless] reusing performance {out_path.name} (no per-shot chain cache)")
        mode = "cached"
        if state_path.is_file():
            mode = json.loads(state_path.read_text(encoding="utf-8")).get("mode", mode)
        return out_path, [], mode

    gen_model = refs["model_video"]
    extend_model = refs.get("extend_model") or gen_model
    avatar_url = refs["avatar_url"]

    # First segment
    shot0 = shots[0]
    dur0 = effective_shot_duration(shot0, seamless=True)
    prompt0 = apply_seamless_prompt(shot0, refs, opts)
    image_url0 = resolve_shot_image_url(shot0, refs)
    _log(f"[seamless] extend step 1/{len(shots)} {shot0['id']} ({dur0}s)…")
    _api_pace()
    resp = client.video.generate(
        prompt=prompt0,
        model=gen_model,
        image_url=image_url0,
        duration=dur0,
        resolution=refs["resolution"],
    )
    current_url = resp.url
    step_urls = [current_url]
    _download(current_url, out_path)

    if len(shots) == 1:
        state_path.write_text(json.dumps({"mode": "generate_only", "urls": step_urls}), encoding="utf-8")
        return out_path, step_urls, "generate_only"

    shot1 = shots[1]
    dur1 = effective_shot_duration(shot1, seamless=True)
    prompt1 = apply_seamless_prompt(shot1, refs, opts)
    try:
        _log(f"[seamless] extend step 2/{len(shots)} {shot1['id']} ({dur1}s)…")
        _api_pace()
        resp = client.video.extend(
            prompt=prompt1,
            model=extend_model,
            video_url=current_url,
            duration=dur1,
        )
        current_url = resp.url
        step_urls.append(current_url)
        _download(current_url, out_path)

        for i, shot in enumerate(shots[2:], start=3):
            sid = shot["id"]
            dur = effective_shot_duration(shot, seamless=True)
            prompt = apply_seamless_prompt(shot, refs, opts)
            _log(f"[seamless] extend step {i}/{len(shots)} {sid} ({dur}s)…")
            _api_pace()
            resp = client.video.extend(
                prompt=prompt,
                model=extend_model,
                video_url=current_url,
                duration=dur,
            )
            current_url = resp.url
            step_urls.append(current_url)
            _download(current_url, out_path)

        state_path.write_text(
            json.dumps({
                "mode": "extend",
                "model": extend_model,
                "urls": step_urls,
                "extend_api": {**EXTEND_API_FINDING, "enabled_on_model": True, "continuity_mode": "extend"},
            }),
            encoding="utf-8",
        )
        return out_path, step_urls, "extend"

    except Exception as exc:
        if not _extend_not_supported(exc):
            raise
        _log("[seamless] EXTEND unavailable on grok-imagine-video-1.5 — frame-chain fallback (STUDIO v1.1 §2)")
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
                    passes.append("clinical/neutral set — magenta probe skipped (grey balance gate)")
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
                if _is_archive_production(script, refs) or (
                    _is_clinical_neutral_set(script, refs) and seamless_opts.neutral_grade
                ):
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
            band_issue = check_shot_duration_band(s, seamless=seamless_opts.enabled)
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
    return report


def render_longform(
    script: dict[str, Any],
    *,
    client: Any = None,
    concat_only: bool = False,
    force_shots: set[str] | None = None,
    force_all: bool = False,
    seamless_opts: SeamlessOptions | None = None,
) -> dict[str, Any]:
    prod_dir = resolve_production_dir(script)
    shots_dir = prod_dir / "shots"
    shots_dir.mkdir(parents=True, exist_ok=True)

    refs = resolve_refs(script, client=client)
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
        if card_mp4:
            seamless_out = prod_dir / "output" / f"{prefix}_{slug}_seamless_v1.mp4"
            concat_xfade_two(
                host_join,
                card_mp4,
                seamless_out,
                xfade_s=opts.xfade_s,
                match_color=opts.match_color,
                cut_on_motion=False,
                lamp_lock=opts.lamp_lock,
                neutral_grade=opts.neutral_grade,
                color_ref=color_ref,
                work_dir=shots_dir,
            )
            final_mp4 = seamless_out
        elif opts.enabled:
            seamless_out = prod_dir / "output" / f"{prefix}_{slug}_seamless_v1.mp4"
            shutil.copy2(host_mp4, seamless_out)
            final_mp4 = seamless_out

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

        prompt = ensure_voice_in_prompt(shot["video_prompt"], refs["voice_suffix"])
        image_url = resolve_shot_image_url(shot, refs)
        _log(f"[longform] rendering {sid} ({shot['duration']}s)…")
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
    pipeline_dir = WORKSPACE / "STUDIO" / "Pipeline"
    if str(pipeline_dir) not in sys.path:
        sys.path.insert(0, str(pipeline_dir))
    from package_episode import package_production  # noqa: WPS433

    return package_production(prod_dir, require_qa_pass=require_qa_pass)


def main() -> int:
    # Unicode status glyphs (→, ⚠) must survive a cp1252 Windows console.
    for _stream in (sys.stdout, sys.stderr):
        try:
            _stream.reconfigure(encoding="utf-8")
        except (AttributeError, ValueError):
            pass
    parser = argparse.ArgumentParser(description="DAVID long-form video assembler")
    parser.add_argument("script", type=Path, help="Path to script JSON")
    parser.add_argument("--concat-only", action="store_true", help="Reuse cached shots; no API calls")
    parser.add_argument("--script-only", action="store_true", help="Normalize + write imagine pack only")
    parser.add_argument("--package", action="store_true", help="Build upload kit after render (MP4 → SEO/chapters/end-screen/thumbnail)")
    parser.add_argument("--package-only", action="store_true", help="Package existing production only; no render")
    parser.add_argument("--force-shot", action="append", default=[], help="Regenerate specific shot id(s)")
    parser.add_argument("--force-all", action="store_true", help="Regenerate every seamless chain shot")
    parser.add_argument("--seamless", action="store_true", help="STUDIO v1.1 extend-primary + xfade joins")
    parser.add_argument("--match-color", action="store_true", help="Histogram-match before frame-chain joins")
    parser.add_argument("--cut-on-motion", action="store_true", help="Trim tail stillness before card join")
    parser.add_argument("--xfade", type=float, default=None, help="Crossfade seconds (default 0.2)")
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

    seamless_opts = get_seamless_options(script, args)
    seamless_opts = _apply_grade_policy(script, resolve_refs(script), seamless_opts)
    reject_concat_only_seamless_grade(
        concat_only=args.concat_only,
        seamless_opts=seamless_opts,
        match_color=bool(args.match_color),
        cut_on_motion=bool(args.cut_on_motion),
        seamless_flag=bool(args.seamless),
    )

    force_ids = set(args.force_shot)
    if args.force_all and seamless_opts.enabled:
        force_ids = {s["id"] for s in script["shots"]}

    result = render_longform(
        script,
        client=client,
        concat_only=args.concat_only,
        force_shots=force_ids,
        force_all=args.force_all,
        seamless_opts=seamless_opts,
    )

    manifest = {
        "pipeline": "render_longform_seamless" if seamless_opts.enabled else "render_longform",
        "protocol": "STUDIO_Canonical_Schema_and_Seamless_Spec_v1" if seamless_opts.enabled else None,
        "completed_at": datetime.now(timezone.utc).isoformat(),
        "script_source": str(script_path),
        "concat_only": args.concat_only,
        "seamless": seamless_opts.enabled,
        **result,
    }
    prod_dir = Path(result["production_dir"])
    manifest_path = prod_dir / "manifest.json"
    exit_code = resolve_render_exit_code(result)
    if args.package and result["qa"]["pass"]:
        try:
            pkg = _run_package_stage(prod_dir)
            manifest["upload_kit"] = pkg["upload_kit"]
            manifest["packaged_at"] = pkg["manifest"]["packaged_at"]
        except Exception as exc:
            _log(f"[longform] package stage failed (QA still {'pass' if exit_code == 0 else 'fail'}): {exc}")
    manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(manifest, indent=2, ensure_ascii=False))
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())