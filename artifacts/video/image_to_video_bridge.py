#!/usr/bin/env python3
"""Image-to-Video Continuity Bridge — map still references to motion prompts."""

import json
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from lib.bootstrap import ensure_paths

ensure_paths()
from lib.studio_paths import studio_path


def build_bridge(image_path: str, motion: str, duration_s: int = 6) -> Path:
    out_dir = studio_path("Video_Prompts")
    stem = Path(image_path).stem or "frame"
    payload = {
        "source_image": image_path,
        "motion_directive": motion,
        "duration_seconds": duration_s,
        "continuity": {
            "preserve_subject": True,
            "preserve_lighting": True,
            "preserve_framing": True,
        },
        "generated": datetime.now().isoformat(),
    }
    out_file = out_dir / f"bridge_{stem}_{datetime.now().strftime('%Y%m%d_%H%M')}.json"
    out_file.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return out_file


if __name__ == "__main__":
    image = input("Source image path: ").strip()
    motion = input("Motion directive: ").strip() or "slow cinematic push-in, natural fabric movement"
    if not image:
        print("❌ Image path required.")
        sys.exit(1)
    out = build_bridge(image, motion)
    print(f"✅ Bridge prompt pack written: {out}")