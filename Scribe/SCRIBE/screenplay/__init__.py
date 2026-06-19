"""SCRIBE screenplay toolkit — #213.

Industry-format screenplay tooling for the Nexus Content_Production layer:

- :mod:`fountain`  — parse Fountain plain-text screenplays into a structured model.
- :mod:`formatter` — render the model to industry-format PDF (zero-dependency) and
  Final Draft FDX.
- :mod:`coverage`  — produce a SCRIBE coverage report (objective metrics + the
  standard industry coverage scaffold).

Design notes
------------
* The PDF writer is dependency-free. Courier / Courier-Bold are PDF base-14 fonts,
  so screenplay metrics are exact (12pt Courier = 10 chars/inch) and no font
  embedding is required.
* Coverage follows SCRIBE's house philosophy: every *measured* field is computed
  from the parsed script; the *editorial* fields (logline, synopsis, comments) are
  scaffolded, not invented. A disposition/box-rating grid is available but opt-in,
  off by default, in keeping with SCRIBE's "no quality judgments" principle.
"""

from __future__ import annotations

from .fountain import Element, ElementType, Screenplay, parse_fountain
from .formatter import format_screenplay, to_fdx, to_pdf_bytes, write_pdf
from .coverage import CoverageReport, build_coverage, coverage_markdown

__all__ = [
    "Element",
    "ElementType",
    "Screenplay",
    "parse_fountain",
    "format_screenplay",
    "to_fdx",
    "to_pdf_bytes",
    "write_pdf",
    "CoverageReport",
    "build_coverage",
    "coverage_markdown",
]

__version__ = "1.0.0"
