#!/usr/bin/env python3
"""
Workspace Initializer v1.1 — Director | New Tool
Sets up the complete recommended folder structure under Grok Projects/Studio.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from lib.bootstrap import ensure_paths
ensure_paths()
from lib.studio_paths import STUDIO_DIR

FOLDERS = (
    "Model_Profiles",
    "Prompt_Versions",
    "Prompt_Templates",
    "ShotLists",
    "Video_Prompts",
    "OneTake_Prompts",
    "Fashion_Prompts",
    "Grok_Video_Packs",
    "Negative_Prompts",
    "Asset_Metadata",
    "References",
    "Compliance_Reports",
    "Batch_Outputs",
    "Canons_Bibles",
    "Refined_Prompts",
    "Physics_Lighting_Blocks",
    "Tool_Logs",
)


def initialize_workspace():
    created = []
    STUDIO_DIR.mkdir(parents=True, exist_ok=True)
    for folder in FOLDERS:
        path = STUDIO_DIR / folder
        if not path.exists():
            path.mkdir(parents=True, exist_ok=True)
            created.append(path)
    if created:
        print("✅ Workspace initialized. Created folders:")
        for path in created:
            print(f"   - {path}")
    else:
        print(f"✅ Workspace already fully initialized under {STUDIO_DIR}")


if __name__ == "__main__":
    initialize_workspace()