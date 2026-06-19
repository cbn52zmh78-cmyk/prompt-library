#!/usr/bin/env python3
"""Regenerate avatar+set until generation_reference_passes (both)."""
from __future__ import annotations

import os
import sys
from pathlib import Path

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import render_host_identity as rhi  # noqa: E402
from color_cast_qa import (  # noqa: E402
    generation_reference_passes,
    measure_color_cast,
    measure_set_shadow_blue_health,
)


def main() -> int:
    import xai_sdk

    token = os.environ.get("XAI_API_KEY") or rhi._load_grok_token()
    client = xai_sdk.Client(api_key=token)
    refs_dir = rhi.PROD / "references"
    best_bmu = -1.0
    for attempt in range(6):
        print(f"--- attempt {attempt + 1} ---")
        archive = rhi.generate_archive_set(client, refs_dir, force=True)
        avatar = rhi.generate_david_avatar(client, archive, refs_dir, force=True)
        with Image.open(avatar["path"]) as img:
            am = measure_color_cast(np.asarray(img.convert("RGB")))
        with Image.open(archive["path"]) as img:
            sm = measure_set_shadow_blue_health(np.asarray(img.convert("RGB")))
        ap = generation_reference_passes(am, host=True)
        sp = generation_reference_passes(sm, host=False)
        bmu = am["host_blue_mean"]
        print(
            f"avatar Bμ={bmu:.1f} B/R={am['host_br_ratio']:.3f} pass={ap} | "
            f"set pass={sp}"
        )
        if bmu > best_bmu:
            best_bmu = bmu
        if bmu >= 45 and ap and sp:
            print("GATE PASS")
            return 0
    print(f"BEST avatar Bμ={best_bmu:.1f} — gate not satisfied after retries")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())