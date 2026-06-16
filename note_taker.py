#!/usr/bin/env python3
import sys
from pathlib import Path
from datetime import datetime

NOTES_DIR = Path.home() / "prompt_library" / "notes"
NOTES_DIR.mkdir(exist_ok=True)

def add_note(topic, content):
    filename = NOTES_DIR / f"{topic.replace(' ', '_')}.md"
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
    entry = f"\n### {timestamp}\n{content}\n"
    
    if filename.exists():
        filename.write_text(filename.read_text(encoding="utf-8") + entry, encoding="utf-8")
    else:
        filename.write_text(f"# {topic}\n{entry}", encoding="utf-8")
    
    print(f"Note added to: {filename}")

def list_notes():
    notes = list(NOTES_DIR.glob("*.md"))
    if not notes:
        print("No notes yet.")
        return
    for note in notes:
        print(note.stem)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: note_taker.py add \"Topic\" \"Note content here\"")
        print("       note_taker.py list")
        sys.exit(1)

    cmd = sys.argv[1]
    if cmd == "add" and len(sys.argv) >= 4:
        add_note(sys.argv[2], sys.argv[3])
    elif cmd == "list":
        list_notes()
    else:
        print("Unknown command")