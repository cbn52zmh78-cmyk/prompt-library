#!/usr/bin/env python3
"""Composite MATILDA variant into Concepts/Plates kitchen plate — island lean pose."""
from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WORKSPACE = ROOT.parent
PLATES = WORKSPACE / "AI/ELEANOR/products/model_variants/Concepts/Plates"
KITCHEN_PLATE = PLATES / "grok-image-2efa731f-f24b-4359-a015-39e400e1fb81.png"
MATILDA_VARIANT = PLATES / "2.jpg"
OUT_JPG = PLATES / "matilda_kitchen_island_composite.jpg"
MODEL = "grok-imagine-image-quality"

PROMPT = (
    "Composite the woman from the talent reference into the kitchen plate environment. "
    "Preserve the kitchen plate layout exactly — do not alter the set, props, or architecture. "
    "Preserve the woman's identity, wardrobe, and accessories exactly as in the talent reference. "
    "Position her center stage behind the kitchen island. "
    "She leans slightly forward at the waist, both hands flat on the island countertop "
    "supporting her weight. "
    "Feet planted, body facing camera, eye contact toward lens. "
    "Relaxed documentary host stance — not rigid, not gesturing. "
    "Medium-wide framing knee to crown, eye-level camera axis. "
    "No other people in frame. Photorealistic 16:9 interior."
)

sys.path.insert(0, str(ROOT / "scripts"))

import xai_sdk  # noqa: E402
from render_longform import (  # noqa: E402
    _api_pace,
    _download,
    _load_grok_token,
    upload_and_capture_id,
)


def main() -> int:
    if not KITCHEN_PLATE.is_file():
        raise SystemExit(f"kitchen plate missing: {KITCHEN_PLATE}")
    if not MATILDA_VARIANT.is_file():
        raise SystemExit(f"MATILDA variant missing: {MATILDA_VARIANT}")

    client = xai_sdk.Client(api_key=_load_grok_token())
    _api_pace()
    _url1, fid1 = upload_and_capture_id(client, KITCHEN_PLATE, friendly="@1_kitchen_plate")
    _api_pace()
    _url2, fid2 = upload_and_capture_id(client, MATILDA_VARIANT, friendly="@2_matilda_variant")
    _api_pace()
    try:
        resp = client.image.sample(
            prompt=PROMPT,
            model=MODEL,
            image_file_ids=[fid1, fid2],
        )
        binding = {"mode": "image_file_ids", "image_file_ids": [fid1, fid2]}
    except TypeError:
        resp = client.image.sample(
            prompt=PROMPT,
            model=MODEL,
            image_url=_url1,
            reference_image_file_ids=[fid2],
        )
        binding = {
            "mode": "image_url+reference_image_file_ids",
            "image_url": _url1,
            "reference_image_file_ids": [fid2],
        }

    _download(resp.url, OUT_JPG)
    manifest = {
        "at": datetime.now(timezone.utc).isoformat(),
        "model": MODEL,
        "prompt": PROMPT,
        "image_inputs": {
            "@1_kitchen_plate": str(KITCHEN_PLATE),
            "@2_matilda_variant": str(MATILDA_VARIANT),
        },
        "binding": binding,
        "output_jpg": OUT_JPG.name,
        "output_path": str(OUT_JPG),
        "pose": "standing behind island, leaning forward, hands on countertop",
    }
    OUT_JPG.with_suffix(".manifest.json").write_text(
        json.dumps(manifest, indent=2), encoding="utf-8"
    )
    print(f"[composite] → {OUT_JPG}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())