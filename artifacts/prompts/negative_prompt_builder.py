#!/usr/bin/env python3
"""
Compliance-Aware Negative Prompt Builder v1.0 — Director | New Tool
Generates strong negatives tied to CARA rating target and shot type. Fully general.
"""

import os
from datetime import datetime

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
        filename = f"../Studio/Negative_Prompts/negative_{target_rating}_{shot_type.replace(' ', '_')}_{timestamp}.txt"
        os.makedirs(os.path.dirname(filename), exist_ok=True)
        with open(filename, "w", encoding="utf-8") as f:
            f.write(neg)
        print(f"✅ Negative prompt saved: {filename}")
        return neg

if __name__ == "__main__":
    builder = NegativePromptBuilder()
    builder.save("R", "studio editorial hero")
    builder.save("PG-13", "slow runway walk")