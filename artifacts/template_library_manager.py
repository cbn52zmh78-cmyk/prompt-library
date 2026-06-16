#!/usr/bin/env python3
"""
Master Prompt Template Library Manager v1.0 — Director | New Tool
Save, search, tag, and instantiate reusable prompt templates. Fully general.
"""

import json
from datetime import datetime

from studio_paths import studio_path

class TemplateLibraryManager:
    def __init__(self, lib_dir=None):
        self.lib_dir = lib_dir or studio_path("Prompt_Templates")
        self.lib_dir.mkdir(parents=True, exist_ok=True)

    def save_template(self, name: str, template: str, tags: list = None, description: str = ""):
        safe_name = name.replace(" ", "_")
        filepath = self.lib_dir / f"{safe_name}.json"
        data = {
            "name": name,
            "template": template,
            "tags": tags or [],
            "description": description,
            "created": datetime.now().isoformat(),
            "version": "1.0"
        }
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
        print(f"✅ Template saved: {filepath}")

    def search(self, tag: str = None):
        results = []
        for path in self.lib_dir.glob("*.json"):
            with open(path, encoding="utf-8") as f:
                data = json.load(f)
            if not tag or tag in data.get("tags", []):
                results.append(data)
        return results

    def instantiate(self, name: str, variables: dict):
        filepath = self.lib_dir / f"{name.replace(' ', '_')}.json"
        with open(filepath, encoding="utf-8") as f:
            data = json.load(f)
        prompt = data["template"]
        for k, v in variables.items():
            prompt = prompt.replace(f"[{k}]", str(v))
        return prompt

if __name__ == "__main__":
    lib = TemplateLibraryManager()
    # Demo: save two templates
    lib.save_template(
        "Hero_Editorial",
        "photorealistic 16:9 hero studio shot of [SUBJECT], [LIGHTING], elegant confident pose, natural fabric physics, single subject, clean composition",
        tags=["hero", "studio", "editorial"],
        description="Standard hero editorial pose with strong lighting and physics"
    )
    lib.save_template(
        "Slow_Runway_Walk",
        "photorealistic 16:9 slow runway walk of [SUBJECT], [LIGHTING], subtle fabric movement and physics, sustained eye contact, dynamic motion",
        tags=["runway", "motion", "editorial"],
        description="Controlled runway walk with fabric physics and eye contact"
    )
    print("\n--- Search for 'editorial' templates ---")
    for t in lib.search("editorial"):
        print(f"  {t['name']}: {t['description']}")