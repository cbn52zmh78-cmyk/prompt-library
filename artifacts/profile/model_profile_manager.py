#!/usr/bin/env python3
"""
Model Profile Manager v1.2 — Director | Integration-Ready
Clean data export methods so other tools can consume profiles.
"""

import json
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import bootstrap  # noqa: F401
from studio_paths import studio_path


class ModelProfileManager:
    def __init__(self, profiles_dir=None):
        self.profiles_dir = profiles_dir or studio_path("Model_Profiles")
        self.profiles_dir.mkdir(parents=True, exist_ok=True)

    def _get_path(self, name):
        return self.profiles_dir / f"{name.replace(' ', '_')}.json"

    def create_profile(self, name: str, data: dict):
        filepath = self._get_path(name)
        if filepath.exists():
            print("⚠️ Profile already exists. Use update_profile().")
            return
        data["created"] = datetime.now().isoformat()
        data["version"] = "1.2"
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
        print(f"✅ Profile created: {name}")

    def get_profile_data(self, name: str):
        """Returns the full profile dict for use by other tools."""
        filepath = self._get_path(name)
        if not filepath.exists():
            return None
        with open(filepath, encoding="utf-8") as f:
            return json.load(f)

    def get_profile(self, name: str):
        return self.get_profile_data(name)

    def view_profile(self, name: str):
        return self.get_profile_data(name)

    def list_profile_names(self):
        return [p.stem for p in self.profiles_dir.glob("*.json")]

    def list_profiles(self):
        profiles = []
        for path in self.profiles_dir.glob("*.json"):
            with open(path, encoding="utf-8") as f:
                data = json.load(f)
            profiles.append({
                "name": data.get("name", path.stem),
                "age": data.get("age", ""),
                "tags": data.get("tags", []),
            })
        return profiles

    def update_profile(self, name: str, updates: dict):
        filepath = self._get_path(name)
        if not filepath.exists():
            print("❌ Profile not found.")
            return
        with open(filepath, encoding="utf-8") as f:
            data = json.load(f)
        data.update(updates)
        data["last_updated"] = datetime.now().isoformat()
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
        print(f"✅ Profile updated: {name}")

    def delete_profile(self, name: str):
        filepath = self._get_path(name)
        if filepath.exists():
            filepath.unlink()
            print(f"✅ Profile deleted: {name}")
        else:
            print("❌ Profile not found.")

    def export_roster(self, output_file=None):
        output_file = output_file or studio_path("model_roster_export.json")
        roster = [self.get_profile_data(p.stem) for p in self.profiles_dir.glob("*.json")]
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(roster, f, indent=2)
        print(f"✅ Roster exported ({len(roster)} profiles) → {output_file}")


if __name__ == "__main__":
    mgr = ModelProfileManager()
    mgr.create_profile("Test_Editorial", {
        "name": "Test Editorial",
        "age": "mid-20s",
        "visual": "striking symmetrical features, sharp cheekbones, captivating eyes",
        "default_lighting": "dramatic cinematic side lighting",
        "default_camera": "slow motivated push-in",
        "default_physics": "natural fabric drape and subtle movement",
    })
    print("\nAvailable profiles:", mgr.list_profile_names())
    profile = mgr.get_profile_data("Test_Editorial")
    if profile:
        print("Loaded profile visual:", profile.get("visual"))