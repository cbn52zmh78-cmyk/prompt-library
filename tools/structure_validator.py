#!/usr/bin/env python3
import _bootstrap  # noqa: F401
from pathlib import Path

from workspace_paths import FLASH, STONEBRIDGE_OPS, STUDIO_DIR, STUDIO_FOLDERS, WORKSPACE

REPOS = {
    "Grok Projects": ["tools", "data", "docs", "prompts", "versions", "outputs", "notes", "artifacts"],
    "Stonebridge_Operations": ["Compliance_Research", "SOPs", "Client_Deliverables", "Scripts"],
    "FLASH": ["data", "scripts", "notebooks", "docs", "output"],
}


def validate():
    print("\n=== STRUCTURE VALIDATOR ===\n")
    for repo, expected_folders in REPOS.items():
        repo_path = {
            "Grok Projects": WORKSPACE,
            "Stonebridge_Operations": STONEBRIDGE_OPS,
            "FLASH": FLASH,
        }[repo]
        print(f"Checking: {repo}")
        if not repo_path.exists():
            print("  ❌ Repo folder missing\n")
            continue
        for folder in expected_folders:
            path = repo_path / folder
            status = "✅" if path.exists() else "❌"
            print(f"  {status} {folder}")
        print()

    print("Checking: Studio scaffold (artifacts toolchain)")
    if not STUDIO_DIR.exists():
        print("  ❌ Studio root missing\n")
    else:
        for folder in STUDIO_FOLDERS:
            path = STUDIO_DIR / folder
            status = "✅" if path.exists() else "❌"
            print(f"  {status} {folder}")
        print()


if __name__ == "__main__":
    validate()