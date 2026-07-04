#!/usr/bin/env python3
"""screenplay_ingest.py — Parse screenplay files into render_longform.py-compatible JSON.

Phase B format parser. Reads PDF, TXT, or Fountain screenplays and emits
JSON conforming to screenplay_ingest_schema_v1.json.

Usage:
    python screenplay_ingest.py screenplay.fountain -o script.json
    python screenplay_ingest.py screenplay.pdf --format-id movies -o script.json
    python screenplay_ingest.py screenplay.txt --title "My Film" -o script.json
"""

import argparse
import json
import os
import re
import sys
from pathlib import Path

# ─────────────────────────── element types ────────────────────────────

SCENE_HEADING   = "scene_heading"
ACTION          = "action"
CHARACTER       = "character"
DIALOGUE        = "dialogue"
PARENTHETICAL   = "parenthetical"
TRANSITION      = "transition"
CAMERA          = "camera"

# ─────────────────────────── patterns ─────────────────────────────────

_SCENE_RE = re.compile(
    r"^(INT\.|EXT\.|INT\.\s*/\s*EXT\.|I/E\.)\s+.+", re.IGNORECASE
)
_TRANSITION_RE = re.compile(
    r"^(CUT TO:|DISSOLVE TO:|FADE IN[.:]|FADE OUT[.:]|FADE TO BLACK[.:]?"
    r"|SMASH CUT TO:|MATCH CUT TO:|JUMP CUT TO:|WIPE TO:|IRIS IN[.:]"
    r"|IRIS OUT[.:]|FADE TO:)\s*$",
    re.IGNORECASE,
)
_FORCED_TRANSITION_RE = re.compile(r"^>\s*.+TO:$")
_CHAR_RE = re.compile(r"^[A-Z][A-Z\s\d.'\-]+(\s*\(.*?\))?\s*$")
_PAREN_RE = re.compile(r"^\(.*\)$")
_CAMERA_RE = re.compile(
    r"^(ANGLE ON|PAN TO|DOLLY|CRANE|STEADICAM|CLOSE ON|WIDE ON|TRACKING"
    r"|POV\b|INSERT\b|CLOSE\s*UP|MEDIUM\s*SHOT|WIDE\s*SHOT|TWO\s*SHOT"
    r"|OVER\s*THE\s*SHOULDER|ECU\b|CU\b|MS\b|WS\b|MCU\b|MLS\b)",
    re.IGNORECASE,
)

# Words that look like character names but aren't
_NOT_CHARACTERS = {
    "FADE IN", "FADE OUT", "FADE TO BLACK", "CUT TO", "DISSOLVE TO",
    "THE END", "CONTINUED", "MORE", "CONT'D", "INTERCUT",
    "FLASHBACK", "END FLASHBACK", "MONTAGE", "END MONTAGE",
    "SUPER", "TITLE", "CHYRON", "CARD", "SERIES OF SHOTS",
    "BEGIN", "END", "BACK TO", "LATER", "RESUME",
}

# Duration estimation constants (from schema contract)
_WPS = 2.5           # words per second (dialogue @ ~150 wpm)
_ACTION_LINE_S = 3   # seconds per action line
_MIN_SHOT_S = 5
_MAX_SHOT_S = 15

# ─────────────────────────── data classes ─────────────────────────────

class Element:
    __slots__ = ("type", "text", "line", "meta")

    def __init__(self, etype, text, line=0, meta=None):
        self.type = etype
        self.text = text
        self.line = line
        self.meta = meta or {}

    def __repr__(self):
        return f"<{self.type}: {self.text[:40]}>"


# ─────────────────────────── file readers ─────────────────────────────

def _read_pdf(path):
    """Extract lines from PDF screenplay. Requires pdfplumber."""
    try:
        import pdfplumber
    except ImportError:
        print(
            "[screenplay_ingest] ERROR: pdfplumber not installed.\n"
            "  Install with: pip install pdfplumber\n"
            "  Or convert your PDF to .txt first.",
            file=sys.stderr,
        )
        sys.exit(1)
    lines = []
    with pdfplumber.open(path) as pdf:
        for page in pdf.pages:
            text = page.extract_text()
            if text:
                lines.extend(text.splitlines())
    return lines


def _read_fountain(path):
    """Read .fountain file, strip title page and boneyard/notes."""
    raw = Path(path).read_text(encoding="utf-8", errors="replace")

    # Strip title page (key: value pairs at top, ended by blank line)
    title_meta = {}
    if re.match(r"^[A-Za-z ]+:", raw):
        parts = re.split(r"\n\s*\n", raw, maxsplit=1)
        if len(parts) == 2:
            header, raw = parts
            for m in re.finditer(r"^([A-Za-z ]+):\s*(.+)$", header, re.MULTILINE):
                title_meta[m.group(1).strip().lower()] = m.group(2).strip()

    # Strip boneyard /* ... */
    raw = re.sub(r"/\*.*?\*/", "", raw, flags=re.DOTALL)
    # Strip notes [[ ... ]]
    raw = re.sub(r"\[\[.*?\]\]", "", raw, flags=re.DOTALL)
    # Strip section/synopsis markers (# and =)
    lines = []
    for line in raw.splitlines():
        stripped = line.strip()
        if stripped.startswith("#") or stripped.startswith("="):
            continue
        # Forced scene heading: leading .
        if stripped.startswith(".") and not stripped.startswith(".."):
            lines.append(stripped[1:])
            continue
        # Forced character: leading @
        if stripped.startswith("@"):
            lines.append(stripped[1:].upper())
            continue
        # Forced transition: leading >  (but not centered >text<)
        if stripped.startswith(">") and not stripped.endswith("<"):
            lines.append(stripped[1:].strip())
            continue
        lines.append(line)

    return lines, title_meta


def _read_txt(path):
    """Read plain text screenplay."""
    raw = Path(path).read_text(encoding="utf-8", errors="replace")
    return raw.splitlines()


def read_screenplay(path):
    """Dispatch to format-specific reader. Returns (lines, title_meta)."""
    ext = Path(path).suffix.lower()
    if ext == ".pdf":
        return _read_pdf(path), {}
    elif ext in (".fountain", ".ftn"):
        return _read_fountain(path)
    elif ext in (".txt", ".text", ""):
        return _read_txt(path), {}
    else:
        print(f"[screenplay_ingest] WARNING: unknown extension '{ext}', treating as .txt", file=sys.stderr)
        return _read_txt(path), {}


# ─────────────────────────── line classifier ──────────────────────────

def classify_lines(lines):
    """Classify raw text lines into screenplay Elements."""
    elements = []
    i = 0
    in_dialogue = False
    current_char = None

    while i < len(lines):
        raw = lines[i].rstrip("\r\n")
        stripped = raw.strip()

        # Blank line — end dialogue block
        if not stripped:
            in_dialogue = False
            current_char = None
            i += 1
            continue

        # Scene heading
        if _SCENE_RE.match(stripped):
            in_dialogue = False
            current_char = None
            elements.append(Element(SCENE_HEADING, stripped, i))
            i += 1
            continue

        # Transition
        if _TRANSITION_RE.match(stripped) or _FORCED_TRANSITION_RE.match(stripped):
            in_dialogue = False
            current_char = None
            elements.append(Element(TRANSITION, stripped, i))
            i += 1
            continue

        # Camera direction (outside dialogue)
        if not in_dialogue and _CAMERA_RE.match(stripped):
            elements.append(Element(CAMERA, stripped, i))
            i += 1
            continue

        # Character cue — ALL CAPS, < 60 chars, not a known non-character
        base_name = re.sub(r"\s*\(.*?\)\s*$", "", stripped).strip()
        if (
            _CHAR_RE.match(stripped)
            and not _SCENE_RE.match(stripped)
            and not _TRANSITION_RE.match(stripped)
            and len(stripped) < 60
            and base_name.upper() not in _NOT_CHARACTERS
            and not stripped.startswith("(")
        ):
            # Peek ahead: next non-blank line should be dialogue or parenthetical
            j = i + 1
            while j < len(lines) and not lines[j].strip():
                j += 1
            if j < len(lines):
                nxt = lines[j].strip()
                if nxt and (
                    _PAREN_RE.match(nxt)
                    or (
                        not _CHAR_RE.match(nxt)
                        and not _SCENE_RE.match(nxt)
                        and not _TRANSITION_RE.match(nxt)
                    )
                ):
                    ext_match = re.search(r"\((.*?)\)", stripped)
                    meta = {}
                    if ext_match:
                        meta["extension"] = ext_match.group(1).strip()
                    elements.append(Element(CHARACTER, base_name, i, meta))
                    current_char = base_name
                    in_dialogue = True
                    i += 1
                    continue

        # Parenthetical inside dialogue
        if in_dialogue and _PAREN_RE.match(stripped):
            elements.append(
                Element(PARENTHETICAL, stripped, i, {"character": current_char})
            )
            i += 1
            continue

        # Dialogue line
        if in_dialogue and current_char:
            elements.append(
                Element(DIALOGUE, stripped, i, {"character": current_char})
            )
            i += 1
            continue

        # Default: action
        elements.append(Element(ACTION, stripped, i))
        i += 1

    return elements


# ─────────────────────────── scene grouping ───────────────────────────

def group_into_scenes(elements):
    """Split element list at scene headings → list of (heading_text, [elements])."""
    scenes = []
    current_heading = None
    current_elems = []

    for el in elements:
        if el.type == SCENE_HEADING:
            if current_heading is not None or current_elems:
                scenes.append((current_heading, current_elems))
            current_heading = el.text
            current_elems = []
        else:
            current_elems.append(el)

    # Final scene
    if current_heading is not None or current_elems:
        scenes.append((current_heading, current_elems))

    return scenes


# ─────────────────────────── shot builder ─────────────────────────────

def _estimate_duration(action_text, speech_text):
    """Estimate shot duration in seconds from content."""
    dur = 0.0
    if speech_text:
        words = len(speech_text.split())
        dur += words / _WPS
    if action_text:
        action_lines = [l for l in action_text.strip().splitlines() if l.strip()]
        dur += len(action_lines) * _ACTION_LINE_S
    # If both are empty, minimum
    dur = max(dur, _MIN_SHOT_S)
    return dur


def _slugify(text):
    """Create a URL-safe slug from text."""
    s = text.lower()
    s = re.sub(r"[^a-z0-9\s]", "", s)
    s = re.sub(r"\s+", "_", s.strip())
    return s[:40] or "scene"


def _map_camera_to_modifier(camera_text):
    """Map screenplay camera direction to modifiers.camera_move value."""
    ct = camera_text.upper()
    mapping = {
        "PAN": "pan",
        "DOLLY": "dolly_in",
        "CRANE": "crane_up",
        "STEADICAM": "steadicam",
        "TRACKING": "tracking",
        "POV": "pov",
    }
    for key, val in mapping.items():
        if key in ct:
            return val
    return None


def _extract_voice_direction(parenthetical_text):
    """Extract voice/performance direction from parenthetical."""
    # Strip outer parens
    inner = parenthetical_text.strip("()")
    # Language detection
    lang_match = re.search(r"in\s+([\w]+)", inner, re.IGNORECASE)
    lang = None
    if lang_match:
        lang_name = lang_match.group(1).lower()
        lang_map = {
            "french": "fr", "spanish": "es", "german": "de",
            "italian": "it", "japanese": "ja", "mandarin": "zh",
            "russian": "ru", "portuguese": "pt", "arabic": "ar",
            "korean": "ko", "english": "en",
        }
        lang = lang_map.get(lang_name)
    return inner, lang


def build_shots(scenes, characters_seen):
    """Convert grouped scenes into shot dicts conforming to schema."""
    shots = []
    shot_num = 1
    t_cursor = 0

    for heading, elems in scenes:
        # Accumulate per-scene content
        action_parts = []
        dialogue_blocks = []     # list of (character, speech, voice_dir, lang)
        camera_move = None
        current_dialogue_char = None
        current_speech = []
        current_voice_dir = None
        current_lang = None

        def _flush_dialogue():
            nonlocal current_dialogue_char, current_speech, current_voice_dir, current_lang
            if current_dialogue_char and current_speech:
                dialogue_blocks.append((
                    current_dialogue_char,
                    " ".join(current_speech),
                    current_voice_dir,
                    current_lang,
                ))
            current_dialogue_char = None
            current_speech = []
            current_voice_dir = None
            current_lang = None

        for el in elems:
            if el.type == ACTION:
                _flush_dialogue()
                action_parts.append(el.text)

            elif el.type == CHARACTER:
                _flush_dialogue()
                current_dialogue_char = el.text
                if el.text not in characters_seen:
                    characters_seen[el.text] = {"first_scene": heading}

            elif el.type == PARENTHETICAL:
                direction, lang = _extract_voice_direction(el.text)
                current_voice_dir = direction
                if lang:
                    current_lang = lang

            elif el.type == DIALOGUE:
                current_speech.append(el.text)

            elif el.type == CAMERA:
                cam = _map_camera_to_modifier(el.text)
                if cam:
                    camera_move = cam
                action_parts.append(el.text)

            elif el.type == TRANSITION:
                _flush_dialogue()
                # Transitions are shot boundaries — handled by scene grouping

        _flush_dialogue()

        # Build video_prompt from heading + action
        heading_desc = heading or ""
        action_text = "\n".join(action_parts)
        visual = []
        if heading_desc:
            # Parse INT/EXT + location + time
            visual.append(heading_desc.rstrip("."))
        if action_text.strip():
            visual.append(action_text.strip())
        video_prompt_base = ". ".join(visual) if visual else heading_desc

        # Decide how many shots this scene needs
        # Combine all dialogue for duration estimate
        all_speech = " ".join(d[1] for d in dialogue_blocks)
        total_dur = _estimate_duration(action_text, all_speech)

        if not dialogue_blocks:
            # Pure visual scene — one shot
            dur = min(max(int(total_dur), _MIN_SHOT_S), _MAX_SHOT_S)
            slug = f"{shot_num:02d}_{_slugify(heading_desc)}"
            role = "broll" if not heading_desc else "insert"
            shot = {
                "id": slug,
                "duration": dur,
                "t_start": t_cursor,
                "t_end": t_cursor + dur,
                "role": role,
                "video_prompt": video_prompt_base,
                "speech_text": None,
            }
            if camera_move:
                shot["modifiers"] = {"camera_move": camera_move}
            shots.append(shot)
            t_cursor += dur
            shot_num += 1

        else:
            # Dialogue scene — one shot per dialogue block (or merge short ones)
            # First shot gets the establishing visual
            for di, (char, speech, voice_dir, lang) in enumerate(dialogue_blocks):
                word_count = len(speech.split())
                speech_dur = max(int(word_count / _WPS), _MIN_SHOT_S)
                if di == 0:
                    speech_dur = max(speech_dur, _MIN_SHOT_S)

                dur = min(speech_dur, _MAX_SHOT_S)
                char_slug = _slugify(char)
                desc_slug = _slugify(heading_desc) if heading_desc else "scene"
                slug = f"{shot_num:02d}_{desc_slug}_{char_slug}"[:50]

                # Build per-shot visual
                if di == 0 and video_prompt_base:
                    vp = video_prompt_base + f" {char} speaks."
                else:
                    loc_hint = heading_desc.split(" - ")[0] if heading_desc and " - " in heading_desc else (heading_desc or "same location")
                    vp = f"{loc_hint}. {char} speaks."
                    if voice_dir:
                        vp += f" ({voice_dir})"

                shot = {
                    "id": slug,
                    "duration": dur,
                    "t_start": t_cursor,
                    "t_end": t_cursor + dur,
                    "role": "host",
                    "video_prompt": vp,
                    "speech_text": speech,
                }
                if lang:
                    shot["speech_lang"] = lang
                if di == 0 and camera_move:
                    shot["modifiers"] = {"camera_move": camera_move}

                shots.append(shot)
                t_cursor += dur
                shot_num += 1

    return shots


# ─────────────────────────── schema assembly ──────────────────────────

def _classify_format(elements, title):
    """Heuristic format_id classification."""
    char_count = sum(1 for e in elements if e.type == CHARACTER)
    action_count = sum(1 for e in elements if e.type == ACTION)
    scene_count = sum(1 for e in elements if e.type == SCENE_HEADING)
    dialogue_count = sum(1 for e in elements if e.type == DIALOGUE)

    if dialogue_count == 0 and action_count > 5:
        return "science-pure-visual"

    # Many characters + many scenes = movie/narrative
    unique_chars = set()
    for e in elements:
        if e.type == CHARACTER:
            unique_chars.add(e.text)

    if len(unique_chars) >= 5 and scene_count >= 10:
        return "movies"
    if len(unique_chars) >= 3:
        return "narrative-short-film"
    if len(unique_chars) == 1 and dialogue_count > action_count:
        return "documentary-host"

    return "narrative-short-film"


def assemble_script(shots, elements, title, format_id, title_meta, characters):
    """Build the final JSON dict conforming to schema contract."""
    slug = _slugify(title) + "_v1"
    total_seconds = shots[-1]["t_end"] if shots else 0

    if not format_id:
        format_id = _classify_format(elements, title)

    # Determine primary character for intake
    char_counts = {}
    for e in elements:
        if e.type == DIALOGUE:
            c = e.meta.get("character", "")
            char_counts[c] = char_counts.get(c, 0) + 1
    protagonist = max(char_counts, key=char_counts.get) if char_counts else None

    # Primary location
    first_heading = None
    for e in elements:
        if e.type == SCENE_HEADING:
            first_heading = e.text
            break

    # Writer from title_meta (Fountain)
    writer = title_meta.get("author", title_meta.get("credit", "Unknown"))

    script = {
        "slug": slug,
        "title": title,
        "format_id": format_id,
        "target_seconds": total_seconds,
        "concept": title_meta.get("notes", None),
        "intake": {
            "format_id": format_id,
            "actor_id": protagonist,
            "set_id": first_heading,
            "style_id": None,
            "source": "screenplay_ingest.py",
        },
        "config": {
            "model_video": "grok-imagine-video-1.5",
            "resolution": "720p",
            "aspect_ratio": "16:9",
            "prompt_mode": "seamless",
            "voice_suffix": "natural conversational voice, synthetic performer only",
            "identity_lock": None,
            "avatar_reference": None,
            "set_reference": None,
            "seamless": {
                "primary": "extend",
                "xfade_s": 0.2,
                "match_color": True,
                "cut_on_motion": True,
                "loudnorm": True,
            },
            "style_dna_tag": None,
            "audio_dna_tag": None,
            "music_dna_tag": None,
            "pacing_dna_tag": None,
            "director_persona_id": None,
            "language": "en",
            "branch_chain": None,
            "native_av": None,
        },
        "shots": shots,
        "provenance_card": {
            "enabled": True,
            "duration_s": 6,
            "card_type": "credits",
            "title": title,
            "subtitle": f"Based on screenplay by {writer}",
            "footer": f"Ingested by screenplay_ingest.py | {len(shots)} shots | {total_seconds}s",
        },
        "qa_rules": {
            "require_identity_lock": False,
            "require_synthetic_guard": True,
            "min_shots": 1,
        },
    }

    # Character index (informational, for HITL catalog resolution)
    if characters:
        script["_characters"] = {
            name: info for name, info in characters.items()
        }

    return script


# ─────────────────────────── CLI ──────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Parse a screenplay into render_longform.py-compatible JSON."
    )
    parser.add_argument("input", help="Path to screenplay file (.pdf, .txt, .fountain)")
    parser.add_argument("-o", "--output", help="Output JSON path (default: stdout)")
    parser.add_argument("--title", help="Override screenplay title")
    parser.add_argument(
        "--format-id",
        choices=[
            "documentary-host",
            "historical-figure-documentary",
            "science-explainer",
            "technical-explainer",
            "narrative-short-film",
            "movies",
            "explainer-ad",
            "science-pure-visual",
            "conversational-companion",
        ],
        help="Force a format_id (default: auto-detect from content)",
    )
    parser.add_argument("--stats", action="store_true", help="Print parse statistics")

    args = parser.parse_args()

    if not os.path.isfile(args.input):
        print(f"[screenplay_ingest] ERROR: file not found: {args.input}", file=sys.stderr)
        sys.exit(1)

    # 1. Read
    lines, title_meta = read_screenplay(args.input)
    if not lines:
        print("[screenplay_ingest] ERROR: no text extracted from file.", file=sys.stderr)
        sys.exit(1)

    # 2. Classify
    elements = classify_lines(lines)
    if not elements:
        print("[screenplay_ingest] ERROR: no screenplay elements found.", file=sys.stderr)
        sys.exit(1)

    # 3. Group into scenes
    scenes = group_into_scenes(elements)

    # 4. Build shots
    characters = {}
    shots = build_shots(scenes, characters)
    if not shots:
        print("[screenplay_ingest] ERROR: no shots produced.", file=sys.stderr)
        sys.exit(1)

    # 5. Title
    title = args.title or title_meta.get("title", Path(args.input).stem.replace("_", " ").title())

    # 6. Assemble
    script = assemble_script(
        shots, elements, title, args.format_id, title_meta, characters
    )

    # 7. Output
    output_json = json.dumps(script, indent=2, ensure_ascii=False)
    if args.output:
        Path(args.output).write_text(output_json, encoding="utf-8")
        print(f"[screenplay_ingest] Written: {args.output}", file=sys.stderr)
        print(f"  Shots  : {len(shots)}", file=sys.stderr)
        print(f"  Duration: {script['target_seconds']}s", file=sys.stderr)
        print(f"  Format : {script['format_id']}", file=sys.stderr)
    else:
        print(output_json)

    # Stats
    if args.stats:
        from collections import Counter
        counts = Counter(e.type for e in elements)
        print("\n--- Parse Statistics ---", file=sys.stderr)
        for etype, count in counts.most_common():
            print(f"  {etype:20s} {count}", file=sys.stderr)
        print(f"  {'scenes':20s} {len(scenes)}", file=sys.stderr)
        print(f"  {'shots':20s} {len(shots)}", file=sys.stderr)
        print(f"  {'characters':20s} {len(characters)}", file=sys.stderr)
        if characters:
            for name in sorted(characters):
                print(f"    - {name}", file=sys.stderr)


if __name__ == "__main__":
    main()
