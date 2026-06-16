#!/usr/bin/env python3
"""
Template Library Manager v1.1 — Director | Physics/Lighting Block Support
Can now store and retrieve physics & lighting blocks as reusable templates.
"""

import json
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import bootstrap  # noqa: F401
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
            "version": "1.1",
        }
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
        print(f"✅ Template saved: {name}")

    def get_template(self, name: str):
        filepath = self.lib_dir / f"{name.replace(' ', '_')}.json"
        if filepath.exists():
            with open(filepath, encoding="utf-8") as f:
                return json.load(f)
        return None

    def save_physics_block(self, block_name: str, block_text: str):
        """Convenience method to save physics/lighting blocks as templates."""
        self.save_template(
            f"PhysicsBlock_{block_name}",
            block_text,
            tags=["physics", "lighting", "injector"],
            description=f"Reusable physics/lighting block from injector: {block_name}",
        )

    def search(self, tag: str = None):
        results = []
        for path in self.lib_dir.glob("*.json"):
            with open(path, encoding="utf-8") as f:
                data = json.load(f)
            if not tag or tag in data.get("tags", []):
                results.append(data)
        return results

    def instantiate(self, name: str, variables: dict):
        data = self.get_template(name)
        if not data:
            return ""
        prompt = data["template"]
        for key, value in variables.items():
            prompt = prompt.replace(f"[{key}]", str(value))
        return prompt


if __name__ == "__main__":
    lib = TemplateLibraryManager()
    lib.save_physics_block(
        "fabric_physics",
        "natural fabric drape, realistic cloth physics, subtle movement and tension in fabric",
    )
    print("\nTemplate library now supports physics/lighting blocks from the injector.")