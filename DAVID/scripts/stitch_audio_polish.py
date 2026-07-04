#!/usr/bin/env python3
"""Post-stitch audio polish — light EQ/crossfade between xfade joins (Pass 6 deferred layer).

Usage:
  python stitch_audio_polish.py path/to/stitched.mp4
  python stitch_audio_polish.py path/to/stitched.mp4 --out path/to/polished.mp4

When rhythm gaps appear after manual review, run this before publish.
Full BPM analysis and tempo ramps are not implemented yet — applies loudnorm + gentle
audio re-encode for consistent perceived level across stitched segments.
"""
from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from render_longform import _ffmpeg_exe, probe_duration  # noqa: E402


def polish_audio(in_mp4: Path, out_mp4: Path) -> Path:
    ff = _ffmpeg_exe()
    dur = probe_duration(in_mp4)
    filt = "loudnorm=I=-16:TP=-1.5:LRA=11"
    subprocess.run(
        [
            ff, "-y", "-i", str(in_mp4),
            "-filter:a", filt,
            "-c:v", "copy", "-c:a", "aac", "-b:a", "192k",
            "-t", f"{dur:.3f}",
            str(out_mp4),
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    return out_mp4


def main() -> int:
    parser = argparse.ArgumentParser(description="Post-stitch audio level polish")
    parser.add_argument("input", type=Path)
    parser.add_argument("--out", type=Path, default=None)
    args = parser.parse_args()
    src = args.input.resolve()
    if not src.is_file():
        raise SystemExit(f"not found: {src}")
    dst = args.out or src.with_name(f"{src.stem}_audio_polish{src.suffix}")
    print(f"[polish] {src.name} -> {dst.name}", flush=True)
    polish_audio(src, dst)
    print(f"[polish] done ({probe_duration(dst):.2f}s)", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())