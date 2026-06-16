#!/usr/bin/env python3
"""Git cleanliness check for Grok Projects and nested ecosystem repos."""

from __future__ import annotations

import _bootstrap  # noqa: F401
import subprocess
from pathlib import Path

from workspace_paths import NESTED_REPOS, REPO_PATHS, WORKSPACE


def _git_porcelain(path: Path) -> str:
    result = subprocess.run(
        ["git", "status", "--porcelain"],
        cwd=path,
        capture_output=True,
        text=True,
    )
    return result.stdout.strip() if result.returncode == 0 else ""


def check_repo(name: str, path: Path) -> str:
    if not path.exists():
        return f"❌ {name} — Folder missing"

    git_dir = path / ".git"
    if not git_dir.exists():
        return f"⚠️  {name} — Not a git repo"

    dirty = _git_porcelain(path)
    if dirty:
        lines = dirty.splitlines()
        return f"⚠️  {name} — {len(lines)} uncommitted change(s)"
    return f"✅ {name} — Clean"


def main() -> None:
    print("\n=== REPO SYNC CHECKER ===\n")

    print("Workspace repos:")
    for repo, path in REPO_PATHS.items():
        print(f"  {check_repo(repo, path)}")

    print("\nNested ecosystem repos:")
    nested_dirty = 0
    for repo, path in NESTED_REPOS.items():
        line = check_repo(repo, path)
        print(f"  {line}")
        if "uncommitted" in line:
            nested_dirty += 1

    root_dirty = _git_porcelain(WORKSPACE)
    print(f"\nRoot summary: {'dirty' if root_dirty else 'clean'}")
    if nested_dirty:
        print(f"Nested repos needing attention: {nested_dirty}/{len(NESTED_REPOS)}")
        print("Commit inside each submodule repo separately (e.g. git -C Studio status).")

    print("\nCheck complete.")


if __name__ == "__main__":
    main()