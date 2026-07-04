#!/usr/bin/env python3
"""
screenplay_pipeline.py -- Phase B full pipeline wrapper.

Chains the four Phase B components into a single CLI:
  1. screenplay_ingest.py   -- parse raw screenplay -> schema-compliant JSON
  2. modifier_suggester.py  -- analyse tone -> suggest DNA tags / modifiers
  3. catalog_resolver.py    -- fuzzy-match names -> production catalog @IDs
  4. Output render-ready JSON for render_longform.py

Usage:
    python screenplay_pipeline.py input.pdf -o render_ready.json
    python screenplay_pipeline.py input.fountain --title "My Film" --format-id movies --auto-register
    python screenplay_pipeline.py input.txt --dry-run --stats
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

from screenplay_ingest import read_screenplay, classify_lines, group_into_scenes, build_shots, assemble_script
from modifier_suggester import suggest_modifiers, apply_suggestions
from catalog_resolver import resolve_catalog, apply_resolutions, auto_register

try:
    from production_catalog import Catalog, catalog_for_product
    _CATALOG_AVAILABLE = True
except ImportError:
    _CATALOG_AVAILABLE = False


def run_pipeline(
    input_path,
    title=None,
    format_id="movies",
    catalog_path=None,
    auto_register_ids=False,
    dry_run=False,
    show_stats=False,
):
    """Run the full screenplay-to-render pipeline. Returns render-ready script dict."""
    t0 = time.time()
    stages = []

    # Stage 1: Parse
    t1 = time.time()
    print("[pipeline] Stage 1/3: Parsing screenplay...", file=sys.stderr)
    raw_lines, title_meta = read_screenplay(input_path)
    elements = classify_lines(raw_lines)
    scenes = group_into_scenes(elements)
    characters = {}
    shots = build_shots(scenes, characters)
    script = assemble_script(
        shots=shots,
        elements=elements,
        title=title or title_meta.get('title', Path(input_path).stem),
        format_id=format_id,
        title_meta=title_meta,
        characters=characters,
    )
    stages.append(("parse", round(time.time() - t1, 2)))
    print("  -> {} shots, {} characters".format(
        len(script["shots"]), len(script.get("_characters", {}))), file=sys.stderr)

    # Stage 2: Modifiers
    t2 = time.time()
    print("[pipeline] Stage 2/3: Suggesting modifiers...", file=sys.stderr)
    suggestions = suggest_modifiers(script)
    if not dry_run:
        script = apply_suggestions(script, suggestions)
    stages.append(("modifiers", round(time.time() - t2, 2)))

    vis = suggestions.get("style_dna_tag", {}).get("recommended", "none")
    aud = suggestions.get("audio_dna_tag", {}).get("recommended", "none")
    mus = suggestions.get("music_dna_tag", {}).get("recommended", "none")
    pac = suggestions.get("pacing_dna_tag", {}).get("recommended", "none")
    print("  -> visual={}, audio={}, music={}, pacing={}".format(vis, aud, mus, pac), file=sys.stderr)

    # Stage 3: Catalog Resolution
    t3 = time.time()
    print("[pipeline] Stage 3/3: Resolving catalog IDs...", file=sys.stderr)
    catalog = None
    if catalog_path and _CATALOG_AVAILABLE:
        catalog = Catalog.load(catalog_path)
    elif _CATALOG_AVAILABLE:
        try:
            catalog = catalog_for_product("movie")
        except Exception:
            pass

    report = resolve_catalog(script, catalog)
    s = report["summary"]
    print("  -> {} entities: {} resolved, {} unresolved, {} HITL".format(
        s["total"], s["resolved"], s["unresolved"], len(report["hitl_queue"])), file=sys.stderr)

    if auto_register_ids and catalog and s["unresolved"] > 0:
        report = auto_register(script, catalog, report)
        print("  -> Auto-registered {} new entries".format(s["unresolved"]), file=sys.stderr)
        if catalog_path:
            catalog.save(catalog_path)

    if not dry_run:
        script = apply_resolutions(script, report, auto_only=not auto_register_ids)

    stages.append(("catalog", round(time.time() - t3, 2)))

    # Provenance
    total_time = round(time.time() - t0, 2)
    script["provenance_card"] = script.get("provenance_card", {})
    script["provenance_card"]["pipeline"] = {
        "version": "phase_b_v1",
        "source": str(input_path),
        "stages": {name: "{}s".format(dur) for name, dur in stages},
        "total_seconds": total_time,
        "auto_registered": auto_register_ids,
        "dry_run": dry_run,
    }

    # Stats
    if show_stats:
        total_dur = sum(sh.get("duration", 0) for sh in script.get("shots", []))
        print("\n[pipeline] Stats:", file=sys.stderr)
        print("  Shots       : {}".format(len(script["shots"])), file=sys.stderr)
        print("  Duration    : {:.1f}s ({:.1f}min)".format(total_dur, total_dur / 60), file=sys.stderr)
        print("  Characters  : {}".format(len(script.get("_characters", {}))), file=sys.stderr)
        print("  Resolved    : {}/{}".format(s["resolved"], s["total"]), file=sys.stderr)
        print("  HITL queue  : {}".format(len(report["hitl_queue"])), file=sys.stderr)
        print("  Pipeline    : {}s".format(total_time), file=sys.stderr)

    # Clean internal metadata before output
    script.pop("_characters", None)

    return script


def main():
    parser = argparse.ArgumentParser(
        description="Full screenplay ingest pipeline: parse -> modifiers -> catalog -> render-ready JSON."
    )
    parser.add_argument("input", help="Path to screenplay (PDF, TXT, or Fountain)")
    parser.add_argument("-o", "--output", help="Output path for render-ready JSON")
    parser.add_argument("--title", help="Override script title")
    parser.add_argument("--format-id", default="movies",
                        choices=["movies", "shorts", "ads", "music_videos", "docs",
                                 "series_episode", "social_content", "trailers",
                                 "cutscenes", "custom"],
                        help="Format ID (default: movies)")
    parser.add_argument("--catalog", help="Path to master_catalog.json")
    parser.add_argument("--auto-register", action="store_true",
                        help="Auto-register unresolved names as new catalog entries")
    parser.add_argument("--dry-run", action="store_true",
                        help="Parse and analyse without applying modifications")
    parser.add_argument("--stats", action="store_true",
                        help="Print pipeline statistics")

    args = parser.parse_args()

    script = run_pipeline(
        args.input,
        title=args.title,
        format_id=args.format_id,
        catalog_path=args.catalog,
        auto_register_ids=args.auto_register,
        dry_run=args.dry_run,
        show_stats=args.stats,
    )

    output_str = json.dumps(script, indent=2, ensure_ascii=False, default=str)
    if args.output:
        Path(args.output).write_text(output_str, encoding="utf-8")
        print("\n[pipeline] Written: {}".format(args.output), file=sys.stderr)
    else:
        print(output_str)


if __name__ == "__main__":
    main()
