#!/usr/bin/env python3
"""T243-B — formal pre-render gate (one-line PASS/FAIL emitter for T4).

Checklist (Nexus/gates/T243_pre_render_gate.json):
  clamp idempotent · single-pass confirmed · refs neutral · xfade/seam present

NO render. Constants HOLD — thresholds imported, not edited.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
WORKSPACE = ROOT.parent
SCRIPTS = ROOT / "scripts"
GATE_SPEC = WORKSPACE / "Nexus" / "gates" / "T243_pre_render_gate.json"
RENDER_LONGFORM = SCRIPTS / "render_longform.py"

if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

PASS_LINE = "T243_PRE_RENDER_GATE PASS"
FAIL_PREFIX = "T243_PRE_RENDER_GATE FAIL:"


def _load_gate_spec() -> dict[str, Any]:
    if GATE_SPEC.is_file():
        return json.loads(GATE_SPEC.read_text(encoding="utf-8"))
    return {}


def probe_magenta_score_image(arr: np.ndarray) -> float:
    """Same magenta fraction logic as render_longform.probe_magenta_score (single frame)."""
    h, w = arr.shape[:2]
    magenta_n = total_n = 0
    for y in range(0, h, 6):
        for x in range(0, w, 6):
            r, g, b = int(arr[y, x, 0]), int(arr[y, x, 1]), int(arr[y, x, 2])
            lum = 0.299 * r + 0.587 * g + 0.114 * b
            if lum < 40 or lum > 200:
                continue
            total_n += 1
            if b > r * 1.08 and b > g * 1.05:
                magenta_n += 1
            elif (r + b) > g * 1.35 and b > g * 0.95:
                magenta_n += 1
    return magenta_n / total_n if total_n else 0.0


def _audit_plumbing(source: str) -> tuple[list[str], list[str]]:
    """Return (passes, failures) for clamp_idempotent + single_pass_confirmed."""
    passes: list[str] = []
    failures: list[str] = []

    clamp_need = [
        "def apply_archive_saturation_clamp_once",
        "def _clamp_already_applied",
        'CLAMP_STAGE_NAME = "process_shot_segment"',
        ".clamp244.json",
    ]
    single_need = [
        "skip_post_clamp = magenta_clamp or neutral_grade",
        "def apply_archive_saturation_clamp_once",
    ]
    for needle in clamp_need:
        if needle in source:
            passes.append(f"clamp_idempotent: found {needle!r}")
        else:
            failures.append(f"clamp_idempotent: missing {needle!r}")

    for needle in single_need:
        if needle in source:
            passes.append(f"single_pass_confirmed: found {needle!r}")
        else:
            failures.append(f"single_pass_confirmed: missing {needle!r}")

    concat_match = re.search(
        r"def concat_xfade_two\((?:.|\n)*?\n(?=def |\Z)",
        source,
    )
    concat_body = concat_match.group(0) if concat_match else ""
    if "apply_lamp_accent_local(matched" in concat_body:
        failures.append("single_pass_confirmed: per-join apply_lamp_accent_local still in concat_xfade_two")
    else:
        passes.append("single_pass_confirmed: no per-join lamp accent in concat_xfade_two")

    return passes, failures


def _check_refs_neutral(
    script: dict[str, Any],
    refs: dict[str, Any],
    *,
    seamless_opts: Any,
    magenta_max: float,
) -> tuple[list[str], list[str]]:
    import render_longform as rl  # noqa: WPS433
    from color_cast_qa import (  # noqa: WPS433
        generation_reference_breaches,
        generation_reference_passes,
        measure_color_cast,
        measure_set_shadow_blue_health,
    )
    from PIL import Image

    passes: list[str] = []
    failures: list[str] = []

    if not seamless_opts.enabled or not seamless_opts.neutral_generation:
        passes.append("refs_neutral: skipped (neutral_generation off or seamless disabled)")
        return passes, failures
    if not rl._is_archive_production(script, refs):
        passes.append("refs_neutral: skipped (non-archive production)")
        return passes, failures

    avatar_path = Path(str(refs.get("avatar_file") or ""))
    set_path = Path(str(refs.get("set_file") or ""))

    for label, path, host_flag, measure_fn in (
        ("avatar", avatar_path, True, measure_color_cast),
        ("set", set_path, False, measure_set_shadow_blue_health),
    ):
        if not path.is_file():
            failures.append(f"refs_neutral: {label} missing {path}")
            continue
        with Image.open(path) as img:
            arr = np.asarray(img.convert("RGB"))
        metrics = measure_fn(arr)
        mag = probe_magenta_score_image(arr)
        if not generation_reference_passes(metrics, host=host_flag):
            failures.append(
                f"refs_neutral: {label} blue-channel FAIL "
                f"{generation_reference_breaches(metrics, host=host_flag)} "
                f"(Bμ={metrics.get('host_blue_mean', 0):.1f} "
                f"B/R={metrics.get('host_br_ratio', 0):.3f} "
                f"starve={metrics.get('blue_starvation_fraction', 0):.3f})"
            )
        else:
            passes.append(
                f"refs_neutral: {label} blue-channel OK "
                f"(Bμ={metrics.get('host_blue_mean', 0):.1f} B/R={metrics.get('host_br_ratio', 0):.3f})"
            )
        if mag > magenta_max:
            failures.append(f"refs_neutral: {label} raw magenta {mag:.4f} > {magenta_max}")
        else:
            passes.append(f"refs_neutral: {label} raw magenta {mag:.4f} <= {magenta_max}")

    return passes, failures


def _check_xfade_seam(
    script: dict[str, Any],
    seamless_opts: Any,
    production_dir: Path | None,
    *,
    xfade_min: float,
) -> tuple[list[str], list[str]]:
    import render_longform as rl  # noqa: WPS433

    passes: list[str] = []
    failures: list[str] = []

    if not seamless_opts.enabled:
        failures.append("xfade_seam_present: seamless mode not enabled")
        return passes, failures

    seam = script.get("config", {}).get("seamless") or {}
    xfade_s = rl.resolve_xfade_s(cli=None, script_seam=seam)
    if xfade_s < xfade_min:
        failures.append(f"xfade_seam_present: resolved xfade_s {xfade_s} < {xfade_min}")
    else:
        passes.append(f"xfade_seam_present: resolved xfade_s={xfade_s}s (min {xfade_min})")

    if not (seam.get("match_color") or seamless_opts.match_color):
        failures.append("xfade_seam_present: match_color not enabled")
    else:
        passes.append("xfade_seam_present: match_color enabled")

    if production_dir and production_dir.is_dir():
        state_path = production_dir / "shots" / "extend_state.json"
        if state_path.is_file():
            st = json.loads(state_path.read_text(encoding="utf-8"))
            join_mode = st.get("join_mode", "")
            if join_mode == "xfade_chain":
                passes.append(f"xfade_seam_present: extend_state join_mode={join_mode}")
            else:
                failures.append(
                    f"xfade_seam_present: extend_state join_mode={join_mode!r} (need xfade_chain)"
                )
        manifest_path = production_dir / "manifest.json"
        if manifest_path.is_file():
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            assembly = manifest.get("assembly") or {}
            if assembly.get("join_mode") == "xfade_chain":
                passes.append("xfade_seam_present: manifest assembly join_mode=xfade_chain")
            elif assembly:
                failures.append(
                    f"xfade_seam_present: manifest assembly join_mode="
                    f"{assembly.get('join_mode')!r}"
                )
    else:
        passes.append("xfade_seam_present: pre-render config OK (no production cache probe)")

    return passes, failures


def evaluate_t243_pre_render_gate(
    script: dict[str, Any],
    refs: dict[str, Any],
    *,
    seamless_opts: Any,
    production_dir: Path | None = None,
    gate_spec: dict[str, Any] | None = None,
) -> dict[str, Any]:
    spec = gate_spec or _load_gate_spec()
    checklist = {c["id"]: c for c in spec.get("checklist", [])}
    magenta_max = float(
        checklist.get("refs_neutral", {})
        .get("thresholds", {})
        .get("raw_magenta_max", 0.42)
    )
    xfade_min = float(
        checklist.get("xfade_seam_present", {})
        .get("pre_render", {})
        .get("xfade_s_min", 0.35)
    )

    all_passes: list[str] = []
    all_failures: list[str] = []

    if RENDER_LONGFORM.is_file():
        source = RENDER_LONGFORM.read_text(encoding="utf-8")
        p, f = _audit_plumbing(source)
        all_passes.extend(p)
        all_failures.extend(f)
    else:
        all_failures.append(f"plumbing_audit: missing {RENDER_LONGFORM}")

    p, f = _check_refs_neutral(script, refs, seamless_opts=seamless_opts, magenta_max=magenta_max)
    all_passes.extend(p)
    all_failures.extend(f)

    p, f = _check_xfade_seam(script, seamless_opts, production_dir, xfade_min=xfade_min)
    all_passes.extend(p)
    all_failures.extend(f)

    ok = not all_failures
    return {
        "gate": "T243_PRE_RENDER",
        "issue": 243,
        "pass": ok,
        "verdict": "PASS" if ok else "FAIL",
        "failures": all_failures,
        "passes": all_passes,
        "evaluated_at": datetime.now(timezone.utc).isoformat(),
        "spec": str(GATE_SPEC.relative_to(WORKSPACE)) if GATE_SPEC.is_file() else None,
    }


def format_one_line(result: dict[str, Any]) -> str:
    if result.get("pass"):
        return PASS_LINE
    reason = "; ".join(result.get("failures") or ["unknown"])
    return f"{FAIL_PREFIX} {reason}"


def assert_t243_pre_render_gate(
    script: dict[str, Any],
    refs: dict[str, Any],
    *,
    seamless_opts: Any,
    production_dir: Path | None = None,
) -> None:
    result = evaluate_t243_pre_render_gate(
        script, refs, seamless_opts=seamless_opts, production_dir=production_dir,
    )
    if not result["pass"]:
        raise SystemExit(format_one_line(result))


def main() -> int:
    import render_longform as rl  # noqa: WPS433

    parser = argparse.ArgumentParser(description="T243-B pre-render gate — one-line PASS/FAIL")
    parser.add_argument("--script", type=Path, required=True, help="Longform script JSON")
    parser.add_argument("--production", type=Path, default=None, help="Optional production dir probe")
    parser.add_argument("--json", action="store_true", help="Emit full JSON report to stdout")
    args = parser.parse_args()

    script = json.loads(args.script.read_text(encoding="utf-8"))
    refs = rl.resolve_refs(script)
    seamless_opts = rl.get_seamless_options(script, argparse.Namespace(seamless=True))
    seamless_opts = rl._apply_grade_policy(script, refs, seamless_opts)

    prod = args.production
    if prod is None and script.get("production_dir"):
        prod = rl.resolve_production_dir(script)

    result = evaluate_t243_pre_render_gate(
        script, refs, seamless_opts=seamless_opts, production_dir=prod,
    )

    if args.json:
        print(json.dumps(result, indent=2))
    else:
        print(format_one_line(result))
    return 0 if result["pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())