#!/usr/bin/env python3
import _bootstrap  # noqa: F401
import os
from pathlib import Path
from datetime import datetime

from workspace_paths import PROMPTS_DIR, STONEBRIDGE_OPS, WORKSPACE

BASE = Path.home()

# Add the folders/repos you want to check here
FOLDERS_TO_CHECK = [
    "~/Videos/Grok Projects",
    "~/Videos/Grok Projects/Studio",
    "~/Videos/Grok Projects/GFE",
    "~/Videos/Grok Projects/MAGAZINE",
    "~/Videos/Grok Projects/Nexus",
    "~/Videos/Grok Projects/Science",
    "~/Videos/Grok Projects/Stonebridge",
    "~/Stonebridge_Operations",  # junction -> Stonebridge/Operations
]

def check_folder(path_str):
    path = Path(path_str).expanduser()
    status = "✅ OK" if path.exists() else "❌ MISSING"
    print(f"{status}  {path}")

def main():
    print(f"Agent Health Check — {datetime.now().strftime('%Y-%m-%d %H:%M')}\n")
    print("=== Folder Check ===")
    for folder in FOLDERS_TO_CHECK:
        check_folder(folder)

    print("\n=== Prompt Library Check ===")
    if PROMPTS_DIR.exists():
        for cat in ["system", "orchestration", "studio", "compliance"]:
            cat_path = PROMPTS_DIR / cat
            count = len(list(cat_path.glob("*.md"))) if cat_path.exists() else 0
            print(f"  {cat}: {count} prompts")
    else:
        print(f"  prompts folder not found at {PROMPTS_DIR}")

    print("\nHealth check finished.")

if __name__ == "__main__":
    main()