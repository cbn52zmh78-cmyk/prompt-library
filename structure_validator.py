#!/usr/bin/env python3
from pathlib import Path

HOME = Path.home()

REPOS = {
    "Stonebridge_Operations": ["Compliance_Research", "SOPs", "Client_Deliverables", "Scripts"],
    "FLASH": ["data", "scripts", "notebooks", "docs", "output"],
    "prompt_library": ["prompts", "versions", "agents"],
}

def validate():
    print("\n=== STRUCTURE VALIDATOR ===\n")
    for repo, expected_folders in REPOS.items():
        repo_path = HOME / repo
        print(f"Checking: {repo}")
        if not repo_path.exists():
            print("  ❌ Repo folder missing\n")
            continue
        for folder in expected_folders:
            path = repo_path / folder
            status = "✅" if path.exists() else "❌"
            print(f"  {status} {folder}")
        print()

if __name__ == "__main__":
    validate()