#!/usr/bin/env python3
"""math_pipeline.py -- Math reasoning dispatcher for the NEXUS system.

Routes mathematical topics and problems through call_reasoning_for_math()
in reasoning_integrations.py.  Mirrors the pattern of science_pipeline.py:
reads a queue, builds a reasoning trace per item, writes output to
AI/federation/output/<problem_id>_math_trace.json.

Math sub-agents (Math_Orchestrator_Agent, Mathematical_Modeling_Agent,
Applied_Math_Stats_Agent) can call call_reasoning_for_math() directly
or use this dispatcher for batch runs.

CLI:
    python3 Math/Pipelines/math_pipeline.py --all
    python3 Math/Pipelines/math_pipeline.py --all --dry-run
    python3 Math/Pipelines/math_pipeline.py --id MATH001
    python3 Math/Pipelines/math_pipeline.py --id MATH001 --mode think_draft
    python3 Math/Pipelines/math_pipeline.py --problem "eigenvalue decomposition of A"
    python3 Math/Pipelines/math_pipeline.py --problem "entropy formula for discrete distributions"
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

# ---------------------------------------------------------------------------
# Path bootstrap — locate project root and AI/federation
# ---------------------------------------------------------------------------

_PIPELINE_DIR = Path(__file__).resolve().parent       # Math/Pipelines/
_PROJECT_ROOT = _PIPELINE_DIR.parents[1]              # Grok Projects/
_FEDERATION_DIR = _PROJECT_ROOT / "AI" / "federation"

OUTPUT_DIR = _PROJECT_ROOT / "AI" / "federation" / "output"
MATH_QUEUE_PATH = _PIPELINE_DIR / "math_queue.json"

# ---------------------------------------------------------------------------
# Reasoning imports — graceful fallback to stub if federation not on path
# ---------------------------------------------------------------------------

_REASONING_AVAILABLE = False
_reasoning_import_err_msg = ""
try:
    if str(_FEDERATION_DIR) not in sys.path:
        sys.path.insert(0, str(_FEDERATION_DIR))
    from reasoning_integrations import (
        call_reasoning_for_math,
        reasoning_gate_check,
        trace_summary,
    )
    _REASONING_AVAILABLE = True
except ImportError as _ie:
    _reasoning_import_err_msg = str(_ie)


# ---------------------------------------------------------------------------
# Default math problem queue (used when math_queue.json is absent)
# ---------------------------------------------------------------------------

_DEFAULT_MATH_PROBLEMS: list[dict] = [
    {
        "id": "MATH001",
        "topic": "Eigenvalue decomposition of a real symmetric matrix",
        "context": "Domain: square n×n matrix A = Aᵀ. Apply spectral theorem.",
        "mode": "full",
        "tags": ["linear_algebra", "eigenvalues"],
    },
    {
        "id": "MATH002",
        "topic": "Shannon entropy formula for discrete probability distributions",
        "context": "H(X) = -Σ p(x) log₂ p(x). Verify boundary cases: p=0, p=1.",
        "mode": "full",
        "tags": ["information_theory", "probability"],
    },
    {
        "id": "MATH003",
        "topic": "Differential equation: dy/dx = ky (exponential growth)",
        "context": "Solve with initial condition y(0) = y₀. Identify equilibria.",
        "mode": "full",
        "tags": ["differential_equations", "modeling"],
    },
    {
        "id": "MATH004",
        "topic": "Gaussian elimination to solve Ax = b",
        "context": "3×3 example system. Show row operations and back-substitution.",
        "mode": "think_draft",
        "tags": ["linear_algebra", "numerical_methods"],
    },
    {
        "id": "MATH005",
        "topic": "Bayes theorem applied to medical test sensitivity and specificity",
        "context": "P(disease|positive) = P(positive|disease)P(disease) / P(positive).",
        "mode": "full",
        "tags": ["statistics", "probability", "applied_math"],
    },
]


def _load_queue() -> list[dict]:
    """Load math problem queue from math_queue.json or return defaults."""
    if MATH_QUEUE_PATH.is_file():
        with open(MATH_QUEUE_PATH, encoding="utf-8") as f:
            data = json.load(f)
        if isinstance(data, list):
            return data
        if isinstance(data, dict) and "problems" in data:
            return data["problems"]
    return _DEFAULT_MATH_PROBLEMS


def _write_output(item: dict, trace_dict: dict, summary: dict, gate: str) -> Path:
    """Write reasoning trace to AI/federation/output/<id>_math_trace.json."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    item_id = item.get("id", "MATH_UNKNOWN")
    out_path = OUTPUT_DIR / f"{item_id}_math_trace.json"

    payload = {
        "math_trace_id": item_id,
        "topic": item.get("topic", ""),
        "tags": item.get("tags", []),
        "gate": gate,
        "as_of": datetime.now(timezone.utc).isoformat(),
        "trace_summary": summary,
        "full_trace": trace_dict,
    }
    # Truncate-then-write for growing files (Windows mount safety)
    with open(out_path, "r+b") if out_path.exists() else open(out_path, "wb") as f:
        f.truncate(0)
    with open(out_path, "wb") as f:
        f.write(json.dumps(payload, indent=2, ensure_ascii=False).encode("utf-8"))
    return out_path


def run_math_reasoning(
    item: dict,
    *,
    dry_run: bool = False,
    mode_override: Optional[str] = None,
    verbose: bool = False,
) -> dict:
    """Run call_reasoning_for_math() on a single queue item.

    Args:
        item:          Queue item dict with keys: id, topic, context, mode, tags.
        dry_run:       If True, skip the actual reasoning call and return a stub result.
        mode_override: Override the mode from the queue item.
        verbose:       Print trace summary to stdout.

    Returns:
        Result dict: {id, topic, gate, safe, summary, output_path}.
    """
    item_id = item.get("id", "MATH_UNKNOWN")
    topic   = item.get("topic", "")
    context = item.get("context", "")
    mode    = mode_override or item.get("mode", "full")

    if dry_run:
        print(f"  [DRY-RUN] {item_id}: {topic[:60]}... (mode={mode})")
        return {
            "id": item_id, "topic": topic, "gate": "DRY_RUN",
            "safe": True, "summary": "dry-run — no reasoning call made",
            "output_path": None,
        }

    if not _REASONING_AVAILABLE:
        print(
            f"  [ERROR] {item_id}: reasoning_integrations not available — "
            f"{_reasoning_import_err_msg}",
            file=sys.stderr,
        )
        return {
            "id": item_id, "topic": topic, "gate": "ERROR",
            "safe": False, "summary": f"import error: {_reasoning_import_err_msg}",
            "output_path": None,
        }

    if verbose:
        print(f"  Running [MATH] reasoning for {item_id}: {topic[:60]}... (mode={mode})")

    # Core call — call_reasoning_for_math() from reasoning_integrations.py
    trace = call_reasoning_for_math(topic=topic, context=context, mode=mode)

    gate = trace.gate_status   # GREEN | YELLOW | RED
    safe = reasoning_gate_check(trace)
    smry = trace_summary(trace)

    if gate == "RED":
        print(
            f"  [WARNING] {item_id}: reasoning gate RED — output held. "
            f"Verdict: {trace.verify_verdict}",
            file=sys.stderr,
        )

    out_path = _write_output(item, trace.to_dict(), smry, gate)

    if verbose:
        print(f"    Gate: {gate}  |  Verdict: {trace.verify_verdict}  |  Written: {out_path.name}")

    return {
        "id": item_id,
        "topic": topic,
        "gate": gate,
        "safe": safe,
        "summary": smry.get("final_preview", ""),
        "output_path": str(out_path),
    }


def run_single_problem(
    problem: str,
    *,
    mode: str = "full",
    dry_run: bool = False,
    verbose: bool = False,
) -> dict:
    """Run reasoning on an ad-hoc problem string (not from the queue).

    Wraps as an inline queue item with id=MATH_ADHOC.
    """
    item = {"id": "MATH_ADHOC", "topic": problem, "context": "", "mode": mode, "tags": ["adhoc"]}
    return run_math_reasoning(item, dry_run=dry_run, mode_override=mode, verbose=verbose)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="math_pipeline",
        description="NEXUS Math Reasoning Dispatcher — routes math problems through the reasoning pipeline.",
    )
    grp = p.add_mutually_exclusive_group(required=True)
    grp.add_argument("--all", action="store_true",
                     help="Process all items in the math problem queue.")
    grp.add_argument("--id", metavar="MATH_ID",
                     help="Process a single queue item by its id (e.g. MATH001).")
    grp.add_argument("--problem", metavar="TEXT",
                     help="Process an ad-hoc problem string (not from queue).")

    p.add_argument("--mode", choices=("full", "think_draft", "draft_critique", "single"),
                   default=None,
                   help="Override pipeline mode (default: from queue item or 'full').")
    p.add_argument("--dry-run", action="store_true",
                   help="Print what would be processed without running reasoning.")
    p.add_argument("--verbose", "-v", action="store_true",
                   help="Print per-item trace summaries.")
    return p


def main(argv: Optional[list] = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)

    if not _REASONING_AVAILABLE:
        print(
            f"[ERROR] reasoning_integrations not importable: {_reasoning_import_err_msg}",
            file=sys.stderr,
        )
        if not args.dry_run:
            return 1

    results: list[dict] = []

    if args.problem:
        mode = args.mode or "full"
        print(f"\nNEXUS Math Pipeline — ad-hoc problem (mode={mode})")
        r = run_single_problem(
            args.problem, mode=mode, dry_run=args.dry_run, verbose=True
        )
        results.append(r)

    elif args.id:
        queue = _load_queue()
        items = [i for i in queue if i.get("id") == args.id]
        if not items:
            print(f"[ERROR] id '{args.id}' not found in queue.", file=sys.stderr)
            return 1
        print(f"\nNEXUS Math Pipeline — single item: {args.id}")
        r = run_math_reasoning(
            items[0], dry_run=args.dry_run, mode_override=args.mode, verbose=True
        )
        results.append(r)

    else:  # --all
        queue = _load_queue()
        print(f"\nNEXUS Math Pipeline — {len(queue)} item(s)")
        for item in queue:
            r = run_math_reasoning(
                item, dry_run=args.dry_run, mode_override=args.mode, verbose=args.verbose
            )
            results.append(r)

    # Summary table
    print(f"\n{'─'*60}")
    print(f"{'ID':<14} {'Gate':<8} {'Safe':<6} {'Topic (preview)'}")
    print(f"{'─'*60}")
    for r in results:
        gate_str = r["gate"] if r["gate"] != "DRY_RUN" else "DRY"
        safe_str = "YES" if r["safe"] else "NO"
        topic_preview = r["topic"][:38]
        print(f"{r['id']:<14} {gate_str:<8} {safe_str:<6} {topic_preview}")
    print(f"{'─'*60}")

    red_count = sum(1 for r in results if r["gate"] == "RED")
    if red_count:
        print(f"\n[WARNING] {red_count} item(s) gated RED — check output for details.")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
