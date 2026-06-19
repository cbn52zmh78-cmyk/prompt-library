#!/usr/bin/env python3
"""SCRIBE Editorial Engine — issue #212.

Drives a written client deliverable through the seven-stage editorial pipeline:

    intake → coverage → architecture → development → draft → revision → deliver

with the Editorial Gate (artifacts/legal/editorial_gate.py) enforced at the two
hard boundaries — intake (a RED gate blocks the project before any work) and
deliver (the gate must be clear, or signed off, before a package ships).

The engine reuses SCRIBE's screenplay coverage for Fountain sources and computes
an equivalent prose coverage for manuscripts/essays/briefs. Every generated
document keeps the SCRIBE house tone: measured fields are computed; editorial
fields describe what is present and never pronounce artistic value.

Usage:
    python Content_Production/SCRIBE/editorial_engine.py stages
    python Content_Production/SCRIBE/editorial_engine.py gate manuscript.md --meta meta.json
    python Content_Production/SCRIBE/editorial_engine.py coverage script.fountain -o build/
    python Content_Production/SCRIBE/editorial_engine.py run manuscript.md --meta meta.json
    python Content_Production/SCRIBE/editorial_engine.py run draft.md --through development --dry-run
    python Content_Production/SCRIBE/editorial_engine.py run draft.md --revision 2 --change-note "address act-two notes"
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

HERE = Path(__file__).resolve().parent          # .../Content_Production/SCRIBE
ROOT = HERE.parents[1]                           # .../Grok Projects
GATE_DIR = ROOT / "artifacts" / "legal"
EDITORIALS_DIR = HERE / "editorials"

for _p in (str(HERE), str(GATE_DIR)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from editorial_gate import evaluate_editorial_gate  # noqa: E402

STAGES = ["intake", "coverage", "architecture", "development", "draft", "revision", "deliver"]

GATE_EXIT_RED = 2
GATE_EXIT_SIGNOFF_REQUIRED = 3

WORDS_PER_MINUTE = 250  # silent-reading rule of thumb for prose runtime estimates

_HEADER_RE = re.compile(r"^(#{1,6})\s+(.*)$")
_CHAPTER_RE = re.compile(r"^\s*(chapter|part|act|book)\s+([\w\d]+)\b.*$", re.I)
_SCENE_HEAD_RE = re.compile(r"^\s*(INT|EXT|EST|INT/EXT|I/E)[\.\s/]", re.I)
_SENTENCE_RE = re.compile(r"[.!?]+[\s\"')\]]*(?=\s+[A-Z0-9\"'(]|$)")
_PROPER_NAME_RE = re.compile(r"\b([A-Z][a-z]{2,}(?:\s+[A-Z][a-z]+){0,2})\b")
_STOP_NAMES = {
    "The", "A", "An", "And", "But", "Or", "If", "When", "Then", "She", "He", "They",
    "It", "We", "You", "I", "His", "Her", "Their", "This", "That", "Chapter", "Part",
    "Act", "Scene", "Genre", "Sources", "Note", "Notes", "By", "From", "With",
}


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _slugify(text: str) -> str:
    s = re.sub(r"[^a-z0-9]+", "_", (text or "untitled").lower()).strip("_")
    return s or "untitled"


def _rel(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT)).replace("\\", "/")
    except ValueError:
        return str(path).replace("\\", "/")


def _write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


def _write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


# --------------------------------------------------------------------------- model
@dataclass
class EditorialProject:
    project_id: str
    source: Path
    text: str
    meta: dict[str, Any]
    doc_kind: str                      # "screenplay" | "prose"
    out_dir: Path
    stages: list[dict[str, Any]] = field(default_factory=list)
    revisions: list[dict[str, Any]] = field(default_factory=list)

    def stage(self, name: str) -> Optional[dict[str, Any]]:
        return next((s for s in self.stages if s["name"] == name), None)

    def record(self, name: str, status: str, *, artifact: Optional[Path] = None, **detail: Any) -> None:
        row = {
            "name": name,
            "status": status,
            "artifact": _rel(artifact) if artifact else None,
            "at": _utc_now(),
            **detail,
        }
        existing = self.stage(name)
        if existing:
            self.stages[self.stages.index(existing)] = row
        else:
            self.stages.append(row)


def detect_doc_kind(source: Path, text: str) -> str:
    if source.suffix.lower() in {".fountain", ".spmd"}:
        return "screenplay"
    scene_heads = sum(1 for line in text.splitlines() if _SCENE_HEAD_RE.match(line))
    return "screenplay" if scene_heads >= 3 else "prose"


def load_meta(meta_arg: Optional[str], source: Path) -> dict[str, Any]:
    """Meta from --meta JSON, or a `<source>.meta.json` sidecar, or {}."""
    if meta_arg:
        p = Path(meta_arg)
        if not p.is_absolute():
            p = (Path.cwd() / p)
        return json.loads(p.read_text(encoding="utf-8"))
    sidecar = source.with_suffix(source.suffix + ".meta.json")
    if sidecar.is_file():
        return json.loads(sidecar.read_text(encoding="utf-8"))
    return {}


def open_project(source_arg: str, meta_arg: Optional[str], out_arg: Optional[str],
                 project_id: Optional[str]) -> EditorialProject:
    source = Path(source_arg)
    if not source.is_absolute():
        source = (Path.cwd() / source).resolve()
    if not source.is_file():
        raise SystemExit(f"[editorial] source not found: {source}")
    text = source.read_text(encoding="utf-8")
    meta = load_meta(meta_arg, source)
    doc_kind = meta.get("doc_kind") or detect_doc_kind(source, text)
    pid = project_id or meta.get("project_id") or _slugify(meta.get("title") or source.stem)
    out_dir = Path(out_arg) if out_arg else (EDITORIALS_DIR / pid)
    if not out_dir.is_absolute():
        out_dir = ROOT / out_dir
    return EditorialProject(pid, source, text, meta, doc_kind, out_dir)


# --------------------------------------------------------------------------- coverage
@dataclass
class ProseCoverage:
    title: str
    author: str
    word_count: int
    est_reading_min: int
    paragraph_count: int
    sentence_count: int
    unit_label: str               # "chapter" | "section"
    units: list[dict[str, Any]]   # [{index, heading, words}]
    named_entities: list[tuple[str, int]]
    prepared_on: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "kind": "prose",
            "title": self.title,
            "author": self.author,
            "word_count": self.word_count,
            "est_reading_min": self.est_reading_min,
            "paragraph_count": self.paragraph_count,
            "sentence_count": self.sentence_count,
            "unit_label": self.unit_label,
            "unit_count": len(self.units),
            "units": self.units,
            "named_entities": self.named_entities,
            "prepared_on": self.prepared_on,
        }


def build_prose_coverage(text: str, meta: dict[str, Any]) -> ProseCoverage:
    lines = text.splitlines()
    units: list[dict[str, Any]] = []
    current: Optional[dict[str, Any]] = None
    seen_title = False

    def _open(heading: str) -> None:
        nonlocal current
        current = {"index": len(units) + 1, "heading": heading.strip(), "words": 0}
        units.append(current)

    for line in lines:
        hm = _HEADER_RE.match(line)
        cm = _CHAPTER_RE.match(line)
        if hm and len(hm.group(1)) == 1 and not seen_title:
            seen_title = True  # leading H1 is the document title, not a content unit
            continue
        if cm:  # "Chapter N" / "Part N" as a plain line
            _open(line.strip())
            continue
        if hm and 1 <= len(hm.group(1)) <= 3 and not hm.group(2).startswith(("Sources", "Genre")):
            _open(hm.group(2))
            continue
        wc = len(line.split())
        if current is not None:
            current["words"] += wc

    if not units:  # undivided document — treat the whole as one unit
        units = [{"index": 1, "heading": meta.get("title") or "(whole document)",
                  "words": len(text.split())}]
    _chap = re.compile(r"^(chapter|part|act|book)\b", re.I)
    unit_label = "chapter" if any(_chap.match(u["heading"]) for u in units) else "section"

    title_line = next((m.group(2).strip() for ln in lines
                       if (m := _HEADER_RE.match(ln)) and len(m.group(1)) == 1), "")
    title = meta.get("title") or title_line or "Untitled"
    words = len(text.split())
    paragraphs = sum(1 for block in re.split(r"\n\s*\n", text) if block.strip())
    sentences = len(_SENTENCE_RE.findall(text)) or max(1, text.count(".") )

    name_counts: Counter = Counter()
    for m in _PROPER_NAME_RE.finditer(text):
        token = m.group(1).split()[0]
        if token in _STOP_NAMES:
            continue
        name_counts[m.group(1)] += 1
    entities = [(n, c) for n, c in name_counts.most_common(20) if c >= 2]

    return ProseCoverage(
        title=title,
        author=meta.get("author") or meta.get("client") or "",
        word_count=words,
        est_reading_min=max(1, round(words / WORDS_PER_MINUTE)),
        paragraph_count=paragraphs,
        sentence_count=sentences,
        unit_label=unit_label,
        units=units,
        named_entities=entities,
        prepared_on=meta.get("prepared_on") or _utc_now()[:10],
    )


def prose_coverage_markdown(c: ProseCoverage) -> str:
    L = ["# SCRIBE Coverage Report", "",
         f"**Title**: {c.title}  ",
         f"**Author / Credit**: {c.author or '—'}  ",
         f"**Format**: Prose manuscript  ",
         f"**Date**: {c.prepared_on}  ",
         f"**Length**: {c.word_count} words (~{c.est_reading_min} min read) · "
         f"{len(c.units)} {c.unit_label}(s)", "", "---", "",
         "## Logline",
         "_[Reader to complete — one sentence: protagonist, goal, central thread.]_", "",
         "## Synopsis",
         "_[Reader to complete — neutral beat-by-beat summary of the work as presented.]_", "",
         "## Measured Overview", "",
         "| Field | Value |", "|-------|-------|",
         f"| Word count | {c.word_count} |",
         f"| Est. reading time | ~{c.est_reading_min} min ({WORDS_PER_MINUTE} wpm) |",
         f"| {c.unit_label.capitalize()}s | {len(c.units)} |",
         f"| Paragraphs | {c.paragraph_count} |",
         f"| Sentences (approx.) | {c.sentence_count} |",
         f"| Recurring named entities | {len(c.named_entities)} |", ""]
    L += [f"## {c.unit_label.capitalize()} Map", "",
          f"| # | {c.unit_label.capitalize()} | Words |",
          "|--:|------|------:|"]
    for u in c.units[:80]:
        L.append(f"| {u['index']} | {u['heading'] or '—'} | {u['words']} |")
    L.append("")
    if c.named_entities:
        L += ["## Recurring Named Entities (by frequency)", "",
              "| Entity | Mentions |", "|--------|---------:|"]
        for name, count in c.named_entities:
            L.append(f"| {name} | {count} |")
        L.append("")
    L += ["## Comments",
          "_[Reader to complete — observational notes on structure, pacing, clarity, "
          "and open threads, per SCRIBE tone guidelines. Describe what is present; do "
          "not pronounce value.]_", "", "---", "",
          "*Prepared by SCRIBE. Measured fields are computed from the manuscript as "
          "submitted. Editorial fields describe what is present in the material reviewed; "
          "they do not evaluate artistic merit or writing quality.*"]
    return "\n".join(L) + "\n"


def coverage_for(project: EditorialProject) -> tuple[dict[str, Any], str]:
    """Return (coverage_dict, coverage_markdown) for the project's doc kind."""
    if project.doc_kind == "screenplay":
        from screenplay.coverage import build_coverage, coverage_markdown
        try:
            report = build_coverage(project.text)
        except Exception:  # noqa: BLE001 - paginator optional; estimate pages from lines
            est_pages = max(1, len(project.text.splitlines()) // 55)
            report = build_coverage(project.text, page_count=est_pages)
        cov = report.to_dict()
        cov["kind"] = "screenplay"
        cov.setdefault("unit_label", "scene")
        cov["unit_count"] = report.scene_count
        cov["word_count"] = sum(c.get("dialogue_words", 0) for c in report.characters)
        return cov, coverage_markdown(report)
    pc = build_prose_coverage(project.text, project.meta)
    return pc.to_dict(), prose_coverage_markdown(pc)


# --------------------------------------------------------------------------- stages
def stage_intake(p: EditorialProject) -> dict[str, Any]:
    gate = evaluate_editorial_gate(p.text, p.meta).to_dict()
    blocked = gate.get("blocked")
    p.record("intake", "blocked" if blocked else "done",
             gate_verdict=gate.get("verdict"), doc_kind=p.doc_kind)
    _write_json(p.out_dir / "intake.json",
                {"project_id": p.project_id, "source": _rel(p.source), "doc_kind": p.doc_kind,
                 "meta": p.meta, "gate": gate, "at": _utc_now()})
    return gate


def stage_coverage(p: EditorialProject) -> dict[str, Any]:
    cov, md = coverage_for(p)
    _write_json(p.out_dir / "coverage.json", cov)
    _write_text(p.out_dir / "coverage.md", md)
    p.record("coverage", "done", artifact=p.out_dir / "coverage.md",
             units=cov.get("unit_count"), words=cov.get("word_count"))
    return cov


def stage_architecture(p: EditorialProject, cov: dict[str, Any]) -> dict[str, Any]:
    label = cov.get("unit_label", "section")
    if p.doc_kind == "screenplay":
        units = [{"index": i + 1, "heading": s["heading"], "size": 1}
                 for i, s in enumerate(cov.get("scene_count_detail", []))]
    else:
        units = [{"index": u["index"], "heading": u["heading"], "size": u["words"]}
                 for u in cov.get("units", [])]
    n = len(units)
    # Describe the spine by position only — no value judgment on the content.
    thirds = {"opening": units[: max(1, n // 3)],
              "middle": units[max(1, n // 3): max(1, 2 * n // 3)],
              "closing": units[max(1, 2 * n // 3):]} if n else {}
    arch = {
        "project_id": p.project_id,
        "unit_label": label,
        "unit_count": n,
        "units": units,
        "spine": {k: [u["index"] for u in v] for k, v in thirds.items()},
        "total_size": sum(u["size"] for u in units),
        "at": _utc_now(),
    }
    _write_json(p.out_dir / "architecture.json", arch)
    L = [f"# Structure Architecture — {p.project_id}", "",
         f"Document kind: **{p.doc_kind}** · {n} {label}(s)", "", "## Outline", ""]
    for u in units:
        L.append(f"{u['index']:>3}. {u['heading'] or '—'}  _({u['size']} {'words' if p.doc_kind=='prose' else 'unit'})_")
    L += ["", "## Spine (by position, not value)", ""]
    for seg, idxs in arch["spine"].items():
        L.append(f"- **{seg}**: {label}s {idxs[0]}–{idxs[-1]}" if idxs else f"- **{seg}**: —")
    L += ["", "*Structural map only — positions and sizes are measured; no evaluation of merit.*"]
    _write_text(p.out_dir / "architecture.md", "\n".join(L) + "\n")
    p.record("architecture", "done", artifact=p.out_dir / "architecture.md", units=n)
    return arch


def stage_development(p: EditorialProject, arch: dict[str, Any]) -> Path:
    label = arch["unit_label"]
    L = [f"# Development Notes — {p.project_id}", "",
         "Scaffold for developmental editing. Observation slots follow the Editing "
         "Federation lenses; fill them with what is present, per SCRIBE tone "
         "(describe, never grade).", "",
         "## Per-" + label + " Observations", ""]
    for u in arch["units"]:
        L += [f"### {label.capitalize()} {u['index']} — {u['heading'] or '—'}",
              "- Structure: _[observation]_",
              "- Continuity / clarity: _[observation]_",
              "- Open threads introduced: _[list]_", ""]
    L += ["## Editing Federation Lenses", "",
          "- **Narrative** (arcs, beats, continuity, open threads): _[notes]_",
          "- **Structure** (act/chapter/scene shape, formatting): _[notes]_",
          "- **Tone** (register, voice consistency, narrative mode): _[notes]_",
          "- **Dialogue** (voice distinction, speech patterns): _[notes]_", "",
          "## Open-Thread Register", "",
          "| # | Thread introduced | First location | Resolved? |",
          "|--:|-------------------|----------------|-----------|",
          "| 1 | _[thread]_ | _[loc]_ | _[y/n]_ |", "",
          "*Developmental scaffold. Observations describe what is present; they do not "
          "evaluate artistic merit or writing quality.*"]
    path = p.out_dir / "development_notes.md"
    _write_text(path, "\n".join(L) + "\n")
    p.record("development", "done", artifact=path, units=arch["unit_count"])
    return path


def stage_draft(p: EditorialProject, revision_round: int) -> dict[str, Any]:
    suffix = p.source.suffix if p.source.suffix in {".md", ".txt", ".fountain"} else ".md"
    draft_path = p.out_dir / "drafts" / f"draft_v{revision_round}{suffix}"
    _write_text(draft_path, p.text)
    metrics = {"words": len(p.text.split()), "lines": len(p.text.splitlines()),
               "chars": len(p.text)}
    rec = {"round": revision_round, "draft": _rel(draft_path), "metrics": metrics, "at": _utc_now()}
    p.record("draft", "done", artifact=draft_path, round=revision_round, words=metrics["words"])
    return rec


def stage_revision(p: EditorialProject, draft_rec: dict[str, Any], revision_round: int,
                   change_note: Optional[str]) -> dict[str, Any]:
    prev = p.revisions[-1] if p.revisions else None
    prev_words = prev["draft_metrics"]["words"] if prev else None
    delta = (draft_rec["metrics"]["words"] - prev_words) if prev_words is not None else 0
    entry = {
        "round": revision_round,
        "change_note": change_note or ("initial draft" if revision_round <= 1 else "revision"),
        "draft_metrics": draft_rec["metrics"],
        "word_delta_vs_prev": delta,
        "at": _utc_now(),
    }
    p.revisions.append(entry)
    p.record("revision", "done", round=revision_round, word_delta=delta)
    return entry


def stage_deliver(p: EditorialProject, *, dry_run: bool) -> tuple[dict[str, Any], int]:
    gate = evaluate_editorial_gate(p.text, p.meta).to_dict()
    deliverable = bool(p.meta.get("client_deliverable"))
    signed = bool(p.meta.get("human_signoff")) or bool(gate.get("human_signoff"))

    required_done = all((p.stage(s) or {}).get("status") == "done"
                        for s in ["coverage", "architecture", "development", "draft", "revision"])

    if gate.get("blocked"):
        p.record("deliver", "blocked", gate_verdict=gate["verdict"], reason="editorial gate RED")
        return gate, GATE_EXIT_RED
    if not required_done:
        p.record("deliver", "blocked", reason="prior stages incomplete")
        return gate, GATE_EXIT_SIGNOFF_REQUIRED
    if gate.get("requires_human_signoff") and deliverable and not signed:
        p.record("deliver", "needs_signoff", gate_verdict=gate["verdict"],
                 reason="YELLOW gate unsigned on client deliverable")
        return gate, GATE_EXIT_SIGNOFF_REQUIRED
    if dry_run:
        p.record("deliver", "skipped", reason="dry-run", gate_verdict=gate["verdict"])
        return gate, 0

    package = {
        "project_id": p.project_id,
        "delivered_at": _utc_now(),
        "doc_kind": p.doc_kind,
        "final_draft": p.revisions[-1]["draft_metrics"] if p.revisions else None,
        "revision_round": p.revisions[-1]["round"] if p.revisions else 1,
        "gate": gate,
        "ip_statement": (
            "Work-for-hire: all rights in the deliverable are assigned to the client."
            if (p.meta.get("ip_attestation") or gate["checklist"].get("row_1_client_ip") == "PASS")
            else "IP ownership UNCONFIRMED — record assignment before release."
        ),
        "originality_statement": (
            "Originality attested for this deliverable."
            if (p.meta.get("originality_attestation") or gate["checklist"].get("row_2_originality") == "PASS")
            else "Originality UNCONFIRMED — run an originality check before release."
        ),
        "artifacts": {s["name"]: s.get("artifact") for s in p.stages if s.get("artifact")},
    }
    _write_json(p.out_dir / "delivery_manifest.json", package)
    p.record("deliver", "done", artifact=p.out_dir / "delivery_manifest.json",
             gate_verdict=gate["verdict"])
    return gate, 0


# --------------------------------------------------------------------------- driver
def write_manifest(p: EditorialProject, gate_intake: dict[str, Any],
                   gate_deliver: Optional[dict[str, Any]], revision_round: int) -> Path:
    delivered = (p.stage("deliver") or {}).get("status") == "done"
    cov_stage = p.stage("coverage") or {}
    manifest = {
        "engine": "editorial",
        "version": "1.0",
        "issue": 212,
        "project_id": p.project_id,
        "generated_at": _utc_now(),
        "source": _rel(p.source),
        "doc_kind": p.doc_kind,
        "meta": p.meta,
        "stages": p.stages,
        "gate_intake": gate_intake,
        "gate_deliver": gate_deliver,
        "revision_round": revision_round,
        "revisions": p.revisions,
        "editorial_summary": {
            "gate_verdict": (gate_deliver or gate_intake).get("verdict"),
            "units": cov_stage.get("units"),
            "words": cov_stage.get("words"),
            "delivered": delivered,
            "stages_done": sum(1 for s in p.stages if s["status"] == "done"),
        },
    }
    path = p.out_dir / "manifest.json"
    _write_json(path, manifest)
    return path


def cmd_run(args: argparse.Namespace) -> int:
    p = open_project(args.source, args.meta, args.out, args.project_id)
    through = args.through
    if through not in STAGES:
        raise SystemExit(f"--through must be one of {STAGES}")
    target = STAGES.index(through)
    revision_round = max(1, args.revision)

    print(f"[editorial] project={p.project_id} kind={p.doc_kind} through={through} "
          f"dry_run={args.dry_run} round={revision_round}")

    gate_intake = stage_intake(p)
    print(f"  intake     gate={gate_intake['verdict']} "
          f"checklist={ {k: v for k, v in gate_intake['checklist'].items() if v != 'PASS'} or 'all PASS'}")
    if gate_intake.get("blocked"):
        for h in gate_intake.get("hard_stops", []):
            print(f"    🛑 {h}")
        write_manifest(p, gate_intake, None, revision_round)
        print(f"[editorial] BLOCKED at intake → {_rel(p.out_dir / 'manifest.json')}")
        return GATE_EXIT_RED

    cov = arch = None
    deliver_gate: Optional[dict[str, Any]] = None
    rc = 0
    for idx, stage in enumerate(STAGES):
        if idx > target:
            break
        if stage == "intake":
            continue
        if stage == "coverage":
            cov = stage_coverage(p)
            print(f"  coverage   {cov.get('unit_count')} {cov.get('unit_label')}(s), "
                  f"{cov.get('word_count')} words → coverage.md")
        elif stage == "architecture":
            arch = stage_architecture(p, cov)
            print(f"  architecture {arch['unit_count']} unit(s) → architecture.md")
        elif stage == "development":
            stage_development(p, arch)
            print("  development scaffold → development_notes.md")
        elif stage == "draft":
            p._draft_rec = stage_draft(p, revision_round)  # type: ignore[attr-defined]
            print(f"  draft      v{revision_round} ({p._draft_rec['metrics']['words']} words)")
        elif stage == "revision":
            entry = stage_revision(p, p._draft_rec, revision_round, args.change_note)  # type: ignore[attr-defined]
            print(f"  revision   round {revision_round} (Δ{entry['word_delta_vs_prev']:+d} words)")
        elif stage == "deliver":
            deliver_gate, rc = stage_deliver(p, dry_run=args.dry_run)
            st = (p.stage('deliver') or {}).get('status')
            print(f"  deliver    {st} (gate={deliver_gate['verdict']})")

    manifest_path = write_manifest(p, gate_intake, deliver_gate, revision_round)
    summary = json.loads(manifest_path.read_text(encoding="utf-8"))["editorial_summary"]
    print(f"[editorial] manifest → {_rel(manifest_path)}")
    print(f"[editorial] summary: {summary}")
    return rc


def cmd_gate(args: argparse.Namespace) -> int:
    p = open_project(args.source, args.meta, None, None)
    gate = evaluate_editorial_gate(p.text, p.meta).to_dict()
    print(json.dumps(gate, indent=2, ensure_ascii=False))
    if gate.get("blocked"):
        return GATE_EXIT_RED
    if gate.get("requires_human_signoff"):
        return GATE_EXIT_SIGNOFF_REQUIRED
    return 0


def cmd_coverage(args: argparse.Namespace) -> int:
    p = open_project(args.source, args.meta, args.out, args.project_id)
    cov, md = coverage_for(p)
    out_dir = p.out_dir
    _write_json(out_dir / "coverage.json", cov)
    _write_text(out_dir / "coverage.md", md)
    print(f"[editorial] coverage ({p.doc_kind}) → {_rel(out_dir / 'coverage.md')}")
    print(f"  {cov.get('unit_count')} {cov.get('unit_label')}(s), {cov.get('word_count')} words")
    return 0


def cmd_stages(_: argparse.Namespace) -> int:
    print("Editorial engine stages (issue #212):")
    for i, s in enumerate(STAGES, 1):
        gate = " ← Editorial Gate" if s in {"intake", "deliver"} else ""
        print(f"  {i}. {s}{gate}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="SCRIBE editorial engine — intake→…→deliver + Editorial Gate")
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("stages", help="List the pipeline stages").set_defaults(func=cmd_stages)

    g = sub.add_parser("gate", help="Run the Editorial Gate on a document")
    g.add_argument("source")
    g.add_argument("--meta", help="Path to meta JSON (else <source>.meta.json sidecar)")
    g.set_defaults(func=cmd_gate)

    c = sub.add_parser("coverage", help="Produce SCRIBE coverage only")
    c.add_argument("source")
    c.add_argument("--meta")
    c.add_argument("--project-id")
    c.add_argument("-o", "--out", help="Output directory")
    c.set_defaults(func=cmd_coverage)

    r = sub.add_parser("run", help="Run the editorial pipeline")
    r.add_argument("source")
    r.add_argument("--meta")
    r.add_argument("--project-id")
    r.add_argument("-o", "--out", help="Output directory (default: SCRIBE/editorials/<id>)")
    r.add_argument("--through", default="deliver", choices=STAGES, help="Run up to and including this stage")
    r.add_argument("--revision", type=int, default=1, help="Revision round number")
    r.add_argument("--change-note", help="Change-log note for this revision round")
    r.add_argument("--dry-run", action="store_true", help="Assess + scaffold; do not write delivery package")
    r.set_defaults(func=cmd_run)

    return parser


def main(argv: Optional[list[str]] = None) -> int:
    args = build_parser().parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
