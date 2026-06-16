#!/usr/bin/env python3
"""
Reference Library Indexer & Suggester v1.0 — Director | New Tool
Indexes reference PDFs/images and suggests relevant ones for prompts. Fully general.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from lib.bootstrap import ensure_paths
ensure_paths()
from lib.studio_paths import studio_path

import json
import os
from datetime import datetime



class ReferenceLibraryIndexer:
    def __init__(self, refs_dir=None, index_file=None):
        self.refs_dir = refs_dir or studio_path("References")
        self.index_file = index_file or studio_path("references_index.json")
        self.refs_dir.mkdir(parents=True, exist_ok=True)

    def rebuild_index(self):
        index = {}
        for root, _, files in os.walk(self.refs_dir):
            for f in files:
                if f.lower().endswith((".pdf", ".jpg", ".png", ".txt")):
                    rel = os.path.relpath(os.path.join(root, f), self.refs_dir)
                    index[rel] = {"tags": [], "added": datetime.now().isoformat()}
        with open(self.index_file, "w") as f:
            json.dump(index, f, indent=2)
        print(f"✅ Index rebuilt with {len(index)} references → {self.index_file}")

    def suggest(self, keywords: list):
        if not os.path.exists(self.index_file):
            print("No index found. Run rebuild_index first.")
            return []
        with open(self.index_file) as f:
            index = json.load(f)
        results = []
        for path, meta in index.items():
            if any(k.lower() in path.lower() for k in keywords):
                results.append(path)
        return results[:10]

if __name__ == "__main__":
    idx = ReferenceLibraryIndexer()
    idx.rebuild_index()
    print("\nExample suggestions for 'lighting':", idx.suggest(["lighting", "dramatic"]))