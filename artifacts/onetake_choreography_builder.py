#!/usr/bin/env python3
"""
One-Take Choreography Prompt Builder v1.0 — Director | New Tool
Helps construct stable long single-take prompts with camera path and timing. Fully general.
"""

from datetime import datetime

from studio_paths import studio_path

class OneTakeChoreographyBuilder:
    def __init__(self, output_dir=None):
        self.output_dir = output_dir or studio_path("OneTake_Prompts")
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def build(self, subject: str, camera_path: str, duration: str, physics_notes: str, lighting: str):
        prompt = (
            f"photorealistic 16:9 single continuous one-take shot of {subject}, "
            f"{camera_path}, exact same framing and composition maintained throughout, "
            f"{lighting}, {physics_notes}, natural fabric and body physics, "
            f"no cuts, no jump cuts, precise motivated camera movement over {duration}, "
            "clean single-subject composition, negative space respected, commercial-ready high-end cinematic quality"
        )
        return prompt

    def save(self, name: str, prompt: str):
        timestamp = datetime.now().strftime("%Y%m%d_%H%M")
        filepath = self.output_dir / f"{name.replace(' ', '_')}_{timestamp}.txt"
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(prompt)
        print(f"✅ One-take prompt saved: {filepath}")

if __name__ == "__main__":
    builder = OneTakeChoreographyBuilder()
    p = builder.build(
        subject="adult woman in structured avant-garde gown",
        camera_path="slow elegant push-in from medium to tight hero framing with subtle arc",
        duration="8-10 seconds",
        physics_notes="subtle fabric drape and movement with natural body physics",
        lighting="dramatic cinematic side lighting with soft rim on shoulders"
    )
    builder.save("Hero_OneTake_PushIn", p)