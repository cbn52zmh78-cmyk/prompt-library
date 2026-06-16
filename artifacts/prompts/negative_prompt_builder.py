#!/usr/bin/env python3
"""
Compliance-Aware Negative Prompt Builder v1.0 — Director | New Tool
Generates strong negatives tied to CARA rating target and shot type. Fully general.
"""

import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from lib.bootstrap import ensure_paths
ensure_paths()
from lib.studio_paths import pipeline_path

class NegativePromptBuilder:
    def __init__(self):
        self.base_negatives = "blurry, low quality, deformed, extra limbs, extra fingers, bad anatomy, watermark, text, logo, multiple people, extra figures, off-center framing, flat lighting"

    def build(self, target_rating: str = "R", shot_type: str = "studio editorial"):
        negatives = self.base_negatives
        if target_rating in ["G", "PG", "PG-13"]:
            negatives += ", explicit nudity, graphic sex, strong profanity, drug use, intense gore"
        if "runway" in shot_type.lower() or "walk" in shot_type.lower():
            negatives += ", static pose, no motion, frozen fabric"
        if "close-up" in shot_type.lower() or "hero" in shot_type.lower():
            negatives += ", wide shot, full body out of frame, head cut off"
        return negatives

    def save(self, target_rating: str, shot_type: str):
        neg = self.build(target_rating, shot_type)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M")
        filepath = pipeline_path(
            "Negative_Prompts",
            f"negative_{target_rating}_{shot_type.replace(' ', '_')}_{timestamp}.txt",
        )
        filepath.write_text(neg, encoding="utf-8")
        print(f"✅ Negative prompt saved: {filepath}")
        return neg

if __name__ == "__main__":
    builder = NegativePromptBuilder()
    builder.save("R", "studio editorial hero")
    builder.save("PG-13", "slow runway walk")