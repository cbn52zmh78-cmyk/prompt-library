#!/usr/bin/env python3
"""
Canon & Bible Version Manager v1.0 — Director | New Tool
Versioning, locking, notes, and diffing for story bibles and canons.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from lib.bootstrap import ensure_paths
ensure_paths()
from lib.studio_paths import studio_path

import difflib
from datetime import datetime




class CanonBibleManager:
    def __init__(self, canon_dir=None):
        self.canon_dir = canon_dir or studio_path("Canons_Bibles")
        self.canon_dir.mkdir(parents=True, exist_ok=True)

    def _safe_name(self, name):
        return name.replace(" ", "_").replace("/", "_")

    def save_version(self, name: str, content: str, note: str = "", locked: bool = False):
        safe = self._safe_name(name)
        version_dir = self.canon_dir / safe
        version_dir.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        filepath = version_dir / f"{timestamp}.txt"
        header = f"# Version: {timestamp}\n# Locked: {locked}\n# Note: {note}\n\n"
        filepath.write_text(header + content, encoding="utf-8")
        print(f"✅ Canon/Bible version saved: {filepath}")
        if locked:
            print(" This version is marked as LOCKED.")

    def list_versions(self, name: str):
        version_dir = self.canon_dir / self._safe_name(name)
        if not version_dir.exists():
            return []
        return sorted(p.name for p in version_dir.glob("*.txt"))

    def diff_versions(self, name: str, v1: str, v2: str):
        version_dir = self.canon_dir / self._safe_name(name)
        with open(version_dir / v1, encoding="utf-8") as f:
            c1 = f.read().splitlines(keepends=True)
        with open(version_dir / v2, encoding="utf-8") as f:
            c2 = f.read().splitlines(keepends=True)
        diff = difflib.unified_diff(c1, c2, fromfile=v1, tofile=v2, lineterm="")
        print("".join(diff))


if __name__ == "__main__":
    mgr = CanonBibleManager()
    mgr.save_version(
        "SPIT_Story_Bible",
        "Core rules: unreliable narrator, family tragedy, Basque entropy themes. Locked visual language.",
        note="Initial locked canon v1",
        locked=True,
    )
    mgr.save_version(
        "SPIT_Story_Bible",
        "Core rules: unreliable narrator, family tragedy, Basque entropy themes. Added visual reference layer notes.",
        note="Added visual refs",
    )
    print("\nVersions of SPIT_Story_Bible:", mgr.list_versions("SPIT_Story_Bible"))