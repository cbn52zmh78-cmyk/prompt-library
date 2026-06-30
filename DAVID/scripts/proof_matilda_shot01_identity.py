#!/usr/bin/env python3
"""Single-shot MATILDA identity proof — BAREBONES prose + configurable pixel seed.

Seed modes (--seed):
  @1        @1 image_file_id + reference_image_file_ids[@2] (R2V+i2v — production path)
  @2        legacy: full turntable as image_url (white flash at t=0)
  @2-front  legacy: front-panel crop as image_url (white flash at t=0)
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from render_longform import (  # noqa: E402
    REFERENCE_IMAGES_API_FINDING,
    SeamlessOptions,
    _api_pace,
    _download,
    _load_grok_token,
    _reference_images_not_supported,
    assert_gate_0_cleared,
    build_barebones_generate_request,
    build_video_generation_prompt,
    capture_editor_session,
    crop_turntable_front_panel,
    extract_frame_at,
    generate_barebones_video,
    normalize_script,
    resolve_production_dir,
    resolve_refs,
    upload_and_capture_id,
)


def _resolve_proof_seed(
    seed: str,
    refs: dict[str, Any],
    client: Any,
    prod_dir: Path,
) -> tuple[str, str, str, str | None]:
    """Return (image_url, seed_slot, role_label, extra_seed_path)."""
    session = refs["editor_session"]
    if seed == "@1":
        return (
            str(refs["@1_plate_url"]),
            "@1",
            "@1 empty warehouse — talent NOT in seed pixels",
            None,
        )
    if seed == "@2":
        return (
            str(session["slots"]["@2"]["url"]),
            "@2",
            "@2 full casting turntable — identity pixel lock",
            str(refs["avatar_file"]),
        )
    if seed == "@2-front":
        avatar = Path(str(refs["avatar_file"]))
        crops_dir = prod_dir / "proof" / "crops"
        crop_path = crop_turntable_front_panel(
            avatar, crops_dir / f"{avatar.stem}_front_panel.jpg",
        )
        _api_pace()
        url, _fid = upload_and_capture_id(client, crop_path, friendly="@2-front")
        return (
            url,
            "@2",
            "@2 front-panel crop — identity pixel lock (no 3-view flash)",
            str(crop_path),
        )
    raise SystemExit(f"unknown --seed {seed!r}; use @1, @2, or @2-front")


def main() -> int:
    parser = argparse.ArgumentParser(description="MATILDA identity proof (BAREBONES)")
    parser.add_argument(
        "script",
        type=Path,
        nargs="?",
        default=ROOT / "scripts" / "longform_scripts" / "matilda_baseline_30s_v1_script.json",
    )
    parser.add_argument("--duration", type=int, default=6)
    parser.add_argument(
        "--seed",
        choices=["@1", "@2", "@2-front"],
        default="@1",
        help="Pixel seed slot (default @1 — empty set source plate, matches 1.mp4 kitchen)",
    )
    parser.add_argument(
        "--proof-id",
        type=str,
        default="",
        help="Output stem under proof/ (default: barebones_{seed}_{duration}s_{timestamp})",
    )
    args = parser.parse_args()

    script_path = args.script if args.script.is_absolute() else ROOT / args.script
    raw = json.loads(script_path.read_text(encoding="utf-8"))
    script = normalize_script(raw, script_path)
    assert_gate_0_cleared(script)

    import xai_sdk

    token = os.environ.get("XAI_API_KEY") or _load_grok_token()
    os.environ["XAI_API_KEY"] = token
    client = xai_sdk.Client(api_key=token)

    refs = resolve_refs(script, client=client)
    prod_dir = resolve_production_dir(script)
    proof_dir = prod_dir / "proof"
    proof_dir.mkdir(parents=True, exist_ok=True)

    if not refs.get("avatar_file"):
        raise SystemExit("proof aborted: no @2 avatar_reference")

    shot = dict(next(s for s in script["shots"] if s["id"] == "01_entry"))
    capture_editor_session(client, refs, script, prod_dir)

    seed_tag = args.seed.replace("@", "").replace("-", "")
    proof_id = args.proof_id.strip() or (
        f"barebones_{seed_tag}_{args.duration}s_"
        f"{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}"
    )
    session_ids = {
        "@1": refs["editor_session"]["slots"]["@1"]["file_id"],
        "@2": refs["editor_session"]["slots"]["@2"]["file_id"],
    }

    bb_req: dict[str, Any] | None = None
    image_url = ""
    seed_slot = ""
    role_label = ""
    seed_path: str | None = None
    prompt = ""

    api_blocked = False
    if args.seed == "@1":
        role_label = "@1 plate + @2 reference_image_file_ids (R2V+i2v)"
        try:
            resp, bb_req = generate_barebones_video(
                client,
                shot,
                refs,
                script,
                prod_dir,
                duration=args.duration,
                seed_slot="@1",
            )
        except Exception as exc:
            if not _reference_images_not_supported(exc):
                raise
            api_blocked = True
            bb_req = build_barebones_generate_request(
                shot,
                refs,
                script,
                prod_dir,
                duration=args.duration,
                seed_slot="@1",
            )
            resp = None
        prompt = bb_req["prompt"]
        image_url = str(bb_req["binding"].get("image_value") or session_ids["@1"])
        seed_slot = "@1"
    else:
        image_url, seed_slot, role_label, seed_path = _resolve_proof_seed(
            args.seed, refs, client, prod_dir,
        )
        prompt = build_video_generation_prompt(
            shot,
            refs,
            SeamlessOptions(),
            script=script,
            prod_dir=prod_dir,
            image_url=image_url,
            seed_slot=seed_slot,
        )
        _api_pace()
        resp = client.video.generate(
            prompt=prompt,
            model=refs["model_video"],
            image_url=image_url,
            duration=args.duration,
            resolution=refs["resolution"],
        )

    manifest = {
        "proof": proof_id,
        "gate": "BLOCKED" if api_blocked else "PASS",
        "prompt_mode": script.get("config", {}).get("prompt_mode", "barebones"),
        "seed_mode": args.seed,
        "seed_slot": seed_slot,
        "at": datetime.now(timezone.utc).isoformat(),
        "session_ids": session_ids,
        "image_url": image_url,
        "image_url_role": role_label,
        "seed_file": seed_path,
        "prompt": prompt,
        "rules": [
            "@1: image_file_id first frame; @2+: reference_image_file_ids compositing",
            "Legacy @2/@2-front seeds use image_url only (white turntable at t=0)",
        ],
        "duration_s": args.duration,
        "model": refs["model_video"],
        "resolution": refs["resolution"],
        "shot_id": shot.get("id"),
    }
    if api_blocked:
        manifest["reference_images_api"] = REFERENCE_IMAGES_API_FINDING
        manifest["wiring_verdict"] = (
            "PR1 binding correct — image_file_id + reference_image_file_ids sent; "
            "API model lacks reference_images support"
        )
    if bb_req:
        manifest["barebones_binding"] = bb_req["binding"]
        manifest["generate_kwargs"] = {
            k: v for k, v in bb_req["kwargs"].items() if k != "prompt"
        }

    manifest_path = proof_dir / f"{proof_id}_manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")

    print(f"[proof] barebones {args.duration}s seed={args.seed} — proof_id={proof_id}")
    print(f"[proof] binding: {role_label}")
    print(f"[proof] session @1={session_ids['@1']}")
    print(f"[proof] session @2={session_ids['@2']}")
    if bb_req:
        print(
            f"[proof] generate: {bb_req['binding'].get('image_field')}=..."
            f" refs={len(bb_req['binding'].get('reference_image_file_ids') or [])}"
        )
    if prompt:
        print(f"[proof] prompt: {prompt[:160]}...")

    if api_blocked:
        print(f"[proof] GATE BLOCKED — {REFERENCE_IMAGES_API_FINDING['finding']}")
        print(f"[proof] wiring manifest → {manifest_path}")
        sys.exit(2)

    out_mp4 = proof_dir / f"{proof_id}.mp4"
    _download(resp.url, out_mp4)
    manifest["video_url"] = resp.url
    manifest["output_mp4"] = str(out_mp4)
    manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")

    for t, label in ((0.5, "0p5s"), (2.0, "2s"), (4.0, "4s"), (8.0, "8s")):
        frame = proof_dir / f"{proof_id}_{label}.jpg"
        extract_frame_at(out_mp4, t, frame)
        manifest[f"frame_{label}"] = str(frame)
    manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")

    print(f"[proof] done → {out_mp4}")
    return 0


if __name__ == "__main__":
    sys.exit(main())