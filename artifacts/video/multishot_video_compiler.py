#!/usr/bin/env python3
"""
Multi-Shot Video Compiler v1.1 — Director | Profile Integration
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from lib.bootstrap import ensure_paths
ensure_paths()
from lib.studio_paths import studio_path

import json
from datetime import datetime



try:
    from profile.model_profile_manager import ModelProfileManager
except ImportError:
    ModelProfileManager = None


class MultiShotVideoCompiler:
    def __init__(self, output_dir=None):
        self.output_dir = output_dir or studio_path("Video_Prompts")
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.profile_mgr = ModelProfileManager() if ModelProfileManager else None

    def compile(self, shotlist_json_path: str, profile_name: str = None, style: str = "cohesive"):
        with open(shotlist_json_path, encoding="utf-8") as f:
            data = json.load(f)
        shots = data.get("shots", [])

        profile_injection = ""
        if profile_name and self.profile_mgr:
            profile = self.profile_mgr.get_profile_data(profile_name)
            if profile:
                profile_injection = f"Maintain consistent appearance: {profile.get('visual', '')}. "
                print(f"→ Using profile across sequence: {profile_name}")

        if style == "cohesive":
            combined = profile_injection + "Cohesive multi-shot sequence. "
            combined += " → ".join(s.get("intent", "") for s in shots)
            combined += ". " + " ".join(s.get("prompt", "") for s in shots)
            out = {"style": "cohesive", "profile_used": profile_name, "prompt": combined}
        else:
            out = {"style": "segmented", "profile_used": profile_name, "segments": shots}

        filepath = self.output_dir / f"compiled_{datetime.now().strftime('%Y%m%d_%H%M')}.json"
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(out, f, indent=2)
        print(f"✅ Compiled {len(shots)} shots → {filepath}")
        return filepath


if __name__ == "__main__":
    compiler = MultiShotVideoCompiler()
    demo = {
        "shots": [
            {"intent": "hero", "prompt": "adult woman, elegant pose"},
            {"intent": "push-in", "prompt": "slow camera push-in"},
        ]
    }
    demo_path = studio_path("demo_shots.json")
    with open(demo_path, "w", encoding="utf-8") as f:
        json.dump(demo, f, indent=2)
    compiler.compile(demo_path, profile_name="Test_Editorial")