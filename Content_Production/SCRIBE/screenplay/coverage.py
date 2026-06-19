"""SCRIBE coverage-report module.

Produces story-department *coverage* for a parsed screenplay. Coverage in the
industry sense = the title-block + logline + synopsis + comments scaffold a reader
files on a script. This module computes every *measurable* field automatically
(page count, scene breakdown, location/time-of-day mix, cast with line counts,
dialogue-to-action balance, estimated runtime) and scaffolds the *editorial*
fields (logline, synopsis, comments) for the reader to complete.

Per the SCRIBE house philosophy ("no quality judgments"), the disposition box —
the RECOMMEND / CONSIDER / PASS grid with element grades — is **opt-in** and off by
default. When enabled it emits an empty grid for a human reader to fill, never an
auto-generated verdict.
"""

from __future__ import annotations

import re
from collections import Counter, defaultdict
from dataclasses import dataclass, field

from .fountain import ElementType, Screenplay, parse_fountain

# words/minute and page→minute heuristics used only for *descriptive* estimates
_PAGES_PER_MINUTE = 1.0  # industry rule of thumb: 1 page ≈ 1 screen minute

_SCENE_RE = re.compile(
    r"^(INT\.?/EXT\.?|EXT\.?/INT\.?|I/E\.?|INT\.?|EXT\.?|EST\.?)\s*[\. ]?\s*(.*)$",
    re.IGNORECASE,
)
_TIME_TOKENS = (
    "DAY", "NIGHT", "DAWN", "DUSK", "MORNING", "EVENING", "AFTERNOON",
    "CONTINUOUS", "LATER", "MOMENTS LATER", "SAME", "SUNSET", "SUNRISE",
)


@dataclass
class SceneInfo:
    heading: str
    setting: str          # INT / EXT / INT-EXT
    location: str
    time_of_day: str
    action_lines: int = 0
    dialogue_lines: int = 0
    characters: set = field(default_factory=set)


@dataclass
class CoverageReport:
    title: str
    author: str
    source_format: str
    page_count: int
    est_runtime_min: int
    scene_count: int
    setting_mix: dict          # {"INT": n, "EXT": n, ...}
    time_of_day_mix: dict      # {"DAY": n, "NIGHT": n, ...}
    locations: list            # [(location, count), ...] most→least
    characters: list           # [{name, dialogue_blocks, dialogue_words, scenes}, ...]
    dialogue_blocks: int
    action_elements: int
    dialogue_action_ratio: float
    scenes: list               # list[SceneInfo]
    sections: list             # structure map from '#' headers
    synopses: list             # '=' synopsis lines, in order
    logline: str = ""          # scaffold — filled by reader
    synopsis: str = ""         # scaffold — filled by reader
    prepared_on: str = ""

    def to_dict(self) -> dict:
        return {
            "title": self.title,
            "author": self.author,
            "source_format": self.source_format,
            "page_count": self.page_count,
            "est_runtime_min": self.est_runtime_min,
            "scene_count": self.scene_count,
            "setting_mix": self.setting_mix,
            "time_of_day_mix": self.time_of_day_mix,
            "locations": self.locations,
            "characters": self.characters,
            "dialogue_blocks": self.dialogue_blocks,
            "action_elements": self.action_elements,
            "dialogue_action_ratio": round(self.dialogue_action_ratio, 3),
            "scene_count_detail": [
                {
                    "heading": s.heading,
                    "setting": s.setting,
                    "location": s.location,
                    "time_of_day": s.time_of_day,
                    "characters": sorted(s.characters),
                }
                for s in self.scenes
            ],
            "structure_sections": self.sections,
            "synopses": self.synopses,
            "logline": self.logline,
            "synopsis": self.synopsis,
            "prepared_on": self.prepared_on,
        }


def _parse_scene_heading(text: str) -> tuple:
    """Return (setting, location, time_of_day) from a scene-heading string."""
    m = _SCENE_RE.match(text.strip())
    if not m:
        return ("", text.strip(), "")
    raw_setting = m.group(1).upper().rstrip(".")
    setting = {
        "INT": "INT", "EXT": "EXT", "EST": "EST",
        "INT/EXT": "INT/EXT", "EXT/INT": "INT/EXT", "I/E": "INT/EXT",
    }.get(raw_setting, raw_setting)
    rest = m.group(2).strip()
    # split location and time on the last ' - ' / ' — '
    location, time_of_day = rest, ""
    parts = re.split(r"\s[-—–]\s", rest)
    if len(parts) >= 2:
        tail = parts[-1].strip().upper()
        if any(tok in tail for tok in _TIME_TOKENS) or len(parts) > 1:
            time_of_day = parts[-1].strip().upper()
            location = " - ".join(p.strip() for p in parts[:-1])
    return (setting, location.strip(" -—–").upper(), time_of_day)


def _normalize_character(cue: str) -> str:
    """Strip extensions like (V.O.), (CONT'D), (O.S.) and trailing markers."""
    name = re.sub(r"\(.*?\)", "", cue).strip()
    name = name.rstrip("^").strip()
    return name.upper()


def build_coverage(
    source,
    page_count: int = None,
    prepared_on: str = None,
    today: str = None,
) -> CoverageReport:
    """Build a :class:`CoverageReport` from a path, Fountain text, or Screenplay."""
    if isinstance(source, Screenplay):
        sp = source
    else:
        from pathlib import Path

        if isinstance(source, (str,)) and not ("\n" in source) and Path(source).is_file():
            sp = parse_fountain(Path(source).read_text(encoding="utf-8"))
        else:
            sp = parse_fountain(str(source))

    if page_count is None:
        # local import avoids a hard cycle at module load
        from .formatter import _paginate

        page_count = len(_paginate(sp))

    scenes: list = []
    current: SceneInfo | None = None
    char_blocks: Counter = Counter()
    char_words: Counter = Counter()
    char_scenes: dict = defaultdict(set)
    dialogue_blocks = 0
    action_elements = 0
    pending_character: str | None = None
    scene_idx = -1

    for el in sp.elements:
        if el.type is ElementType.SCENE_HEADING:
            setting, location, tod = _parse_scene_heading(el.text)
            current = SceneInfo(el.text, setting, location, tod)
            scenes.append(current)
            scene_idx += 1
            pending_character = None
        elif el.type is ElementType.ACTION:
            action_elements += 1
            if current:
                current.action_lines += 1
        elif el.type is ElementType.CHARACTER:
            name = _normalize_character(el.text)
            pending_character = name
            char_blocks[name] += 1
            dialogue_blocks += 1
            if current:
                current.characters.add(name)
            if scene_idx >= 0:
                char_scenes[name].add(scene_idx)
        elif el.type is ElementType.DIALOGUE:
            if current:
                current.dialogue_lines += 1
            if pending_character:
                char_words[pending_character] += len(el.text.split())
        # parentheticals/transitions/etc. do not affect the tallies

    setting_mix = Counter(s.setting for s in scenes if s.setting)
    tod_mix = Counter(s.time_of_day for s in scenes if s.time_of_day)
    loc_mix = Counter(s.location for s in scenes if s.location)

    characters = [
        {
            "name": name,
            "dialogue_blocks": char_blocks[name],
            "dialogue_words": char_words.get(name, 0),
            "scenes": len(char_scenes.get(name, set())),
        }
        for name, _ in char_blocks.most_common()
    ]

    ratio = (dialogue_blocks / action_elements) if action_elements else 0.0
    sections = [
        {"level": e.level, "text": e.text}
        for e in sp.elements
        if e.type is ElementType.SECTION
    ]
    synopses = [e.text for e in sp.elements if e.type is ElementType.SYNOPSIS]

    return CoverageReport(
        title=sp.title,
        author=sp.author,
        source_format="Feature screenplay (Fountain source)",
        page_count=page_count,
        est_runtime_min=round(page_count * _PAGES_PER_MINUTE),
        scene_count=len(scenes),
        setting_mix=dict(setting_mix),
        time_of_day_mix=dict(tod_mix),
        locations=loc_mix.most_common(),
        characters=characters,
        dialogue_blocks=dialogue_blocks,
        action_elements=action_elements,
        dialogue_action_ratio=ratio,
        scenes=scenes,
        sections=sections,
        synopses=synopses,
        prepared_on=prepared_on or today or "",
    )


# ---------------------------------------------------------------------------
# Markdown renderer (SCRIBE house format)
# ---------------------------------------------------------------------------
def coverage_markdown(report: CoverageReport, disposition: bool = False) -> str:
    """Render the coverage report as a SCRIBE-format Markdown document.

    ``disposition=True`` appends an *empty* RECOMMEND/CONSIDER/PASS grid for a
    human reader to complete. No verdict is ever auto-generated.
    """
    r = report
    L: list = []
    L.append("# SCRIBE Coverage Report")
    L.append("")
    L.append(f"**Title**: {r.title}  ")
    L.append(f"**Author / Credit**: {r.author or '—'}  ")
    L.append(f"**Format**: {r.source_format}  ")
    L.append(f"**Date**: {r.prepared_on or '—'}  ")
    L.append(f"**Length**: {r.page_count} pages (~{r.est_runtime_min} min) · "
             f"{r.scene_count} scenes")
    L.append("")
    L.append("---")
    L.append("")
    L.append("## Logline")
    L.append(r.logline or "_[Reader to complete — one sentence: protagonist, goal, "
             "central conflict.]_")
    L.append("")
    L.append("## Synopsis")
    L.append(r.synopsis or "_[Reader to complete — neutral beat-by-beat summary of "
             "the story as presented.]_")
    L.append("")

    L.append("## Measured Overview")
    L.append("")
    L.append("| Field | Value |")
    L.append("|-------|-------|")
    L.append(f"| Page count | {r.page_count} |")
    L.append(f"| Est. runtime | ~{r.est_runtime_min} min (1 pg ≈ 1 min) |")
    L.append(f"| Scenes | {r.scene_count} |")
    L.append(f"| Setting mix | {_fmt_mix(r.setting_mix)} |")
    L.append(f"| Time-of-day mix | {_fmt_mix(r.time_of_day_mix)} |")
    L.append(f"| Distinct locations | {len(r.locations)} |")
    L.append(f"| Speaking characters | {len(r.characters)} |")
    L.append(f"| Dialogue blocks | {r.dialogue_blocks} |")
    L.append(f"| Action elements | {r.action_elements} |")
    L.append(f"| Dialogue : action ratio | {r.dialogue_action_ratio:.2f} : 1 |")
    L.append("")

    if r.locations:
        L.append("## Locations (most → least used)")
        L.append("")
        L.append("| Location | Scenes |")
        L.append("|----------|-------:|")
        for loc, count in r.locations[:25]:
            L.append(f"| {loc} | {count} |")
        L.append("")

    if r.characters:
        L.append("## Cast (by dialogue volume)")
        L.append("")
        L.append("| Character | Dialogue blocks | Words | Scenes |")
        L.append("|-----------|----------------:|------:|-------:|")
        for c in r.characters[:40]:
            L.append(f"| {c['name']} | {c['dialogue_blocks']} | "
                     f"{c['dialogue_words']} | {c['scenes']} |")
        L.append("")

    if r.sections:
        L.append("## Structure Map (from sections)")
        L.append("")
        for s in r.sections:
            L.append(f"{'  ' * (s['level'] - 1)}- {s['text']}")
        L.append("")

    if r.synopses:
        L.append("## Embedded Synopsis Notes")
        L.append("")
        for s in r.synopses:
            L.append(f"- {s}")
        L.append("")

    L.append("## Comments")
    L.append("_[Reader to complete — observational notes on structure, pacing, "
             "clarity, and open threads, per SCRIBE tone guidelines. Describe what is "
             "present; do not pronounce value.]_")
    L.append("")

    if disposition:
        L.append("## Disposition (optional — reader completes)")
        L.append("")
        L.append("| Element | RECOMMEND | CONSIDER | PASS |")
        L.append("|---------|:---------:|:--------:|:----:|")
        for elem in ("Premise", "Structure", "Characterization", "Dialogue", "Overall"):
            L.append(f"| {elem} |  |  |  |")
        L.append("")
        L.append("> SCRIBE does not auto-assign a disposition. This grid is provided "
                 "blank for a human reader to complete if the engagement requires one.")
        L.append("")

    L.append("---")
    L.append("")
    L.append("*Prepared by SCRIBE. Measured fields are computed from the script as "
             "submitted. Editorial fields describe what is present in the material "
             "reviewed; they do not evaluate artistic merit or writing quality.*")
    return "\n".join(L) + "\n"


def _fmt_mix(mix: dict) -> str:
    if not mix:
        return "—"
    return ", ".join(f"{k} {v}" for k, v in sorted(mix.items(), key=lambda kv: -kv[1]))


__all__ = [
    "CoverageReport",
    "SceneInfo",
    "build_coverage",
    "coverage_markdown",
]
