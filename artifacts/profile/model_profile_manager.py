#!/usr/bin/env python3
"""
Model Profile Manager v1.1 — Director | Improved
Full CRUD + structured profiles + roster export. Fully general.
"""

import json
from datetime import datetime

import sys
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
            print(f"⚠️ Profile '{name}' already exists. Use update instead.")
            return
        data["created"] = datetime.now().isoformat()
        data["version"] = "1.1"
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
        print(f"✅ Profile created: {filepath}")

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

    def view_profile(self, name: str):
        filepath = self._get_path(name)
        if not filepath.exists():
            print(f"❌ Profile '{name}' not found.")
            return None
        with open(filepath, encoding="utf-8") as f:
            return json.load(f)

    def get_profile(self, name: str):
        return self.view_profile(name)

    def update_profile(self, name: str, updates: dict):
        filepath = self._get_path(name)
        if not filepath.exists():
            print(f"❌ Profile '{name}' not found.")
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
            print(f"❌ Profile '{name}' not found.")

    def export_roster(self, output_file=None):
        output_file = output_file or studio_path("model_roster_export.json")
        roster = []
        for path in self.profiles_dir.glob("*.json"):
            with open(path, encoding="utf-8") as f:
                roster.append(json.load(f))
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(roster, f, indent=2)
        print(f"✅ Roster exported ({len(roster)} profiles) → {output_file}")

if __name__ == "__main__":
    mgr = ModelProfileManager()
    mgr.create_profile("Test_Editorial_Model", {
        "name": "Test Editorial Model",
        "age": "mid-20s",
        "visual": "striking symmetrical features, sharp cheekbones, captivating eyes",
        "default_lighting": "dramatic cinematic side lighting",
        "default_camera": "static hero or slow motivated push-in",
        "default_physics": "natural fabric drape and subtle body movement",
        "tags": ["editorial", "studio", "hero"],
    })
    print("\n--- Current Profiles ---")
    for p in mgr.list_profiles():
        print(f"  {p['name']} | {p['age']} | {p['tags']}")