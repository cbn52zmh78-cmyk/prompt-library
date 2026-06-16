#!/usr/bin/env python3
import _bootstrap  # noqa: F401
from datetime import datetime
from pathlib import Path

from workspace_paths import DAVID_DIR, NESTED_REPOS, PROMPT_SOURCES, PROMPTS_DIR, STONEBRIDGE_OPS, WORKSPACE, count_prompt_files

FOLDERS_TO_CHECK = [
    "~/Videos/Grok Projects",
    "~/Videos/Grok Projects/DAVID",
    "~/Videos/Grok Projects/Studio",
    "~/Videos/Grok Projects/artifacts",
    "~/Videos/Grok Projects/GFE",
    "~/Videos/Grok Projects/Studio/MAGAZINE",
    "~/Videos/Grok Projects/Nexus",
    "~/Videos/Grok Projects/Science",
    "~/Videos/Grok Projects/History",
    "~/Videos/Grok Projects/AI",
    "~/Videos/Grok Projects/Stonebridge",
    "~/Stonebridge_Operations",
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
    for label, root in PROMPT_SOURCES.items():
        n = count_prompt_files(root)
        print(f"  {label}: {n} prompts ({root})")

    if not PROMPTS_DIR.exists():
        print(f"  central prompts folder not found at {PROMPTS_DIR}")

    print("\n=== Nested Repos ===")
    for name, path in NESTED_REPOS.items():
        git_ok = (path / ".git").exists()
        status = "✅" if path.exists() and git_ok else ("⚠️ " if path.exists() else "❌")
        print(f"  {status} {name}: {path}")

    print("\nHealth check finished.")


if __name__ == "__main__":
    main()