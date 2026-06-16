#!/usr/bin/env python3
import _bootstrap  # noqa: F401
import subprocess
from pathlib import Path
from datetime import datetime, timedelta

from workspace_paths import REPO_PATHS

REPOS = list(REPO_PATHS.keys())

def get_recent_commits(repo_path, days=7):
    since = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
    result = subprocess.run(
        ["git", "log", f"--since={since}", "--oneline"],
        cwd=repo_path,
        capture_output=True,
        text=True
    )
    return result.stdout.strip().split("\n") if result.stdout.strip() else []

def main():
    print(f"\n=== WEEKLY SUMMARY ({datetime.now().strftime('%Y-%m-%d')}) ===\n")
    for repo in REPOS:
        path = REPO_PATHS[repo]
        if not path.exists():
            continue
        commits = get_recent_commits(path)
        print(f" {repo}")
        if commits and commits[0]:
            for c in commits[:5]:
                print(f"   - {c}")
        else:
            print("   No recent commits")
        print()

if __name__ == "__main__":
    main()