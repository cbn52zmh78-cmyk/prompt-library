#!/usr/bin/env python3
"""
Fashion Modeling Prompt Generator v1.1 — Director | Profile Integration
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from lib.bootstrap import ensure_paths
ensure_paths()
from lib.studio_paths import pipeline_path

from datetime import datetime



try:
    from profile.model_profile_manager import ModelProfileManager
except ImportError:
    ModelProfileManager = None


class FashionModelingPromptGenerator:
    def __init__(self, output_dir=None):
        self.output_dir = output_dir or pipeline_path("Fashion_Prompts")
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.profile_mgr = ModelProfileManager() if ModelProfileManager else None

    def generate_prompt(self, shot_type: str, profile_name: str = None, extra: str = ""):
        subject = "adult woman"
        lighting = "dramatic cinematic lighting"
        camera = "elegant hero framing"

        if profile_name and self.profile_mgr:
            profile = self.profile_mgr.get_profile_data(profile_name)
            if profile:
                subject = profile.get("visual", subject)
                lighting = profile.get("default_lighting", lighting)
                camera = profile.get("default_camera", camera)
                print(f"→ Using profile: {profile_name}")

        prompt = (
            f"photorealistic 16:9 {shot_type} of {subject}, {lighting}, {camera}, "
            f"{extra}, natural physics, single subject, high-end editorial quality"
        )
        return prompt

    def save(self, name: str, prompt: str):
        filepath = self.output_dir / f"{name.replace(' ', '_')}_{datetime.now().strftime('%Y%m%d_%H%M')}.txt"
        filepath.write_text(prompt, encoding="utf-8")
        print(f"✅ Saved: {filepath}")


if __name__ == "__main__":
    gen = FashionModelingPromptGenerator()
    p = gen.generate_prompt("hero studio shot", profile_name="Test_Editorial", extra="subtle fabric movement")
    gen.save("Hero_Editorial_Profile", p)