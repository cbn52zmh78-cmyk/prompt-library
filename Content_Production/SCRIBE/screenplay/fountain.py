r"""Fountain parser → structured screenplay model.

Implements the practical subset of the Fountain spec (https://fountain.io) that
matters for industry formatting and coverage:

  title page · scene headings (INT./EXT. + forced ``.``) · action (+ forced ``!``)
  · character (+ forced ``@``, dual ``^``) · parenthetical · dialogue · transition
  (+ forced ``>``) · centered (``> .. <``) · lyric (``~``) · section (``#``) ·
  synopsis (``=``) · page break (``===``) · notes (``[[ ]]``) · boneyard (``/* */``)
  · emphasis (``*``/``**``/``***``/``_``).

The parser is deliberately dependency-free and line-oriented.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from enum import Enum


class ElementType(Enum):
    SCENE_HEADING = "scene_heading"
    ACTION = "action"
    CHARACTER = "character"
    PARENTHETICAL = "parenthetical"
    DIALOGUE = "dialogue"
    TRANSITION = "transition"
    CENTERED = "centered"
    LYRIC = "lyric"
    SECTION = "section"
    SYNOPSIS = "synopsis"
    PAGE_BREAK = "page_break"


@dataclass
class Element:
    type: ElementType
    text: str = ""
    scene_number: "str | None" = None
    level: int = 0
    dual: bool = False

    def __repr__(self) -> str:  # pragma: no cover - debug aid
        snippet = (self.text[:40] + "…") if len(self.text) > 40 else self.text
        return f"Element({self.type.value}, {snippet!r})"


@dataclass
class Screenplay:
    title_page: dict = field(default_factory=dict)
    elements: list = field(default_factory=list)

    @property
    def title(self) -> str:
        for key in ("title",):
            if key in self.title_page:
                return " ".join(self.title_page[key]).strip()
        return "Untitled"

    @property
    def author(self) -> str:
        for key in ("author", "authors", "credit"):
            if key in self.title_page:
                return " ".join(self.title_page[key]).strip()
        return ""

    def title_page_field(self, *keys: str) -> str:
        for key in keys:
            if key.lower() in self.title_page:
                return "\n".join(self.title_page[key.lower()]).strip()
        return ""

    def scenes(self) -> list:
        return [e for e in self.elements if e.type is ElementType.SCENE_HEADING]


# ---------------------------------------------------------------------------
# Emphasis handling
# ---------------------------------------------------------------------------
_EMPHASIS_RE = re.compile(r"(\*{1,3}|_)(.+?)\1")
_ESC_STAR = "\x00STAR\x00"
_ESC_USCORE = "\x00USCORE\x00"
_BACKSLASH_STAR = chr(92) + "*"
_BACKSLASH_USCORE = chr(92) + "_"


def strip_emphasis(text: str) -> str:
    """Remove Fountain emphasis markers, returning plain text.

    ``*italic*`` / ``**bold**`` / ``***bold italic***`` / ``_underline_`` collapse
    to their inner text. Escaped ``\\*`` / ``\\_`` are preserved as literals.
    """
    text = text.replace(_BACKSLASH_STAR, _ESC_STAR).replace(_BACKSLASH_USCORE, _ESC_USCORE)
    prev = None
    while prev != text:
        prev = text
        text = _EMPHASIS_RE.sub(r"\2", text)
    return text.replace(_ESC_STAR, "*").replace(_ESC_USCORE, "_")


# ---------------------------------------------------------------------------
# Pre-processing: strip boneyard + notes
# ---------------------------------------------------------------------------
_BONEYARD_RE = re.compile(r"/\*.*?\*/", re.DOTALL)
_NOTE_RE = re.compile(r"\[\[.*?\]\]", re.DOTALL)


def _preprocess(raw: str) -> str:
    raw = raw.replace("\r\n", "\n").replace("\r", "\n")
    raw = _BONEYARD_RE.sub("", raw)
    raw = _NOTE_RE.sub("", raw)
    raw = raw.replace("\t", "    ")
    return raw


# ---------------------------------------------------------------------------
# Title page
# ---------------------------------------------------------------------------
_TITLE_KEY_RE = re.compile(r"^([A-Za-z][A-Za-z0-9 _-]*):\s*(.*)$")


def _split_title_page(lines: list) -> tuple:
    idx = 0
    while idx < len(lines) and lines[idx].strip() == "":
        idx += 1
    if idx >= len(lines) or not _TITLE_KEY_RE.match(lines[idx]):
        return {}, lines

    title_page: dict = {}
    current_key = None
    i = idx
    while i < len(lines):
        line = lines[i]
        if line.strip() == "":
            i += 1
            break
        m = _TITLE_KEY_RE.match(line)
        if m and not line.startswith(" "):
            current_key = m.group(1).strip().lower()
            value = m.group(2).strip()
            title_page[current_key] = [value] if value else []
        elif current_key is not None and line.strip():
            title_page[current_key].append(line.strip())
        else:
            return {}, lines
        i += 1
    return title_page, lines[i:]


# ---------------------------------------------------------------------------
# Body element classification
# ---------------------------------------------------------------------------
_SCENE_PREFIX_RE = re.compile(
    r"^(INT\.?/EXT\.?|EXT\.?/INT\.?|INT\.?|EXT\.?|EST\.?|I/E\.?)([\. /].*)?$",
    re.IGNORECASE,
)
_SCENE_NUMBER_RE = re.compile(r"#([\w.\-]+)#\s*$")
_TRANSITION_RE = re.compile(r"^[A-Z0-9 ]+TO:$")


def _is_upper(text: str) -> bool:
    return text == text.upper() and any(c.isalpha() for c in text)


def _looks_like_character(line: str) -> bool:
    stripped = line.strip()
    if not stripped:
        return False
    core = re.sub(r"\(.*?\)", "", stripped).strip().rstrip("^").strip()
    if not core:
        return False
    if _SCENE_PREFIX_RE.match(stripped):
        return False
    if stripped.endswith("TO:"):
        return False
    return _is_upper(core)


def parse_fountain(raw: str) -> Screenplay:
    """Parse a Fountain document into a :class:`Screenplay`."""
    text = _preprocess(raw)
    lines = text.split("\n")
    title_page, body = _split_title_page(lines)

    elements: list = []
    n = len(body)
    i = 0
    in_dialogue = False

    def prev_blank(idx: int) -> bool:
        return idx == 0 or body[idx - 1].strip() == ""

    def next_blank(idx: int) -> bool:
        return idx + 1 >= n or body[idx + 1].strip() == ""

    while i < n:
        line = body[i].strip()

        if line == "":
            in_dialogue = False
            i += 1
            continue

        if re.fullmatch(r"={3,}", line):
            elements.append(Element(ElementType.PAGE_BREAK))
            in_dialogue = False
            i += 1
            continue

        if line.startswith("#"):
            depth = len(line) - len(line.lstrip("#"))
            elements.append(
                Element(ElementType.SECTION, strip_emphasis(line[depth:].strip()), level=depth)
            )
            in_dialogue = False
            i += 1
            continue

        if line.startswith("=") and not re.fullmatch(r"={3,}", line):
            elements.append(Element(ElementType.SYNOPSIS, strip_emphasis(line[1:].strip())))
            i += 1
            continue

        if line.startswith(">") and line.endswith("<"):
            elements.append(Element(ElementType.CENTERED, strip_emphasis(line[1:-1].strip())))
            in_dialogue = False
            i += 1
            continue

        if line.startswith(">"):
            elements.append(
                Element(ElementType.TRANSITION, strip_emphasis(line[1:].strip()).upper())
            )
            in_dialogue = False
            i += 1
            continue

        if line.startswith(".") and not line.startswith(".."):
            heading = line[1:].strip()
            scene_no = None
            m = _SCENE_NUMBER_RE.search(heading)
            if m:
                scene_no = m.group(1)
                heading = _SCENE_NUMBER_RE.sub("", heading).strip()
            elements.append(
                Element(
                    ElementType.SCENE_HEADING,
                    strip_emphasis(heading).upper(),
                    scene_number=scene_no,
                )
            )
            in_dialogue = False
            i += 1
            continue

        if line.startswith("!"):
            elements.append(Element(ElementType.ACTION, strip_emphasis(line[1:])))
            in_dialogue = False
            i += 1
            continue

        if line.startswith("~"):
            elements.append(Element(ElementType.LYRIC, strip_emphasis(line[1:].strip())))
            i += 1
            continue

        if line.startswith("@"):
            cue = line[1:].strip()
            dual = cue.endswith("^")
            cue = cue.rstrip("^").strip()
            elements.append(Element(ElementType.CHARACTER, strip_emphasis(cue), dual=dual))
            if dual:
                _mark_dual(elements)
            in_dialogue = True
            i += 1
            continue

        if _SCENE_PREFIX_RE.match(line) and prev_blank(i):
            scene_no = None
            heading = line
            m = _SCENE_NUMBER_RE.search(heading)
            if m:
                scene_no = m.group(1)
                heading = _SCENE_NUMBER_RE.sub("", heading).strip()
            elements.append(
                Element(
                    ElementType.SCENE_HEADING,
                    strip_emphasis(heading).upper(),
                    scene_number=scene_no,
                )
            )
            in_dialogue = False
            i += 1
            continue

        if _TRANSITION_RE.match(line) and prev_blank(i) and next_blank(i):
            elements.append(Element(ElementType.TRANSITION, strip_emphasis(line)))
            in_dialogue = False
            i += 1
            continue

        if in_dialogue and line.startswith("(") and line.endswith(")"):
            elements.append(Element(ElementType.PARENTHETICAL, strip_emphasis(line)))
            i += 1
            continue

        if in_dialogue:
            elements.append(Element(ElementType.DIALOGUE, strip_emphasis(line)))
            i += 1
            continue

        if _looks_like_character(line) and prev_blank(i) and not next_blank(i):
            dual = line.endswith("^")
            cue = line.rstrip("^").strip()
            elements.append(Element(ElementType.CHARACTER, strip_emphasis(cue), dual=dual))
            if dual:
                _mark_dual(elements)
            in_dialogue = True
            i += 1
            continue

        elements.append(Element(ElementType.ACTION, strip_emphasis(line)))
        in_dialogue = False
        i += 1

    return Screenplay(title_page=title_page, elements=elements)


def _mark_dual(elements: list) -> None:
    """Flag the preceding character+dialogue block as the left column of a dual pair."""
    right_idx = len(elements) - 1
    j = right_idx - 1
    while j >= 0 and elements[j].type is not ElementType.CHARACTER:
        if elements[j].type not in (ElementType.DIALOGUE, ElementType.PARENTHETICAL):
            return
        j -= 1
    if j >= 0 and elements[j].type is ElementType.CHARACTER:
        for k in range(j, right_idx):
            if elements[k].type in (
                ElementType.CHARACTER,
                ElementType.DIALOGUE,
                ElementType.PARENTHETICAL,
            ):
                elements[k].dual = True


def parse_file(path) -> Screenplay:
    from pathlib import Path

    return parse_fountain(Path(path).read_text(encoding="utf-8"))


__all__ = [
    "Element",
    "ElementType",
    "Screenplay",
    "parse_fountain",
    "parse_file",
    "strip_emphasis",
]
