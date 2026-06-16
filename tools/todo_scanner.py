#!/usr/bin/env python3
import _bootstrap  # noqa: F401
import re
from pathlib import Path

KEYWORDS = ["TODO", "FIXME", "HACK", "XXX"]

def scan_repo(repo_path):
    path = Path(repo_path).expanduser()
    if not path.exists():
        print(f"Repo not found: {path}")
        return

    findings = []
    for py_file in path.rglob("*.py"):
        try:
            content = py_file.read_text()
            for line_num, line in enumerate(content.splitlines(), 1):
                for kw in KEYWORDS:
                    if kw in line:
                        findings.append(f"{py_file.name}:{line_num} - {line.strip()}")
        except:
            pass

    if findings:
        print(f"\nFindings in {path.name}:")
        for f in findings:
            print(f"  {f}")
    else:
        print(f"No TODO/FIXME comments found in {path.name}")

if __name__ == "__main__":
    from workspace_paths import FLASH, STONEBRIDGE_OPS, WORKSPACE

    for repo in [WORKSPACE, STONEBRIDGE_OPS, FLASH]:
        scan_repo(repo)