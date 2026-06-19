#!/usr/bin/env python3
"""#194 — scope-check seamless joins + color across Observable (and optional DAVID) episodes.

Concat-only reassembly — no API spend. Reports systemic verdict JSON on stdout.
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RENDER = ROOT / "DAVID" / "scripts" / "render_longform.py"

OBSERVABLE_SLUGS = (
    "science_star_lifecycle_v1",
    "science_galaxy_formation_v1",
    "science_black_hole_anatomy_v1",
)

SCRIPT_CANDIDATES = {
    "science_star_lifecycle_v1": [
        ROOT / "DAVID/batches/T4_181_science_astro/scripts/science_star_lifecycle_v1_480p_script.json",
        ROOT / "DAVID/scripts/longform_scripts/science_star_lifecycle_v1_480p_script.json",
    ],
    "science_galaxy_formation_v1": [
        ROOT / "DAVID/batches/T4_181_science_astro/scripts/science_galaxy_formation_v1_480p_script.json",
        ROOT / "DAVID/scripts/longform_scripts/science_galaxy_formation_v1_script.json",
    ],
    "science_black_hole_anatomy_v1": [
        ROOT / "DAVID/batches/T4_181_science_astro/scripts/science_black_hole_anatomy_v1_480p_script.json",
        ROOT / "DAVID/scripts/longform_scripts/science_black_hole_anatomy_v1_script.json",
    ],
    "david_latin_corpus_v1": [
        ROOT / "DAVID/scripts/longform_scripts/david_latin_corpus_v1_script.json",
    ],
}


def _resolve_script(slug: str) -> Path | None:
    for p in SCRIPT_CANDIDATES.get(slug, []):
        if p.is_file():
            return p
    return None


def _parse_manifest(stdout: str) -> dict | None:
    text = stdout.strip()
    if not text:
        return None
    # render_longform prints pretty-printed JSON blob on stdout
    start = text.find("{")
    if start < 0:
        return None
    try:
        return json.loads(text[start:])
    except json.JSONDecodeError:
        for line in reversed(text.splitlines()):
            line = line.strip()
            if line.startswith("{") and '"qa"' in line:
                try:
                    return json.loads(line)
                except json.JSONDecodeError:
                    continue
    return None


def _qa_from_production(slug: str) -> dict | None:
    for base in (
        ROOT / "DAVID/productions" / f"{slug}_longform_v1",
        ROOT / "STUDIO/Productions/Editorial" / f"{slug}_longform_v1",
    ):
        qa_path = base / "qa_report.json"
        if qa_path.is_file():
            return json.loads(qa_path.read_text(encoding="utf-8"))
    return None


def run_scope(slug: str, *, package: bool = False) -> dict:
    script = _resolve_script(slug)
    row: dict = {"slug": slug, "script": str(script) if script else None}
    if not script:
        row.update(status="skip", reason="script not found")
        return row

    cmd = [
        sys.executable, str(RENDER), str(script),
        "--concat-only", "--seamless", "--match-color", "--cut-on-motion",
    ]
    if package:
        cmd.append("--package")

    proc = subprocess.run(
        cmd, cwd=str(ROOT), capture_output=True,
        text=True, encoding="utf-8", errors="replace",
    )
    manifest = _parse_manifest(proc.stdout) or {}
    qa = manifest.get("qa") or _qa_from_production(slug) or {}
    passes = qa.get("passes") or []
    issues = qa.get("issues") or []
    seam_ok = any(
        k in " ".join(passes)
        for k in ("xfade chain", "re-concat join preserved")
    )
    color_ok = qa.get("pass") or (
        seam_ok
        and not any(
            k in " ".join(issues).lower()
            for k in ("yellow-green", "hue drift", "magenta detected", "lamp hue drift")
        )
    )
    row.update(
        status="pass" if proc.returncode == 0 and qa.get("pass") else "fail",
        exit_code=proc.returncode,
        qa_pass=qa.get("pass"),
        output=manifest.get("output"),
        issues=issues,
        seam_ok=seam_ok,
        color_ok=color_ok,
    )
    return row


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="#194 scope-check color + seams")
    p.add_argument("--include-latin", action="store_true", help="Also check david_latin_corpus_v1")
    p.add_argument("--package", action="store_true", help="Run package stage on pass")
    args = p.parse_args(argv)

    slugs = list(OBSERVABLE_SLUGS)
    if args.include_latin:
        slugs.append("david_latin_corpus_v1")

    results = [run_scope(s, package=args.package) for s in slugs]
    passed = sum(1 for r in results if r.get("status") == "pass")
    failed = sum(1 for r in results if r.get("status") == "fail")
    skipped = sum(1 for r in results if r.get("status") == "skip")

    latin = next((r for r in results if r["slug"] == "david_latin_corpus_v1"), None)
    observable = [r for r in results if r["slug"] in OBSERVABLE_SLUGS]
    obs_seam_ok = all(r.get("seam_ok") for r in observable) if observable else False
    obs_color_ok = all(r.get("color_ok") for r in observable) if observable else False
    latin_ship = latin and latin.get("qa_pass") is True

    if latin_ship and obs_seam_ok and obs_color_ok:
        systemic = "PASS"
    elif latin_ship:
        systemic = "DAVID_PASS / OBSERVABLE_COLOR_PENDING"
    else:
        systemic = "FAIL"

    verdict = {
        "issue": 194,
        "checked_at": datetime.now(timezone.utc).isoformat(),
        "systemic_verdict": systemic,
        "david_latin_ship": latin_ship,
        "observable_seams_ok": obs_seam_ok,
        "observable_color_ok": obs_color_ok,
        "summary": {"pass": passed, "fail": failed, "skip": skipped, "total": len(results)},
        "items": results,
    }
    print(json.dumps(verdict, indent=2, ensure_ascii=False))
    return 0 if latin_ship else 1


if __name__ == "__main__":
    raise SystemExit(main())