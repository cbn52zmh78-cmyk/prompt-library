#!/usr/bin/env python3
import _bootstrap  # noqa: F401
import json
import sys
from datetime import datetime
from workspace_paths import DECISIONS_FILE

LOG_FILE = DECISIONS_FILE

def load():
    if LOG_FILE.exists():
        return json.loads(LOG_FILE.read_text())
    return []

def save(data):
    LOG_FILE.write_text(json.dumps(data, indent=2))

def add_decision(title, details):
    data = load()
    entry = {
        "date": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "title": title,
        "details": details
    }
    data.append(entry)
    save(data)
    print(f"Decision logged: {title}")

def list_decisions():
    data = load()
    if not data:
        print("No decisions logged yet.")
        return
    for i, d in enumerate(data, 1):
        print(f"\n{i}. [{d['date']}] {d['title']}")
        print(f"   {d['details']}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage:")
        print("  decision_log.py add \"Title\" \"Details here...\"")
        print("  decision_log.py list")
        sys.exit(1)

    cmd = sys.argv[1]

    if cmd == "add" and len(sys.argv) >= 4:
        add_decision(sys.argv[2], sys.argv[3])
    elif cmd == "list":
        list_decisions()
    else:
        print("Unknown command")