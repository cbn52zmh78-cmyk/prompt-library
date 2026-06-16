#!/usr/bin/env python3
"""
Workspace Status Reporter v1.0 — Director | New Tool
Shows counts and health of all major Studio folders.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from lib.bootstrap import ensure_paths
ensure_paths()
from lib.studio_paths import STUDIO_DIR

from datetime import datetime



FOLDERS = (
    "Model_Profiles",
    "Prompt_Templates",
    "Prompt_Versions",
    "OneTake_Prompts",
    "Video_Prompts",
    "Refined_Prompts",
    "Fashion_Prompts",
    "Grok_Video_Packs",
    "Canons_Bibles",
    "References",
    "Asset_Metadata",
    "Physics_Lighting_Blocks",
    "Batch_Outputs",
    "Tool_Logs",
)


def report_status():
    print("\n" + "=" * 65)
    print("WORKSPACE STATUS REPORT —", datetime.now().strftime("%Y-%m-%d %H:%M"))
    print(f"Studio root: {STUDIO_DIR}")
    print("=" * 65)
    for folder in FOLDERS:
        path = STUDIO_DIR / folder
        if path.is_dir():
            count = sum(1 for p in path.iterdir() if p.is_file())
            print(f"  {folder:<28} → {count:3} files")
        else:
            print(f"  {folder:<28} → (missing)")
    print("=" * 65)


if __name__ == "__main__":
    report_status()