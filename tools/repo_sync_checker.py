#!/usr/bin/env python3
import _bootstrap  # noqa: F401
import subprocess
from pathlib import Path

from workspace_paths import REPO_PATHS

REPOS = list(REPO_PATHS.keys())

def check_repo(name):
    path = REPO_PATHS[name]
    if not path.exists():
        return f"❌ {name} — Folder missing"

    git_dir = path / ".git"
    if not git_dir.exists():
        return f"⚠️  {name} — Not a git repo"

    # Check for uncommitted changes
    result = subprocess.run(
        ["git", "status", "--porcelain"],
        cwd=path,
        capture_output=True,
        text=True
    )

    if result.stdout.strip():
        return f"⚠️  {name} — Has uncommitted changes"
    else:
        return f"✅ {name} — Clean"

def main():
    print("\n=== REPO SYNC CHECKER ===\n")
    for repo in REPOS:
        print(check_repo(repo))
    print("\nCheck complete.")

if __name__ == "__main__":
    main()