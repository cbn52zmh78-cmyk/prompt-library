"""Industry-format renderers for the parsed screenplay model.

Two outputs:

* :func:`to_pdf_bytes` / :func:`write_pdf` — a US-Letter, 12pt Courier PDF laid out
  to standard US screenplay metrics. Dependency-free: Courier and Courier-Bold are
  PDF base-14 fonts, so no font file is embedded and character metrics are exact
  (Courier 12pt = 10 chars/inch = 60 chars across a 6" text block).

* :func:`to_fdx` — Final Draft 8+ ``.fdx`` XML (UTF-8, full Unicode).

Standard US screenplay geometry used here (1 inch = 72 pt, page = 612 x 792 pt):

    left margin  1.5"   right margin 1.0"   top margin 1.0"   bottom margin 1.0"
    action / scene heading   x = 1.5", width 60 ch
    character cue            x = 3.7"
    parenthetical            x = 3.1", width ~25 ch
    dialogue                 x = 2.5", width ~35 ch
    transition               right-aligned to the 7.5" right edge
    page number              top-right, 0.5" down, "N."   (suppressed on page 1)
    ~ 55 text lines per page
"""

from __future__ import annotations

import textwrap
from pathlib import Path
from xml.sax.saxutils import escape as _xml_escape

from .fountain import Element, ElementType, Screenplay, parse_fountain

# ---------------------------------------------------------------------------
# Geometry (points)
# ---------------------------------------------------------------------------
PT = 72.0
PAGE_W = int(8.5 * PT)   # 612
PAGE_H = int(11.0 * PT)  # 792
FONT_SIZE = 12.0
LINE_H = 12.0            # single-spaced 12pt Courier
CHAR_W = FONT_SIZE * 0.6  # Courier advance = 600/1000 em

LEFT = 1.5 * PT          # 108
RIGHT_EDGE = PAGE_W - 1.0 * PT   # 540  (1" right margin)
TOP = PAGE_H - 1.0 * PT          # 720  (first baseline region)
BOTTOM = 1.0 * PT                # 72

LINES_PER_PAGE = 55

# element x-offsets (points from page left edge)
X_ACTION = LEFT
X_SCENE = LEFT
X_CHARACTER = 3.7 * PT
X_PAREN = 3.1 * PT
X_DIALOGUE = 2.5 * PT
X_TRANS_LEFT = LEFT

# wrap widths (characters)
W_ACTION = 60
W_DIALOGUE = 35
W_PAREN = 25
W_CHARACTER = 38
W_TRANS = 60


# ---------------------------------------------------------------------------
# Layout: turn elements into positioned text lines, paginated.
# ---------------------------------------------------------------------------
class _Line:
    __slots__ = ("x", "text", "bold", "centered")

    def __init__(self, x: float, text: str, bold: bool = False, centered: bool = False):
        self.x = x
        self.text = text
        self.bold = bold
        self.centered = centered


def _wrap(text: str, width: int) -> list:
    text = text.rstrip()
    if not text:
        return [""]
    return textwrap.wrap(
        text, width=width, break_long_words=True, break_on_hyphens=False
    ) or [""]


def _blank_before(etype: ElementType) -> int:
    """Number of blank lines that precede an element (industry spacing)."""
    if etype in (ElementType.SCENE_HEADING, ElementType.ACTION, ElementType.TRANSITION,
                 ElementType.CHARACTER, ElementType.CENTERED, ElementType.LYRIC):
        return 1
    return 0


def _element_lines(el: Element) -> list:
    """Render a single element to a list of (_Line | None-for-blank) entries."""
    t = el.type
    out: list = []
    if t is ElementType.SCENE_HEADING:
        for ln in _wrap(el.text, W_ACTION):
            out.append(_Line(X_SCENE, ln, bold=True))
    elif t is ElementType.ACTION:
        for ln in _wrap(el.text, W_ACTION):
            out.append(_Line(X_ACTION, ln))
    elif t is ElementType.LYRIC:
        for ln in _wrap(el.text, W_ACTION):
            out.append(_Line(X_ACTION, ln))
    elif t is ElementType.CHARACTER:
        out.append(_Line(X_CHARACTER, el.text.upper()))
    elif t is ElementType.PARENTHETICAL:
        for ln in _wrap(el.text, W_PAREN):
            out.append(_Line(X_PAREN, ln))
    elif t is ElementType.DIALOGUE:
        for ln in _wrap(el.text, W_DIALOGUE):
            out.append(_Line(X_DIALOGUE, ln))
    elif t is ElementType.TRANSITION:
        for ln in _wrap(el.text, W_TRANS):
            out.append(_Line(X_TRANS_LEFT, ln, centered=False))
            out[-1].x = RIGHT_EDGE - len(ln) * CHAR_W  # right align
    elif t is ElementType.CENTERED:
        for ln in _wrap(el.text, W_ACTION):
            out.append(_Line(0, ln, centered=True))
    else:
        return []
    return out


def _paginate(screenplay: Screenplay) -> list:
    """Return a list of pages; each page is a list of (x, y, text, bold) tuples."""
    pages: list = []
    current: list = []
    line_no = 0  # text lines used on the current page

    def new_page():
        nonlocal current, line_no
        if current:
            pages.append(current)
        current = []
        line_no = 0

    printable = [
        e for e in screenplay.elements
        if e.type not in (ElementType.SECTION, ElementType.SYNOPSIS)
    ]

    for idx, el in enumerate(printable):
        if el.type is ElementType.PAGE_BREAK:
            new_page()
            continue

        rendered = _element_lines(el)
        if not rendered:
            continue

        gap = _blank_before(el.type) if line_no > 0 else 0
        needed = gap + len(rendered)

        # Widow/orphan guard: never strand a scene heading or character cue as the
        # last line of a page.
        keep_with_next = el.type in (ElementType.SCENE_HEADING, ElementType.CHARACTER)
        budget = LINES_PER_PAGE
        if keep_with_next:
            needed += 1  # reserve a line for what follows

        if line_no + needed > budget and line_no > 0:
            new_page()
            gap = 0

        line_no += gap
        for ln in rendered:
            y = TOP - line_no * LINE_H
            x = ln.x
            if ln.centered:
                x = LEFT + (RIGHT_EDGE - LEFT - len(ln.text) * CHAR_W) / 2.0
            current.append((x, y, ln.text, ln.bold))
            line_no += 1
            if line_no >= LINES_PER_PAGE:
                new_page()

    new_page()
    return pages


# ---------------------------------------------------------------------------
# Minimal PDF writer (Courier base-14, no embedding)
# ---------------------------------------------------------------------------
def _pdf_escape(s: str) -> str:
    return s.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")


def _encode_text(s: str) -> str:
    # PDF standard Courier uses WinAnsi/Latin-1. Degrade gracefully for non-Latin
    # glyphs (full Unicode is preserved in the FDX path).
    return s.encode("latin-1", "replace").decode("latin-1")


def _title_page_lines(sp: Screenplay) -> list:
    """Build a classic centered title page; returns positioned tuples."""
    title = sp.title
    author = sp.author
    credit = sp.title_page_field("credit") or "Written by"
    source = sp.title_page_field("source")
    draft = sp.title_page_field("draft date", "draft_date")
    contact = sp.title_page_field("contact")

    out: list = []

    def centered(text: str, y: float, bold: bool = False):
        text = _encode_text(text)
        x = LEFT + (RIGHT_EDGE - LEFT - len(text) * CHAR_W) / 2.0
        out.append((x, y, text, bold))

    mid = PAGE_H * 0.62
    centered(title.upper(), mid, bold=True)
    if credit:
        centered(credit, mid - 3 * LINE_H)
    if author:
        centered(author, mid - 4 * LINE_H)
    if source:
        centered(source, mid - 6 * LINE_H)

    # bottom-left contact block
    if contact:
        y = BOTTOM + 4 * LINE_H
        for ln in contact.split("\n"):
            out.append((LEFT, y, _encode_text(ln), False))
            y -= LINE_H
    if draft:
        out.append((RIGHT_EDGE - len(draft) * CHAR_W, BOTTOM + 2 * LINE_H,
                    _encode_text(draft), False))
    return out


def to_pdf_bytes(screenplay: Screenplay, title_page: bool = True) -> bytes:
    """Render the screenplay to industry-format PDF bytes."""
    body_pages = _paginate(screenplay)

    pages_content: list = []
    if title_page and (screenplay.title != "Untitled" or screenplay.title_page):
        pages_content.append(("title", _title_page_lines(screenplay)))
    for p in body_pages:
        pages_content.append(("body", p))

    # number body pages starting at 1
    objects: list = []  # raw object bodies (without "N 0 obj")

    # Fixed objects:
    # 1 Catalog, 2 Pages, 3 Font Courier, 4 Font Courier-Bold, then page + content objs
    font_courier = "<< /Type /Font /Subtype /Type1 /BaseFont /Courier /Encoding /WinAnsiEncoding >>"
    font_bold = "<< /Type /Font /Subtype /Type1 /BaseFont /Courier-Bold /Encoding /WinAnsiEncoding >>"

    page_obj_nums: list = []
    content_streams: list = []

    # We will assign object numbers:
    #   1 = Catalog, 2 = Pages, 3 = Courier, 4 = Courier-Bold
    #   then for each page: one Page obj and one Content obj
    next_num = 5
    body_page_counter = 0
    for kind, lines in pages_content:
        page_num_obj = next_num
        content_obj = next_num + 1
        next_num += 2
        page_obj_nums.append(page_num_obj)

        parts = ["BT /F1 12 Tf"]
        last_font_bold = False
        for (x, y, text, bold) in lines:
            text = _encode_text(text)
            if bold and not last_font_bold:
                parts.append("/F2 12 Tf")
                last_font_bold = True
            elif not bold and last_font_bold:
                parts.append("/F1 12 Tf")
                last_font_bold = False
            parts.append(f"1 0 0 1 {x:.2f} {y:.2f} Tm ({_pdf_escape(text)}) Tj")

        # page number (top-right) for body pages after the first body page
        if kind == "body":
            body_page_counter += 1
            if body_page_counter > 1:
                label = f"{body_page_counter}."
                px = RIGHT_EDGE - len(label) * CHAR_W
                py = PAGE_H - 0.5 * PT
                if last_font_bold:
                    parts.append("/F1 12 Tf")
                    last_font_bold = False
                parts.append(f"1 0 0 1 {px:.2f} {py:.2f} Tm ({label}) Tj")
        parts.append("ET")
        stream = "\n".join(parts)
        content_streams.append((content_obj, stream))

        page_dict = (
            f"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 {PAGE_W} {PAGE_H}] "
            f"/Resources << /Font << /F1 3 0 R /F2 4 0 R >> >> "
            f"/Contents {content_obj} 0 R >>"
        )
        objects.append((page_num_obj, page_dict))

    for content_obj, stream in content_streams:
        body = (
            f"<< /Length {len(stream.encode('latin-1'))} >>\nstream\n{stream}\nendstream"
        )
        objects.append((content_obj, body))

    kids = " ".join(f"{num} 0 R" for num in page_obj_nums)
    catalog = "<< /Type /Catalog /Pages 2 0 R >>"
    pages = f"<< /Type /Pages /Kids [{kids}] /Count {len(page_obj_nums)} >>"

    all_objects = {
        1: catalog,
        2: pages,
        3: font_courier,
        4: font_bold,
    }
    for num, body in objects:
        all_objects[num] = body

    # Serialise with xref table.
    out = bytearray()
    out += b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n"
    offsets = {}
    for num in sorted(all_objects):
        offsets[num] = len(out)
        out += f"{num} 0 obj\n".encode("latin-1")
        out += all_objects[num].encode("latin-1")
        out += b"\nendobj\n"

    xref_pos = len(out)
    count = max(all_objects) + 1
    out += f"xref\n0 {count}\n".encode("latin-1")
    out += b"0000000000 65535 f \n"
    for num in range(1, count):
        off = offsets.get(num, 0)
        out += f"{off:010d} 00000 n \n".encode("latin-1")
    out += b"trailer\n"
    out += f"<< /Size {count} /Root 1 0 R >>\n".encode("latin-1")
    out += b"startxref\n"
    out += f"{xref_pos}\n".encode("latin-1")
    out += b"%%EOF\n"
    return bytes(out)


def write_pdf(screenplay: Screenplay, path, title_page: bool = True) -> Path:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(to_pdf_bytes(screenplay, title_page=title_page))
    return path


# ---------------------------------------------------------------------------
# FDX (Final Draft) writer
# ---------------------------------------------------------------------------
_FDX_TYPE = {
    ElementType.SCENE_HEADING: "Scene Heading",
    ElementType.ACTION: "Action",
    ElementType.CHARACTER: "Character",
    ElementType.PARENTHETICAL: "Parenthetical",
    ElementType.DIALOGUE: "Dialogue",
    ElementType.TRANSITION: "Transition",
    ElementType.CENTERED: "Action",
    ElementType.LYRIC: "Action",
}


def to_fdx(screenplay: Screenplay) -> str:
    """Render the screenplay as Final Draft 8 ``.fdx`` XML."""
    lines = ['<?xml version="1.0" encoding="UTF-8" standalone="no"?>']
    lines.append('<FinalDraft DocumentType="Script" Template="No" Version="1">')
    lines.append("  <Content>")

    for el in screenplay.elements:
        ftype = _FDX_TYPE.get(el.type)
        if ftype is None:
            continue
        attrs = f'Type="{ftype}"'
        if el.type is ElementType.SCENE_HEADING and el.scene_number:
            attrs += f' Number="{_xml_escape(el.scene_number)}"'
        if el.type is ElementType.CENTERED:
            attrs += ' Alignment="Center"'
        text = _xml_escape(el.text)
        lines.append(f"    <Paragraph {attrs}>")
        lines.append(f"      <Text>{text}</Text>")
        lines.append("    </Paragraph>")

    lines.append("  </Content>")

    # Title page
    if screenplay.title_page:
        lines.append("  <TitlePage>")
        lines.append("    <Content>")
        for key in ("title", "credit", "author", "source", "draft date", "contact"):
            val = screenplay.title_page.get(key)
            if not val:
                continue
            for v in val:
                lines.append('      <Paragraph Alignment="Center">')
                lines.append(f"        <Text>{_xml_escape(v)}</Text>")
                lines.append("      </Paragraph>")
        lines.append("    </Content>")
        lines.append("  </TitlePage>")

    lines.append("</FinalDraft>")
    return "\n".join(lines) + "\n"


def format_screenplay(
    source,
    out_dir,
    basename: str = None,
    pdf: bool = True,
    fdx: bool = True,
    title_page: bool = True,
) -> dict:
    """Parse ``source`` (path or Fountain text) and write requested formats.

    Returns a dict of {format: output_path}.
    """
    out_dir = Path(out_dir)
    if isinstance(source, (str, Path)) and Path(source).is_file():
        sp = parse_fountain(Path(source).read_text(encoding="utf-8"))
        basename = basename or Path(source).stem
    else:
        sp = parse_fountain(str(source))
        basename = basename or "screenplay"

    results: dict = {}
    if pdf:
        p = write_pdf(sp, out_dir / f"{basename}.pdf", title_page=title_page)
        results["pdf"] = p
    if fdx:
        fp = out_dir / f"{basename}.fdx"
        fp.parent.mkdir(parents=True, exist_ok=True)
        fp.write_text(to_fdx(sp), encoding="utf-8")
        results["fdx"] = fp
    results["pages"] = len(_paginate(sp))
    return results


__all__ = [
    "to_pdf_bytes",
    "write_pdf",
    "to_fdx",
    "format_screenplay",
]
