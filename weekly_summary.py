#!/usr/bin/env python3
import subprocess
from pathlib import Path
from datetime import datetime, timedelta

HOME = Path.home()
REPOS = ["Stonebridge_Operations", "FLASH", "SPIT", "prompt_library"]

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
        path = HOME / repo
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