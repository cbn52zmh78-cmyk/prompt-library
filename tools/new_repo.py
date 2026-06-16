#!/usr/bin/env python3
import _bootstrap  # noqa: F401
import sys
import subprocess
from pathlib import Path

def create_repo(name, description=""):
    repo_path = Path.home() / name

    if repo_path.exists():
        print(f"Error: Folder '{name}' already exists.")
        return

    # Create folder
    repo_path.mkdir()

    # Initialize git
    subprocess.run(["git", "init"], cwd=repo_path)

    # Create basic README
    readme = f"# {name}\n\n{description}\n"
    (repo_path / "README.md").write_text(readme)

    # Create common folders
    for folder in ["docs", "scripts", "data", "output"]:
        (repo_path / folder).mkdir()
        (repo_path / folder / ".gitkeep").touch()

    # Create .gitignore
    gitignore = """__pycache__/
*.pyc
.env
.DS_Store
*.log
"""
    (repo_path / ".gitignore").write_text(gitignore)

    print(f"\n✅ Repository '{name}' created at: {repo_path}")
    print("   - Initialized with git")
    print("   - Added README.md")
    print("   - Created folders: docs, scripts, data, output")
    print("   - Added .gitignore")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: new_repo.py <repo-name> [\"optional description\"]")
        sys.exit(1)

    name = sys.argv[1]
    desc = sys.argv[2] if len(sys.argv) > 2 else ""
    create_repo(name, desc)