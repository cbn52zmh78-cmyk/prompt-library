#!/usr/bin/env python3
import subprocess
from pathlib import Path

HOME = Path.home()

REPOS = [
    "Stonebridge_Operations",
    "FLASH",
    "SPIT",
    "prompt_library",
]

def check_repo(name):
    path = HOME / name
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