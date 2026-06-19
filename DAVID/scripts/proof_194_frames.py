#!/usr/bin/env python3
"""Extract #194 proof frames from a seamless Latin master."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "DAVID" / "scripts"))
import render_longform as rl  # noqa: E402

PROD = ROOT / "DAVID/productions/david_latin_corpus_v1_longform_v1"
DEFAULT_MASTER = PROD / "output/david_david_latin_corpus_v1_seamless_v1.mp4"
XFADE = 0.2

# Cumulative timeline with xfade overlaps (8 host shots)
SHOT_ENDS = [8, 15.8, 23.6, 30.4, 38.2, 46.0, 54.8, 62.6]
JOIN_03_04 = SHOT_ENDS[2] - XFADE  # mid-xfade between shots 3 and 4


def extract_proof_set(video: Path, out_dir: Path, *, tag: str) -> dict:
    out_dir.mkdir(parents=True, exist_ok=True)
    frames = {
        f"{tag}_01_cold_open_mid": 4.0,
        f"{tag}_05_method_mid": SHOT_ENDS[3] - XFADE + 4.0,
        f"{tag}_07_demonstration_mid": SHOT_ENDS[5] - XFADE + 4.5,
        f"{tag}_join_03_04_xfade": JOIN_03_04,
    }
    manifest: dict = {"video": str(video), "tag": tag, "frames": {}}
    for name, at_s in frames.items():
        jpg = out_dir / f"{name}.jpg"
        rl.extract_frame_at(video, at_s, jpg)
        manifest["frames"][name] = {"at_s": at_s, "path": str(jpg)}
    (out_dir / f"{tag}_manifest.json").write_text(
        json.dumps(manifest, indent=2), encoding="utf-8"
    )
    return manifest


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--video", type=Path, default=DEFAULT_MASTER)
    p.add_argument("--out", type=Path, required=True)
    p.add_argument("--tag", default="frame")
    args = p.parse_args()
    if not args.video.is_file():
        raise SystemExit(f"Video not found: {args.video}")
    print(json.dumps(extract_proof_set(args.video, args.out, tag=args.tag), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())