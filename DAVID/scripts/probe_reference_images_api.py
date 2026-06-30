#!/usr/bin/env python3
"""Probe video.generate reference_images gate — PR 1 validation, no production changes.

Tests model strings and binding modes documented in xAI SDK:
  - i2v + reference_image_file_ids (PR1 dual-slot)
  - i2v + reference_image_urls
  - pure R2V: reference_image_file_ids only (no image_file_id)
  - pure R2V: reference_image_urls only

Output: productions/matilda_kitchen_stonebridge_10s_longform_v1/proof/reference_images_probe_report.json
"""
from __future__ import annotations

import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from render_longform import (  # noqa: E402
    REFERENCE_IMAGES_API_FINDING,
    _api_pace,
    _load_grok_token,
    _reference_images_not_supported,
    capture_editor_session,
    normalize_script,
    resolve_production_dir,
    resolve_refs,
)

MODELS = [
    "grok-imagine-video",
    "grok-imagine-video-1.5",
    "grok-imagine-video-1.5-preview",
    "grok-imagine-video-1.5-beta",
    "grok-imagine-video-r2v",
]

MODES: list[tuple[str, dict[str, Any]]] = [
    (
        "i2v_plus_ref_file_ids",
        {"use_image_file_id": True, "use_ref_file_ids": True, "use_ref_urls": False},
    ),
    (
        "i2v_plus_ref_urls",
        {"use_image_file_id": True, "use_ref_file_ids": False, "use_ref_urls": True},
    ),
    (
        "r2v_ref_file_ids_only",
        {"use_image_file_id": False, "use_ref_file_ids": True, "use_ref_urls": False},
    ),
    (
        "r2v_ref_urls_only",
        {"use_image_file_id": False, "use_ref_file_ids": False, "use_ref_urls": True},
    ),
    (
        "r2v_ref_file_ids_and_urls",
        {"use_image_file_id": False, "use_ref_file_ids": True, "use_ref_urls": True},
    ),
]

PROMPT = (
    "MATILDA in modern kitchen, static medium shot, documentary host, 6 seconds"
)
DURATION = 6


def _classify_error(exc: BaseException) -> dict[str, Any]:
    msg = str(exc)
    low = msg.lower()
    if _reference_images_not_supported(exc):
        kind = "reference_images_not_supported"
    elif "not found" in low or "does not exist" in low or "unknown model" in low:
        kind = "model_not_found"
    elif "rate" in low or "resource_exhausted" in low:
        kind = "rate_limited"
    elif "not supported" in low or "invalid_argument" in low:
        kind = "invalid_argument_other"
    else:
        kind = "other_error"
    return {"kind": kind, "message": msg[:500]}


def _build_kwargs(
    mode: dict[str, Any],
    *,
    plate_id: str,
    avatar_id: str,
    plate_url: str,
    avatar_url: str,
    model: str,
) -> dict[str, Any]:
    kw: dict[str, Any] = {
        "prompt": PROMPT,
        "model": model,
        "duration": DURATION,
        "resolution": "480p",
        "aspect_ratio": "16:9",
    }
    if mode["use_image_file_id"]:
        kw["image_file_id"] = plate_id
    refs_fid = [avatar_id]
    refs_url = [avatar_url]
    if mode["use_ref_file_ids"]:
        kw["reference_image_file_ids"] = refs_fid
    if mode["use_ref_urls"]:
        kw["reference_image_urls"] = refs_url
    return kw


def main() -> int:
    import xai_sdk

    script_path = (
        ROOT / "scripts/longform_scripts/matilda_kitchen_stonebridge_10s_v1_script.json"
    )
    script = normalize_script(
        json.loads(script_path.read_text(encoding="utf-8")), script_path,
    )
    token = os.environ.get("XAI_API_KEY") or _load_grok_token()
    os.environ["XAI_API_KEY"] = token
    client = xai_sdk.Client(api_key=token)
    refs = resolve_refs(script, client=client)
    prod_dir = resolve_production_dir(script)
    proof_dir = prod_dir / "proof"
    proof_dir.mkdir(parents=True, exist_ok=True)

    capture_editor_session(client, refs, script, prod_dir)
    slots = refs["editor_session"]["slots"]
    plate_id = slots["@1"]["file_id"]
    avatar_id = slots["@2"]["file_id"]
    plate_url = slots["@1"]["url"]
    avatar_url = slots["@2"]["url"]

    results: list[dict[str, Any]] = []
    print(f"[probe] models={len(MODELS)} modes={len(MODES)} duration={DURATION}s")

    for model in MODELS:
        for mode_name, mode in MODES:
            kw = _build_kwargs(
                mode,
                plate_id=plate_id,
                avatar_id=avatar_id,
                plate_url=plate_url,
                avatar_url=avatar_url,
                model=model,
            )
            sent = [k for k in kw if k not in ("prompt", "model", "duration", "resolution", "aspect_ratio")]
            entry: dict[str, Any] = {
                "model": model,
                "mode": mode_name,
                "sent_fields": sent,
                "status": "unknown",
            }
            print(f"[probe] {model} / {mode_name} sent={sent} …", flush=True)
            t0 = time.monotonic()
            try:
                _api_pace()
                resp = client.video.generate(**kw)
                elapsed = round(time.monotonic() - t0, 1)
                entry.update({
                    "status": "PASS",
                    "elapsed_s": elapsed,
                    "video_url": resp.url,
                })
                print(f"  -> PASS ({elapsed}s) {resp.url[:60]}…")
            except Exception as exc:
                elapsed = round(time.monotonic() - t0, 1)
                err = _classify_error(exc)
                entry.update({
                    "status": "FAIL",
                    "elapsed_s": elapsed,
                    "error": err,
                })
                print(f"  -> FAIL {err['kind']}: {err['message'][:120]}")
            results.append(entry)

    passes = [r for r in results if r["status"] == "PASS"]
    ref_fails = [
        r for r in results
        if r.get("error", {}).get("kind") == "reference_images_not_supported"
    ]
    report = {
        "probe": "reference_images_api_matrix",
        "at": datetime.now(timezone.utc).isoformat(),
        "finding_doc": REFERENCE_IMAGES_API_FINDING,
        "sdk_note": (
            "SDK documents separate modes: i2v (image_file_id) vs pure R2V "
            "(reference_image_* only, no image_file_id). PR1 uses i2v+refs combo."
        ),
        "sdk_exposed_params": [
            "reference_image_file_ids",
            "reference_image_urls",
        ],
        "sdk_no_exposed": [
            "x-grok-beta header",
            "enable_references flag",
            "api_version override",
        ],
        "session_ids": {"@1": plate_id, "@2": avatar_id},
        "summary": {
            "total": len(results),
            "pass": len(passes),
            "reference_images_rejected": len(ref_fails),
            "passing_combos": [
                {"model": p["model"], "mode": p["mode"]} for p in passes
            ],
        },
        "results": results,
        "stance": (
            "Beta gate on primary endpoint — PR1 wiring preserved; "
            "composite-first-frame remains production path until a PASS combo appears."
        ),
    }
    out_path = proof_dir / "reference_images_probe_report.json"
    out_path.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"\n[probe] report → {out_path}")
    print(f"[probe] PASS={len(passes)}/{len(results)} ref_rejected={len(ref_fails)}")
    return 0 if passes else 2


if __name__ == "__main__":
    sys.exit(main())