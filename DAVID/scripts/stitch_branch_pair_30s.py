#!/usr/bin/env python3
"""Stitch branch A (15s origin) + branch B (tight close 02) via xfade."""
from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from render_longform import concat_xfade_chain, probe_duration  # noqa: E402

PROOF = ROOT / "productions/matilda_kitchen_stonebridge_10s_longform_v1/proof"
BRANCH_A = PROOF / "ceiling_probe/kitchen_composite_baked@1_15s_ceiling_probe.mp4"
BRANCH_B = PROOF / "branch_probe/branch_02_tight_close_static_15s_from_origin_14.9s.mp4"
OUT_DIR = PROOF / "branch_probe"
OUT = OUT_DIR / "matilda_kitchen_branch_A_B_stitched_30s_v1.mp4"
XFADE_S = 0.35


def main() -> int:
    for p in (BRANCH_A, BRANCH_B):
        if not p.is_file():
            raise SystemExit(f"missing segment: {p}")

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    work = OUT_DIR / "stitch_work"
    work.mkdir(parents=True, exist_ok=True)

    print(f"[stitch] A={BRANCH_A.name} ({probe_duration(BRANCH_A):.2f}s)", flush=True)
    print(f"[stitch] B={BRANCH_B.name} ({probe_duration(BRANCH_B):.2f}s)", flush=True)
    print(f"[stitch] xfade={XFADE_S}s", flush=True)

    concat_xfade_chain(
        [BRANCH_A, BRANCH_B],
        OUT,
        xfade_s=XFADE_S,
        match_color=False,
        magenta_clamp=False,
        work_dir=work,
    )
    dur = probe_duration(OUT)
    report = {
        "at": datetime.now(timezone.utc).isoformat(),
        "branch_a": str(BRANCH_A),
        "branch_b": str(BRANCH_B),
        "xfade_s": XFADE_S,
        "output": str(OUT),
        "duration_s": round(dur, 3),
    }
    (OUT_DIR / "matilda_kitchen_branch_A_B_stitched_30s_v1.json").write_text(
        json.dumps(report, indent=2), encoding="utf-8",
    )
    print(f"[stitch] → {OUT} ({dur:.3f}s)", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())