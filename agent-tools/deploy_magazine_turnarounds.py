#!/usr/bin/env python3
"""Deploy MAGAZINE casting turnaround plates + prompts, then rebuild registry.

BUG (fixed 2026-06-19): Earlier versions mapped session images by positional index
(1.jpg -> first roster name, 2.jpg -> second, …). Parallel image_gen calls complete
out of order, so numeric indices do NOT correspond to prompt/call order. That caused
4-way rotation (Valentina/Zara/Liora/Sofia) and Freya↔Nadia swaps.

SAFE RE-DEPLOY: Always pass --manifest with explicit actor_name -> source_path pairs.
Each source must be visually verified against appearance_lock_verbatim BEFORE listing
in the manifest. Never infer actor identity from filename index or generation order.
"""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path

WORKSPACE = Path(__file__).resolve().parents[1]
MAG_ROOT = WORKSPACE / "Studio" / "MAGAZINE" / "Editorial" / "Models"
BUILD_SCRIPT = WORKSPACE / "Studio" / "Cast" / "Scripts" / "build_gfe_magazine_casting_bible.py"
AUDIT_SCRIPT = WORKSPACE / "Studio" / "Cast" / "Scripts" / "audit_cast_compliance.py"

sys.path.insert(0, str(WORKSPACE / "Studio" / "MAGAZINE" / "scripts"))
from supermodel_roster_data import SUPERMODEL_ROSTER_10  # noqa: E402

FRAMING_TAIL = (
    "Single 16:9 turnaround reference sheet on solid pure white background. "
    "LEFT panel: side profile. CENTER panel: front view. RIGHT panel: back view. "
    "FULL-LENGTH WIDE SHOT in every panel — camera pulled back, entire body head to toe "
    "with headroom and footroom, feet visible on the floor. "
    "NOT a close-up. NOT a medium close-up. NOT a medium shot. NOT a bust shot. "
    "NOT waist-up. NOT knee-up. NOT cropped. "
    "Editorial couture base outfit in all three views — fully clothed casting wardrobe, "
    "NOT topless, NOT nude, NOT implied nudity. "
    "Standing upright, arms at their sides, hands free of any objects. "
    "Same person, identical proportions, hairstyle, and wardrobe in all three panels. "
    "Even soft studio lighting, full-length body illumination. "
    "Hyper-realistic photoreal 3D character reference model. No text, no labels, no props."
)


def build_prompt(model: dict) -> str:
    age = int(model["age"])
    ethnicity = model["ethnicity"]
    name = model["name"]
    visuals = model["visuals"]
    outfit = model["outfit"]
    age_clause = (
        f"clearly mature adult woman age {age} with fully developed adult facial features (21+ minimum)"
        if age <= 23
        else f"clearly adult woman age {age} (21+ minimum)"
    )
    person = (
        f"{age}-year-old {ethnicity} woman named {name}, {visuals}, "
        f"{age_clause}, synthetic fictional character only, no real-person likeness, "
        f"wearing {outfit} as editorial couture base outfit"
    )
    return f"GENERATE 3D MODEL of back, side and front profiles of {person}. {FRAMING_TAIL}"


def load_manifest(path: Path) -> dict[str, str]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("manifest must be a JSON object: {actor_name: source_path}")
    out: dict[str, str] = {}
    for name, src in data.items():
        if name.startswith("_"):
            continue
        if not isinstance(name, str) or not isinstance(src, str):
            raise ValueError(f"invalid manifest entry: {name!r} -> {src!r}")
        out[name] = src
    return out


def deploy_manifest(manifest: dict[str, str], *, rebuild: bool = True) -> int:
    by_name = {m["name"]: m for m in SUPERMODEL_ROSTER_10}
    unknown = set(manifest) - set(by_name)
    if unknown:
        print(f"ERROR: unknown actor names in manifest: {sorted(unknown)}")
        return 1

    for name, src_raw in manifest.items():
        src = Path(src_raw)
        if not src.is_file():
            print(f"ERROR: missing source for {name}: {src}")
            return 1
        model = by_name[name]
        dest_dir = MAG_ROOT / name / "01_casting_shots"
        dest_dir.mkdir(parents=True, exist_ok=True)
        dest_jpg = dest_dir / "casting_turnaround_v1.jpg"
        shutil.copy2(src, dest_jpg)
        (dest_dir / "casting_prompt.txt").write_text(build_prompt(model), encoding="utf-8")
        print(f"OK {name} <- {src.name} -> {dest_jpg} ({dest_jpg.stat().st_size} bytes)")

    if not rebuild:
        return 0

    print("\nRebuilding MAGAZINE casting bible...")
    result = subprocess.run(
        [sys.executable, str(BUILD_SCRIPT)],
        cwd=str(WORKSPACE),
        capture_output=True,
        text=True,
    )
    if result.stdout:
        print(result.stdout)
    if result.stderr:
        print(result.stderr, file=sys.stderr)
    if result.returncode != 0:
        return result.returncode

    audit = subprocess.run(
        [sys.executable, str(AUDIT_SCRIPT)],
        cwd=str(WORKSPACE),
        capture_output=True,
        text=True,
    )
    if audit.stdout:
        print(audit.stdout)
    return audit.returncode


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--manifest",
        required=True,
        help="JSON file mapping actor display name -> absolute path to verified source JPG",
    )
    parser.add_argument("--no-rebuild", action="store_true", help="Copy only; skip registry/audit")
    args = parser.parse_args()
    manifest_path = Path(args.manifest)
    if not manifest_path.is_file():
        print(f"ERROR: manifest not found: {manifest_path}")
        return 1
    return deploy_manifest(load_manifest(manifest_path), rebuild=not args.no_rebuild)


if __name__ == "__main__":
    raise SystemExit(main())