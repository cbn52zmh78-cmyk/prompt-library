#!/usr/bin/env python3
"""Magazine Shot List Templater — scaffold JSON shot lists under Studio/ShotLists."""

import json
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from lib.bootstrap import ensure_paths

ensure_paths()
from lib.studio_paths import pipeline_path


def create_template(title: str, shot_count: int = 6) -> Path:
    out_dir = pipeline_path("ShotLists")
    shots = [
        {
            "shot": i,
            "framing": "medium editorial",
            "movement": "slow push-in",
            "lighting": "dramatic side key",
            "notes": "",
        }
        for i in range(1, shot_count + 1)
    ]
    payload = {
        "title": title,
        "created": datetime.now().isoformat(),
        "shots": shots,
    }
    slug = title.replace(" ", "_")
    out_file = out_dir / f"shotlist_{slug}_{datetime.now().strftime('%Y%m%d_%H%M')}.json"
    out_file.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return out_file


if __name__ == "__main__":
    name = input("Shot list title: ").strip() or "Editorial_Session"
    path = create_template(name)
    print(f"✅ Shot list template written: {path}")