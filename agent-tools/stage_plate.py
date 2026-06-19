"""Copy generated session image to batch session and append manifest."""
import json
import shutil
import sys
from pathlib import Path

GEN_SESSION = Path(
    r"C:\Users\NCG\.grok\sessions\C%3A%5CUsers%5CNCG%5CVideos%5CGrok%20Projects"
    r"\019eddc5-5d2c-7da3-a327-ae379b3529b0\images"
)
BATCH_SESSION = Path(
    r"C:\Users\NCG\.grok\sessions\C%3A%5CUsers%5CNCG%5CVideos%5CGrok%20Projects"
    r"\019eddc3-bfa1-7771-b50c-970b8d141730\images"
)
MANIFEST = Path(r"C:\Users\NCG\Videos\Grok Projects\agent-tools\plate_manifest.json")


def main():
    gen_file, session_file, stage_name, out_path = sys.argv[1:5]
    src = GEN_SESSION / gen_file
    dst = BATCH_SESSION / session_file
    if not src.exists():
        raise SystemExit(f"MISSING SRC: {src}")
    shutil.copy2(src, dst)
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    manifest.append({
        "session_file": session_file,
        "stage_name": stage_name,
        "out_path": out_path,
    })
    MANIFEST.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(f"STAGED {session_file}: {stage_name}")


if __name__ == "__main__":
    main()