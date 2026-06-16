#!/usr/bin/env python3
import _bootstrap  # noqa: F401
import shutil
import subprocess
from pathlib import Path

from workspace_paths import FLASH, STONEBRIDGE_OPS, WORKSPACE

FOLDERS = [
    WORKSPACE,
    STONEBRIDGE_OPS,
    FLASH,
    Path.home() / "SPIT",
]


def _dir_size(path: Path) -> int:
    total = 0
    for entry in path.rglob("*"):
        if entry.is_file():
            try:
                total += entry.stat().st_size
            except OSError:
                pass
    return total


def _human_size(num_bytes: int) -> str:
    size = float(num_bytes)
    for unit in ("B", "K", "M", "G", "T"):
        if size < 1024.0 or unit == "T":
            if unit == "B":
                return f"{int(size)}{unit}"
            return f"{size:.1f}{unit}"
        size /= 1024.0
    return f"{size:.1f}T"


def get_size(path):
    if not path.exists():
        return "N/A"
    if shutil.which("du"):
        result = subprocess.run(
            ["du", "-sh", str(path)],
            capture_output=True,
            text=True,
        )
        if result.returncode == 0 and result.stdout.strip():
            return result.stdout.strip().split()[0]
    return _human_size(_dir_size(path))


def main():
    print("\n=== FOLDER SIZE REPORT ===\n")
    for folder in FOLDERS:
        size = get_size(folder)
        print(f"{size:>8}  {folder.name}")


if __name__ == "__main__":
    main()