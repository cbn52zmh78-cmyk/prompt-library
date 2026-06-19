#!/usr/bin/env python3
"""#218 — probe RAW chain magenta PRE-clamp for forced shots."""
from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import render_longform as rl  # noqa: E402
from color_cast_qa import probe_video_midframe  # noqa: E402

MAGENTA_MAX = 0.42
BURDEN_MAX = 0.20
SHOTS_DIR = ROOT / "productions" / "david_latin_corpus_v1_longform_v1" / "shots"
SHOT_IDS = ("01_cold_open", "05_method")


def main() -> int:
    rows = []
    for sid in SHOT_IDS:
        raw = SHOTS_DIR / f"chain_{sid}.mp4"
        proc = SHOTS_DIR / f"chain_{sid}_processed.mp4"
        raw_mag = rl.probe_magenta_score(raw)
        proc_mag = rl.probe_magenta_score(proc) if proc.is_file() else None
        cc = probe_video_midframe(raw)
        burden = (raw_mag - proc_mag) if proc_mag is not None else None
        row = {
            "shot_id": sid,
            "raw_magenta_pre_clamp": round(raw_mag, 4),
            "processed_magenta": round(proc_mag, 4) if proc_mag is not None else None,
            "clamp_burden": round(burden, 4) if burden is not None else None,
            "host_blue_mean": round(cc["host_blue_mean"], 1),
            "host_br_ratio": round(cc["host_br_ratio"], 3),
            "blue_starvation_fraction": round(cc["blue_starvation_fraction"], 3),
            "raw_magenta_pass": raw_mag < MAGENTA_MAX,
            "clamp_burden_pass": burden is not None and burden < BURDEN_MAX,
        }
        rows.append(row)
        burden_s = f"{burden:.4f}" if burden is not None else "n/a"
        print(f"{sid}: RAW magenta={raw_mag:.4f} burden={burden_s} Bμ={cc['host_blue_mean']:.1f}")

    out = {
        "issue": 218,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "resolution": "480p",
        "magenta_max": MAGENTA_MAX,
        "clamp_burden_max": BURDEN_MAX,
        "proof_218": "HELD",
        "shots": rows,
    }
    report_path = ROOT / "productions" / "david_latin_corpus_v1_longform_v1" / "proof_218" / "raw_magenta_report.json"
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(out, indent=2), encoding="utf-8")
    print(f"report → {report_path}")
    all_pass = all(r["raw_magenta_pass"] and r["clamp_burden_pass"] for r in rows)
    return 0 if all_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())