#!/usr/bin/env python3
"""
Fashion Modeling Prompt Generator v1.1 — Director | Profile Integration
"""

import os
from datetime import datetime

try:
    from model_profile_manager import ModelProfileManager
except ImportError:
    ModelProfileManager = None

class FashionModelingPromptGenerator:
    def __init__(self, output_dir="studio/Fashion_Prompts"):
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)
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

        prompt = f"photorealistic 16:9 {shot_type} of {subject}, {lighting}, {camera}, {extra}, natural physics, single subject, high-end editorial quality"
        return prompt

    def save(self, name: str, prompt: str):
        filepath = os.path.join(self.output_dir, f"{name.replace(' ', '_')}_{datetime.now().strftime('%Y%m%d_%H%M')}.txt")
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(prompt)
        print(f"✅ Saved: {filepath}")

if __name__ == "__main__":
    gen = FashionModelingPromptGenerator()
    p = gen.generate_prompt("hero studio shot", profile_name="Test_Editorial", extra="subtle fabric movement")
    gen.save("Hero_Editorial_Profile", p)