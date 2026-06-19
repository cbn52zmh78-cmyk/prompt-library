#!/usr/bin/env python3
"""T4 #218 — purge warm-global Archive lighting from longform script video_prompts."""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SPEC = ROOT / "DAVID" / "handoff" / "T243_neutral_lighting_prompt_spec.json"
SCRIPTS_DIR = ROOT / "DAVID" / "scripts" / "longform_scripts"

WARM_BLOCK_RE = re.compile(
    r"Warm gold brass desk lamp 3200K key light locked[^.]*\."
    r"(?:\s*Motivated practical key only[^.]*\.)?"
    r"\s*COLOR LOCK Archive: dominant amber 3200K[^.]*\."
    r"\s*GRADE LOCK Documentary-Prestige: skin warmth \+3% amber max[^.]*\.",
    re.I,
)

NEUTRAL_REPLACEMENT = (
    "LIGHTING: Neutral balanced 5000K ambient key on host — natural skin, blue channel intact; "
    "brass desk lamp 3200K localized warm pool on desk quadrant only (desk, codex, lamp shade), "
    "NOT global amber wash on face or room; soft 5200K shelf bounce ≤25%; no yellow-green cast; "
    "no blue-starved shadows; no magenta ambient. "
    "GENERATION LOCK Archive-neutral (#243): balanced white balance 4800–5200K base; natural skin "
    "midtones with intact blue channel (B≥40 in mids); wood burnt umber #3D2B1F to #5C4033; "
    "parchment cream #F5F0E6; shadow neutral warm-grey #3A3530; brass lamp warmth localized to "
    "desk pool only — forbid dominant amber 3200K full-frame, forbid yellow-green global cast, "
    "forbid blue-starved generation (B<25 in host mids), forbid magenta cast, forbid global orange "
    "skin push. "
    "GRADE LOCK Documentary-Prestige (#243): natural skin at generation — neutral WB, blue channel "
    "preserved; post grade may add +3% amber warmth LOCAL to lamp-side cheek and desk only — forbid "
    "global orange push, forbid yellow-green cast, forbid blue-starved shadows, forbid magenta "
    "midtones. Motivated practical accent only — no unmotivated beauty dish, no fashion rim, "
    "lamp or window must be visible or implied."
)

SUBS = [
    (re.compile(r"\bwarm brass lamplight\b", re.I), "neutral ambient light, brass lamp accent on desk only"),
    (re.compile(r"\bWarm inviting close\b"), "Neutral inviting close"),
    (re.compile(r"\bCamera: warm inviting close\b", re.I), "Camera: neutral inviting close"),
    (re.compile(r"\bshadows warm-neutral not blue\b", re.I), "shadows neutral warm-grey with blue present"),
    (re.compile(r"\bno blue fill\b", re.I), "blue channel preserved in mids"),
    (re.compile(r"\bamber pool only on desk and face\b", re.I), "localized warm pool on desk quadrant only"),
]

CORPUS_GLOB = "david_*_corpus_v1_script.json"
TEMPLATE_GLOBS = [
    "template_validate_documentary_host_script.json",
    "template_validate_historical_figure_documentary_script.json",
]


def purge_prompt(text: str) -> tuple[str, bool]:
    original = text
    text = WARM_BLOCK_RE.sub(NEUTRAL_REPLACEMENT, text)
    for pat, repl in SUBS:
        text = pat.sub(repl, text)
    return text, text != original


def purge_file(path: Path) -> int:
    data = json.loads(path.read_text(encoding="utf-8"))
    changed = 0
    for shot in data.get("shots", []):
        vp = shot.get("video_prompt", "")
        new_vp, did = purge_prompt(vp)
        if did:
            shot["video_prompt"] = new_vp
            changed += 1
    if changed:
        path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return changed


def main() -> int:
    targets: list[Path] = sorted(SCRIPTS_DIR.glob(CORPUS_GLOB))
    for g in TEMPLATE_GLOBS:
        p = SCRIPTS_DIR / g
        if p.is_file():
            targets.append(p)
    total = 0
    for path in targets:
        n = purge_file(path)
        status = f"{n} shots updated" if n else "already clean"
        print(f"{path.name}: {status}")
        total += n
    print(f"total shots purged: {total}")
    return 0


if __name__ == "__main__":
    sys.exit(main())