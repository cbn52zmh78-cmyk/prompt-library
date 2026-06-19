#!/usr/bin/env python3
"""Output-path validator  (#259) — the gate that replaces consolidation passes.

Two modes:

* ``scan``  — sweep the workspace for *scatter*: stray files dumped at the workspace
  root (redirection artifacts like ``=``, ``2>&1`` leftovers, loose ``*.json`` reports)
  and stamped outputs whose on-disk location disagrees with the ledger. Exit 1 on any
  violation so it can run as a round-boundary / CI gate.

* ``check`` — validate explicit path(s) against the canonical registry, optionally
  asserting an expected kind. Use in a producer's tests to prove a path is canonical
  before shipping.

``scan --fix`` removes only *empty* stray root files (the classic ``=`` redirection
artifact) and reports them; it never touches non-empty files.

Pure stdlib. Companion to ``tools/output_registry.py``.
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass
from pathlib import Path

_TOOLS = Path(__file__).resolve().parent
if str(_TOOLS) not in sys.path:
    sys.path.insert(0, str(_TOOLS))

from output_registry import (  # noqa: E402
    LEDGER_PATH,
    WORKSPACE,
    canonicalize,
    classify,
    has_case_drift,
    is_canonical,
    rel_canonical,
)

# Files permitted to live directly at the workspace root. Everything else at the
# root is treated as scatter. Dotfiles are always allowed.
ALLOWED_ROOT_FILES: set[str] = {
    "README.md",
    "requirements.txt",
    "nh_licensing.html",
    "LICENSE",
    "MEMORY.md",
}
ALLOWED_ROOT_SUFFIXES: set[str] = {".ps1", ".toml", ".cfg", ".ini"}


@dataclass
class Violation:
    code: str
    path: str
    message: str

    def to_dict(self) -> dict:
        return {"code": self.code, "path": self.path, "message": self.message}

    def __str__(self) -> str:
        return f"[{self.code}] {self.path} — {self.message}"


def _is_allowed_root_file(p: Path) -> bool:
    if p.name.startswith("."):
        return True
    if p.name in ALLOWED_ROOT_FILES:
        return True
    return p.suffix.lower() in ALLOWED_ROOT_SUFFIXES


# --------------------------------------------------------------------------- scans
def scan_root_scatter() -> list:
    """Stray files dumped directly at the workspace root."""
    violations: list = []
    for child in sorted(WORKSPACE.iterdir()):
        if child.is_dir():
            continue
        if _is_allowed_root_file(child):
            continue
        empty = child.is_file() and child.stat().st_size == 0
        violations.append(
            Violation(
                "ROOT_SCATTER",
                child.name,
                "stray file at workspace root"
                + (" (empty — likely a redirection artifact)" if empty else ""),
            )
        )
    return violations


def scan_ledger() -> list:
    """Verify every stamped output in the ledger still lives at its canonical path."""
    violations: list = []
    if not LEDGER_PATH.is_file():
        return violations
    seen: set[str] = set()
    for line in LEDGER_PATH.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            stamp = json.loads(line)
        except json.JSONDecodeError:
            violations.append(Violation("LEDGER_CORRUPT", "data/output_ledger.jsonl",
                                        f"unparseable ledger line: {line[:60]}…"))
            continue
        rel = stamp.get("canonical_path")
        if not rel or rel in seen:
            continue
        seen.add(rel)
        on_disk = WORKSPACE / rel
        if not on_disk.exists():
            # tolerate: the file may have been a transient; only flag case drift / wrong root
            continue
        ok, reasons = is_canonical(on_disk)
        if not ok:
            violations.append(Violation("LEDGER_NONCANON", rel, "; ".join(reasons)))
    return violations


def scan(fix: bool = False) -> "tuple[list, list]":
    """Full workspace scan. Returns ``(violations, fixed_paths)``."""
    violations = scan_root_scatter() + scan_ledger()
    fixed: list = []
    if fix:
        remaining: list = []
        for v in violations:
            target = WORKSPACE / v.path
            if v.code == "ROOT_SCATTER" and target.is_file() and target.stat().st_size == 0:
                target.unlink()
                fixed.append(v.path)
            else:
                remaining.append(v)
        violations = remaining
    return violations, fixed


# --------------------------------------------------------------------------- check
def check_paths(paths: list, expected_kind: "str | None" = None) -> list:
    violations: list = []
    for raw in paths:
        ok, reasons = is_canonical(raw)
        if not ok:
            for r in reasons:
                violations.append(Violation("NONCANON", str(raw), r))
        kind = classify(raw)
        if expected_kind:
            if kind != expected_kind:
                violations.append(Violation(
                    "WRONG_KIND", str(raw),
                    f"resolved kind '{kind}' != expected '{expected_kind}'"))
    return violations


# --------------------------------------------------------------------------- CLI
def _print(violations: list, fixed: list, as_json: bool) -> None:
    if as_json:
        print(json.dumps({"violations": [v.to_dict() for v in violations],
                          "fixed": fixed}, indent=2))
        return
    for f in fixed:
        print(f"  fixed: removed empty stray root file '{f}'")
    if not violations:
        print("✓ no output scatter — all outputs canonical")
        return
    print(f"✗ {len(violations)} output-path violation(s):")
    for v in violations:
        print(f"  {v}")


def main(argv: "list | None" = None) -> int:
    for _s in (sys.stdout, sys.stderr):
        try:
            _s.reconfigure(encoding="utf-8", errors="replace")  # type: ignore[union-attr]
        except Exception:
            pass

    ap = argparse.ArgumentParser(description="Output-path validator (#259)")
    sub = ap.add_subparsers(dest="cmd", required=True)

    sc = sub.add_parser("scan", help="Sweep the workspace for output scatter")
    sc.add_argument("--fix", action="store_true", help="remove empty stray root files")
    sc.add_argument("--json", action="store_true", help="machine-readable output")

    ck = sub.add_parser("check", help="Validate explicit path(s) against the registry")
    ck.add_argument("paths", nargs="+")
    ck.add_argument("--kind", help="assert these paths resolve to this registry kind")
    ck.add_argument("--json", action="store_true")

    args = ap.parse_args(argv)

    if args.cmd == "scan":
        violations, fixed = scan(fix=args.fix)
        _print(violations, fixed, args.json)
        return 1 if violations else 0

    violations = check_paths(args.paths, args.kind)
    _print(violations, [], args.json)
    return 1 if violations else 0


if __name__ == "__main__":
    raise SystemExit(main())
