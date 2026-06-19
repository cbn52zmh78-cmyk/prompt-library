#!/usr/bin/env python3
"""Canonical output-path registry + path-stamping  (#259).

The permanent fix for output fragmentation. Three cooperating ideas:

1. **Registry** — one declarative source of truth mapping a logical *output kind*
   (``gate_report``, ``batch_manifest``, ``editorial_project`` …) to its canonical
   location and filename template. Terminals ask the registry where an output
   *belongs* instead of hardcoding a path — so they cannot invent a new one.

2. **Path-stamping** — :func:`write_stamped` resolves the canonical path, embeds an
   ``_output_stamp`` provenance block in JSON payloads (or a ``.stamp.json`` sidecar
   for other files), and appends one line to the append-only ledger
   (``data/output_ledger.jsonl``). Every stamped output therefore *declares where it
   lives*, and a validator can prove it actually lives there.

3. **Canonical casing** — the workspace has historically been addressed as both
   ``Studio/`` and ``STUDIO/`` (same dir on Windows, two strings in code). The
   registry declares one canonical spelling per top-level dir and
   :func:`canonicalize` rewrites drift, so the validator can flag it.

Companion: ``tools/output_validator.py`` (scan + verify). Pure stdlib.
"""

from __future__ import annotations

import json
import os
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

_TOOLS = Path(__file__).resolve().parent
if str(_TOOLS) not in sys.path:
    sys.path.insert(0, str(_TOOLS))

from workspace_paths import WORKSPACE  # noqa: E402

# --------------------------------------------------------------------------- casing
# lower-cased top-level dir -> canonical spelling (the git submodule / repo name).
CANONICAL_TOP: dict[str, str] = {
    "studio": "Studio",
    "david": "DAVID",
    "science": "Science",
    "content_production": "Content_Production",
    "nexus": "Nexus",
    "history": "History",
    "ai": "AI",
    "gfe": "GFE",
    "stonebridge": "Stonebridge",
    "flash": "FLASH",
    "creator4": "Creator4",
    "data": "data",
    "docs": "docs",
    "outputs": "outputs",
    "artifacts": "artifacts",
    "tools": "tools",
    "prompts": "prompts",
    "notes": "notes",
    "agents": "AGENTS",
    "mcps": "mcps",
    "tests": "tests",
    "terminals": "terminals",
    "scripts": "scripts",
    "groundtruth": "GroundTruth",
}

LEDGER_PATH = WORKSPACE / "data" / "output_ledger.jsonl"
STAMP_KEY = "_output_stamp"


# --------------------------------------------------------------------------- registry
@dataclass(frozen=True)
class OutputKind:
    """One canonical output destination.

    ``root`` is workspace-relative in canonical casing. ``template`` is an optional
    sub-path (may contain ``{param}`` placeholders and a filename); when empty the
    kind resolves to the root directory itself.
    """

    key: str
    root: str
    template: str = ""
    is_dir: bool = False
    description: str = ""

    def rel(self, **params: str) -> str:
        base = self.root.format(**params) if "{" in self.root else self.root
        sub = self.template.format(**params) if self.template else ""
        return f"{base}/{sub}".rstrip("/") if sub else base


# The canonical map. Every output a fan-out can produce should have a home here.
_KINDS: tuple[OutputKind, ...] = (
    # ---- legal / compliance gates --------------------------------------------
    OutputKind("gate_report", "Studio/Legal/Gate_Reports", "{filename}",
               description="Legal/editorial Gate-0 markdown reports (shared sink)."),
    OutputKind("legal_gate_json", "Studio/Producers_Office/Legal_Gate", "{filename}",
               description="Legal Gate machine-readable JSON stamps."),
    OutputKind("editorial_gate_json", "Studio/Producers_Office/Editorial_Gate", "{filename}",
               description="Editorial Gate machine-readable JSON stamps."),
    OutputKind("compliance_report", "Studio/Producers_Office/Compliance_Reports", "{filename}",
               description="CARA / compliance reports."),
    OutputKind("session_log", "Studio/Producers_Office/Session_Logs", "{filename}",
               description="Per-session terminal logs."),
    # ---- batches / scripts ----------------------------------------------------
    OutputKind("batch", "DAVID/batches/{batch_id}", is_dir=True,
               description="A render batch working directory."),
    OutputKind("batch_manifest", "DAVID/batches/{batch_id}", "manifest.json",
               description="Canonical batch manifest."),
    OutputKind("longform_script", "DAVID/scripts/longform_scripts", "{slug}_script.json",
               description="render_longform canonical script.json."),
    # ---- productions ----------------------------------------------------------
    OutputKind("production", "Studio/Productions/{lane}/{slug}", is_dir=True,
               description="A production working directory (lane in Narrative/History/Editorial/GFE)."),
    OutputKind("production_output", "Studio/Productions/{lane}/{slug}/output", "{filename}",
               description="Rendered production deliverables."),
    # ---- editorial (SCRIBE) ---------------------------------------------------
    OutputKind("editorial_project", "Content_Production/SCRIBE/editorials/{project_id}", is_dir=True,
               description="SCRIBE editorial-engine project directory."),
    # ---- science reference ----------------------------------------------------
    OutputKind("reference_plate", "Science/reference_plates/{domain}", "{filename}",
               description="Science reference-plate assets + manifests."),
    # ---- pipeline concepts ----------------------------------------------------
    OutputKind("concept_slate", "Studio/Pipeline/Concepts/{slate}", is_dir=True,
               description="A concept slate directory."),
    # ---- science groundtruth (was drifting to ad-hoc Science/ sub-dirs) -------
    OutputKind("groundtruth_pack", "Science/groundtruth_poc", "{filename}",
               description="GroundTruth POC packs / knowledge-gate reports / papers."),
    # ---- compliance GroundTruth (#282) ------------------------------------------
    OutputKind("groundtruth_compliance", "GroundTruth/Compliance", is_dir=True,
               description="Workspace GroundTruth compliance corpus root."),
    OutputKind("groundtruth_compliance_file", "GroundTruth/Compliance", "{filename}",
               description="Top-level compliance corpus artifacts (INDEX, templates, triage)."),
    OutputKind("groundtruth_compliance_lane", "GroundTruth/Compliance/lanes/{lane_slug}", is_dir=True,
               description="Compliance lane directory (workspace mirror)."),
    OutputKind("groundtruth_compliance_lane_file", "GroundTruth/Compliance/lanes/{lane_slug}", "{subpath}",
               description="Lane artifact (states/pa.json, cited_data_pack.json, …)."),
    OutputKind("groundtruth_compliance_bible", "GroundTruth/Compliance/lanes/{lane_slug}/bibles", "{filename}",
               description="Compliance knowledge bible deliverables."),
    OutputKind("stonebridge_groundtruth_compliance",
               "Stonebridge/Operations/Compliance_Research/groundtruth/Compliance", is_dir=True,
               description="Stonebridge-authoritative compliance corpus."),
    OutputKind("stonebridge_groundtruth_compliance_file",
               "Stonebridge/Operations/Compliance_Research/groundtruth/Compliance", "{filename}",
               description="Stonebridge compliance corpus artifact."),
    OutputKind("stonebridge_groundtruth_lane",
               "Stonebridge/Operations/Compliance_Research/groundtruth/Compliance/lanes/{lane_slug}",
               is_dir=True, description="Stonebridge compliance lane directory."),
    OutputKind("stonebridge_groundtruth_lane_file",
               "Stonebridge/Operations/Compliance_Research/groundtruth/Compliance/lanes/{lane_slug}",
               "{subpath}", description="Stonebridge lane artifact."),
    OutputKind("science_corpus", "Science/corpus", "{filename}",
               description="Science fact-base corpora."),
    OutputKind("science_report", "Science/reports", "{filename}",
               description="Science accuracy / verification reports."),
    # ---- cast / references / prompts ------------------------------------------
    OutputKind("casting_bible", "Studio/Cast/Casting_Bible", is_dir=True,
               description="Casting Bible registry / schema / lock cards."),
    OutputKind("set_reference", "Studio/Pipeline/references", "{filename}",
               description="Set / neutral reference plates for generation."),
    OutputKind("prompt_pack", "Studio/Pipeline/Grok_Video_Packs", "{filename}",
               description="Imagine / Grok video prompt packs."),
    OutputKind("music_clearance_manifest", "Studio/Music_Sound", "clearance_manifest.json",
               description="Canonical music-clearance manifest pointer."),
    OutputKind("workflow_template", "Nexus/Workflows/templates", "{filename}",
               description="NEXUS workflow templates."),
    # ---- ledger ---------------------------------------------------------------
    OutputKind("output_ledger", "data", "output_ledger.jsonl",
               description="Append-only stamp ledger."),
)

REGISTRY: dict[str, OutputKind] = {k.key: k for k in _KINDS}


# --------------------------------------------------------------------------- casing helpers
def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def canonicalize(path: "str | Path") -> Path:
    """Return ``path`` as an absolute path with canonical top-level casing.

    A bare relative path is taken relative to the workspace. The first path segment
    under the workspace is rewritten to its canonical spelling (``STUDIO`` → ``Studio``).
    """
    p = Path(path)
    if not p.is_absolute():
        p = WORKSPACE / p
    try:
        rel_parts = p.relative_to(WORKSPACE).parts
    except ValueError:
        return p  # outside the workspace — leave untouched
    if not rel_parts:
        return WORKSPACE
    head, *tail = rel_parts
    head = CANONICAL_TOP.get(head.lower(), head)
    return WORKSPACE.joinpath(head, *tail)


def rel_canonical(path: "str | Path") -> str:
    """Workspace-relative POSIX string with canonical casing (for comparisons/keys)."""
    p = canonicalize(path)
    try:
        return p.relative_to(WORKSPACE).as_posix()
    except ValueError:
        return p.as_posix()


def has_case_drift(path: "str | Path") -> bool:
    """True if the path's top-level segment is spelled non-canonically."""
    p = Path(path)
    if not p.is_absolute():
        p = WORKSPACE / p
    try:
        rel_parts = p.relative_to(WORKSPACE).parts
    except ValueError:
        return False
    if not rel_parts:
        return False
    head = rel_parts[0]
    canonical = CANONICAL_TOP.get(head.lower())
    return canonical is not None and head != canonical


# --------------------------------------------------------------------------- resolve / classify
def resolve(kind: str, *, mkdirs: bool = True, **params: str) -> Path:
    """Resolve a logical output kind to its canonical absolute path.

    Raises ``KeyError`` for an unknown kind and ``ValueError`` if the template needs
    parameters that were not supplied. With ``mkdirs`` the directory (for ``is_dir``
    kinds) or the parent directory (for file kinds) is created.
    """
    if kind not in REGISTRY:
        raise KeyError(f"unknown output kind '{kind}' (known: {', '.join(sorted(REGISTRY))})")
    entry = REGISTRY[kind]
    try:
        rel = entry.rel(**params)
    except KeyError as exc:
        raise ValueError(f"output kind '{kind}' requires template param {exc}") from exc
    path = WORKSPACE / rel
    if mkdirs:
        (path if entry.is_dir else path.parent).mkdir(parents=True, exist_ok=True)
    return path


def _match_root(rel_parts: list, root_parts: list) -> int:
    """Return the number of matched leading segments, or -1 if the root doesn't apply.

    A ``{param}`` segment in the root matches any single path segment (wildcard).
    """
    if len(rel_parts) < len(root_parts):
        return -1
    for rp, kp in zip(rel_parts, root_parts):
        if kp.startswith("{") and kp.endswith("}"):
            continue
        if rp != kp:
            return -1
    return len(root_parts)


def classify(path: "str | Path") -> "str | None":
    """Return the registry kind whose canonical root contains ``path`` (longest match).

    Templated root segments (``{batch_id}``, ``{lane}`` …) match any segment, so a
    concrete production/batch path still classifies correctly.
    """
    rel_parts = rel_canonical(path).split("/")
    candidates: list = []
    for key, entry in REGISTRY.items():
        score = _match_root(rel_parts, entry.root.split("/"))
        if score >= 0:
            # prefer the more specific (deeper) root; break ties so a file kind
            # (non-dir) wins over the bare directory kind sharing its root.
            candidates.append((score, not entry.is_dir, key))
    if not candidates:
        return None
    candidates.sort(reverse=True)
    return candidates[0][2]


def is_canonical(path: "str | Path") -> "tuple[bool, list[str]]":
    """Validate ``path`` against the registry. Returns ``(ok, reasons)``.

    A path is canonical when it is under the workspace, uses canonical top-level
    casing, and is not a stray file sitting directly at the workspace root.
    """
    reasons: list[str] = []
    p = Path(path)
    if not p.is_absolute():
        p = WORKSPACE / p
    try:
        rel_parts = p.relative_to(WORKSPACE).parts
    except ValueError:
        return False, ["outside the workspace"]
    if has_case_drift(p):
        head = rel_parts[0]
        reasons.append(f"case drift: '{head}' should be '{CANONICAL_TOP[head.lower()]}'")
    if len(rel_parts) == 1:
        reasons.append("stray output at workspace root (no canonical sub-directory)")
    return (not reasons), reasons


def registry_entries() -> list:
    """Public listing of the registry (for the validator / docs / tooling)."""
    return [
        {"key": e.key, "root": e.root, "template": e.template,
         "is_dir": e.is_dir, "description": e.description}
        for e in _KINDS
    ]


# --------------------------------------------------------------------------- stamping
def current_terminal() -> str:
    for var in ("GROK_TERMINAL", "TERMINAL_ID", "GROK_LANE", "WAVE_TERMINAL"):
        val = os.environ.get(var)
        if val:
            return val
    return "unknown"


def make_stamp(kind: str, path: "str | Path", *, params: "dict | None" = None,
               terminal: "str | None" = None, extra: "dict | None" = None) -> dict:
    entry = REGISTRY.get(kind)
    stamp = {
        "key": kind,
        "kind_root": entry.root if entry else None,
        "canonical_path": rel_canonical(path),
        "stamped_at": _utc_now(),
        "terminal": terminal or current_terminal(),
        "params": params or {},
        "registry": "tools/output_registry.py#259",
    }
    if extra:
        stamp.update(extra)
    return stamp


def record_ledger(stamp: dict, *, ledger: "Path | None" = None) -> None:
    """Append one stamp line to the append-only ledger."""
    ledger = ledger or LEDGER_PATH
    ledger.parent.mkdir(parents=True, exist_ok=True)
    with ledger.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(stamp, ensure_ascii=False) + "\n")


def stamp_payload(payload: dict, kind: str, path: "str | Path", **stamp_kw) -> dict:
    """Embed an ``_output_stamp`` block into a JSON-bound dict payload (in place)."""
    payload[STAMP_KEY] = make_stamp(kind, path, **stamp_kw)
    return payload


def canonical_str(path: "str | Path") -> str:
    """Canonical workspace-relative pointer string (fixes ``STUDIO/`` → ``Studio/``).

    Use when *embedding* a path into output data so every emitted pointer is
    canonical regardless of how it was typed.
    """
    return rel_canonical(path)


def note(path: "str | Path", *, kind: "str | None" = None, terminal: "str | None" = None,
         ledger: bool = True, **meta) -> "tuple[bool, str | None]":
    """One-line registry adoption for an *already-written* output.

    Classifies ``path`` against the registry, records a ledger stamp (so the
    validator can audit it), and returns ``(is_canonical_ok, kind)``. Producers add
    ``note(out_path)`` after each write to adopt the registry without restructuring
    their path logic — and to surface drift the moment it happens.
    """
    resolved_kind = kind or classify(path)
    ok, _reasons = is_canonical(path)
    if ledger:
        stamp = make_stamp(resolved_kind or "unregistered", path,
                           terminal=terminal, extra={"canonical": ok, **meta})
        record_ledger(stamp)
    return ok, resolved_kind


def write_stamped(
    kind: str,
    payload,
    *,
    params: "dict | None" = None,
    terminal: "str | None" = None,
    indent: int = 2,
    ledger: bool = True,
    **stamp_extra,
) -> Path:
    """Resolve the canonical path for ``kind``, write ``payload`` there, and stamp it.

    ``payload`` may be a ``dict`` (written as JSON with an embedded ``_output_stamp``),
    a ``str`` (written as text + a ``<file>.stamp.json`` sidecar), or ``bytes`` (binary
    + sidecar). Every write also appends to the ledger unless ``ledger=False``.
    """
    params = params or {}
    path = resolve(kind, **params)
    stamp = make_stamp(kind, path, params=params, terminal=terminal,
                       extra={k: v for k, v in stamp_extra.items()})

    if isinstance(payload, dict):
        body = dict(payload)
        body[STAMP_KEY] = stamp
        path.write_text(json.dumps(body, indent=indent, ensure_ascii=False), encoding="utf-8")
    elif isinstance(payload, str):
        path.write_text(payload, encoding="utf-8")
        _write_sidecar(path, stamp)
    elif isinstance(payload, (bytes, bytearray)):
        path.write_bytes(bytes(payload))
        _write_sidecar(path, stamp)
    else:
        raise TypeError(f"write_stamped payload must be dict|str|bytes, got {type(payload).__name__}")

    if ledger:
        record_ledger(stamp)
    return path


def _write_sidecar(path: Path, stamp: dict) -> None:
    sidecar = path.with_name(path.name + ".stamp.json")
    sidecar.write_text(json.dumps(stamp, indent=2, ensure_ascii=False), encoding="utf-8")


__all__ = [
    "OutputKind",
    "REGISTRY",
    "CANONICAL_TOP",
    "LEDGER_PATH",
    "STAMP_KEY",
    "canonicalize",
    "rel_canonical",
    "has_case_drift",
    "resolve",
    "classify",
    "is_canonical",
    "registry_entries",
    "current_terminal",
    "make_stamp",
    "record_ledger",
    "stamp_payload",
    "canonical_str",
    "note",
    "write_stamped",
]


if __name__ == "__main__":  # pragma: no cover - quick introspection
    import argparse

    for _s in (sys.stdout, sys.stderr):
        try:
            _s.reconfigure(encoding="utf-8", errors="replace")  # type: ignore[union-attr]
        except Exception:
            pass

    ap = argparse.ArgumentParser(description="Canonical output-path registry (#259)")
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("list", help="List registry kinds")
    rp = sub.add_parser("resolve", help="Resolve a kind to its canonical path")
    rp.add_argument("kind")
    rp.add_argument("params", nargs="*", help="key=value template params")
    args = ap.parse_args()

    if args.cmd == "list":
        for e in registry_entries():
            tmpl = f"/{e['template']}" if e["template"] else ""
            print(f"  {e['key']:22} → {e['root']}{tmpl}{'  (dir)' if e['is_dir'] else ''}")
            print(f"  {'':22}   {e['description']}")
    elif args.cmd == "resolve":
        kv = dict(p.split("=", 1) for p in args.params if "=" in p)
        print(resolve(args.kind, mkdirs=False, **kv))
