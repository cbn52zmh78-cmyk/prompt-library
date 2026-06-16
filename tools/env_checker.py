#!/usr/bin/env python3
import _bootstrap  # noqa: F401
import sys
import platform
from pathlib import Path

def check():
    print("\n=== ENVIRONMENT CHECKER ===\n")
    print(f"Python Version: {sys.version.split()[0]}")
    print(f"Platform: {platform.system()} {platform.release()}")
    print(f"Home Directory: {Path.home()}")
    print(f"Current Working Directory: {Path.cwd()}\n")

    from workspace_paths import FLASH, STONEBRIDGE_OPS, WORKSPACE

    key_paths = [
        WORKSPACE,
        STONEBRIDGE_OPS,
        FLASH,
    ]

    print("Key Paths:")
    for path in key_paths:
        status = "✅ Exists" if path.exists() else "❌ Missing"
        print(f"  {status} {path}")

if __name__ == "__main__":
    check()