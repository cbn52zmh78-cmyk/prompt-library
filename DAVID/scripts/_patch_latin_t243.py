#!/usr/bin/env python3
"""One-shot: swap david_latin_corpus_v1 shot lighting clauses per T243."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
spec = json.loads((ROOT / "DAVID/handoff/T243_neutral_lighting_prompt_spec.json").read_text(encoding="utf-8"))
blocks = spec["blocks"]
clauses = spec["per_shot_lighting_clauses"]
shared_light = blocks["shared_per_shot_lighting_clause"]
color_guard = blocks["archive_set_color_guard"]
grade_lock = blocks["style_grade_lock"]
voice = (
    "mid-low resonant unhurried voice, precise diction, documentary gravitas, "
    "Attenborough-calm, accessible never stuffy, synthetic host only"
)
prefix = (
    "CONTINUITY LOCK @David-001: identical host face, charcoal sweater, Archive desk, brass lamp, "
    "same eye-line — seamless continuation of prior take, zero jump cut. "
    "CONTINUITY LOCK @Set-Archive-001: identical Archive interior — floor-to-ceiling manuscript shelves, "
    "long wooden worktable, open illuminated codex, cuneiform tablet, rolled papyrus, single brass desk lamp, "
    "same shelf blur depth, same eye-line to desk — seamless continuation, zero jump cut. "
    "STYLE LOCK @Style-Documentary-Prestige-001: documentary prestige grade — rich midtones, restrained contrast, "
    "natural skin texture, subtle film grain, trustworthy broadcast gravitas, no beauty-filter smoothing, "
    "no Instagram saturation. "
)
suffix = (
    f"{color_guard} {grade_lock} "
    "Motivated practical accent only — no unmotivated beauty dish, no fashion rim, "
    "lamp or window must be visible or implied. "
    "Slow motivated push-in or locked-off medium; handheld only for insert B-roll — never jitter on host. "
)
finish = f" {voice}. Finish on gesture peak (hand motion or lean), never hold dead stillness or dead frame."

path = ROOT / "DAVID/scripts/longform_scripts/david_latin_corpus_v1_script.json"
script = json.loads(path.read_text(encoding="utf-8"))
for shot in script["shots"]:
    sid = shot["id"]
    body = clauses[sid]
    if "[shared" in body:
        body = body.replace(
            "LIGHTING: [shared — identical stack, zero hue drift from prior segment].",
            f"LIGHTING: {shared_light}",
        )
        body = body.replace(
            "LIGHTING: [shared — neutral authority framing; no warmth push on delivery close].",
            f"LIGHTING: {shared_light}",
        )
    speech = shot.get("speech_text", "")
    shot["video_prompt"] = (
        prefix + body + " " + suffix + f'Lip-synced, delivers: "{speech}"' + finish
    )
script["config"]["seamless"]["neutral_generation"] = True
path.write_text(json.dumps(script, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
print(f"patched {len(script['shots'])} shots → {path}")