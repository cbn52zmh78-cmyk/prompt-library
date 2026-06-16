#!/usr/bin/env python3
import _bootstrap  # noqa: F401
import json
import sys
from workspace_paths import PROJECT_INDEX_FILE

INDEX_FILE = PROJECT_INDEX_FILE

PROJECTS = {
    "Grok Projects": "Central workspace for all AI Systems, multi-agent tools, and prompts.",
    "Stonebridge_Operations": "Main business operations, SOPs, client deliverables, and compliance work.",
    "FLASH": "Baseball sabermetrics work for dad's company (player projections, data processing).",
    "SPIT": "Main cinematic project (long-form narrative filmmaking and 3D renders).",
}

def update_index():
    INDEX_FILE.write_text(json.dumps(PROJECTS, indent=2))
    print("Project index updated.")

def show_index():
    if INDEX_FILE.exists():
        data = json.loads(INDEX_FILE.read_text())
        print("\n=== PROJECT INDEX ===\n")
        for name, desc in data.items():
            print(f" {name}")
            print(f"   {desc}\n")
    else:
        print("No index found. Run with 'update' first.")

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "update":
        update_index()
    else:
        show_index()