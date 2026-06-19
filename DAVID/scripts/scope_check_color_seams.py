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
    for line in reversed(stdout.splitlines()):
        line = line.strip()
        if line.startswith("{") and '"qa"' in line:
            try:
                return json.loads(line)
            except json.JSONDecodeError:
                continue
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
    qa = manifest.get("qa") or {}
    passes = qa.get("passes") or []
    row.update(
        status="pass" if proc.returncode == 0 and qa.get("pass") else "fail",
        exit_code=proc.returncode,
        qa_pass=qa.get("pass"),
        output=manifest.get("output"),
        issues=qa.get("issues") or [],
        seam_ok=any("xfade chain" in p for p in passes),
        color_ok=any(
            k in " ".join(passes).lower()
            for k in ("grey balance", "zero hue drift", "neutral wb", "yellow-green suppressed", "clinical/neutral")
        ),
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

    verdict = {
        "issue": 194,
        "checked_at": datetime.now(timezone.utc).isoformat(),
        "systemic_verdict": "PASS" if failed == 0 and passed > 0 else "FAIL",
        "summary": {"pass": passed, "fail": failed, "skip": skipped, "total": len(results)},
        "items": results,
    }
    print(json.dumps(verdict, indent=2, ensure_ascii=False))
    return 0 if verdict["systemic_verdict"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())