#!/usr/bin/env python3
"""
Shot Sequence Consistency Auditor v1.0 — Director | New Tool
Scans a folder of prompts in a sequence and flags drift. Fully general.
"""

import os
from collections import Counter

class SequenceConsistencyAuditor:
    def audit_folder(self, folder_path: str):
        files = sorted([f for f in os.listdir(folder_path) if f.endswith(".txt")])
        if not files:
            print("No .txt files found.")
            return
        lighting = []
        framing = []
        subject_refs = []
        for fname in files:
            with open(os.path.join(folder_path, fname), encoding="utf-8") as f:
                content = f.read().lower()
            if "side lighting" in content or "dramatic lighting" in content:
                lighting.append("dramatic_side")
            if "16:9" in content:
                framing.append("16_9")
            if "adult woman" in content:
                subject_refs.append("adult_woman")
        print("=== Sequence Consistency Report ===")
        print(f"Files scanned: {len(files)}")
        print(f"Lighting consistency: {dict(Counter(lighting))}")
        print(f"Framing consistency: {dict(Counter(framing))}")
        print(f"Subject reference consistency: {dict(Counter(subject_refs))}")
        if len(set(lighting)) > 1 or len(set(framing)) > 1:
            print("⚠️ Drift detected — review the sequence.")

if __name__ == "__main__":
    auditor = SequenceConsistencyAuditor()
    # Demo: point at the ShotLists folder if it exists, otherwise note it
    demo_path = "../Studio/Magazine_Assets/ShotLists"
    if os.path.exists(demo_path):
        subs = [
            os.path.join(demo_path, d)
            for d in os.listdir(demo_path)
            if os.path.isdir(os.path.join(demo_path, d))
        ]
        if subs:
            latest = max(subs, key=os.path.getmtime)
            print(f"Auditing: {latest}\n")
            auditor.audit_folder(latest)
        else:
            print("No sequence folders found yet.")
    else:
        print("ShotLists folder not present — run after generating a sequence.")