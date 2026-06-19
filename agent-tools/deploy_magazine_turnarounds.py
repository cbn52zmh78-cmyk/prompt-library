#!/usr/bin/env python3
"""Deploy MAGAZINE casting turnaround plates + prompts, then rebuild registry."""

from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

WORKSPACE = Path(r"C:\Users\NCG\Videos\Grok Projects")
SESSION_IMAGES = Path(
    r"C:\Users\NCG\.grok\sessions\C%3A%5CUsers%5CNCG%5CVideos%5CGrok%20Projects"
    r"\019eddbf-7950-7b51-ac0a-d019bc76abb7\images"
)
MAG_ROOT = WORKSPACE / "Studio" / "MAGAZINE" / "Editorial" / "Models"
BUILD_SCRIPT = WORKSPACE / "Studio" / "Cast" / "Scripts" / "build_gfe_magazine_casting_bible.py"

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
        f"{age_clause}, synthetic character only, no real-person or celebrity likeness, "
        f"wearing {outfit} as editorial couture base outfit"
    )
    return f"GENERATE 3D MODEL of back, side and front profiles of {person}. {FRAMING_TAIL}"


def main() -> int:
    if not SESSION_IMAGES.exists():
        print(f"ERROR: session images folder missing: {SESSION_IMAGES}")
        return 1

    roster = sorted(SUPERMODEL_ROSTER_10, key=lambda m: m["name"])
    # Generation order (batch 1-4, 5-8, 9-10) mapped to roster call order.
    gen_order = [
        "Valentina Rossi",
        "Zara Khan",
        "Liora Voss",
        "Sofia Alvarez",
        "Anya Petrova",
        "Nadia Okoro",
        "Freya Lind",
        "Mei Lin Chen",
        "Isolde Moreau",
        "Priya Singh",
    ]
    by_name = {m["name"]: m for m in SUPERMODEL_ROSTER_10}

    for idx, name in enumerate(gen_order, start=1):
        src = SESSION_IMAGES / f"{idx}.jpg"
        if not src.exists():
            print(f"ERROR: missing generated plate {src}")
            return 1
        model = by_name[name]
        dest_dir = MAG_ROOT / name / "01_casting_shots"
        dest_dir.mkdir(parents=True, exist_ok=True)
        dest_jpg = dest_dir / "casting_turnaround_v1.jpg"
        shutil.copy2(src, dest_jpg)
        prompt_path = dest_dir / "casting_prompt.txt"
        prompt_path.write_text(build_prompt(model), encoding="utf-8")
        print(f"OK {name} -> {dest_jpg} ({dest_jpg.stat().st_size} bytes)")

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

    verify = subprocess.run(
        [sys.executable, str(WORKSPACE / "agent-tools" / "verify_batch_b.py")],
        cwd=str(WORKSPACE),
        capture_output=True,
        text=True,
    )
    print(verify.stdout)
    return verify.returncode


if __name__ == "__main__":
    raise SystemExit(main())