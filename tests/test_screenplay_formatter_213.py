"""C3 #213 — screenplay formatter (Fountain → PDF/FDX) + coverage-report module."""

from __future__ import annotations

import sys
import xml.dom.minidom as minidom
from collections import Counter
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
PKG_PARENT = ROOT / "Content_Production" / "SCRIBE"
SAMPLE = PKG_PARENT / "screenplay" / "samples" / "sample.fountain"

# Import the package (Content_Production has no __init__; add SCRIBE dir to path).
sys.path.insert(0, str(PKG_PARENT))
from screenplay import (  # noqa: E402
    ElementType,
    build_coverage,
    coverage_markdown,
    parse_fountain,
    to_fdx,
    to_pdf_bytes,
)
from screenplay.fountain import parse_file  # noqa: E402


@pytest.fixture(scope="module")
def screenplay():
    assert SAMPLE.is_file(), f"sample missing: {SAMPLE}"
    return parse_file(SAMPLE)


# --- Parser ----------------------------------------------------------------
def test_title_page_parsed(screenplay):
    assert screenplay.title == "The Long Field"
    assert screenplay.author == "J. Cartwright"


def test_element_types(screenplay):
    counts = Counter(e.type for e in screenplay.elements)
    assert counts[ElementType.SCENE_HEADING] == 3
    assert counts[ElementType.CHARACTER] == counts[ElementType.DIALOGUE] != 0
    assert counts[ElementType.TRANSITION] == 1
    assert counts[ElementType.CENTERED] == 1  # > THE END <


def test_scene_heading_detection_and_caps():
    sp = parse_fountain("INT. ROOM - DAY\n\nA chair.\n")
    sh = sp.scenes()
    assert len(sh) == 1
    assert sh[0].text == "INT. ROOM - DAY"


def test_forced_scene_heading():
    sp = parse_fountain(".A WEIRD PLACE\n\nAction.\n")
    assert sp.scenes()[0].text == "A WEIRD PLACE"


def test_emphasis_stripped():
    sp = parse_fountain("INT. X - DAY\n\nHe runs *fast* and **hard** and _far_.\n")
    action = [e for e in sp.elements if e.type is ElementType.ACTION][0]
    assert "*" not in action.text and "_" not in action.text
    assert "fast" in action.text and "hard" in action.text


def test_notes_and_boneyard_removed():
    sp = parse_fountain("INT. X - DAY\n\nReal action. [[a note]]\n\n/* hidden */\n\nMore.\n")
    text = " ".join(e.text for e in sp.elements)
    assert "note" not in text and "hidden" not in text
    assert "Real action." in text and "More." in text


def test_dual_dialogue_flag():
    src = "INT. X - DAY\n\nANNA\nHello.\n\nBEN ^\nHi.\n"
    sp = parse_fountain(src)
    chars = [e for e in sp.elements if e.type is ElementType.CHARACTER]
    assert any(c.dual for c in chars)


# --- PDF -------------------------------------------------------------------
def test_pdf_structure(screenplay):
    data = to_pdf_bytes(screenplay)
    assert data[:5] == b"%PDF-"
    assert b"%%EOF" in data[-8:]
    assert b"/Courier" in data
    assert b"MediaBox [0 0 612 792]" in data  # US Letter


def test_pdf_opens_with_reader(screenplay):
    pypdf = pytest.importorskip("pypdf")
    import io

    reader = pypdf.PdfReader(io.BytesIO(to_pdf_bytes(screenplay)))
    # title page + >=1 body page
    assert len(reader.pages) >= 2
    all_text = " ".join(p.extract_text() for p in reader.pages).upper()
    assert "THE LONG FIELD" in all_text
    assert "FARMHOUSE KITCHEN" in all_text


def test_pdf_no_title_page_option(screenplay):
    pypdf = pytest.importorskip("pypdf")
    import io

    with_tp = len(pypdf.PdfReader(io.BytesIO(to_pdf_bytes(screenplay, title_page=True))).pages)
    without = len(pypdf.PdfReader(io.BytesIO(to_pdf_bytes(screenplay, title_page=False))).pages)
    assert with_tp == without + 1


# --- FDX -------------------------------------------------------------------
def test_fdx_is_valid_xml(screenplay):
    xml = to_fdx(screenplay)
    doc = minidom.parseString(xml)  # raises on malformed
    assert doc.documentElement.tagName == "FinalDraft"
    types = {p.getAttribute("Type")
             for p in doc.getElementsByTagName("Paragraph") if p.getAttribute("Type")}
    assert {"Scene Heading", "Action", "Character", "Dialogue", "Transition"} <= types


# --- Coverage --------------------------------------------------------------
def test_coverage_metrics(screenplay):
    cov = build_coverage(screenplay, prepared_on="2026-06-19")
    assert cov.title == "The Long Field"
    assert cov.scene_count == 3
    assert cov.setting_mix.get("INT") == 1
    assert cov.setting_mix.get("EXT") == 2
    names = {c["name"] for c in cov.characters}
    assert {"MARGARET", "THOMAS"} <= names
    margaret = next(c for c in cov.characters if c["name"] == "MARGARET")
    assert margaret["dialogue_blocks"] >= 1 and margaret["dialogue_words"] > 0


def test_character_extension_normalized(screenplay):
    # THOMAS (O.S.) and THOMAS (CONT'D) must fold into THOMAS
    cov = build_coverage(screenplay)
    names = [c["name"] for c in cov.characters]
    assert "THOMAS" in names
    assert not any("(" in n for n in names)


def test_coverage_markdown_no_autograde(screenplay):
    cov = build_coverage(screenplay, prepared_on="2026-06-19")
    md = coverage_markdown(cov, disposition=True)
    assert "# SCRIBE Coverage Report" in md
    assert "The Long Field" in md
    # disposition grid present but blank — no auto verdict text
    assert "RECOMMEND" in md
    assert "does not auto-assign a disposition" in md  # grid stays blank
    # measured table present
    assert "Dialogue : action ratio" in md


def test_coverage_dict_roundtrip(screenplay):
    cov = build_coverage(screenplay)
    d = cov.to_dict()
    assert d["scene_count"] == 3
    assert isinstance(d["characters"], list)
    assert d["dialogue_action_ratio"] >= 0
