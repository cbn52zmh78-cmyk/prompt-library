#!/usr/bin/env python3
"""
Model Profile Manager v1.0 — Director | New Tool
CRUD for model/character profiles with structured descriptors. Fully general.
"""

import json
from datetime import datetime

from studio_paths import studio_path

class ModelProfileManager:
    def __init__(self, profiles_dir=None):
        self.profiles_dir = profiles_dir or studio_path("Model_Profiles")
        self.profiles_dir.mkdir(parents=True, exist_ok=True)

    def create_profile(self, name: str, data: dict):
        safe = name.replace(" ", "_")
        filepath = self.profiles_dir / f"{safe}.json"
        data["created"] = datetime.now().isoformat()
        data["version"] = "1.0"
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
        print(f"✅ Profile created: {filepath}")

    def list_profiles(self):
        return [p.stem for p in self.profiles_dir.glob("*.json")]

    def get_profile(self, name: str):
        filepath = self.profiles_dir / f"{name.replace(' ', '_')}.json"
        if filepath.exists():
            with open(filepath, encoding="utf-8") as f:
                return json.load(f)
        return None

if __name__ == "__main__":
    mgr = ModelProfileManager()
    # Demo: create one generic profile
    mgr.create_profile("Generic_Editorial_Model", {
        "age": "mid-20s",
        "visual": "striking symmetrical features, sharp cheekbones, captivating eyes, flawless skin",
        "default_lighting": "dramatic cinematic side lighting with soft shadows",
        "default_camera": "static hero or slow motivated push-in",
        "tags": ["editorial", "studio", "runway"]
    })
    print("\nCurrent profiles:", mgr.list_profiles())