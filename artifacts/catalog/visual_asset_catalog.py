#!/usr/bin/env python3
"""Visual Asset Catalog — SQLite index for Studio visual assets."""

import sqlite3
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from lib.bootstrap import ensure_paths

ensure_paths()
from lib.studio_paths import reference_path


def db_path() -> Path:
    return reference_path("Asset_Metadata", "visual_assets.db")


def init_db() -> Path:
    path = db_path()
    conn = sqlite3.connect(path)
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS assets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            path TEXT NOT NULL,
            category TEXT,
            tags TEXT,
            created TEXT
        )
        """
    )
    conn.commit()
    conn.close()
    return path


def register_asset(file_path: str, category: str = "", tags: str = "") -> None:
    path = init_db()
    conn = sqlite3.connect(path)
    conn.execute(
        "INSERT INTO assets (path, category, tags, created) VALUES (?, ?, ?, ?)",
        (file_path, category, tags, datetime.now().isoformat()),
    )
    conn.commit()
    conn.close()


if __name__ == "__main__":
    catalog = init_db()
    print(f"✅ Visual asset catalog ready: {catalog}")
    sample = input("Register asset path (blank to skip): ").strip()
    if sample:
        register_asset(sample, category="magazine", tags="editorial")
        print(f"✅ Registered: {sample}")