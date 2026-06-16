#!/usr/bin/env python3
import sys
import platform
from pathlib import Path

def check():
    print("\n=== ENVIRONMENT CHECKER ===\n")
    print(f"Python Version: {sys.version.split()[0]}")
    print(f"Platform: {platform.system()} {platform.release()}")
    print(f"Home Directory: {Path.home()}")
    print(f"Current Working Directory: {Path.cwd()}\n")

    key_paths = [
        Path.home() / "Stonebridge_Operations",
        Path.home() / "prompt_library",
        Path.home() / "FLASH",
    ]

    print("Key Paths:")
    for path in key_paths:
        status = "✅ Exists" if path.exists() else "❌ Missing"
        print(f"  {status} {path}")

if __name__ == "__main__":
    check()