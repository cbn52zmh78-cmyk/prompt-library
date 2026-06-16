#!/usr/bin/env python3
"""
One-Take Choreography Builder v1.1 — Director | Profile Integration
Can pull subject, lighting, and camera data from a saved Model Profile.
"""

import os
from datetime import datetime

try:
    from model_profile_manager import ModelProfileManager
except ImportError:
    ModelProfileManager = None

class OneTakeChoreographyBuilder:
    def __init__(self, output_dir="studio/OneTake_Prompts"):
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)
        self.profile_mgr = ModelProfileManager() if ModelProfileManager else None

    def build(self, subject: str = "", camera_path: str = "", duration: str = "", 
              physics_notes: str = "", lighting: str = "", profile_name: str = None):

        # If profile is provided, pull data from it
        if profile_name and self.profile_mgr:
            profile = self.profile_mgr.get_profile_data(profile_name)
            if profile:
                subject = profile.get("visual", subject)
                lighting = profile.get("default_lighting", lighting)
                camera_path = profile.get("default_camera", camera_path)
                physics_notes = profile.get("default_physics", physics_notes)
                print(f"→ Using profile: {profile_name}")

        prompt = (
            f"photorealistic 16:9 single continuous one-take shot of {subject}, "
            f"{camera_path}, exact same framing maintained throughout, "
            f"{lighting}, {physics_notes}, natural fabric and body physics, "
            f"no cuts, precise motivated camera movement over {duration}, "
            "clean single-subject composition, commercial-ready high-end cinematic quality"
        )
        return prompt

    def save(self, name: str, prompt: str):
        timestamp = datetime.now().strftime("%Y%m%d_%H%M")
        filepath = os.path.join(self.output_dir, f"{name.replace(' ', '_')}_{timestamp}.txt")
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(prompt)
        print(f"✅ One-take prompt saved: {filepath}")

if __name__ == "__main__":
    builder = OneTakeChoreographyBuilder()
    p = builder.build(
        duration="8-10 seconds",
        profile_name="Test_Editorial"   # ← Now pulls from profile
    )
    builder.save("Hero_OneTake_From_Profile", p)