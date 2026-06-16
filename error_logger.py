#!/usr/bin/env python3
import json
import sys
from pathlib import Path
from datetime import datetime

LOG_FILE = Path.home() / "prompt_library" / "errors.json"

def load():
    if LOG_FILE.exists():
        return json.loads(LOG_FILE.read_text())
    return []

def save(data):
    LOG_FILE.write_text(json.dumps(data, indent=2))

def log_error(source, message):
    data = load()
    entry = {
        "date": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "source": source,
        "message": message
    }
    data.append(entry)
    save(data)
    print(f"Error logged from: {source}")

def list_errors():
    data = load()
    if not data:
        print("No errors logged.")
        return
    for e in data[-10:]:  # Show last 10
        print(f"\n[{e['date']}] {e['source']}")
        print(f"  {e['message']}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: error_logger.py log \"Source\" \"Message\"")
        print("       error_logger.py list")
        sys.exit(1)

    cmd = sys.argv[1]
    if cmd == "log" and len(sys.argv) >= 4:
        log_error(sys.argv[2], sys.argv[3])
    elif cmd == "list":
        list_errors()
    else:
        print("Unknown command")