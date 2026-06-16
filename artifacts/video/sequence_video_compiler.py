#!/usr/bin/env python3
"""
Multi-Shot Video Sequence Compiler v1.0 — Director
Turns a _MASTER_SEQUENCE.json into a single cohesive video prompt or timed list.
"""

import os
import json
from datetime import datetime

def compile_sequence(json_path: str, output_style: str = "single_prompt"):
    with open(json_path, encoding="utf-8") as f:
        data = json.load(f)

    shots = data.get("shots", [])
    model = data.get("model", "Model")
    scene = data.get("scene", "Scene")

    if output_style == "single_prompt":
        combined = f"Cohesive {len(shots)}-shot video sequence of {model} in {scene}. "
        combined += "Maintain exact same woman, lighting, and framing across all shots. "
        combined += "Shot order: " + " → ".join([s["intent"] for s in shots])
        print(combined)
    else:
        for i, shot in enumerate(shots, 1):
            print(f"Shot {i:02d} ({shot['intent']}): {shot['prompt'][:120]}...")

if __name__ == "__main__":
    # Demo using the latest Valentina sequence (adjust path if needed)
    base = "../Studio/Magazine_Assets/ShotLists"
    folders = [f for f in os.listdir(base) if "Valentina_Rossi" in f]
    if folders:
        latest = sorted(folders)[-1]
        json_path = os.path.join(base, latest, "_MASTER_SEQUENCE.json")
        print(f"Compiling: {json_path}\n")
        compile_sequence(json_path, output_style="single_prompt")
    else:
        print(f"No Valentina_Rossi folders found in {os.path.abspath(base)}")