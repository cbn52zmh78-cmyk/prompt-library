#!/usr/bin/env python3
import sys

TEMPLATES = {
    "feat": "feat: ",
    "fix": "fix: ",
    "docs": "docs: ",
    "refactor": "refactor: ",
    "chore": "chore: ",
    "test": "test: "
}

def show_templates():
    print("\nCommit Message Templates:\n")
    for key, prefix in TEMPLATES.items():
        print(f"  {key}: {prefix}<message>")
    print("\nExample: python git_commit_helper.py feat \"add decision log tool\"")

if __name__ == "__main__":
    if len(sys.argv) < 3:
        show_templates()
    else:
        prefix = TEMPLATES.get(sys.argv[1], "")
        message = " ".join(sys.argv[2:])
        print(f"\nSuggested commit message:\n{prefix}{message}\n")