#!/usr/bin/env python3
"""DAVID batch runner — concepts folder → Gate 0 intake → draft render → manifest → promote.

Turns one-at-a-time production into volume:
  folder of *.concept.json  →  intake (Gate 0 enforced)  →  480p draft render
  →  qa_report per item  →  batch manifest (pass/fail/needs-signoff)
  →  promote subcommand re-renders approved items at 720p final.

Rate-limit aware: sequential processing, exponential backoff on timeout/rate-limit,
--concat-only cache resume when shots are partially cached (T1 shot-6 recovery pattern).

Usage:
    python DAVID/scripts/batch_runner.py run STUDIO/Pipeline/Concepts/dead_languages --dry-run
    python DAVID/scripts/batch_runner.py run STUDIO/Pipeline/Concepts/dead_languages
    python DAVID/scripts/batch_runner.py promote DAVID/batches/<id>/manifest.json
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

ROOT = Path(__file__).resolve().parents[2]
DAVID = ROOT / "DAVID"
PIPELINE = ROOT / "STUDIO" / "Pipeline"
INTAKE = PIPELINE / "production_intake.py"
RENDER = DAVID / "scripts" / "render_longform.py"

GATE_EXIT_RED = 2
GATE_EXIT_SIGNOFF_REQUIRED = 3

DRAFT_RES = "480p"
FINAL_RES = "720p"

DEFAULT_T3_CONCEPTS = PIPELINE / "Concepts" / "dead_languages"

TIMEOUT_RE = re.compile(
    r"timeout|timed out|deadline exceeded|read timed out|operation timed out|600s",
    re.I,
)
RATE_LIMIT_RE = re.compile(r"rate.?limit|too many requests|429|quota", re.I)

SHOT_MP4_RE = re.compile(r"\.mp4$", re.I)


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _import_intake():
    if str(PIPELINE) not in sys.path:
        sys.path.insert(0, str(PIPELINE))
    import production_intake as intake  # noqa: WPS433

    return intake


def discover_concepts(concepts_dir: Path) -> list[Path]:
    if not concepts_dir.is_dir():
        raise FileNotFoundError(f"Concepts folder not found: {concepts_dir}")
    files = sorted(concepts_dir.glob("*.concept.json"))
    if not files:
        raise FileNotFoundError(f"No *.concept.json in {concepts_dir}")
    return files


def gate_allows_render(gate: dict[str, Any]) -> tuple[bool, str]:
    if gate.get("blocked") or gate.get("verdict") == "RED":
        return False, "skipped_red"
    if gate.get("requires_human_signoff") and not gate.get("human_signoff"):
        return False, "needs_signoff"
    return True, "eligible"


def resolve_production_dir(script: dict[str, Any]) -> Path:
    if script.get("production_dir"):
        raw = str(script["production_dir"]).replace("\\", "/")
        if raw.startswith("STUDIO/"):
            return ROOT / raw.replace("/", "\\") if "\\" in str(ROOT) else ROOT / raw
        p = Path(script["production_dir"])
        return p if p.is_absolute() else (DAVID / p)
    slug = script.get("slug", "longform")
    fmt = script.get("format_id", "")
    if fmt and fmt != "documentary-host":
        return ROOT / "STUDIO" / "Productions" / "Editorial" / f"{slug}_longform_v1"
    return DAVID / "productions" / f"{slug}_longform_v1"


def patch_resolution(script: dict[str, Any], resolution: str, *, phase: str, batch_id: str) -> dict[str, Any]:
    out = json.loads(json.dumps(script))
    out.setdefault("config", {})["resolution"] = resolution
    out.setdefault("batch", {})["batch_id"] = batch_id
    out["batch"]["phase"] = phase
    out["batch"]["resolution"] = resolution
    return out


def write_script(script: dict[str, Any], path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(script, indent=2, ensure_ascii=False), encoding="utf-8")
    return path


def run_intake(concept_path: Path) -> tuple[Optional[dict[str, Any]], dict[str, Any], int]:
    """Return (script_or_none, gate_stamp, exit_code)."""
    intake = _import_intake()
    concept = json.loads(concept_path.read_text(encoding="utf-8"))
    try:
        script = intake.build_longform_script(concept)
    except intake.Gate0BlockedError as exc:
        return None, exc.stamp, GATE_EXIT_RED

    gate = script["intake"]["gate_0"]
    exit_code = 0
    if gate.get("requires_human_signoff") and not gate.get("human_signoff"):
        exit_code = GATE_EXIT_SIGNOFF_REQUIRED
    return script, gate, exit_code


def count_cached_shots(prod_dir: Path) -> tuple[int, int]:
    shots_dir = prod_dir / "shots"
    if not shots_dir.is_dir():
        return 0, 0
    mp4s = [p for p in shots_dir.iterdir() if p.is_file() and SHOT_MP4_RE.search(p.name)]
    return len(mp4s), len(mp4s)


def can_concat_resume(script: dict[str, Any]) -> bool:
    """True when production dir has cached shot media worth concat-only resume."""
    prod_dir = resolve_production_dir(script)
    shots_dir = prod_dir / "shots"
    if not shots_dir.is_dir():
        return False
    shots = script.get("shots", [])
    if not shots:
        return False
    cached = 0
    for shot in shots:
        sid = shot["id"]
        candidates = list(shots_dir.glob(f"*{sid}*.mp4")) + list(shots_dir.glob(f"{sid}.mp4"))
        if any(p.stat().st_size > 10_000 for p in candidates if p.is_file()):
            cached += 1
    host_perf = shots_dir / "host_performance_extend.mp4"
    if host_perf.is_file() and host_perf.stat().st_size > 10_000:
        return True
    return cached >= max(1, len(shots) - 1)


def read_qa_report(prod_dir: Path) -> Optional[dict[str, Any]]:
    qa_path = prod_dir / "qa_report.json"
    if not qa_path.is_file():
        return None
    return json.loads(qa_path.read_text(encoding="utf-8"))


def render_script(
    script_path: Path,
    *,
    dry_run: bool,
    seamless_cli: bool,
    max_attempts: int,
    backoff_base: float,
    backoff_max: float,
) -> dict[str, Any]:
    """Run render_longform with timeout/rate-limit backoff and concat-only resume."""
    if dry_run:
        return {"exit_code": 0, "mode": "dry-run", "concat_only": False, "attempts": 0, "output": ""}

    script = json.loads(script_path.read_text(encoding="utf-8"))
    prod_dir = resolve_production_dir(script)

    cmd_base = [sys.executable, str(RENDER), str(script_path)]
    if seamless_cli:
        cmd_base.extend(["--seamless", "--match-color", "--cut-on-motion"])

    attempt = 0
    last_out = ""
    used_concat = False

    while attempt < max_attempts:
        attempt += 1
        concat_only = False
        if attempt > 1 and can_concat_resume(script):
            concat_only = True
            used_concat = True

        cmd = list(cmd_base)
        if concat_only:
            cmd.append("--concat-only")

        proc = subprocess.run(
            cmd,
            cwd=str(ROOT),
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
        last_out = (proc.stdout or "") + (proc.stderr or "")

        if proc.returncode == 0:
            return {
                "exit_code": 0,
                "mode": "concat-only" if concat_only else "full",
                "concat_only": concat_only,
                "attempts": attempt,
                "output": last_out[-4000:],
            }

        combined = last_out
        if RATE_LIMIT_RE.search(combined) or TIMEOUT_RE.search(combined):
            if can_concat_resume(script) and not concat_only:
                continue
            delay = min(backoff_base * (2 ** (attempt - 1)), backoff_max)
            print(f"  [batch] rate-limit/timeout — backoff {delay:.0f}s (attempt {attempt}/{max_attempts})")
            time.sleep(delay)
            continue
        break

    return {
        "exit_code": proc.returncode,
        "mode": "concat-only" if used_concat else "full",
        "concat_only": used_concat,
        "attempts": attempt,
        "output": last_out[-4000:],
    }


def classify_item(
    *,
    gate: dict[str, Any],
    render_result: Optional[dict[str, Any]],
    qa: Optional[dict[str, Any]],
    dry_run: bool,
) -> str:
    can_render, gate_status = gate_allows_render(gate)
    if gate_status == "skipped_red":
        return "skipped_red"
    if gate_status == "needs_signoff":
        return "needs_signoff"
    if dry_run:
        return "pending"
    if not render_result or render_result.get("exit_code") != 0:
        return "fail"
    if qa and qa.get("pass") is True:
        return "pass"
    return "fail"


def build_item_row(
    *,
    concept_path: Path,
    script_path: Optional[Path],
    gate: dict[str, Any],
    intake_exit: int,
    status: str,
    resolution: str,
    phase: str,
    render_result: Optional[dict[str, Any]] = None,
    qa: Optional[dict[str, Any]] = None,
    dry_run: bool = False,
) -> dict[str, Any]:
    prod_dir = None
    if script_path and script_path.is_file():
        script = json.loads(script_path.read_text(encoding="utf-8"))
        prod_dir = resolve_production_dir(script)

    promote_eligible = status == "pass" and bool(qa and qa.get("pass"))

    return {
        "slug": json.loads(concept_path.read_text(encoding="utf-8"))["slug"],
        "concept_path": str(concept_path.relative_to(ROOT)).replace("\\", "/"),
        "script_path": str(script_path.relative_to(ROOT)).replace("\\", "/") if script_path else None,
        "production_dir": str(prod_dir.relative_to(ROOT)).replace("\\", "/") if prod_dir else None,
        "gate_0_verdict": gate.get("verdict"),
        "gate_0_signed": bool(gate.get("human_signoff")),
        "gate_0_report": gate.get("report_path"),
        "intake_exit": intake_exit,
        "phase": phase,
        "resolution": resolution,
        "status": status,
        "dry_run": dry_run,
        "qa_report_path": (
            str((prod_dir / "qa_report.json").relative_to(ROOT)).replace("\\", "/")
            if prod_dir and (prod_dir / "qa_report.json").is_file()
            else None
        ),
        "qa_pass": qa.get("pass") if qa else None,
        "qa_issues": qa.get("issues", []) if qa else [],
        "render_exit": render_result.get("exit_code") if render_result else None,
        "render_mode": render_result.get("mode") if render_result else None,
        "render_attempts": render_result.get("attempts") if render_result else None,
        "promote_eligible": promote_eligible,
        "promote_command": (
            _promote_command_for(script_path) if promote_eligible and script_path else None
        ),
    }


def _promote_command_for(script_path: Path) -> str:
    rel = script_path.relative_to(ROOT).as_posix()
    return (
        f"python DAVID/scripts/batch_runner.py promote --from-manifest "
        f"<manifest.json> --slug {script_path.stem.replace('_480p_script', '').replace('_720p_script', '')}"
    )


def summarize_manifest(items: list[dict[str, Any]]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for item in items:
        status = item.get("status", "unknown")
        counts[status] = counts.get(status, 0) + 1
    return counts


def write_manifest(manifest: dict[str, Any], path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")
    return path


def cmd_run(args: argparse.Namespace) -> int:
    concepts_dir = Path(args.concepts_dir)
    if not concepts_dir.is_absolute():
        concepts_dir = (ROOT / concepts_dir).resolve()

    batch_id = args.batch_id or datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    batch_dir = Path(args.batch_dir) if args.batch_dir else (DAVID / "batches" / batch_id)
    if not batch_dir.is_absolute():
        batch_dir = ROOT / batch_dir
    scripts_dir = batch_dir / "scripts"
    manifest_path = batch_dir / "manifest.json"

    concept_files = discover_concepts(concepts_dir)
    items: list[dict[str, Any]] = []

    print(f"[batch] id={batch_id} concepts={len(concept_files)} dry_run={args.dry_run} res={DRAFT_RES}")

    for concept_path in concept_files:
        slug = json.loads(concept_path.read_text(encoding="utf-8"))["slug"]
        print(f"\n[batch] intake {slug} ← {concept_path.name}")

        script, gate, intake_exit = run_intake(concept_path)
        gate = gate or {"verdict": "RED", "blocked": True, "slug": slug}

        if script is None:
            row = build_item_row(
                concept_path=concept_path,
                script_path=None,
                gate=gate,
                intake_exit=intake_exit,
                status="skipped_red",
                resolution=DRAFT_RES,
                phase="draft_480p",
                dry_run=args.dry_run,
            )
            items.append(row)
            print(f"  🛑 RED — skipped (intake exit {intake_exit})")
            continue

        draft_script = patch_resolution(script, DRAFT_RES, phase="draft_480p", batch_id=batch_id)
        script_path = write_script(draft_script, scripts_dir / f"{slug}_480p_script.json")

        can_render, gate_status = gate_allows_render(gate)
        if not can_render:
            row = build_item_row(
                concept_path=concept_path,
                script_path=script_path,
                gate=gate,
                intake_exit=intake_exit,
                status=gate_status,
                resolution=DRAFT_RES,
                phase="draft_480p",
                dry_run=args.dry_run,
            )
            items.append(row)
            print(f"  ⚠️  {gate.get('verdict')} — render skipped (unsigned Gate 0)")
            continue

        render_result = None
        qa = None
        if args.dry_run:
            status = "pending"
            print(f"  ○ dry-run — would render at {DRAFT_RES}")
        else:
            print(f"  ▶ render {DRAFT_RES} …")
            render_result = render_script(
                script_path,
                dry_run=False,
                seamless_cli=not args.no_seamless,
                max_attempts=args.max_attempts,
                backoff_base=args.backoff_base,
                backoff_max=args.backoff_max,
            )
            prod_dir = resolve_production_dir(draft_script)
            qa = read_qa_report(prod_dir)
            status = classify_item(gate=gate, render_result=render_result, qa=qa, dry_run=False)
            icon = "✅" if status == "pass" else "✗"
            print(f"  {icon} render exit={render_result.get('exit_code')} qa_pass={qa.get('pass') if qa else None}")

        row = build_item_row(
            concept_path=concept_path,
            script_path=script_path,
            gate=gate,
            intake_exit=intake_exit,
            status=status,
            resolution=DRAFT_RES,
            phase="draft_480p",
            render_result=render_result,
            qa=qa,
            dry_run=args.dry_run,
        )
        items.append(row)

    manifest = {
        "batch_id": batch_id,
        "phase": "draft_480p",
        "generated_at": _utc_now(),
        "concepts_dir": str(concepts_dir.relative_to(ROOT)).replace("\\", "/"),
        "dry_run": args.dry_run,
        "resolution": DRAFT_RES,
        "items": items,
        "summary": summarize_manifest(items),
        "promote_command": (
            None
            if args.dry_run
            else f"python DAVID/scripts/batch_runner.py promote {manifest_path.as_posix()}"
        ),
    }
    write_manifest(manifest, manifest_path)

    print(f"\n[batch] manifest → {manifest_path}")
    print(f"[batch] summary: {manifest['summary']}")
    if not args.dry_run and manifest["promote_command"]:
        print(f"[batch] next: {manifest['promote_command']}")

    return 0


def cmd_promote(args: argparse.Namespace) -> int:
    manifest_path = Path(args.manifest)
    if not manifest_path.is_absolute():
        manifest_path = (ROOT / manifest_path).resolve()
    if not manifest_path.is_file():
        raise SystemExit(f"Manifest not found: {manifest_path}")

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    batch_id = manifest.get("batch_id", manifest_path.parent.name)
    batch_dir = manifest_path.parent
    scripts_dir = batch_dir / "scripts"

    eligible = [
        item
        for item in manifest.get("items", [])
        if item.get("promote_eligible")
        and (not args.slug or item.get("slug") == args.slug)
    ]
    if args.approved_only:
        eligible = [i for i in eligible if i.get("status") == "pass"]

    if not eligible:
        print("[promote] no promote_eligible items in manifest")
        return 0

    print(f"[promote] batch={batch_id} items={len(eligible)} res={FINAL_RES} dry_run={args.dry_run}")

    promoted: list[dict[str, Any]] = []
    for item in eligible:
        slug = item["slug"]
        draft_script_path = ROOT / item["script_path"] if item.get("script_path") else None
        if not draft_script_path or not draft_script_path.is_file():
            print(f"  ✗ {slug}: missing draft script")
            continue

        draft = json.loads(draft_script_path.read_text(encoding="utf-8"))
        final_script = patch_resolution(draft, FINAL_RES, phase="final_720p", batch_id=batch_id)
        final_path = write_script(final_script, scripts_dir / f"{slug}_720p_script.json")

        if args.dry_run:
            print(f"  ○ {slug}: would promote to {FINAL_RES}")
            promoted.append({**item, "status": "promote_pending", "resolution": FINAL_RES})
            continue

        print(f"  ▶ {slug}: final render {FINAL_RES}")
        render_result = render_script(
            final_path,
            dry_run=False,
            seamless_cli=not args.no_seamless,
            max_attempts=args.max_attempts,
            backoff_base=args.backoff_base,
            backoff_max=args.backoff_max,
        )
        prod_dir = resolve_production_dir(final_script)
        qa = read_qa_report(prod_dir)
        status = "promoted" if render_result.get("exit_code") == 0 and qa and qa.get("pass") else "promote_fail"
        print(f"    {'✅' if status == 'promoted' else '✗'} exit={render_result.get('exit_code')} qa_pass={qa.get('pass') if qa else None}")

        promoted.append(
            {
                **item,
                "status": status,
                "phase": "final_720p",
                "resolution": FINAL_RES,
                "script_path": str(final_path.relative_to(ROOT)).replace("\\", "/"),
                "qa_pass": qa.get("pass") if qa else None,
                "render_exit": render_result.get("exit_code"),
                "render_mode": render_result.get("mode"),
            }
        )

    promote_manifest = {
        "batch_id": batch_id,
        "phase": "final_720p",
        "generated_at": _utc_now(),
        "source_manifest": str(manifest_path.relative_to(ROOT)).replace("\\", "/"),
        "dry_run": args.dry_run,
        "resolution": FINAL_RES,
        "items": promoted,
        "summary": summarize_manifest(promoted),
    }
    out_path = batch_dir / "manifest_final_720p.json"
    write_manifest(promote_manifest, out_path)
    print(f"\n[promote] manifest → {out_path}")
    print(f"[promote] summary: {promote_manifest['summary']}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="DAVID batch runner — intake → draft → manifest → promote")
    sub = parser.add_subparsers(dest="command", required=True)

    run_p = sub.add_parser("run", help="Process a folder of concept JSON files")
    run_p.add_argument(
        "concepts_dir",
        nargs="?",
        default=str(DEFAULT_T3_CONCEPTS.relative_to(ROOT)),
        help="Folder containing *.concept.json (default: T3 dead_languages slate)",
    )
    run_p.add_argument("--batch-id", help="Batch identifier (default: UTC timestamp)")
    run_p.add_argument("--batch-dir", help="Output directory (default: DAVID/batches/<batch-id>)")
    run_p.add_argument("--dry-run", action="store_true", help="Intake + manifest only; no API renders")
    run_p.add_argument("--no-seamless", action="store_true", help="Omit --seamless render flags")
    run_p.add_argument("--max-attempts", type=int, default=4, help="Render retries on timeout/rate-limit")
    run_p.add_argument("--backoff-base", type=float, default=30.0, help="Initial backoff seconds")
    run_p.add_argument("--backoff-max", type=float, default=300.0, help="Max backoff seconds")
    run_p.set_defaults(func=cmd_run)

    prom_p = sub.add_parser("promote", help="Re-render approved draft items at 720p")
    prom_p.add_argument("manifest", type=Path, help="Path to draft manifest.json")
    prom_p.add_argument("--slug", help="Promote a single slug only")
    prom_p.add_argument("--approved-only", action="store_true", default=True)
    prom_p.add_argument("--dry-run", action="store_true")
    prom_p.add_argument("--no-seamless", action="store_true")
    prom_p.add_argument("--max-attempts", type=int, default=4)
    prom_p.add_argument("--backoff-base", type=float, default=30.0)
    prom_p.add_argument("--backoff-max", type=float, default=300.0)
    prom_p.set_defaults(func=cmd_promote)

    return parser


def main(argv: Optional[list[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())