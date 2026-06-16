#!/usr/bin/env python3
"""
Physics & Lighting Reference Injector v1.0 — Director | New Tool
Quick injection of high-quality physics, lighting, and camera language blocks.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from lib.bootstrap import ensure_paths
ensure_paths()
from lib.studio_paths import studio_path

BLOCKS = {
    "fabric_physics": "natural fabric drape, realistic cloth physics, subtle movement and tension in fabric, micro-folds and natural settling",
    "f1_tire": "aggressive tire deformation under load, visible sidewall flex, heat haze from tires, realistic rubber physics",
    "f1_suspension": "visible suspension compression and extension, precise mechanical movement, realistic damper and spring behavior",
    "dramatic_side_lighting": "dramatic cinematic side lighting, strong key light from camera left or right, deep but readable shadows, subtle rim light on edges",
    "high_contrast_cinematic": "high contrast cinematic lighting, deep blacks, bright specular highlights, moody atmosphere",
    "slow_push_in": "slow motivated camera push-in, smooth continuous movement, slight natural handheld micro-movement, precise framing progression",
    "static_hero": "locked-off static hero framing, perfect symmetrical or rule-of-thirds composition, no camera movement, maximum stability",
    "runway_motion": "controlled runway walk with natural body sway, realistic fabric flow and physics, subtle ground contact and weight shift",
}


class PhysicsLightingInjector:
    def list_blocks(self):
        print("\nAvailable injection blocks:")
        for key, desc in BLOCKS.items():
            print(f"  {key}: {desc[:60]}...")

    def get_block(self, key: str):
        return BLOCKS.get(key, "")

    def save_block(self, key: str, filename=None):
        if key not in BLOCKS:
            print(f"❌ Block '{key}' not found.")
            return
        if filename:
            parts = [p for p in filename.replace("\\", "/").split("/") if p and p.lower() != "studio"]
            filepath = studio_path(*parts)
        else:
            filepath = studio_path("Physics_Lighting_Blocks", f"{key}.txt")
        filepath.parent.mkdir(parents=True, exist_ok=True)
        filepath.write_text(BLOCKS[key], encoding="utf-8")
        print(f"✅ Block saved: {filepath}")


if __name__ == "__main__":
    inj = PhysicsLightingInjector()
    inj.list_blocks()
    inj.save_block("fabric_physics")
    inj.save_block("dramatic_side_lighting")