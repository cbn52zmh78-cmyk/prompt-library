#!/usr/bin/env python3
"""
Workspace Status Reporter v1.0 — Director | New Tool
Shows counts and health of all major folders in the project.
"""

import os
from datetime import datetime

FOLDERS = [
    "studio/Model_Profiles",
    "studio/Prompt_Templates",
    "studio/Prompt_Versions",
    "studio/OneTake_Prompts",
    "studio/Video_Prompts",
    "studio/Refined_Prompts",
    "studio/Grok_Video_Packs",
    "studio/Canons_Bibles",
    "studio/References",
    "studio/Asset_Metadata",
]

def report_status():
    print("\n" + "="*65)
    print("WORKSPACE STATUS REPORT —", datetime.now().strftime("%Y-%m-%d %H:%M"))
    print("="*65)
    for folder in FOLDERS:
        if os.path.exists(folder):
            count = len([f for f in os.listdir(folder) if os.path.isfile(os.path.join(folder, f))])
            print(f"  {folder:<35} → {count:3} files")
        else:
            print(f"  {folder:<35} → (missing)")
    print("="*65)

if __name__ == "__main__":
    report_status()