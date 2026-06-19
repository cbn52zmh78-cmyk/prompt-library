#!/usr/bin/env python3
"""Production Templates v1.0 — format blueprints → canonical render_longform scripts.

Loads STUDIO/Pipeline/Production_Templates/Production_Templates_v1.json and composes
shot video_prompts with set/style continuity prefix + end-guard for seamless assembly.

Usage:
    python artifacts/production/production_templates.py select "warm daily check-in companion"
    python artifacts/production/production_templates.py build documentary-host --slug my_intro --out script.json
    python artifacts/production/production_templates.py list
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from lib.bootstrap import ensure_paths

ensure_paths()
from lib.studio_paths import pipeline_path

SYNTHETIC_GUARD = "synthetic host only"
TEMPLATES_FILE = "Production_Templates/Production_Templates_v1.json"
SET_LIBRARY = "Set_Library_v1.json"
STYLE_LIBRARY = "Style_Library_v1.json"

SPEAKING_ROLES = frozenset({
    "host", "character", "companion", "presenter", "host_pie",
})


def _load_json(rel_path: str) -> dict[str, Any]:
    path = pipeline_path(rel_path)
    if not path.is_file():
        raise FileNotFoundError(f"Missing library file: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def load_templates() -> dict[str, Any]:
    return _load_json(TEMPLATES_FILE)


def load_set_library() -> dict[str, Any]:
    return _load_json(SET_LIBRARY)


def load_style_library() -> dict[str, Any]:
    return _load_json(STYLE_LIBRARY)


def list_formats() -> list[str]:
    return list(load_templates()["formats"].keys())


def get_format(format_id: str) -> dict[str, Any]:
    templates = load_templates()
    if format_id not in templates["formats"]:
        valid = ", ".join(templates["formats"])
        raise KeyError(f"Unknown format '{format_id}'. Valid: {valid}")
    return templates["formats"][format_id]


def _resolve_library_entry(library: dict[str, Any], entry_id: str) -> dict[str, Any]:
    bucket = library.get("sets") or library.get("styles") or {}
    if entry_id not in bucket:
        raise KeyError(f"Library entry not found: {entry_id}")
    return bucket[entry_id]


def _substitute(template: str, values: dict[str, str]) -> str:
    out = template
    for key, value in values.items():
        out = out.replace(f"{{{key}}}", value)
    return out


def compose_video_prompt(
    *,
    action_prompt: str,
    speech_text: str = "",
    role: str = "host",
    set_id: str,
    style_id: str,
    identity_continuity_lock: str,
    voice_suffix: str,
    include_lip_sync: bool = True,
) -> str:
    """Build a seamless-ready video_prompt with prefix locks and end guard."""
    set_entry = _resolve_library_entry(load_set_library(), set_id)
    style_entry = _resolve_library_entry(load_style_library(), style_id)

    parts = [
        identity_continuity_lock,
        set_entry["continuity_lock"],
        style_entry["continuity_lock"],
        action_prompt.strip(),
        set_entry.get("lighting_lock", ""),
        style_entry.get("lighting_lock", ""),
        set_entry.get("color_guard", ""),
        style_entry.get("color_guard", ""),
        style_entry.get("lens_motion", ""),
    ]

    speaks = include_lip_sync and role in SPEAKING_ROLES and speech_text.strip()
    if speaks:
        parts.append(f'Lip-synced, delivers: "{speech_text.strip()}"')

    voice = voice_suffix.strip()
    if voice:
        parts.append(voice)
    if SYNTHETIC_GUARD.lower() not in voice.lower() and "synthetic" not in voice.lower():
        parts.append(SYNTHETIC_GUARD)

    parts.append(style_entry.get("end_guard", ""))
    return " ".join(p.strip() for p in parts if p and p.strip())


def select_format(concept: str, *, format_id: str | None = None) -> dict[str, Any]:
    """Score concept text and return best-matching format with rationale."""
    templates = load_templates()
    if format_id:
        if format_id not in templates["formats"]:
            raise KeyError(f"Unknown format '{format_id}'")
        return {
            "format_id": format_id,
            "format_name": templates["formats"][format_id]["name"],
            "score": None,
            "method": "explicit",
            "concept": concept,
        }

    selector = templates["concept_selector"]
    text = concept.lower()
    scores: dict[str, float] = {}

    for fid, signals in selector["formats"].items():
        score = 0.0
        for kw in signals.get("keywords", []):
            if kw.lower() in text:
                score += 2.0
        for nkw in signals.get("negative_keywords", []):
            if nkw.lower() in text:
                score -= 3.0
        scores[fid] = score * signals.get("weight", 1.0)

    best_id = max(scores, key=scores.get)
    if scores[best_id] <= 0:
        best_id = selector.get("default_format", "documentary-host")

    ranked = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    return {
        "format_id": best_id,
        "format_name": templates["formats"][best_id]["name"],
        "score": scores[best_id],
        "ranking": ranked,
        "method": "concept_selector",
        "concept": concept,
    }


def _slugify(text: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "_", text.lower()).strip("_")
    return slug[:48] or "production"


def build_longform_script(
    format_id: str,
    *,
    concept: str = "",
    slug: str | None = None,
    title: str | None = None,
    beats: list[dict[str, Any]] | None = None,
    set_id: str | None = None,
    style_id: str | None = None,
    identity_lock: str | None = None,
    avatar_reference: str | None = None,
    brand: dict[str, str] | None = None,
    target_seconds: int | None = None,
) -> dict[str, Any]:
    """Map a format blueprint + optional beat content to canonical render_longform schema."""
    templates = load_templates()
    fmt = get_format(format_id)
    seamless = templates["compose_contract"]["seamless_defaults"]

    resolved_set = set_id or fmt["default_set"]
    resolved_style = style_id or fmt["default_style"]
    voice = fmt["voice_suffix"]
    identity_continuity_lock = fmt["identity_continuity_lock"]

    shots: list[dict[str, Any]] = []
    t = 0
    blueprints = fmt["shot_blueprints"]
    beat_map = {b["id"]: b for b in (beats or []) if "id" in b}

    for bp in blueprints:
        beat = beat_map.get(bp["id"], {})
        duration = int(beat.get("duration", bp["duration"]))
        speech = beat.get("speech_text", beat.get("speech", bp.get("speech_placeholder", "")))
        if speech.startswith("[") and speech.endswith("]"):
            speech = ""

        action = beat.get("action_prompt", beat.get("action", bp["action_template"]))
        camera_note = beat.get("camera", bp.get("camera", ""))
        if camera_note and camera_note not in action:
            action = f"{action.rstrip()} {camera_note}"

        role = beat.get("role", bp["role"])
        video_prompt = compose_video_prompt(
            action_prompt=action,
            speech_text=speech,
            role=role,
            set_id=resolved_set,
            style_id=resolved_style,
            identity_continuity_lock=identity_continuity_lock,
            voice_suffix=voice,
            include_lip_sync=role in SPEAKING_ROLES,
        )

        shot: dict[str, Any] = {
            "id": bp["id"],
            "duration": duration,
            "t_start": t,
            "t_end": t + duration,
            "role": role,
            "video_prompt": video_prompt,
            "speech_text": speech,
        }
        if beat.get("on_screen"):
            shot["on_screen"] = beat["on_screen"]
        if beat.get("on_screen_labels"):
            shot["on_screen_labels"] = beat["on_screen_labels"]
        shots.append(shot)
        t += duration

    brand = brand or {}
    prov_template = fmt.get("provenance_card", {"enabled": False})
    prov: dict[str, Any] = {"enabled": prov_template.get("enabled", False)}
    if prov["enabled"]:
        prov.update({
            "duration_s": prov_template.get("duration_s", 6),
            "card_type": prov_template.get("card_type", "closing"),
            "title": _substitute(prov_template.get("title", ""), {
                "brand_title": brand.get("title", title or slug or "Production"),
                "brand": brand.get("brand", title or slug or "Production"),
                "title": title or slug or "Production",
            }),
            "subtitle": _substitute(prov_template.get("subtitle", ""), {
                "brand_subtitle": brand.get("subtitle", concept or ""),
                "subtitle": brand.get("subtitle", concept or ""),
                "cta": brand.get("cta", ""),
            }),
            "footer": _substitute(prov_template.get("footer", ""), {
                "cta": brand.get("cta", ""),
                "credit_line": brand.get("credit", ""),
                "legal_line": brand.get("legal", ""),
            }),
        })

    cfg: dict[str, Any] = {
        "model_video": "grok-imagine-video-1.5",
        "resolution": "720p",
        "aspect_ratio": "16:9",
        "voice_suffix": voice,
        "seamless": seamless,
    }
    if identity_lock:
        cfg["identity_lock"] = identity_lock
    elif format_id == "documentary-host":
        cfg["identity_lock"] = "productions/host_identity_v1/david_identity_lock.json"
    if avatar_reference:
        cfg["avatar_reference"] = avatar_reference
    elif format_id == "documentary-host":
        cfg["avatar_reference"] = "productions/host_identity_v1/references/david_avatar_reference.jpg"

    script_title = title or f"{fmt['name']} — {concept or slug or format_id}"
    script_slug = slug or _slugify(concept or format_id)

    return {
        "slug": script_slug,
        "title": script_title,
        "target_seconds": target_seconds or fmt["target_seconds"].get("default", t),
        "format_id": format_id,
        "concept": concept,
        "config": cfg,
        "shots": shots,
        "provenance_card": prov,
        "qa_rules": dict(fmt.get("qa_rules", {})),
        "guardrails": list(templates.get("global_guardrails", [])) + list(fmt.get("guardrails", [])),
        "production_meta": {
            "set_id": resolved_set,
            "style_id": resolved_style,
            "identity_anchor": fmt["identity_anchor"],
            "pacing": fmt["pacing"],
            "camera": fmt["camera"],
            "target_rating": fmt.get("target_rating", "PG"),
        },
    }


def write_script(script: dict[str, Any], out_path: Path) -> Path:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(script, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return out_path


def main() -> int:
    parser = argparse.ArgumentParser(description="Production Templates v1.0")
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("list", help="List available format IDs")

    p_sel = sub.add_parser("select", help="Concept → format selector")
    p_sel.add_argument("concept", help="Concept description text")
    p_sel.add_argument("--format", dest="format_id", help="Force format ID")

    p_build = sub.add_parser("build", help="Build canonical longform script JSON")
    p_build.add_argument("format_id", nargs="?", help="Format ID (optional if --concept selects)")
    p_build.add_argument("--concept", default="", help="Concept for title/selector")
    p_build.add_argument("--slug", help="Production slug")
    p_build.add_argument("--title", help="Production title")
    p_build.add_argument("--set", dest="set_id", help="Override set ID")
    p_build.add_argument("--style", dest="style_id", help="Override style ID")
    p_build.add_argument("--out", type=Path, help="Output script.json path")
    p_build.add_argument("--beats", type=Path, help="JSON file with per-shot beat overrides")

    args = parser.parse_args()

    if args.command == "list":
        for fid in list_formats():
            fmt = get_format(fid)
            ts = fmt["target_seconds"]
            print(f"  {fid:28} {fmt['name']:32} {ts['min']}–{ts['max']}s ({len(fmt['shot_blueprints'])} shots)")
        return 0

    if args.command == "select":
        result = select_format(args.concept, format_id=args.format_id)
        print(json.dumps(result, indent=2))
        return 0

    if args.command == "build":
        format_id = args.format_id
        if not format_id:
            format_id = select_format(args.concept)["format_id"]
        beats = None
        if args.beats and args.beats.is_file():
            beats = json.loads(args.beats.read_text(encoding="utf-8"))
            if isinstance(beats, dict):
                beats = beats.get("beats", beats.get("shots", []))
        script = build_longform_script(
            format_id,
            concept=args.concept,
            slug=args.slug,
            title=args.title,
            beats=beats,
            set_id=args.set_id,
            style_id=args.style_id,
        )
        if args.out:
            write_script(script, args.out)
            print(f"Wrote {args.out} ({len(script['shots'])} shots, {script['target_seconds']}s target)")
        else:
            print(json.dumps(script, indent=2, ensure_ascii=False))
        return 0

    return 1


if __name__ == "__main__":
    sys.exit(main())