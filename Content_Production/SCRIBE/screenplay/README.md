# SCRIBE Screenplay Toolkit — #213

Industry-format screenplay tooling for the Nexus **Content_Production / SCRIBE** layer.

Two deliverables:

1. **Screenplay formatter** — Fountain → industry-format **PDF** and **FDX** (Final Draft).
2. **Coverage-report module** — objective script metrics + the standard coverage scaffold.

Everything is **dependency-free** (standard library only). `pypdf` is used by the test
suite for verification but is **not** required to generate output.

---

## Layout

```
screenplay/
├── __init__.py        public API
├── fountain.py        Fountain parser → Screenplay model
├── formatter.py       Screenplay → PDF (zero-dep) + FDX
├── coverage.py        coverage-report module
├── cli.py             command-line entry point
├── samples/sample.fountain
└── README.md
```

Tests: `tests/test_screenplay_formatter_213.py` (run `pytest` from repo root).

---

## CLI

```bash
# Format → PDF + FDX (written alongside the input by default)
python -m Content_Production.SCRIBE.screenplay.cli format script.fountain

# Pick outputs / directory
python -m Content_Production.SCRIBE.screenplay.cli format script.fountain --pdf-only -o build/

# Coverage report (Markdown; add --json for machine-readable; --disposition for the
# optional blank RECOMMEND/CONSIDER/PASS grid)
python -m Content_Production.SCRIBE.screenplay.cli coverage script.fountain --json --disposition -o build/
```

## Library

```python
from Content_Production.SCRIBE.screenplay import (
    parse_fountain, to_pdf_bytes, to_fdx, build_coverage, coverage_markdown,
)

sp = parse_fountain(open("script.fountain", encoding="utf-8").read())
open("script.pdf", "wb").write(to_pdf_bytes(sp))
open("script.fdx", "w", encoding="utf-8").write(to_fdx(sp))

report = build_coverage(sp, prepared_on="2026-06-19")
open("coverage.md", "w", encoding="utf-8").write(coverage_markdown(report))
```

---

## Industry format (PDF)

US Letter (612×792 pt), 12 pt **Courier** (a PDF base-14 font, so no embedding and
exact metrics: 10 chars/inch).

| Element | Left edge | Wrap width |
|---------|-----------|-----------|
| Scene heading (bold) | 1.5″ | 60 ch |
| Action | 1.5″ | 60 ch |
| Character cue | 3.7″ | — |
| Parenthetical | 3.1″ | 25 ch |
| Dialogue | 2.5″ | 35 ch |
| Transition | right-aligned to 7.5″ | — |
| Centered | centered | — |

- 1″ margins (1.5″ left), ~55 lines/page.
- Title page rendered from Fountain title-page keys (Title, Credit, Author, Source,
  Draft date, Contact).
- Page numbers top-right as `N.`; the first script page is unnumbered (industry standard).
- Scene-heading / character-cue **widow-orphan guard** prevents a cue stranded at a page foot.

## Fountain support

Title page · scene headings (`INT./EXT.` + forced `.`) · action (+ forced `!`) ·
character (+ forced `@`, dual `^`) · parenthetical · dialogue · transition (+ forced `>`)
· centered (`> .. <`) · lyric (`~`) · section (`#`) · synopsis (`=`) · page break (`===`)
· notes (`[[ ]]`, stripped) · boneyard (`/* */`, stripped) · emphasis (`*`,`**`,`***`,`_`).

**Known v1 limitations:** dual dialogue is parsed and flagged but rendered stacked (not
two-column) in PDF; emphasis runs are flattened to plain text in PDF layout (full Unicode
and structure are preserved in FDX, which is UTF-8). PDF text degrades non-Latin glyphs
via WinAnsi `replace`; use FDX for full-Unicode scripts.

## Coverage report

`build_coverage()` computes from the parsed script:

- page count (from the formatter's pagination) and estimated runtime (1 pg ≈ 1 min)
- scene count; INT/EXT setting mix; time-of-day mix; location frequency
- cast list with dialogue-block count, word count, and scene count per character
  (character extensions like `(V.O.)`, `(CONT'D)` are folded into the base name)
- dialogue-to-action balance
- structure map from `#` sections and embedded `=` synopsis notes

Editorial fields (logline, synopsis, comments) are **scaffolded, not invented**. Per the
SCRIBE house rule ("no quality judgments"), the disposition box is **opt-in** and, when
enabled, emitted **blank** for a human reader — SCRIBE never auto-assigns a verdict.

---

*SCRIBE v1 — #213. Respectful observation. Professional clarity. No quality judgments.*
