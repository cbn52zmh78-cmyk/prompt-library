"""Append one entry to plate_manifest.json."""
import json
import sys
from pathlib import Path

MANIFEST = Path(r"C:\Users\NCG\Videos\Grok Projects\agent-tools\plate_manifest.json")

def main():
    session_file, stage_name, out_path = sys.argv[1:4]
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    manifest.append({
        "session_file": session_file,
        "stage_name": stage_name,
        "out_path": out_path,
    })
    MANIFEST.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(f"Appended {session_file}: {stage_name} ({len(manifest)} total)")

if __name__ == "__main__":
    main()