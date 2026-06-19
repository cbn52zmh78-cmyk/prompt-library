"""Add queue items 9-14 to plate_manifest.json."""
import json
from pathlib import Path

QUEUE = Path(r"C:\Users\NCG\Videos\Grok Projects\agent-tools\batch_b_queue.json")
MANIFEST = Path(r"C:\Users\NCG\Videos\Grok Projects\agent-tools\plate_manifest.json")

queue = json.loads(QUEUE.read_text(encoding="utf-8"))
manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))

existing = {e["session_file"] for e in manifest}
for i, item in enumerate(queue[8:14], start=9):
    sf = f"{i}.jpg"
    if sf in existing:
        continue
    manifest.append({
        "session_file": sf,
        "stage_name": item["stage_name"],
        "out_path": item["out_path"],
    })
    print(f"Added {sf}: {item['stage_name']}")

MANIFEST.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
print(f"Manifest now has {len(manifest)} entries")