#!/usr/bin/env python3
"""
Prompt Version Control v1.0 — Director | New Tool
Local versioning + unified diff for prompts. Fully general.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from lib.bootstrap import ensure_paths
ensure_paths()
from lib.studio_paths import pipeline_path

import difflib
from datetime import datetime



class PromptVersionControl:
    def __init__(self, base_dir=None):
        self.base_dir = base_dir or pipeline_path("Prompt_Versions")
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def save_version(self, name: str, content: str, note: str = ""):
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        safe_name = name.replace(" ", "_").replace("/", "_")
        version_dir = self.base_dir / safe_name
        version_dir.mkdir(parents=True, exist_ok=True)
        filepath = version_dir / f"{timestamp}.txt"
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(f"# Version: {timestamp}\n# Note: {note}\n\n{content}")
        print(f"✅ Saved: {filepath}")
        return filepath

    def diff_versions(self, name: str, v1_filename: str, v2_filename: str):
        version_dir = self.base_dir / name.replace(" ", "_").replace("/", "_")
        with open(version_dir / v1_filename, encoding="utf-8") as f:
            c1 = f.read().splitlines(keepends=True)
        with open(version_dir / v2_filename, encoding="utf-8") as f:
            c2 = f.read().splitlines(keepends=True)
        diff = difflib.unified_diff(c1, c2, fromfile=v1_filename, tofile=v2_filename, lineterm="")
        print("".join(diff))

if __name__ == "__main__":
    pvc = PromptVersionControl()
    # Demo: save two versions of a generic prompt
    p1 = pvc.save_version("Hero_Editorial_Teasing", "adult woman, sustained eye contact, soft directional lighting, elegant pose", "Initial clean version")
    p2 = pvc.save_version("Hero_Editorial_Teasing", "adult woman, sustained eye contact, soft directional lighting, elegant pose, subtle fabric movement", "Added fabric physics note")
    print("\n--- Diff between the two versions ---")
    pvc.diff_versions("Hero_Editorial_Teasing", p1.name, p2.name)