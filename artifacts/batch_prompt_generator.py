#!/usr/bin/env python3
"""
Batch Prompt Generator v1.0 — Director | New Tool
Reads JSON parameter file and generates many prompts at once. Fully general.
"""

import os
import json
from datetime import datetime

class BatchPromptGenerator:
    def __init__(self, output_dir="../../studio/Batch_Outputs"):
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)

    def generate_from_json(self, json_path: str):
        with open(json_path, encoding="utf-8") as f:
            data = json.load(f)
        base = data.get("base_prompt", "")
        variations = data.get("variations", [])
        results = []
        for i, var in enumerate(variations, 1):
            prompt = base
            for key, value in var.items():
                prompt = prompt.replace(f"[{key}]", str(value))
            results.append({"index": i, "prompt": prompt})
        timestamp = datetime.now().strftime("%Y%m%d_%H%M")
        out_file = os.path.join(self.output_dir, f"batch_{timestamp}.json")
        with open(out_file, "w", encoding="utf-8") as f:
            json.dump({"generated": timestamp, "prompts": results}, f, indent=2)
        print(f"✅ Generated {len(results)} prompts → {out_file}")
        return out_file

if __name__ == "__main__":
    gen = BatchPromptGenerator()
    # Demo: create a small example JSON and run it
    demo_json = {
        "base_prompt": "photorealistic 16:9 [SHOT_TYPE] of [SUBJECT], [LIGHTING], elegant confident pose, natural physics",
        "variations": [
            {"SHOT_TYPE": "hero studio shot", "SUBJECT": "adult woman in structured gown", "LIGHTING": "dramatic side lighting"},
            {"SHOT_TYPE": "slow push-in runway", "SUBJECT": "adult woman in metallic avant-garde dress", "LIGHTING": "high contrast cinematic lighting"}
        ]
    }
    demo_path = "../../studio/batch_demo_params.json"
    with open(demo_path, "w", encoding="utf-8") as f:
        json.dump(demo_json, f, indent=2)
    gen.generate_from_json(demo_path)