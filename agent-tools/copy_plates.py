"""Copy generated session images to roster/magazine plate paths."""
import json
import shutil
from pathlib import Path

SESSION = Path(r"C:\Users\NCG\.grok\sessions\C%3A%5CUsers%5CNCG%5CVideos%5CGrok%20Projects\019eddc3-bfa1-7771-b50c-970b8d141730\images")
MANIFEST = Path(r"C:\Users\NCG\Videos\Grok Projects\agent-tools\plate_manifest.json")

if not MANIFEST.exists():
    print("No manifest yet")
    raise SystemExit(0)

manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
for entry in manifest:
    src = SESSION / entry["session_file"]
    dst = Path(entry["out_path"])
    if not src.exists():
        print(f"MISSING SRC: {src} -> {entry['stage_name']}")
        continue
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)
    print(f"OK {entry['stage_name']}")