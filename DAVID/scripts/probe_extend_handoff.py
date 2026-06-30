#!/usr/bin/env python3
"""Probe whether legacy extend accepts 1.5-generated source vs trimmed re-upload."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import xai_sdk  # noqa: E402
from render_longform import _api_pace, _load_grok_token, upload_video_url  # noqa: E402

NATIVE_15_URL = (
    "https://vidgen.x.ai/xai-vidgen-bucket/"
    "xai-video-66f867ea-0e91-9aa0-8545-7a4118ae648c.mp4"
)
TRIM_PATH = (
    ROOT / "productions/matilda_stonebridge_kitchen_30s_longform_v1/shots/"
    "extend_sources/extend_source_01_intro_7.50s.mp4"
)
PROMPT = "MATILDA continues speaking to camera, medium close-up, maintains eye contact"
MODEL = "grok-imagine-video"


def _detail(exc: BaseException) -> str:
    msg = str(exc)
    if "details = " in msg:
        return msg.split("details = ")[1].split("\n")[0].strip('"')
    return msg[:240]


def main() -> int:
    client = xai_sdk.Client(api_key=_load_grok_token())
    cases: list[tuple[str, str]] = [("native_1.5_api_url", NATIVE_15_URL)]

    _api_pace()
    uploaded = upload_video_url(client, TRIM_PATH)
    cases.append(("trimmed_reupload_7.5s", uploaded))

    for label, url in cases:
        print(f"[probe] {label} ...", flush=True)
        try:
            _api_pace()
            resp = client.video.extend(
                prompt=PROMPT, model=MODEL, video_url=url, duration=10,
            )
            print(f"  PASS url={resp.url[:72]}...")
        except Exception as exc:
            print(f"  FAIL {_detail(exc)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())