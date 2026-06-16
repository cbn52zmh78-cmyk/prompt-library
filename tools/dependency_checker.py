#!/usr/bin/env python3
import _bootstrap  # noqa: F401
import importlib
import sys

REQUIRED = [
    "pathlib",
    "json",
    "datetime",
    "subprocess"
]

def check():
    print("\n=== DEPENDENCY CHECKER ===\n")
    missing = []
    for package in REQUIRED:
        try:
            importlib.import_module(package)
            print(f"✅ {package}")
        except ImportError:
            print(f"❌ {package} - MISSING")
            missing.append(package)

    if missing:
        print(f"\nMissing packages: {', '.join(missing)}")
        print("Install them using: pip install <package_name>")
    else:
        print("\nAll core dependencies are installed.")

if __name__ == "__main__":
    check()