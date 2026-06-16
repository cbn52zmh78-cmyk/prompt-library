#!/usr/bin/env python3
import _bootstrap  # noqa: F401
import json
import sys

from workspace_paths import PROJECT_INDEX_FILE

INDEX_FILE = PROJECT_INDEX_FILE

PROJECTS = {
    "Grok Projects": "Central workspace — Nexus ops tools, artifacts pipeline, prompts, data.",
    "Studio": "Cinematic/video production — prompts, references, model profiles, renders.",
    "AI": "Multi-agent orchestration and federation routing.",
    "Science": "Scientific visualization principles and validation.",
    "Nexus": "Ecosystem registry, workflows, and governance.",
    "History": "Historical documentary research, timelines, and figure data.",
    "Stonebridge": "Security consulting — compliance research, SOPs, client deliverables.",
    "Stonebridge_Operations": "Business ops junction — SOPs, compliance, client work.",
    "FLASH": "Baseball sabermetrics — player projections and data processing.",
    "GFE": "Girlfriend Experience video assets and production scripts.",
    "MAGAZINE": "Supermodel editorial assets and production scripts.",
    "artifacts": "Studio production toolchain — prompt gen, video compile, catalog, compliance.",
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