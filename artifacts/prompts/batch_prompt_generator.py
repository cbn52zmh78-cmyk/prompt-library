#!/usr/bin/env python3
"""
Batch Prompt Generator v1.1 — Director | Now integrates with Model Profiles
Can pull subject data from a saved profile in Model Profile Manager.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from lib.bootstrap import ensure_paths
ensure_paths()
from lib.studio_paths import pipeline_path

import json
from datetime import datetime



try:
    from profile.model_profile_manager import ModelProfileManager
except ImportError:
    ModelProfileManager = None


class BatchPromptGenerator:
    def __init__(self, output_dir=None):
        self.output_dir = output_dir or pipeline_path("Batch_Outputs")
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.profile_mgr = ModelProfileManager() if ModelProfileManager else None

    def generate_from_json(self, json_path: str, profile_name: str = None):
        with open(json_path, encoding="utf-8") as f:
            data = json.load(f)

        base = data.get("base_prompt", "")

        if profile_name and self.profile_mgr:
            profile = self.profile_mgr.get_profile_data(profile_name)
            if profile:
                base = base.replace("[SUBJECT]", profile.get("visual", ""))
                base = base.replace("[LIGHTING]", profile.get("default_lighting", ""))
                base = base.replace("[CAMERA]", profile.get("default_camera", ""))
                print(f"→ Injected data from profile: {profile_name}")

        variations = data.get("variations", [])
        results = []
        for i, var in enumerate(variations, 1):
            prompt = base
            for key, value in var.items():
                prompt = prompt.replace(f"[{key}]", str(value))
            results.append({"index": i, "prompt": prompt})

        timestamp = datetime.now().strftime("%Y%m%d_%H%M")
        out_file = self.output_dir / f"batch_{timestamp}.json"
        with open(out_file, "w", encoding="utf-8") as f:
            json.dump(
                {"generated": timestamp, "profile_used": profile_name, "prompts": results},
                f,
                indent=2,
            )
        print(f"✅ Generated {len(results)} prompts → {out_file}")
        return out_file


if __name__ == "__main__":
    gen = BatchPromptGenerator()
    demo = {
        "base_prompt": "photorealistic 16:9 [SHOT_TYPE] of [SUBJECT], [LIGHTING], [CAMERA], elegant confident pose",
        "variations": [
            {"SHOT_TYPE": "hero studio shot"},
            {"SHOT_TYPE": "slow push-in runway"},
        ],
    }
    demo_path = pipeline_path("batch_demo.json")
    with open(demo_path, "w", encoding="utf-8") as f:
        json.dump(demo, f, indent=2)

    gen.generate_from_json(demo_path, profile_name="Test_Editorial")