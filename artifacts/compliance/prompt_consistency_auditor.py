#!/usr/bin/env python3
"""
Prompt Consistency Auditor v1.0 — Director
Scans a folder of prompts and flags drift in key elements.
"""

import os
import re
from collections import Counter

def audit_folder(folder_path: str):
    files = [f for f in os.listdir(folder_path) if f.endswith(".txt")]
    model_names = []
    lighting = []
    framing = []

    for f in files:
        with open(os.path.join(folder_path, f), encoding="utf-8") as file:
            content = file.read().lower()
            if "valentina" in content: model_names.append("Valentina Rossi")
            if "side lighting" in content or "dramatic lighting" in content: lighting.append("dramatic side")
            if "16:9" in content: framing.append("16:9")

    print("=== Consistency Report ===")
    print(f"Model consistency: {dict(Counter(model_names))}")
    print(f"Lighting consistency: {dict(Counter(lighting))}")
    print(f"Framing consistency: {dict(Counter(framing))}")
    print(f"Total prompts scanned: {len(files)}")

if __name__ == "__main__":
    # Demo on the latest Valentina sequence
    base = "../Studio/Magazine_Assets/ShotLists"
    folders = [f for f in os.listdir(base) if "Valentina_Rossi" in f]
    if folders:
        latest = sorted(folders)[-1]
        audit_folder(os.path.join(base, latest))
    else:
        print(f"No Valentina_Rossi folders found in {os.path.abspath(base)}")