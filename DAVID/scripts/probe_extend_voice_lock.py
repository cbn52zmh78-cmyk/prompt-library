#!/usr/bin/env python3
"""Extend voice consistency probe — full shot-02 barebones on 15s 1.5 origin."""
from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import xai_sdk  # noqa: E402
from render_longform import (  # noqa: E402
    LEGACY_EXTEND_MODEL,
    SeamlessOptions,
    _api_pace,
    _download,
    _load_grok_token,
    build_extend_prose_prompt,
    normalize_script,
    probe_duration,
    resolve_refs,
)

SCRIPT = ROOT / "scripts/longform_scripts/matilda_stonebridge_kitchen_30s_script.json"
ORIGIN_URL = (
    "https://vidgen.x.ai/xai-vidgen-bucket/"
    "xai-video-0bc9d287-19c2-96dc-91ec-79e3012c6962.mp4"
)
EXTEND_S = 10
SHOT_ID = "02_role"


def main() -> int:
    script = normalize_script(json.loads(SCRIPT.read_text(encoding="utf-8")), SCRIPT)
    shot = next(s for s in script["shots"] if s["id"] == SHOT_ID)
    opts = SeamlessOptions(enabled=True)

    client = xai_sdk.Client(api_key=_load_grok_token())
    refs = resolve_refs(script, client=client)
    prod_dir = ROOT / "productions/matilda_kitchen_stonebridge_10s_longform_v1"
    prompt = build_extend_prose_prompt(
        shot, refs, opts, script, prod_dir, baked_pipeline=True,
    )

    proof_dir = prod_dir / "proof" / "ceiling_probe"
    proof_dir.mkdir(parents=True, exist_ok=True)
    prompt_path = proof_dir / "extend_voice_lock_02_role_prompt.txt"
    prompt_path.write_text(prompt, encoding="utf-8")

    print(f"[voice-lock] extend {EXTEND_S}s from 15s origin shot={SHOT_ID}", flush=True)
    print(f"[voice-lock] model={LEGACY_EXTEND_MODEL}", flush=True)
    print(f"[voice-lock] prompt_chars={len(prompt)} → {prompt_path.name}", flush=True)

    _api_pace()
    resp = client.video.extend(
        prompt=prompt,
        model=LEGACY_EXTEND_MODEL,
        video_url=ORIGIN_URL,
        duration=EXTEND_S,
    )

    out = proof_dir / "extend_voice_lock_15s_origin_plus_10s_02_role.mp4"
    _download(resp.url, out)
    actual = probe_duration(out)

    report = {
        "probe": "extend_voice_lock_shot02",
        "at": datetime.now(timezone.utc).isoformat(),
        "origin_url": ORIGIN_URL,
        "origin_duration_s": 15.04,
        "extend_model": LEGACY_EXTEND_MODEL,
        "extend_duration_requested_s": EXTEND_S,
        "output_duration_s": round(actual, 3),
        "shot_id": SHOT_ID,
        "prompt_path": str(prompt_path),
        "output": str(out),
        "api_url": resp.url,
        "prompt_preview": prompt[:500] + ("…" if len(prompt) > 500 else ""),
    }
    report_path = proof_dir / "extend_voice_lock_02_role.json"
    report_path.write_text(json.dumps(report, indent=2), encoding="utf-8")

    print(f"[voice-lock] actual={actual:.3f}s → {out.name}", flush=True)
    print(f"[voice-lock] report → {report_path.name}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())