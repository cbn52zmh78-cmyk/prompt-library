#!/usr/bin/env python3
"""Branch B — 15s 1.5 generate from tight close frame of 15s origin end, shot-02 dialogue."""
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
    compile_barebones_prose_prompt,
    extract_frame_at,
    generate_baked_chain_video,
    normalize_script,
    probe_duration,
    resolve_refs,
    upload_and_capture_id,
)

SCRIPT = ROOT / "scripts/longform_scripts/matilda_stonebridge_kitchen_30s_script.json"
SOURCE_VIDEO = (
    ROOT / "productions/matilda_kitchen_stonebridge_10s_longform_v1/proof/ceiling_probe/"
    "kitchen_composite_baked@1_15s_ceiling_probe.mp4"
)
BRANCH_FRAME_S = float(sys.argv[1]) if len(sys.argv) > 1 else -1.0  # -1 = origin end
DURATION_S = 15
SHOT_ID = "02_role_branch_B_v2"
MODEL = "grok-imagine-video-1.5"

PERSONA = (
    "MATILDA: sassy, witty and charming with a soft, gentle voice; speaks German and English "
    "fluently with native Bavarian/Munich regional accent; must NOT sound American investigative "
    "journalist, NOT CNN/60 Minutes cadence"
)


def main() -> int:
    if not SOURCE_VIDEO.is_file():
        raise SystemExit(f"source video missing: {SOURCE_VIDEO}")

    script = normalize_script(json.loads(SCRIPT.read_text(encoding="utf-8")), SCRIPT)
    base = next(s for s in script["shots"] if s["id"] == "02_role")
    shot = dict(base)
    shot["id"] = SHOT_ID
    shot["duration"] = DURATION_S
    shot["extend_at_s"] = 9.5
    shot["speech_text"] = base["speech_text"]

    bb = dict(shot.get("barebones") or {})
    bb["scene"] = (
        "MATILDA already in tight close-up — face and shoulders dominate frame, no waist visible; "
        "maintains unbroken eye contact with camera entire scene; delivers Stonebridge role and "
        "Munich background in English; dialogue completes around 9.5 seconds then holds composed "
        "static close-up with natural micro-expression through end — no camera move, no pull-back"
    )
    bb["camera"] = (
        "locked tight close-up from first frame — static, zero dolly, zero zoom, zero reframing, "
        "zero pull-back to medium — framing matches seed plate exactly, face-forward portrait "
        "distance entire 15 seconds"
    )
    bb["extension_composition"] = (
        "tight close-up — face fills upper frame, shoulders only, NOT medium shot, NOT MCU drift"
    )
    bb["output"] = {"sequence_length": f"{DURATION_S}s"}
    audio = dict(bb.get("audio") or {})
    audio["voice_direction"] = (
        f"{PERSONA}; Munich-born native speaker English — subtle Bavarian lilt, soft gentle "
        "mid-register, natural German cultural references"
    )
    bb["audio"] = audio
    bb["@2"] = dict(bb.get("@2") or {})
    bb["@2"]["description"] = f"see attached render. {PERSONA}"
    shot["barebones"] = bb

    prod_dir = ROOT / "productions/matilda_kitchen_stonebridge_10s_longform_v1"
    proof_dir = prod_dir / "proof" / "branch_probe"
    proof_dir.mkdir(parents=True, exist_ok=True)

    frames_dir = proof_dir / "frames"
    frames_dir.mkdir(parents=True, exist_ok=True)
    origin_dur = probe_duration(SOURCE_VIDEO)
    seed_at = BRANCH_FRAME_S if BRANCH_FRAME_S > 0 else max(0.0, origin_dur - 0.15)
    frame_jpg = frames_dir / f"branch_seed_origin_{seed_at:.2f}s_tight_close.jpg"
    extract_frame_at(SOURCE_VIDEO, seed_at, frame_jpg)
    print(
        f"[branch] seed frame @ {seed_at:.2f}s (origin end close) ← {SOURCE_VIDEO.name}",
        flush=True,
    )

    client = xai_sdk.Client(api_key=_load_grok_token())
    refs = resolve_refs(script, client=client)
    _api_pace()
    chain_url, chain_fid = upload_and_capture_id(
        client, frame_jpg, friendly="branch_02_close_seed",
    )

    prompt = compile_barebones_prose_prompt(
        shot, refs, prod_dir, script, image_url=chain_url, seed_slot="@1", talent_baked_in=True,
    )
    # baked@1 drops @2 mods — inject persona for voice hold
    if PERSONA not in prompt:
        prompt = f"{prompt} ; VOICE PERSONA LOCK: {PERSONA}"

    prompt_path = proof_dir / "branch_02_tight_close_static_15s_prompt.txt"
    prompt_path.write_text(prompt, encoding="utf-8")
    print(f"[branch] model={MODEL} duration={DURATION_S}s prompt_chars={len(prompt)}", flush=True)

    _api_pace()
    resp, req = generate_baked_chain_video(
        client,
        shot,
        refs,
        script,
        prod_dir,
        chain_image_file_id=chain_fid,
        chain_image_url=chain_url,
        duration=DURATION_S,
    )

    out = proof_dir / f"branch_02_tight_close_static_15s_from_origin_{seed_at:.1f}s.mp4"
    _download(resp.url, out)
    actual = probe_duration(out)

    report = {
        "probe": "branch_B_close_static_15s",
        "at": datetime.now(timezone.utc).isoformat(),
        "mode": "branch_from_source_video",
        "source_video": str(SOURCE_VIDEO),
        "branch_seed_frame_s": seed_at,
        "branch_seed_note": "origin end frame — post creep-zoom close, not 9.5s medium",
        "branch_seed_frame": str(frame_jpg),
        "model": MODEL,
        "duration_requested_s": DURATION_S,
        "dialogue_wrap_target_s": 9.5,
        "shot_id": SHOT_ID,
        "dialogue_shot": "02_role",
        "actual_duration_s": round(actual, 3),
        "output": str(out),
        "api_url": resp.url,
        "prompt_path": str(prompt_path),
        "generate_kwargs": req.get("kwargs"),
    }
    report_path = proof_dir / "branch_02_tight_close_static_15s.json"
    report_path.write_text(json.dumps(report, indent=2), encoding="utf-8")

    print(f"[branch] actual={actual:.3f}s → {out.name}", flush=True)
    print(f"[branch] report → {report_path.name}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())