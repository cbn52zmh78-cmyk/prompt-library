#!/usr/bin/env python3
"""
Grok Video Prompt Pack Exporter v1.0 — Director | New Tool
Bundles positive + negative + settings into a clean export pack for Grok video. Fully general.
"""

import os
import json
from datetime import datetime

class GrokVideoPackExporter:
    def __init__(self, output_dir="../../studio/Grok_Video_Packs"):
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)

    def export_pack(self, name: str, positive: str, negative: str, target_rating: str = "R", notes: str = ""):
        pack = {
            "name": name,
            "positive_prompt": positive,
            "negative_prompt": negative,
            "target_rating": target_rating,
            "exported": datetime.now().isoformat(),
            "version": "1.0",
            "notes": notes,
            "recommended_settings": {
                "motion_strength": "medium-high for fashion/editorial",
                "camera_movement": "use explicit camera language in positive prompt",
                "duration_target": "6-10 seconds for stable one-takes"
            }
        }
        filepath = os.path.join(self.output_dir, f"{name.replace(' ', '_')}_{datetime.now().strftime('%Y%m%d_%H%M')}.json")
        with open(filepath, "w") as f:
            json.dump(pack, f, indent=2)
        print(f"✅ Grok Video Pack exported: {filepath}")
        return filepath

if __name__ == "__main__":
    exp = GrokVideoPackExporter()
    exp.export_pack(
        "Hero_Editorial_Teasing_v1",
        positive="photorealistic 16:9 hero studio shot of adult woman, sustained eye contact, dramatic cinematic side lighting, elegant confident pose, natural fabric physics",
        negative="blurry, deformed, extra figures, flat lighting, static pose, watermark, text",
        target_rating="R",
        notes="Strong single-subject hero with eye contact and physics. Good base for variations."
    )