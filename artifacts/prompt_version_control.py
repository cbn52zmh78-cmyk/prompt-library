#!/usr/bin/env python3
"""
Prompt Version Control v1.0 — Director | New Tool
Local versioning + unified diff for prompts. Fully general.
"""

import os
import difflib
from datetime import datetime

class PromptVersionControl:
    def __init__(self, base_dir="../../studio/Prompt_Versions"):
        self.base_dir = base_dir
        os.makedirs(base_dir, exist_ok=True)

    def save_version(self, name: str, content: str, note: str = ""):
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        safe_name = name.replace(" ", "_").replace("/", "_")
        version_dir = os.path.join(self.base_dir, safe_name)
        os.makedirs(version_dir, exist_ok=True)
        filepath = os.path.join(version_dir, f"{timestamp}.txt")
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(f"# Version: {timestamp}\n# Note: {note}\n\n{content}")
        print(f"✅ Saved: {filepath}")
        return filepath

    def diff_versions(self, name: str, v1_filename: str, v2_filename: str):
        version_dir = os.path.join(self.base_dir, name.replace(" ", "_").replace("/", "_"))
        with open(os.path.join(version_dir, v1_filename), encoding="utf-8") as f:
            c1 = f.read().splitlines(keepends=True)
        with open(os.path.join(version_dir, v2_filename), encoding="utf-8") as f:
            c2 = f.read().splitlines(keepends=True)
        diff = difflib.unified_diff(c1, c2, fromfile=v1_filename, tofile=v2_filename, lineterm="")
        print("".join(diff))

if __name__ == "__main__":
    pvc = PromptVersionControl()
    # Demo: save two versions of a generic prompt
    p1 = pvc.save_version("Hero_Editorial_Teasing", "adult woman, sustained eye contact, soft directional lighting, elegant pose", "Initial clean version")
    p2 = pvc.save_version("Hero_Editorial_Teasing", "adult woman, sustained eye contact, soft directional lighting, elegant pose, subtle fabric movement", "Added fabric physics note")
    print("\n--- Diff between the two versions ---")
    pvc.diff_versions("Hero_Editorial_Teasing", os.path.basename(p1), os.path.basename(p2))