#!/usr/bin/env python3
"""
One-Take Choreography Builder v1.1 — Director | Profile Integration
Can pull subject, lighting, and camera data from a saved Model Profile.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from lib.bootstrap import ensure_paths
ensure_paths()
from lib.studio_paths import studio_path

from datetime import datetime



try:
    from model_profile_manager import ModelProfileManager
except ImportError:
    ModelProfileManager = None


class OneTakeChoreographyBuilder:
    def __init__(self, output_dir=None):
        self.output_dir = output_dir or studio_path("OneTake_Prompts")
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.profile_mgr = ModelProfileManager() if ModelProfileManager else None

    def build(
        self,
        subject: str = "",
        camera_path: str = "",
        duration: str = "",
        physics_notes: str = "",
        lighting: str = "",
        profile_name: str = None,
    ):
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
        filepath = self.output_dir / f"{name.replace(' ', '_')}_{timestamp}.txt"
        filepath.write_text(prompt, encoding="utf-8")
        print(f"✅ One-take prompt saved: {filepath}")


if __name__ == "__main__":
    builder = OneTakeChoreographyBuilder()
    p = builder.build(duration="8-10 seconds", profile_name="Test_Editorial")
    builder.save("Hero_OneTake_From_Profile", p)