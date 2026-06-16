#!/usr/bin/env python3
import shutil
import sys
from pathlib import Path
from datetime import datetime

BACKUP_DIR = Path.home() / "Backups"
BACKUP_DIR.mkdir(exist_ok=True)

IMPORTANT_FOLDERS = [
    Path.home() / "Stonebridge_Operations",
    Path.home() / "prompt_library",
    Path.home() / "FLASH",
]

def backup():
    timestamp = datetime.now().strftime("%Y%m%d_%H%M")
    backup_path = BACKUP_DIR / f"backup_{timestamp}"
    backup_path.mkdir()

    print(f"\nCreating backup at: {backup_path}\n")

    for folder in IMPORTANT_FOLDERS:
        if folder.exists():
            dest = backup_path / folder.name
            shutil.copytree(folder, dest)
            print(f"✅ Backed up: {folder.name}")
        else:
            print(f"⚠️  Skipped (not found): {folder.name}")

    print(f"\nBackup complete: {backup_path}")

if __name__ == "__main__":
    backup()