"""ELEANOR-DAVID style modifier resolver — style/hybrid/sound/music/pacing/language/director persona IDs.

Per-field resolution (first explicit match wins; director persona fills gaps last):
  1. shot.modifiers.*
  2. shot.barebones / shot top-level (dialogue.language for per-line)
  3. config.style_blocks / config.pacing_blocks / config.music_blocks[<block_key>]
  4. script.style / general_style blocks + default
  5. config.branch_chain.blocks when shot listed
  6. config.* production defaults (config.language for whole-production)
  7. director_persona_id expansion (fills unset style/audio/music/pacing/performance/editing)
"""
from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path
from typing import Any

from color_cast_qa import DEFAULT_GRADE_FAMILY, resolve_grade_family

ROOT = Path(__file__).resolve().parents[1]
WORKSPACE = ROOT.parent
RESEARCH = WORKSPACE / "DAVID" / "ELEANOR" / "research"

# ── @ID → slug translation (Oliver creative asset IDs) ──────────────────────
# When a script references @HYB_003 instead of "hybrid_fincher_deakins",
# this layer resolves the permanent ID to the slug the modifier lookup expects.

_CREATIVE_ID_PATTERN = re.compile(r"^@(DIR|VIS|ANI|HYB|SND|MUS|PAC|LNG)_\d{3,}$")

# Fields that can hold creative asset @IDs (all the modifier tag fields)
_ID_TRANSLATABLE_FIELDS = frozenset({
    "director_persona_id", "style_dna_tag", "audio_dna_tag", "audio_dna_combo",
    "music_dna_tag", "music_dna_combo", "pacing_dna_tag", "anim_style_id",
    "camera_move",
})


def _translate_creative_ids(
    resolved: dict[str, str | None],
    catalog: Any | None = None,
) -> None:
    """In-place: replace @TYPE_NNN values with their slug from the catalog.

    If catalog is None or a value isn't a creative @ID, leaves it untouched.
    Backward-compatible: raw slugs pass through unchanged.
    """
    if catalog is None:
        return
    # Lazy import to avoid circular dependency
    from production_catalog import resolve_creative_id

    for fld in _ID_TRANSLATABLE_FIELDS:
        val = resolved.get(fld)
        if not val or not isinstance(val, str) or not _CREATIVE_ID_PATTERN.match(val):
            continue
        info = resolve_creative_id(catalog, val)
        if info and info.get("slug"):
            resolved[fld] = info["slug"]
            # Annotate that this came from an @ID so logs show provenance
            source_key = f"_{fld}_source"
            prev_source = resolved.get(source_key, "")
            resolved[source_key] = f"{prev_source}→{val}" if prev_source else val  # type: ignore[literal-required]

ANTI_GENERIC_ARMOR_DEFAULT = (
    "tactile film imperfections + soulful micro-errors + deliberate beautiful mistakes"
)


@dataclass
class ResolvedModifiers:
    director_persona_id: str | None = None
    pacing_dna_tag: str | None = None
    style_dna_tag: str | None = None
    grade_family: str | None = None
    audio_dna_tag: str | None = None
    audio_dna_combo: str | None = None
    music_dna_tag: str | None = None
    music_dna_combo: str | None = None
    language: str | None = None
    emotional_beat: str | None = None
    anim_style_id: str | None = None
    persona_clause: str | None = None
    performance_clause: str | None = None
    editing_clause: str | None = None
    pacing_clause: str | None = None
    block_continue_clause: str | None = None
    visual_clause: str | None = None
    camera_move_clause: str | None = None
    anim_clause: str | None = None
    audio_clause: str | None = None
    music_clause: str | None = None
    language_clause: str | None = None
    anti_generic_clause: str | None = None
    source: dict[str, str] = field(default_factory=dict)


def _read_json(path: Path) -> dict[str, Any]:
    if not path.is_file():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {}


@lru_cache(maxsize=1)
def _load_registry() -> dict[str, Any]:
    return _read_json(RESEARCH / "style_modifier_registry_v1.json")


@lru_cache(maxsize=1)
def _load_visual_styles() -> dict[str, dict[str, Any]]:
    data = _read_json(RESEARCH / "director_cinematographer_style_prompts_v1.json")
    return {s["id"]: s for s in data.get("styles") or [] if s.get("id")}


@lru_cache(maxsize=1)
def _load_hybrid_styles() -> dict[str, dict[str, Any]]:
    data = _read_json(RESEARCH / "grok_hybrid_styles_camera_innovations_v1.json")
    return {s["id"]: s for s in data.get("hybrid_styles") or [] if s.get("id")}


@lru_cache(maxsize=1)
def _load_anim_styles() -> dict[str, dict[str, Any]]:
    data = _read_json(RESEARCH / "director_cinematographer_animation_styles_v1.json")
    return {s["id"]: s for s in data.get("animation_styles") or [] if s.get("id")}


@lru_cache(maxsize=1)
def _load_sonic_doc() -> dict[str, Any]:
    return _read_json(RESEARCH / "sonic_signatures_grok_audio_v1.json")


@lru_cache(maxsize=1)
def _load_sonic_styles() -> dict[str, dict[str, Any]]:
    data = _load_sonic_doc()
    return {s["id"]: s for s in data.get("sonic_signatures") or [] if s.get("id")}


@lru_cache(maxsize=1)
def _load_audio_combos() -> dict[str, dict[str, Any]]:
    data = _load_sonic_doc()
    return {c["id"]: c for c in data.get("audio_combos") or [] if c.get("id")}


@lru_cache(maxsize=1)
def _load_music_doc() -> dict[str, Any]:
    return _read_json(RESEARCH / "music_signatures_v1.json")


@lru_cache(maxsize=1)
def _load_music_styles() -> dict[str, dict[str, Any]]:
    data = _load_music_doc()
    return {s["id"]: s for s in data.get("music_signatures") or [] if s.get("id")}


@lru_cache(maxsize=1)
def _load_music_combos() -> dict[str, dict[str, Any]]:
    data = _load_music_doc()
    return {c["id"]: c for c in data.get("music_combos") or [] if c.get("id")}


@lru_cache(maxsize=1)
def _load_music_beat_map() -> dict[str, str]:
    data = _load_music_doc()
    raw = data.get("music_beat_map") or {}
    return {
        str(k).strip().lower(): str(v).strip()
        for k, v in raw.items()
        if k and not str(k).startswith("_") and v
    }


def _music_chain_rule() -> str:
    return str(_load_music_doc().get("_chain_rule") or "").strip()


@lru_cache(maxsize=1)
def _load_language_doc() -> dict[str, Any]:
    return _read_json(RESEARCH / "language_profiles_v1.json")


@lru_cache(maxsize=1)
def _load_language_profiles() -> dict[str, dict[str, Any]]:
    data = _load_language_doc()
    return {p["id"]: p for p in data.get("language_profiles") or [] if p.get("id")}


@lru_cache(maxsize=1)
def _load_game_art_styles() -> dict[str, dict[str, Any]]:
    data = _read_json(RESEARCH / "game_art_style_registry_v1.json")
    return {s["id"]: s for s in data.get("game_art_styles") or [] if s.get("id")}


@lru_cache(maxsize=1)
def _load_emotional_beat_map() -> dict[str, str]:
    data = _load_sonic_doc()
    raw = data.get("emotional_beat_map") or {}
    return {
        str(k).strip().lower(): str(v).strip()
        for k, v in raw.items()
        if k and not str(k).startswith("_") and v
    }


@lru_cache(maxsize=1)
def _load_emotional_beat_combo_map() -> dict[str, str]:
    data = _load_sonic_doc()
    raw = data.get("emotional_beat_combo_map") or {}
    return {
        str(k).strip().lower(): str(v).strip()
        for k, v in raw.items()
        if k and not str(k).startswith("_") and v
    }


@lru_cache(maxsize=1)
def _load_technique_taxonomy() -> dict[str, str]:
    """Flat id → prompt language lookup from technique_taxonomy groups."""
    data = _load_sonic_doc()
    taxonomy = data.get("technique_taxonomy") or {}
    out: dict[str, str] = {}
    for group in taxonomy.values():
        if not isinstance(group, list):
            continue
        for item in group:
            if isinstance(item, dict) and item.get("id") and item.get("prompt"):
                out[str(item["id"])] = str(item["prompt"])
    return out


@lru_cache(maxsize=1)
def _load_director_personas() -> dict[str, dict[str, Any]]:
    data = _read_json(RESEARCH / "director_bible_v1.json")
    return {p["id"]: p for p in data.get("personas") or [] if p.get("id")}


@lru_cache(maxsize=1)
def _load_pacing_signatures() -> dict[str, dict[str, Any]]:
    data = _read_json(RESEARCH / "pacing_signatures_v1.json")
    return {p["id"]: p for p in data.get("pacing_signatures") or [] if p.get("id")}


@lru_cache(maxsize=1)
def _pacing_chain_prompt() -> str:
    data = _read_json(RESEARCH / "pacing_signatures_v1.json")
    return str(data.get("chain_pacing_prompt") or "").strip()


def _sonic_chain_rule() -> str:
    return str(_load_sonic_doc().get("_chain_rule") or "").strip()


def native_av_enabled(
    script: dict[str, Any] | None,
    shot: dict[str, Any] | None = None,
) -> bool:
    """True when Grok native synchronized audio (dialogue/SFX/ambient) should be injected."""
    shot = shot or {}
    cfg = (script or {}).get("config") or {}
    mods = shot.get("modifiers") if isinstance(shot.get("modifiers"), dict) else {}
    bb = shot.get("barebones") if isinstance(shot.get("barebones"), dict) else {}
    audio = bb.get("audio") if isinstance(bb.get("audio"), dict) else {}

    for obj in (shot, cfg, mods, audio):
        if isinstance(obj, dict) and obj.get("native_av") is True:
            return True
    if shot.get("native_av") is False:
        return False
    if cfg.get("native_av") is False:
        return False
    if shot.get("narration") is False or cfg.get("narration") is False:
        return False
    return True


def _block_keys_for_shot(shot: dict[str, Any]) -> list[str]:
    """Candidate block keys for style_blocks lookup (most specific first)."""
    keys: list[str] = []
    for raw in (
        shot.get("block"),
        shot.get("block_id"),
        shot.get("scene_block"),
    ):
        if raw is not None:
            s = str(raw).strip().lower()
            if s:
                keys.append(s)
                if s.isdigit():
                    keys.append(f"b{s.zfill(2)}")
                    keys.append(s.zfill(2))
                elif re.fullmatch(r"b\d+", s):
                    keys.append(s[1:].zfill(2))
                    keys.append(s[1:])
    sid = str(shot.get("id") or "")
    m = re.match(r"^(b\d+)", sid, re.I)
    if m:
        bk = m.group(1).lower()
        if bk not in keys:
            keys.append(bk)
        num = bk[1:]
        keys.append(num.zfill(2))
        keys.append(num)
    return keys


def _dict_field(block: dict[str, Any] | None, key: str) -> str | None:
    if not isinstance(block, dict):
        return None
    val = block.get(key)
    if val is None:
        return None
    s = str(val).strip()
    return s or None


def _merge_field(
    out: dict[str, str | None],
    field: str,
    value: str | None,
    source: str,
) -> None:
    if value and not out.get(field):
        out[field] = value
        out[f"_{field}_source"] = source  # type: ignore[literal-required]


def resolve_modifier_ids(
    script: dict[str, Any] | None,
    shot: dict[str, Any] | None,
    catalog: Any | None = None,
) -> dict[str, str | None]:
    """Return raw modifier IDs resolved from script + shot (no prompt text yet).

    If *catalog* is provided (a production_catalog.Catalog instance), any value
    that looks like @TYPE_NNN is resolved to its modifier slug before return.
    Existing string slugs pass through unchanged — fully backward-compatible.
    """
    script = script or {}
    shot = shot or {}
    cfg = script.get("config") or {}
    mods_shot = shot.get("modifiers") if isinstance(shot.get("modifiers"), dict) else {}
    bb = shot.get("barebones") if isinstance(shot.get("barebones"), dict) else {}
    bb_audio = bb.get("audio") if isinstance(bb.get("audio"), dict) else {}

    resolved: dict[str, str | None] = {
        "director_persona_id": None,
        "pacing_dna_tag": None,
        "style_dna_tag": None,
        "audio_dna_tag": None,
        "audio_dna_combo": None,
        "music_dna_tag": None,
        "music_dna_combo": None,
        "language": None,
        "emotional_beat": None,
        "anim_style_id": None,
        "camera_move": None,
        "anti_generic_armor": None,
        "audio_chain_prompt_override": None,
        "music_chain_prompt_override": None,
    }
    audio_explicit = False
    combo_explicit = False

    # 1 — shot.modifiers
    _merge_field(resolved, "director_persona_id", _dict_field(mods_shot, "director_persona_id"), "shot.modifiers")
    _merge_field(resolved, "pacing_dna_tag", _dict_field(mods_shot, "pacing_dna_tag"), "shot.modifiers")
    _merge_field(resolved, "style_dna_tag", _dict_field(mods_shot, "style_dna_tag"), "shot.modifiers")
    _merge_field(resolved, "audio_dna_tag", _dict_field(mods_shot, "audio_dna_tag"), "shot.modifiers")
    _merge_field(resolved, "audio_dna_combo", _dict_field(mods_shot, "audio_dna_combo"), "shot.modifiers")
    _merge_field(resolved, "music_dna_tag", _dict_field(mods_shot, "music_dna_tag"), "shot.modifiers")
    _merge_field(resolved, "music_dna_combo", _dict_field(mods_shot, "music_dna_combo"), "shot.modifiers")
    _merge_field(resolved, "language", _dict_field(mods_shot, "language"), "shot.modifiers")
    _merge_field(resolved, "emotional_beat", _dict_field(mods_shot, "emotional_beat"), "shot.modifiers")
    if resolved.get("audio_dna_tag") and resolved.get("_audio_dna_tag_source") == "shot.modifiers":
        audio_explicit = True
    if resolved.get("audio_dna_combo") and resolved.get("_audio_dna_combo_source") == "shot.modifiers":
        combo_explicit = True
    _merge_field(resolved, "anim_style_id", _dict_field(mods_shot, "anim_style_id"), "shot.modifiers")
    _merge_field(resolved, "camera_move", _dict_field(mods_shot, "camera_move"), "shot.modifiers")
    armor = mods_shot.get("anti_generic_armor")
    if armor is True:
        _merge_field(resolved, "anti_generic_armor", ANTI_GENERIC_ARMOR_DEFAULT, "shot.modifiers")
    elif isinstance(armor, str) and armor.strip():
        _merge_field(resolved, "anti_generic_armor", armor.strip(), "shot.modifiers")

    # 2 — barebones inline tags
    _merge_field(resolved, "style_dna_tag", _dict_field(bb, "style_dna_tag"), "shot.barebones")
    _merge_field(resolved, "audio_dna_tag", _dict_field(bb_audio, "dna_tag"), "shot.barebones.audio")
    _merge_field(resolved, "audio_dna_combo", _dict_field(bb_audio, "dna_combo"), "shot.barebones.audio")
    bb_music = bb.get("music") if isinstance(bb.get("music"), dict) else {}
    _merge_field(resolved, "music_dna_tag", _dict_field(bb_music, "dna_tag"), "shot.barebones.music")
    _merge_field(resolved, "music_dna_combo", _dict_field(bb_music, "dna_combo"), "shot.barebones.music")
    bb_dialogue = bb.get("dialogue") if isinstance(bb.get("dialogue"), dict) else {}
    _merge_field(resolved, "language", _dict_field(bb_dialogue, "language"), "shot.barebones.dialogue")
    _merge_field(resolved, "emotional_beat", _dict_field(bb_audio, "emotional_beat"), "shot.barebones.audio")
    _merge_field(resolved, "emotional_beat", _dict_field(bb, "emotional_beat"), "shot.barebones")
    if resolved.get("audio_dna_tag") and str(resolved.get("_audio_dna_tag_source", "")).startswith("shot."):
        audio_explicit = True
    if resolved.get("audio_dna_combo") and str(resolved.get("_audio_dna_combo_source", "")).startswith("shot."):
        combo_explicit = True
    chain_ov = bb_audio.get("chain_prompt")
    if isinstance(chain_ov, str) and chain_ov.strip():
        resolved["audio_chain_prompt_override"] = chain_ov.strip()
    music_chain_ov = bb_music.get("chain_prompt")
    if isinstance(music_chain_ov, str) and music_chain_ov.strip():
        resolved["music_chain_prompt_override"] = music_chain_ov.strip()

    # 3 — top-level shot fields
    _merge_field(resolved, "director_persona_id", _dict_field(shot, "director_persona_id"), "shot")
    _merge_field(resolved, "pacing_dna_tag", _dict_field(shot, "pacing_dna_tag"), "shot")
    _merge_field(resolved, "style_dna_tag", _dict_field(shot, "style_dna_tag"), "shot")
    _merge_field(resolved, "audio_dna_tag", _dict_field(shot, "audio_dna_tag"), "shot")
    _merge_field(resolved, "audio_dna_combo", _dict_field(shot, "audio_dna_combo"), "shot")
    _merge_field(resolved, "music_dna_tag", _dict_field(shot, "music_dna_tag"), "shot")
    _merge_field(resolved, "music_dna_combo", _dict_field(shot, "music_dna_combo"), "shot")
    _merge_field(resolved, "language", _dict_field(shot, "language"), "shot")
    _merge_field(resolved, "emotional_beat", _dict_field(shot, "emotional_beat"), "shot")
    if resolved.get("audio_dna_tag") and resolved.get("_audio_dna_tag_source") == "shot":
        audio_explicit = True
    if resolved.get("audio_dna_combo") and resolved.get("_audio_dna_combo_source") == "shot":
        combo_explicit = True

    block_keys = _block_keys_for_shot(shot)

    def _apply_style_block(block: dict[str, Any] | None, source: str) -> None:
        if not isinstance(block, dict):
            return
        _merge_field(resolved, "director_persona_id", _dict_field(block, "director_persona_id"), source)
        _merge_field(resolved, "pacing_dna_tag", _dict_field(block, "pacing_dna_tag"), source)
        _merge_field(resolved, "style_dna_tag", _dict_field(block, "style_dna_tag"), source)
        _merge_field(resolved, "audio_dna_tag", _dict_field(block, "audio_dna_tag"), source)
        _merge_field(resolved, "audio_dna_combo", _dict_field(block, "audio_dna_combo"), source)
        _merge_field(resolved, "music_dna_tag", _dict_field(block, "music_dna_tag"), source)
        _merge_field(resolved, "music_dna_combo", _dict_field(block, "music_dna_combo"), source)
        _merge_field(resolved, "language", _dict_field(block, "language"), source)
        _merge_field(resolved, "emotional_beat", _dict_field(block, "emotional_beat"), source)
        _merge_field(resolved, "anim_style_id", _dict_field(block, "anim_style_id"), source)
        _merge_field(resolved, "camera_move", _dict_field(block, "camera_move"), source)
        if block.get("anti_generic_armor") is True:
            _merge_field(resolved, "anti_generic_armor", ANTI_GENERIC_ARMOR_DEFAULT, source)
        elif isinstance(block.get("anti_generic_armor"), str):
            _merge_field(resolved, "anti_generic_armor", str(block["anti_generic_armor"]).strip(), source)

    # 4 — config.style_blocks + pacing_blocks
    style_blocks = cfg.get("style_blocks") or {}
    if isinstance(style_blocks, dict):
        for bk in block_keys:
            _apply_style_block(style_blocks.get(bk), f"config.style_blocks.{bk}")
    pacing_blocks = cfg.get("pacing_blocks") or {}
    if isinstance(pacing_blocks, dict):
        for bk in block_keys:
            block = pacing_blocks.get(bk)
            if isinstance(block, dict):
                _merge_field(
                    resolved, "pacing_dna_tag", _dict_field(block, "pacing_dna_tag"),
                    f"config.pacing_blocks.{bk}",
                )
    music_blocks = cfg.get("music_blocks") or {}
    if isinstance(music_blocks, dict):
        for bk in block_keys:
            block = music_blocks.get(bk)
            if isinstance(block, dict):
                _merge_field(
                    resolved, "music_dna_tag", _dict_field(block, "music_dna_tag"),
                    f"config.music_blocks.{bk}",
                )
                _merge_field(
                    resolved, "music_dna_combo", _dict_field(block, "music_dna_combo"),
                    f"config.music_blocks.{bk}",
                )

    # 5 — script.style / general_style
    for root_key in ("style", "general_style"):
        root = script.get(root_key)
        if not isinstance(root, dict):
            continue
        blocks = root.get("blocks")
        if isinstance(blocks, dict):
            for bk in block_keys:
                _apply_style_block(blocks.get(bk), f"script.{root_key}.blocks.{bk}")
        _apply_style_block(root.get("default"), f"script.{root_key}.default")
        if not resolved["director_persona_id"]:
            _merge_field(
                resolved, "director_persona_id", _dict_field(root, "director_persona_id"), f"script.{root_key}",
            )
        if not resolved["pacing_dna_tag"]:
            _merge_field(resolved, "pacing_dna_tag", _dict_field(root, "pacing_dna_tag"), f"script.{root_key}")
        if not resolved["style_dna_tag"]:
            _merge_field(resolved, "style_dna_tag", _dict_field(root, "style_dna_tag"), f"script.{root_key}")
        if not resolved["audio_dna_tag"]:
            _merge_field(resolved, "audio_dna_tag", _dict_field(root, "audio_dna_tag"), f"script.{root_key}")
        if not resolved["audio_dna_combo"]:
            _merge_field(resolved, "audio_dna_combo", _dict_field(root, "audio_dna_combo"), f"script.{root_key}")
        if not resolved["music_dna_tag"]:
            _merge_field(resolved, "music_dna_tag", _dict_field(root, "music_dna_tag"), f"script.{root_key}")
        if not resolved["music_dna_combo"]:
            _merge_field(resolved, "music_dna_combo", _dict_field(root, "music_dna_combo"), f"script.{root_key}")
        if not resolved["language"]:
            _merge_field(resolved, "language", _dict_field(root, "language"), f"script.{root_key}")

    # 6 — branch_chain named blocks (kitchen, living_room, ...)
    branch_blocks = (cfg.get("branch_chain") or {}).get("blocks") or {}
    sid = str(shot.get("id") or "")
    if isinstance(branch_blocks, dict):
        for name, block in branch_blocks.items():
            if not isinstance(block, dict):
                continue
            shots_in = block.get("shots") or []
            if sid in shots_in:
                _apply_style_block(block, f"config.branch_chain.blocks.{name}")

    # 7 — config production defaults
    _merge_field(resolved, "director_persona_id", _dict_field(cfg, "director_persona_id"), "config")
    _merge_field(resolved, "pacing_dna_tag", _dict_field(cfg, "pacing_dna_tag"), "config")
    _merge_field(resolved, "style_dna_tag", _dict_field(cfg, "style_dna_tag"), "config")
    _merge_field(resolved, "audio_dna_tag", _dict_field(cfg, "audio_dna_tag"), "config")
    _merge_field(resolved, "audio_dna_combo", _dict_field(cfg, "audio_dna_combo"), "config")
    _merge_field(resolved, "music_dna_tag", _dict_field(cfg, "music_dna_tag"), "config")
    _merge_field(resolved, "music_dna_combo", _dict_field(cfg, "music_dna_combo"), "config")
    _merge_field(resolved, "language", _dict_field(cfg, "language"), "config")
    _merge_field(resolved, "emotional_beat", _dict_field(cfg, "emotional_beat"), "config")
    _merge_field(resolved, "anim_style_id", _dict_field(cfg, "anim_style_id"), "config")
    if cfg.get("anti_generic_armor") is True:
        _merge_field(resolved, "anti_generic_armor", ANTI_GENERIC_ARMOR_DEFAULT, "config")

    # 7b — language default fallback (en unless animation_default differs)
    if not resolved.get("language"):
        lang_defaults = _load_language_doc().get("language_defaults") or {}
        fmt = str(cfg.get("format") or "").lower()
        default_lang = (
            lang_defaults.get("animation_default")
            if fmt == "animation"
            else lang_defaults.get("default")
        )
        if default_lang:
            _merge_field(resolved, "language", default_lang, "language_defaults")

    # 8 — director persona fills unset modifier IDs (lowest priority)
    _apply_persona_defaults(resolved)

    # 9 — Randy Thom beat-first audio picker (overrides config/persona, not explicit shot audio)
    _apply_emotional_beat_picker(
        resolved,
        script,
        shot,
        cfg,
        audio_explicit=audio_explicit,
        combo_explicit=combo_explicit,
    )

    # 10 — @ID → slug translation (Oliver creative asset permanent IDs)
    _translate_creative_ids(resolved, catalog)

    # 11 — grade family for style-aware color QA (style first, frame second).
    # Explicit grade_family wins (shot → branch-chain block for this shot → config);
    # else derive from the fully-resolved style_dna_tag, then the director persona.
    # Unmapped → left unset (clinical-neutral, i.e. today's behavior).
    grade_fam = _dict_field(shot, "grade_family")
    if not grade_fam and isinstance(branch_blocks, dict):
        for _bname, _block in branch_blocks.items():
            if isinstance(_block, dict) and sid in (_block.get("shots") or []) and _block.get("grade_family"):
                grade_fam = str(_block["grade_family"]).strip()
                break
    if not grade_fam:
        grade_fam = _dict_field(cfg, "grade_family")
    if not grade_fam:
        grade_fam = resolve_grade_family(resolved.get("style_dna_tag"))
        if grade_fam == DEFAULT_GRADE_FAMILY and resolved.get("director_persona_id"):
            grade_fam = resolve_grade_family(resolved.get("director_persona_id"))
    if grade_fam and grade_fam != DEFAULT_GRADE_FAMILY:
        resolved["grade_family"] = grade_fam

    # 12 — documentary-host: flat prestige grade only (no cinematic DNA in API prompts).
    if _documentary_host_format(script):
        for field in (
            "director_persona_id",
            "style_dna_tag",
            "audio_dna_tag",
            "audio_dna_combo",
            "music_dna_tag",
            "music_dna_combo",
            "pacing_dna_tag",
            "anim_style_id",
            "anti_generic_armor",
        ):
            resolved[field] = None
            resolved.pop(f"_{field}_source", None)

    return resolved


def _documentary_host_format(script: dict[str, Any] | None) -> bool:
    script = script or {}
    fmt = str(
        script.get("format_id")
        or (script.get("intake") or {}).get("format_id")
        or ""
    ).strip()
    return fmt == "documentary-host"


def _normalize_beat_key(raw: str | None) -> str | None:
    if not raw:
        return None
    key = str(raw).strip().lower().replace(" ", "_").replace("-", "_")
    return key or None


def _apply_emotional_beat_picker(
    resolved: dict[str, str | None],
    script: dict[str, Any],
    shot: dict[str, Any],
    cfg: dict[str, Any],
    *,
    audio_explicit: bool,
    combo_explicit: bool,
) -> None:
    """Match audio_dna_tag to emotional beat (Randy Thom) when beat is set on shot."""
    beat = _normalize_beat_key(resolved.get("emotional_beat"))
    if not beat and cfg.get("audio_beat_picker"):
        bb = shot.get("barebones") if isinstance(shot.get("barebones"), dict) else {}
        for alt in (
            shot.get("narrative_beat"),
            shot.get("beat"),
            bb.get("beat"),
            bb.get("narrative_beat"),
        ):
            beat = _normalize_beat_key(str(alt) if alt is not None else None)
            if beat:
                resolved["emotional_beat"] = beat
                break
    if not beat:
        return

    beat_map = _load_emotional_beat_map()
    combo_map = _load_emotional_beat_combo_map()

    if not audio_explicit and beat in beat_map:
        resolved["audio_dna_tag"] = beat_map[beat]
        resolved["_audio_dna_tag_source"] = f"emotional_beat.{beat}"  # type: ignore[literal-required]

    if not combo_explicit and beat in combo_map:
        resolved["audio_dna_combo"] = combo_map[beat]
        resolved["_audio_dna_combo_source"] = f"emotional_beat.{beat}"  # type: ignore[literal-required]


def _apply_persona_defaults(resolved: dict[str, str | None]) -> None:
    pid = resolved.get("director_persona_id")
    if not pid:
        return
    persona = _load_director_personas().get(pid)
    if not persona:
        return
    for field, key in (
        ("style_dna_tag", "style_dna_tag"),
        ("audio_dna_tag", "audio_dna_tag"),
        ("audio_dna_combo", "audio_dna_combo"),
        ("music_dna_tag", "music_dna_tag"),
        ("music_dna_combo", "music_dna_combo"),
        ("pacing_dna_tag", "pacing_dna_tag"),
        ("anim_style_id", "anim_style_id"),
    ):
        if not resolved.get(field) and persona.get(key):
            resolved[field] = str(persona[key])
            resolved[f"_{field}_source"] = f"director_persona.{pid}"  # type: ignore[literal-required]
    if not resolved.get("anti_generic_armor") and persona.get("anti_generic_armor"):
        resolved["anti_generic_armor"] = ANTI_GENERIC_ARMOR_DEFAULT
        resolved["_anti_generic_armor_source"] = f"director_persona.{pid}"  # type: ignore[literal-required]


def shot_is_chain_continuation(script: dict[str, Any] | None, shot: dict[str, Any] | None) -> bool:
    """True when this shot should append sonic/visual chain prompts (extend / handoff)."""
    shot = shot or {}
    if shot.get("chain_continuation") is False:
        return False
    if shot.get("new_origin") is True:
        return False
    mods = shot.get("modifiers") if isinstance(shot.get("modifiers"), dict) else {}
    if mods.get("chain_audio") or mods.get("chain_visual"):
        return True
    if shot.get("chain_continuation") is True:
        return True
    if str(shot.get("block_part") or "").lower() in ("ext", "extension", "b02", "continue"):
        return True
    sid = str(shot.get("id") or "").lower()
    if "_ext" in sid or sid.endswith("_continue"):
        return True
    if shot.get("new_origin") is False:
        return True
    return False


def _lookup_visual(style_id: str | None) -> tuple[str | None, str | None]:
    if not style_id:
        return None, None
    if style_id.startswith("hybrid_"):
        entry = _load_hybrid_styles().get(style_id)
        if not entry:
            return None, None
        prompt = entry.get("prompt_seed") or entry.get("name") or ""
        move = entry.get("camera_move")
        move_desc = entry.get("camera_move_description") or ""
        cam = f"CAMERA MOVE [{move}]: {move_desc}" if move else None
        return (f"STYLE DNA [{style_id}]: {prompt}" if prompt else None, cam)
    if style_id.startswith("gameart_"):
        entry = _load_game_art_styles().get(style_id)
        if not entry:
            return None, None
        p = entry.get("prompt") or ""
        return (f"STYLE DNA [{style_id}]: {p}" if p else None, None)
    entry = _load_visual_styles().get(style_id)
    if entry:
        p = entry.get("prompt") or ""
        return (f"STYLE DNA [{style_id}]: {p}" if p else None, None)
    return None, None


def _lookup_anim(anim_id: str | None) -> str | None:
    if not anim_id:
        return None
    entry = _load_anim_styles().get(anim_id)
    if not entry:
        return None
    desc = entry.get("description") or entry.get("technique") or entry.get("name") or ""
    return f"ANIM STYLE [{anim_id}]: {desc}" if desc else None


def _with_chain_rule(text: str, *, chain: bool) -> str:
    rule = _sonic_chain_rule()
    if not chain or not rule or rule in text:
        return text
    return f"{rule} {text}"


def _audio_technique_suffix(entry: dict[str, Any] | None) -> str:
    if not entry:
        return ""
    ids = entry.get("techniques")
    if not isinstance(ids, list) or not ids:
        return ""
    taxonomy = _load_technique_taxonomy()
    clauses = [taxonomy[tid] for tid in ids if tid in taxonomy]
    return f" Techniques: {'; '.join(clauses)}." if clauses else ""


def _lookup_audio(
    audio_id: str | None,
    *,
    chain: bool,
    chain_override: str | None = None,
    combo_id: str | None = None,
) -> str | None:
    if chain_override:
        return _with_chain_rule(chain_override, chain=chain)
    if combo_id:
        combo = _load_audio_combos().get(combo_id)
        if combo:
            if chain and combo.get("chain_prompt"):
                return _with_chain_rule(str(combo["chain_prompt"]), chain=chain)
            desc = combo.get("description") or combo.get("label") or ""
            label = combo.get("label") or combo_id
            return f"SONIC DNA COMBO [{combo_id}] ({label}): {desc}" if desc else None
    if not audio_id:
        return None
    entry = _load_sonic_styles().get(audio_id)
    if not entry:
        return None
    tech = _audio_technique_suffix(entry)
    if chain and entry.get("chain_prompt"):
        return _with_chain_rule(f"{entry['chain_prompt']}{tech}", chain=chain)
    desc = entry.get("description") or entry.get("name") or ""
    return f"SONIC DNA [{audio_id}]: {desc}{tech}" if desc else None


def _with_music_chain_rule(text: str, *, chain: bool) -> str:
    rule = _music_chain_rule()
    if not chain or not rule or rule in text:
        return text
    return f"{rule} {text}"


def _lookup_music(
    music_id: str | None,
    *,
    chain: bool,
    chain_override: str | None = None,
    combo_id: str | None = None,
) -> str | None:
    """Resolve music_dna_tag / music_dna_combo to a prompt clause."""
    if chain_override:
        return _with_music_chain_rule(chain_override, chain=chain)
    if combo_id:
        combo = _load_music_combos().get(combo_id)
        if combo:
            if chain and combo.get("chain_prompt"):
                return _with_music_chain_rule(str(combo["chain_prompt"]), chain=chain)
            desc = combo.get("description") or combo.get("label") or ""
            label = combo.get("label") or combo_id
            return f"MUSIC DNA COMBO [{combo_id}] ({label}): {desc}" if desc else None
    if not music_id:
        return None
    entry = _load_music_styles().get(music_id)
    if not entry:
        return None
    if chain and entry.get("chain_prompt"):
        return _with_music_chain_rule(str(entry["chain_prompt"]), chain=chain)
    desc = entry.get("description") or entry.get("name") or ""
    return f"MUSIC DNA [{music_id}]: {desc}" if desc else None


def _pronunciation_guidance(slug: str) -> str:
    """Optional phonology/lip-sync clause from top-10 language data."""
    try:
        from top10_languages import pronunciation_guidance_for_prompt
        guidance = pronunciation_guidance_for_prompt(slug)
        return f" {guidance}" if guidance else ""
    except (ImportError, Exception):
        return ""


def language_clause_for_profile(lang_id: str | None) -> str | None:
    """Public wrapper for interpreter / render pipeline bridge."""
    return _lookup_language(lang_id)


def _lookup_language(lang_id: str | None) -> str | None:
    """Resolve language profile ID to a production-level prompt clause.

    Composes two layers:
    1. Production clause from language_profiles_v1.json (code-switching, bilingual framing)
    2. Pronunciation/lip-sync guidance from top10_languages.py (phonology, Grok AV hints)
    """
    if not lang_id:
        return None
    profiles = _load_language_profiles()
    entry = profiles.get(lang_id)
    if not entry:
        return None
    clause = entry.get("production_clause") or ""
    if not clause:
        return None
    # For primary (single-language) profiles, append pronunciation guidance if available
    bcp = entry.get("bcp47") or ""
    slug = bcp.split("-")[0] if "-" in bcp else bcp  # de-BY → de
    # Map BCP47 codes to top-10 slugs where they differ
    bcp_to_slug = {"en": "english", "de": "german", "yi": "yiddish",
                   "zh": "mandarin", "hi": "hindi", "es": "spanish",
                   "fr": "french", "ar": "arabic", "bn": "bengali",
                   "pt": "portuguese", "ru": "russian", "ja": "japanese",
                   "id": "indonesian", "ur": "urdu"}
    pron = ""
    if entry.get("tier") == "primary":
        top10_slug = bcp_to_slug.get(slug, slug)
        pron = _pronunciation_guidance(top10_slug)
        # Fallback: voice_note covers languages not in top-10 (de, yi)
        if not pron:
            voice = entry.get("voice_note") or ""
            if voice:
                pron = f" {voice}"
    return f"LANGUAGE [{lang_id}]: {clause}{pron}"


def _lookup_pacing(pacing_id: str | None, *, chain: bool) -> str | None:
    if not pacing_id:
        return None
    entry = _load_pacing_signatures().get(pacing_id)
    if entry and entry.get("prompt"):
        return str(entry["prompt"])
    if chain:
        chain_p = _pacing_chain_prompt()
        return chain_p if chain_p else None
    return None


def _persona_clauses(
    persona_id: str | None,
    *,
    chain: bool,
) -> tuple[str | None, str | None, str | None, str | None]:
    if not persona_id:
        return None, None, None, None
    persona = _load_director_personas().get(persona_id)
    if not persona:
        return None, None, None, None
    name = persona.get("name") or persona_id
    lead = persona.get("persona_lead") or ""
    persona_clause = f"DIRECTOR PERSONA [{persona_id}] ({name}): {lead}" if lead else None
    perf = persona.get("performance")
    performance_clause = f"PERFORMANCE [{name}]: {perf}" if perf else None
    edit = persona.get("editing")
    editing_clause = f"EDITING [{name}]: {edit}" if edit else None
    block_cont = None
    if chain and persona.get("block_continue"):
        block_cont = str(persona["block_continue"])
        sound_addon = persona.get("sound_addon")
        if sound_addon:
            block_cont = f"{block_cont} {sound_addon}"
    return persona_clause, performance_clause, editing_clause, block_cont


def resolve_style_modifiers(
    script: dict[str, Any] | None,
    shot: dict[str, Any] | None,
    *,
    chain_continuation: bool | None = None,
    include_audio: bool = True,
    catalog: Any | None = None,
) -> ResolvedModifiers:
    """Resolve IDs to prompt clauses for compile_barebones_prose_prompt.

    If *catalog* is provided, @TYPE_NNN creative asset IDs are resolved to
    slugs before modifier lookup. Existing string slugs work unchanged.
    """
    ids = resolve_modifier_ids(script, shot, catalog=catalog)
    chain = (
        shot_is_chain_continuation(script, shot)
        if chain_continuation is None
        else chain_continuation
    )

    persona_clause, performance_clause, editing_clause, block_continue = _persona_clauses(
        ids.get("director_persona_id"), chain=chain,
    )
    pacing_clause = _lookup_pacing(ids.get("pacing_dna_tag"), chain=chain)

    visual, camera = _lookup_visual(ids.get("style_dna_tag"))
    if ids.get("camera_move") and not camera:
        camera = f"CAMERA MOVE: {ids['camera_move']}"

    anim = _lookup_anim(ids.get("anim_style_id"))
    audio = (
        _lookup_audio(
            ids.get("audio_dna_tag"),
            chain=chain,
            chain_override=ids.get("audio_chain_prompt_override"),
            combo_id=ids.get("audio_dna_combo"),
        )
        if include_audio
        else None
    )
    music = (
        _lookup_music(
            ids.get("music_dna_tag"),
            chain=chain,
            chain_override=ids.get("music_chain_prompt_override"),
            combo_id=ids.get("music_dna_combo"),
        )
        if include_audio
        else None
    )

    lang = _lookup_language(ids.get("language"))

    armor = ids.get("anti_generic_armor")
    armor_clause = f"ANTI-GENERIC: {armor}" if armor else None

    sources = {
        k[1:].replace("_source", ""): v
        for k, v in ids.items()
        if k.startswith("_") and k.endswith("_source") and isinstance(v, str)
    }
    if ids.get("director_persona_id"):
        sources["director_persona_id"] = ids["director_persona_id"]

    return ResolvedModifiers(
        director_persona_id=ids.get("director_persona_id"),
        pacing_dna_tag=ids.get("pacing_dna_tag"),
        style_dna_tag=ids.get("style_dna_tag"),
        grade_family=ids.get("grade_family"),
        audio_dna_tag=ids.get("audio_dna_tag"),
        audio_dna_combo=ids.get("audio_dna_combo"),
        music_dna_tag=ids.get("music_dna_tag"),
        music_dna_combo=ids.get("music_dna_combo"),
        language=ids.get("language"),
        emotional_beat=ids.get("emotional_beat"),
        anim_style_id=ids.get("anim_style_id"),
        persona_clause=persona_clause,
        performance_clause=performance_clause,
        editing_clause=editing_clause,
        pacing_clause=pacing_clause,
        block_continue_clause=block_continue,
        visual_clause=visual,
        camera_move_clause=camera,
        anim_clause=anim,
        audio_clause=audio,
        music_clause=music,
        language_clause=lang,
        anti_generic_clause=armor_clause,
        source=sources,
    )


def modifier_prompt_clauses(
    script: dict[str, Any] | None,
    shot: dict[str, Any] | None,
    *,
    chain_continuation: bool | None = None,
    include_audio: bool = True,
) -> list[str]:
    """Ordered clauses to append during barebones prose assembly."""
    resolved = resolve_style_modifiers(
        script,
        shot,
        chain_continuation=chain_continuation,
        include_audio=include_audio,
    )
    return modifier_clauses_from_resolved(resolved)


def modifier_clauses_from_resolved(resolved: ResolvedModifiers) -> list[str]:
    """Ordered prompt clauses for barebones compile."""
    clauses: list[str] = []
    for clause in (
        resolved.language_clause,
        resolved.persona_clause,
        resolved.block_continue_clause,
        resolved.performance_clause,
        resolved.pacing_clause,
        resolved.editing_clause,
        resolved.visual_clause,
        resolved.camera_move_clause,
        resolved.anim_clause,
        resolved.audio_clause,
        resolved.music_clause,
        resolved.anti_generic_clause,
    ):
        if clause and clause not in clauses:
            clauses.append(clause)
    return clauses


def log_resolved_modifiers(
    shot_id: str,
    resolved: ResolvedModifiers,
    log_fn: Any,
) -> None:
    """Emit one-line diagnostic for render logs."""
    if not any(
        (
            resolved.director_persona_id,
            resolved.style_dna_tag,
            resolved.audio_dna_tag,
            resolved.music_dna_tag,
            resolved.pacing_dna_tag,
            resolved.anim_style_id,
            resolved.language,
        )
    ):
        return
    log_fn(
        f"[style_dna] {shot_id}: director={resolved.director_persona_id or '-'} "
        f"visual={resolved.style_dna_tag or '-'} audio={resolved.audio_dna_tag or '-'} "
        f"music={resolved.music_dna_tag or '-'} lang={resolved.language or '-'} "
        f"pacing={resolved.pacing_dna_tag or '-'} beat={resolved.emotional_beat or '-'} "
        f"combo={resolved.audio_dna_combo or '-'} music_combo={resolved.music_dna_combo or '-'} "
        f"anim={resolved.anim_style_id or '-'} sources={resolved.source}"
    )