#!/usr/bin/env python3
"""
Multi-Shot Video Prompt Compiler v1.0 — Director | New Tool
Turns a shot list JSON into cohesive video prompts or segmented list. Fully general.
"""

import json
from datetime import datetime

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import bootstrap  # noqa: F401
from studio_paths import studio_path

class MultiShotVideoCompiler:
    def __init__(self, output_dir=None):
        self.output_dir = output_dir or studio_path("Video_Prompts")
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def compile(self, shotlist_json_path: str, style: str = "cohesive"):
        with open(shotlist_json_path, encoding="utf-8") as f:
            data = json.load(f)
        shots = data.get("shots", [])
        if not shots:
            print("No shots found in JSON.")
            return
        if style == "cohesive":
            combined = "Cohesive multi-shot video sequence. Maintain exact same woman, lighting direction, framing, and single-subject composition across all shots. "
            combined += "Shot progression: " + " → ".join([s.get("intent", "") for s in shots])
            combined += ". " + " ".join([s.get("prompt", "")[:80] for s in shots])
            out = {"style": "cohesive", "prompt": combined}
        else:
            out = {"style": "segmented", "segments": [{"shot": s.get("shot"), "prompt": s.get("prompt")} for s in shots]}
        timestamp = datetime.now().strftime("%Y%m%d_%H%M")
        out_file = self.output_dir / f"compiled_video_{timestamp}.json"
        with open(out_file, "w", encoding="utf-8") as f:
            json.dump(out, f, indent=2)
        print(f"✅ Compiled {len(shots)} shots → {out_file}")
        return out_file

if __name__ == "__main__":
    compiler = MultiShotVideoCompiler()
    # Demo: create minimal shot list and compile
    demo = {
        "shots": [
            {"shot": "Shot 01", "intent": "hero pose", "prompt": "adult woman, elegant hero pose, dramatic side lighting"},
            {"shot": "Shot 02", "intent": "slow push-in", "prompt": "adult woman, slow camera push-in, fabric movement, same lighting"}
        ]
    }
    demo_path = studio_path("demo_shotlist.json")
    with open(demo_path, "w", encoding="utf-8") as f:
        json.dump(demo, f, indent=2)
    compiler.compile(demo_path, style="cohesive")