#!/usr/bin/env python3
"""Single-shot duration ceiling probe — baked kitchen composite, no extend/chain."""
from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import xai_sdk  # noqa: E402
from render_longform import (  # noqa: E402
    _api_pace,
    _download,
    _load_grok_token,
    _resolve_composite_first_frame,
    generate_baked_composite_video,
    normalize_script,
    probe_duration,
    resolve_production_dir,
    resolve_refs,
)

SCRIPT = ROOT / "scripts/longform_scripts/matilda_kitchen_stonebridge_10s_v1_script.json"
REQUESTED_S = int(sys.argv[1]) if len(sys.argv) > 1 else 30
MODEL = "grok-imagine-video-1.5"


def main() -> int:
    script = normalize_script(json.loads(SCRIPT.read_text(encoding="utf-8")), SCRIPT)
    script.setdefault("config", {})["composite_first_frame"] = (
        "DAVID/productions/matilda_kitchen_stonebridge_10s_longform_v1/proof/"
        "composite_first_frame_probe.jpg"
    )
    shot = dict(script["shots"][0])
    shot["duration"] = REQUESTED_S
    bb = dict(shot.get("barebones") or {})
    bb["output"] = {"sequence_length": f"{REQUESTED_S}s"}
    shot["barebones"] = bb

    prod_dir = resolve_production_dir(script)
    proof_dir = prod_dir / "proof" / "ceiling_probe"
    proof_dir.mkdir(parents=True, exist_ok=True)

    client = xai_sdk.Client(api_key=_load_grok_token())
    refs = resolve_refs(script, client=client)
    composite = _resolve_composite_first_frame(script, prod_dir)
    if not composite:
        raise SystemExit("composite_first_frame missing")

    print(f"[ceiling] model={MODEL} requested={REQUESTED_S}s seed={composite.name}", flush=True)
    _api_pace()
    resp, req = generate_baked_composite_video(
        client, shot, refs, script, prod_dir, composite, duration=REQUESTED_S,
    )

    out = proof_dir / f"kitchen_composite_baked@1_{REQUESTED_S}s_ceiling_probe.mp4"
    _download(resp.url, out)
    actual = probe_duration(out)

    report = {
        "probe": "duration_ceiling_native_generate",
        "at": datetime.now(timezone.utc).isoformat(),
        "model": MODEL,
        "requested_duration_s": REQUESTED_S,
        "actual_duration_s": round(actual, 3),
        "delta_s": round(actual - REQUESTED_S, 3),
        "status": "PASS" if actual >= REQUESTED_S - 0.25 else "SHORT",
        "composite_seed": str(composite),
        "api_url": resp.url,
        "output": str(out),
        "generate_kwargs": req.get("kwargs"),
    }
    report_path = proof_dir / f"ceiling_probe_{REQUESTED_S}s.json"
    report_path.write_text(json.dumps(report, indent=2), encoding="utf-8")

    print(f"[ceiling] actual={actual:.3f}s delta={actual - REQUESTED_S:+.3f}s → {out}", flush=True)
    print(f"[ceiling] report → {report_path}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())