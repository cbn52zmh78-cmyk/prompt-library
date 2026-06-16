#!/usr/bin/env python3
import json
import sys
from pathlib import Path
from datetime import datetime

LOG_FILE = Path.home() / "prompt_library" / "changelog.json"

def load():
    if LOG_FILE.exists():
        return json.loads(LOG_FILE.read_text())
    return []

def save(data):
    LOG_FILE.write_text(json.dumps(data, indent=2))

def add_entry(title, details):
    data = load()
    entry = {
        "date": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "title": title,
        "details": details
    }
    data.append(entry)
    save(data)
    print(f"Entry added: {title}")

def list_entries():
    data = load()
    if not data:
        print("No changelog entries yet.")
        return
    for i, e in enumerate(data, 1):
        print(f"\n{i}. [{e['date']}] {e['title']}")
        print(f"   {e['details']}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: changelog_manager.py add \"Title\" \"Details\"")
        print("       changelog_manager.py list")
        sys.exit(1)

    cmd = sys.argv[1]
    if cmd == "add" and len(sys.argv) >= 4:
        add_entry(sys.argv[2], sys.argv[3])
    elif cmd == "list":
        list_entries()
    else:
        print("Unknown command")