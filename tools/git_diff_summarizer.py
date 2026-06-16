#!/usr/bin/env python3
import _bootstrap  # noqa: F401
import subprocess
import sys
from pathlib import Path

def summarize(repo_path, commits=3):
    path = Path(repo_path).expanduser()
    if not path.exists():
        print(f"Repo not found: {path}")
        return

    result = subprocess.run(
        ["git", "log", f"-{commits}", "--pretty=format:%h - %s", "--shortstat"],
        cwd=path,
        capture_output=True,
        text=True
    )
    print(result.stdout)

if __name__ == "__main__":
    from workspace_paths import WORKSPACE

    repo = sys.argv[1] if len(sys.argv) > 1 else str(WORKSPACE)
    summarize(repo)