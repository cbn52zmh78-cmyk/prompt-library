#!/usr/bin/env python3
"""#199 — definitive seam + color audit across recent production masters."""

from __future__ import annotations

import json
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
RENDER = ROOT / "DAVID" / "scripts" / "render_longform.py"

# Production roots scanned for qa_report.json + manifest.json masters.
SCAN_ROOTS = [
    ROOT / "DAVID" / "productions",
    ROOT / "Studio" / "Productions" / "Editorial",
    ROOT / "Studio" / "Productions" / "Companion",
    ROOT / "Studio" / "Productions" / "Narrative",
    ROOT / "Studio" / "Productions" / "Science",
    ROOT / "Studio" / "Productions" / "HistoricalFigures",
]

SKIP_DIR_PARTS = {"shots", "upload_kit", "cache", "__pycache__"}

# Armed batch slugs — blast-radius priority.
B183_SLUGS = {
    "david_ancient_greek_corpus_v1",
    "david_old_english_corpus_v1",
    "david_old_norse_corpus_v1",
    "david_gothic_corpus_v1",
    "david_sumerian_corpus_v1",
    "david_eleanor_aquitaine_v1",
    "david_richard_lionheart_v1",
    "david_elizabeth_tudor_v1",
}
B192_SLUGS = {
    "science_black_hole_anatomy_v1",
    "science_star_lifecycle_v1",
    "science_galaxy_formation_v1",
    "science_dna_replication_v1",
    "science_protein_folding_v1",
    "science_immune_checkpoint_v1",
}
REFERENCE_SHIP = "david_latin_corpus_v1"


def _utc() -> str:
    return datetime.now(timezone.utc).isoformat()


def classify_lane(prod_dir: Path) -> str:
    parts = {p.lower() for p in prod_dir.parts}
    rel = str(prod_dir.relative_to(ROOT)).replace("\\", "/").lower()
    if "companion" in rel or "gfe_companion" in prod_dir.name:
        return "Companion"
    if "narrative" in rel or "movies_lane" in prod_dir.name:
        return "Movies"
    if "/science/" in rel or "actors_157" in prod_dir.name or "black_hole_science_proof" in prod_dir.name:
        return "Science"
    if prod_dir.name.startswith("science_") or "editorial/science" in rel:
        return "Observable"
    if "historicalfigures" in rel or "figure_proof" in prod_dir.name:
        return "DAVID"
    if "david/productions" in rel:
        return "DAVID"
    return "Other"


def infer_slug(prod_dir: Path, qa: dict[str, Any], manifest: dict[str, Any] | None) -> str:
    if qa.get("slug"):
        return str(qa["slug"])
    if manifest and manifest.get("script"):
        stem = Path(str(manifest["script"])).stem
        for suffix in ("_script", "_longform_v1", "_480p_v1", "_720p_v1"):
            if stem.endswith(suffix):
                stem = stem[: -len(suffix)]
        return stem
    name = prod_dir.name
    if name.endswith("_longform_v1"):
        return name[: -len("_longform_v1")]
    return name


COLOR_ISSUE_KEYS = (
    "magenta detected",
    "yellow-green cast",
    "hue drift across",
    "hue drift detected",
    "lamp hue drift",
    "grey_balance",
    "loudness spread",
)
SEAM_ISSUE_KEYS = (
    "a/v sync drift",
    "re-concat stripped",
    "missing host performance",
    "hard cut",
)


def _issue_hits(issues: list[str], keys: tuple[str, ...]) -> list[str]:
    return [i for i in issues if any(k in i.lower() for k in keys)]


def parse_seam_color(qa: dict[str, Any]) -> dict[str, Any]:
    passes = qa.get("passes") or []
    issues = qa.get("issues") or []
    pass_text = " ".join(passes).lower()

    color_hits = _issue_hits(issues, COLOR_ISSUE_KEYS)
    seam_hits = _issue_hits(issues, SEAM_ISSUE_KEYS)

    seamless_on = qa.get("seamless") or "seamless mode active" in pass_text
    seam_joins = any(
        k in pass_text for k in ("xfade chain", "re-concat join preserved", "extend chain")
    )

    color_ok = qa.get("pass", False) and not color_hits
    seam_ok = qa.get("pass", False) and not seam_hits and (not seamless_on or seam_joins)

    return {
        "seam_ok": seam_ok,
        "color_ok": color_ok,
        "color_issues": color_hits,
        "seam_issues": seam_hits,
    }


def find_master(prod_dir: Path, manifest: dict[str, Any] | None) -> str | None:
    if manifest and manifest.get("output"):
        p = Path(str(manifest["output"]))
        if p.is_file():
            return str(p.relative_to(ROOT)).replace("\\", "/")
    out = prod_dir / "output"
    if out.is_dir():
        mp4s = sorted(out.glob("*.mp4"), key=lambda p: p.stat().st_mtime, reverse=True)
        for mp4 in mp4s:
            if "vs_" not in mp4.name and mp4.stat().st_size > 50_000:
                return str(mp4.relative_to(ROOT)).replace("\\", "/")
    return None


def find_script(prod_dir: Path, slug: str) -> Path | None:
    candidates = [
        prod_dir / f"{slug}_script.json",
        ROOT / "DAVID" / "scripts" / "longform_scripts" / f"{slug}_script.json",
        ROOT / "DAVID" / "batches" / "T4_181_science_astro" / "scripts" / f"{slug}_480p_script.json",
        ROOT / "DAVID" / "batches" / "T4_181_science_molecular" / "scripts" / f"{slug}_480p_script.json",
    ]
    for c in candidates:
        if c.is_file():
            return c
    scripts = list(prod_dir.glob("*_script.json"))
    return scripts[0] if scripts else None


def _parse_render_stdout(stdout: str) -> dict[str, Any] | None:
    for line in reversed(stdout.splitlines()):
        line = line.strip()
        if line.startswith("{") and '"qa"' in line:
            try:
                return json.loads(line)
            except json.JSONDecodeError:
                continue
    return None


def live_reaudit(slug: str, script: Path | None) -> dict[str, Any] | None:
    if not script or not script.is_file():
        return None
    cmd = [
        sys.executable,
        str(RENDER),
        str(script),
        "--concat-only",
        "--seamless",
        "--match-color",
        "--cut-on-motion",
    ]
    proc = subprocess.run(
        cmd,
        cwd=str(ROOT),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    manifest = _parse_render_stdout(proc.stdout) or {}
    qa = manifest.get("qa") or {}
    sc = parse_seam_color(qa)
    return {
        "live_exit": proc.returncode,
        "live_qa_pass": qa.get("pass"),
        "live_issues": qa.get("issues") or [],
        **sc,
    }


def discover_productions() -> list[Path]:
    found: list[Path] = []
    for root in SCAN_ROOTS:
        if not root.is_dir():
            continue
        for qa_path in root.rglob("qa_report.json"):
            if any(part in SKIP_DIR_PARTS for part in qa_path.parts):
                continue
            prod = qa_path.parent
            if prod.name == "output":
                prod = prod.parent
            found.append(prod)
    # Dedupe; keep most recently qa'd per slug
    by_slug: dict[str, Path] = {}
    for prod in found:
        qa_path = prod / "qa_report.json"
        try:
            qa = json.loads(qa_path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            continue
        slug = infer_slug(prod, qa, None)
        prev = by_slug.get(slug)
        if not prev:
            by_slug[slug] = prod
            continue
        prev_qa_at = json.loads((prev / "qa_report.json").read_text(encoding="utf-8")).get("qa_at", "")
        if str(qa.get("qa_at", "")) >= str(prev_qa_at):
            by_slug[slug] = prod
    return sorted(by_slug.values(), key=lambda p: p.name)


def audit_row(prod_dir: Path, *, live: bool) -> dict[str, Any]:
    qa_path = prod_dir / "qa_report.json"
    qa = json.loads(qa_path.read_text(encoding="utf-8"))
    manifest = None
    mf = prod_dir / "manifest.json"
    if mf.is_file():
        manifest = json.loads(mf.read_text(encoding="utf-8"))

    slug = infer_slug(prod_dir, qa, manifest)
    lane = classify_lane(prod_dir)
    sc = parse_seam_color(qa)
    master = find_master(prod_dir, manifest)

    resolution = "?"
    script_path = find_script(prod_dir, slug)
    if script_path and script_path.is_file():
        try:
            script = json.loads(script_path.read_text(encoding="utf-8"))
            resolution = (script.get("config") or {}).get("resolution", "?")
        except (json.JSONDecodeError, OSError):
            pass

    if not qa.get("pass", False):
        verdict = "NEEDS_RE-RENDER"
        needs_rerender = True
    elif sc["seam_ok"] and sc["color_ok"]:
        verdict = "CLEAN"
        needs_rerender = False
    else:
        verdict = "MARGINAL"
        needs_rerender = True

    row: dict[str, Any] = {
        "slug": slug,
        "lane": lane,
        "resolution": resolution,
        "qa_pass": qa.get("pass"),
        "qa_at": qa.get("qa_at"),
        "seam_ok": sc["seam_ok"],
        "color_ok": sc["color_ok"],
        "issues": qa.get("issues") or [],
        "verdict": verdict,
        "needs_rerender": needs_rerender,
        "master": master,
        "production_dir": str(prod_dir.relative_to(ROOT)).replace("\\", "/"),
        "in_b183": slug in B183_SLUGS,
        "in_b192": slug in B192_SLUGS,
        "reference_ship": slug == REFERENCE_SHIP,
    }

    if live:
        live_data = live_reaudit(slug, script_path)
        if live_data:
            row["live_audit"] = live_data
            if live_data.get("live_qa_pass") is False or live_data.get("live_exit", 1) != 0:
                row["verdict"] = "NEEDS_RE-RENDER"
                row["needs_rerender"] = True
                row["issues"] = live_data.get("live_issues") or row["issues"]

    return row


def main(argv: list[str] | None = None) -> int:
    import argparse

    p = argparse.ArgumentParser(description="#199 seam + color master audit")
    p.add_argument("--live", action="store_true", help="Concat-only re-audit (no API)")
    p.add_argument("--recent-only", action="store_true", help="Only masters with qa_at >= 2026-06-18")
    p.add_argument("-o", "--output", type=Path, help="Write JSON report path")
    args = p.parse_args(argv)

    rows = [audit_row(prod, live=args.live) for prod in discover_productions()]
    if args.recent_only:
        rows = [r for r in rows if str(r.get("qa_at", "")) >= "2026-06-18"]

    # Priority sort: armed batches → lane → slug
    rows.sort(
        key=lambda r: (
            0 if r.get("in_b183") or r.get("in_b192") else 1,
            0 if r.get("reference_ship") else 1,
            r.get("lane", ""),
            r.get("slug", ""),
        )
    )

    clean = [r for r in rows if r["verdict"] == "CLEAN"]
    marginal = [r for r in rows if r["verdict"] == "MARGINAL"]
    rerender = [r for r in rows if r["verdict"] == "NEEDS_RE-RENDER"]

    report = {
        "issue": 199,
        "task": "T4 — definitive seam + color audit",
        "audited_at": _utc(),
        "live_reaudit": args.live,
        "summary": {
            "total": len(rows),
            "clean": len(clean),
            "marginal": len(marginal),
            "needs_rerender": len(rerender),
            "b183_blocked": sum(1 for r in rows if r.get("in_b183") and r["needs_rerender"]),
            "b192_blocked": sum(1 for r in rows if r.get("in_b192") and r["needs_rerender"]),
        },
        "blast_radius": {
            "b183_go_blocked": any(r["needs_rerender"] for r in rows if r.get("in_b183")),
            "b192_go_blocked": any(r["needs_rerender"] for r in rows if r.get("in_b192")),
            "reference_ship_clean": next(
                (r["verdict"] == "CLEAN" for r in rows if r.get("reference_ship")), False
            ),
        },
        "rows": rows,
        "rerender_list": [
            {
                "slug": r["slug"],
                "lane": r["lane"],
                "reason": "; ".join(r["issues"]) or "seam/color marginal",
                "production_dir": r["production_dir"],
                "in_b183": r.get("in_b183"),
                "in_b192": r.get("in_b192"),
            }
            for r in rerender
        ],
    }

    out_path = args.output or (ROOT / "Studio" / "Pipeline" / "seam_color_audit_T4_199.json")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")

    print(json.dumps(report["summary"], indent=2))
    print(json.dumps(report["blast_radius"], indent=2))
    print(f"Wrote {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())