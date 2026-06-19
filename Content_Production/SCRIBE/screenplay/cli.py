"""Command-line entry point for the SCRIBE screenplay toolkit.

Examples
--------
    # Format a Fountain script to PDF + FDX next to it
    python -m Content_Production.SCRIBE.screenplay.cli format script.fountain

    # Choose outputs / directory
    python -m ...cli format script.fountain --pdf --no-fdx -o build/

    # Coverage report (Markdown + JSON), with the optional blank disposition grid
    python -m ...cli coverage script.fountain --disposition -o build/
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import date
from pathlib import Path

from .coverage import build_coverage, coverage_markdown
from .fountain import parse_file
from .formatter import format_screenplay


def _cmd_format(args: argparse.Namespace) -> int:
    src = Path(args.input)
    if not src.is_file():
        print(f"[scribe] input not found: {src}", file=sys.stderr)
        return 2
    out_dir = Path(args.out or src.parent)
    do_pdf = args.pdf or not args.fdx_only
    do_fdx = args.fdx or not args.pdf_only
    if args.pdf_only:
        do_pdf, do_fdx = True, False
    if args.fdx_only:
        do_pdf, do_fdx = False, True
    res = format_screenplay(
        src, out_dir, basename=args.name,
        pdf=do_pdf, fdx=do_fdx, title_page=not args.no_title_page,
    )
    for fmt in ("pdf", "fdx"):
        if fmt in res:
            print(f"[scribe] wrote {fmt.upper()}: {res[fmt]}")
    print(f"[scribe] paginated to {res['pages']} page(s)")
    return 0


def _cmd_coverage(args: argparse.Namespace) -> int:
    src = Path(args.input)
    if not src.is_file():
        print(f"[scribe] input not found: {src}", file=sys.stderr)
        return 2
    report = build_coverage(str(src), prepared_on=args.date or date.today().isoformat())
    out_dir = Path(args.out or src.parent)
    out_dir.mkdir(parents=True, exist_ok=True)
    base = args.name or src.stem

    md = coverage_markdown(report, disposition=args.disposition)
    md_path = out_dir / f"{base}_coverage.md"
    md_path.write_text(md, encoding="utf-8")
    print(f"[scribe] wrote coverage: {md_path}")

    if args.json:
        json_path = out_dir / f"{base}_coverage.json"
        json_path.write_text(json.dumps(report.to_dict(), indent=2, ensure_ascii=False),
                             encoding="utf-8")
        print(f"[scribe] wrote coverage JSON: {json_path}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="scribe-screenplay",
                                description="SCRIBE screenplay formatter + coverage")
    sub = p.add_subparsers(dest="command", required=True)

    fmt = sub.add_parser("format", help="Fountain → industry PDF / FDX")
    fmt.add_argument("input", help="Fountain (.fountain/.txt) source file")
    fmt.add_argument("-o", "--out", help="output directory (default: alongside input)")
    fmt.add_argument("-n", "--name", help="output basename (default: input stem)")
    fmt.add_argument("--pdf", action="store_true", help="emit PDF")
    fmt.add_argument("--fdx", action="store_true", help="emit FDX")
    fmt.add_argument("--pdf-only", action="store_true", help="emit only PDF")
    fmt.add_argument("--fdx-only", action="store_true", help="emit only FDX")
    fmt.add_argument("--no-title-page", action="store_true", help="skip the title page")
    fmt.set_defaults(func=_cmd_format)

    cov = sub.add_parser("coverage", help="Coverage report (Markdown + JSON)")
    cov.add_argument("input", help="Fountain (.fountain/.txt) source file")
    cov.add_argument("-o", "--out", help="output directory (default: alongside input)")
    cov.add_argument("-n", "--name", help="output basename (default: input stem)")
    cov.add_argument("--json", action="store_true", help="also emit coverage JSON")
    cov.add_argument("--disposition", action="store_true",
                     help="append a blank RECOMMEND/CONSIDER/PASS grid (opt-in)")
    cov.add_argument("--date", help="report date (default: today)")
    cov.set_defaults(func=_cmd_coverage)
    return p


def main(argv=None) -> int:
    args = build_parser().parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
