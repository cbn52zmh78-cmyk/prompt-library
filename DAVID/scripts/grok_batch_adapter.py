"""grok_batch_adapter.py — xAI Batch API adapter for render_longform.py

Converts an imagine_pack (from build_imagine_pack) into a Batch API JSONL,
submits, polls, collects, and re-batches failures. No new external deps
beyond xai_sdk (already in render_longform.py).

Usage from render_longform.py:
    from grok_batch_adapter import (
        pack_to_jsonl, submit_batch, poll_batch,
        collect_results, rebatch_failures,
        save_batch_state, load_batch_state,
    )

Standalone test:
    python grok_batch_adapter.py --self-test
"""

from __future__ import annotations

import json
import os
import sys
import time
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
BATCH_API_BASE = "https://api.x.ai/v1"
VIDEO_GEN_ENDPOINT = "/v1/videos/generations"
VIDEO_EXT_ENDPOINT = "/v1/videos/extensions"
DEFAULT_POLL_INTERVAL_S = 30
DEFAULT_POLL_TIMEOUT_S = 86400  # 24 h — xAI batch SLA
URL_EXPIRY_WARNING_S = 3600  # video URLs expire after 1 hour


# ---------------------------------------------------------------------------
# JSONL assembly
# ---------------------------------------------------------------------------

def pack_to_jsonl(
    imagine_pack: dict[str, Any],
    output_path: Path,
    *,
    mode: str = "legacy",
    model_override: str | None = None,
) -> Path:
    """Convert imagine_pack to xAI Batch API JSONL.

    Modes:
        legacy         — one generate request per shot (fully parallel)
        seamless_first — one generate request for the first segment only
                         (extensions run real-time after collect)

    Returns path to the written JSONL file.
    """
    model = model_override or imagine_pack.get("model_video", "grok-imagine-video-1.5")
    resolution = imagine_pack.get("resolution", "1080p")
    aspect = imagine_pack.get("aspect_ratio", "16:9")
    shots = imagine_pack.get("shots", [])

    if not shots:
        raise ValueError("imagine_pack has no shots")

    if mode == "seamless_first":
        shots = shots[:1]  # only first segment is batch-able

    lines: list[str] = []
    for shot in shots:
        sid = shot["shot_id"]
        body: dict[str, Any] = {
            "model": model,
            "prompt": shot["video_prompt"],
            "duration": shot["duration"],
            "resolution": resolution,
            "aspect_ratio": aspect,
        }

        # Image source — prefer URL; fall back to file_id if present
        img_url = shot.get("image_url")
        img_fid = shot.get("image_file_id")
        if img_url:
            body["image"] = {"url": img_url}
        elif img_fid:
            body["image"] = {"file_id": img_fid}

        request_line = {
            "custom_id": f"shot_{sid}",
            "method": "POST",
            "url": VIDEO_GEN_ENDPOINT,
            "body": body,
        }
        lines.append(json.dumps(request_line, ensure_ascii=False))

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return output_path


# ---------------------------------------------------------------------------
# Batch submission
# ---------------------------------------------------------------------------

def _api_key() -> str:
    key = os.environ.get("XAI_API_KEY", "")
    if not key:
        raise RuntimeError("XAI_API_KEY not set")
    return key


def _rest_post(path: str, payload: dict | None = None, *, files: dict | None = None) -> dict:
    """Low-level POST to xAI REST API."""
    url = f"{BATCH_API_BASE}{path}"
    key = _api_key()

    if files:
        # multipart/form-data for file upload
        import uuid
        boundary = uuid.uuid4().hex
        body_parts: list[bytes] = []
        for field_name, (filename, filedata, content_type) in files.items():
            body_parts.append(f"--{boundary}\r\n".encode())
            body_parts.append(
                f'Content-Disposition: form-data; name="{field_name}"; filename="{filename}"\r\n'
                f"Content-Type: {content_type}\r\n\r\n".encode()
            )
            body_parts.append(filedata)
            body_parts.append(b"\r\n")
        if payload:
            for k, v in payload.items():
                body_parts.append(f"--{boundary}\r\n".encode())
                body_parts.append(
                    f'Content-Disposition: form-data; name="{k}"\r\n\r\n{v}\r\n'.encode()
                )
        body_parts.append(f"--{boundary}--\r\n".encode())
        data = b"".join(body_parts)
        content_type = f"multipart/form-data; boundary={boundary}"
    else:
        data = json.dumps(payload or {}).encode("utf-8")
        content_type = "application/json"

    req = urllib.request.Request(
        url,
        data=data,
        headers={
            "Authorization": f"Bearer {key}",
            "Content-Type": content_type,
        },
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=120) as resp:
        return json.loads(resp.read().decode("utf-8"))


def _rest_get(path: str) -> dict:
    """Low-level GET to xAI REST API."""
    url = f"{BATCH_API_BASE}{path}"
    key = _api_key()
    req = urllib.request.Request(
        url,
        headers={"Authorization": f"Bearer {key}"},
        method="GET",
    )
    with urllib.request.urlopen(req, timeout=120) as resp:
        return json.loads(resp.read().decode("utf-8"))


def submit_batch(
    jsonl_path: Path,
    batch_name: str,
    *,
    client: Any = None,
) -> str:
    """Submit JSONL to xAI Batch API. Returns batch_id.

    Tries xai_sdk.Client first (if provided); falls back to REST.
    """
    if not jsonl_path.is_file():
        raise FileNotFoundError(f"JSONL not found: {jsonl_path}")

    # --- SDK path ---
    if client is not None and hasattr(client, "batch"):
        try:
            batch = client.batch.create(
                input_file=str(jsonl_path),
                metadata={"name": batch_name},
            )
            return batch.id
        except Exception as exc:
            print(f"[batch] SDK submit failed ({exc}), falling back to REST", file=sys.stderr)

    # --- REST path ---
    jsonl_bytes = jsonl_path.read_bytes()
    # Step 1: upload the JSONL file
    upload_resp = _rest_post(
        "/files",
        payload={"purpose": "batch"},
        files={"file": (jsonl_path.name, jsonl_bytes, "application/jsonl")},
    )
    file_id = upload_resp.get("id")
    if not file_id:
        raise RuntimeError(f"File upload failed: {upload_resp}")

    # Step 2: create the batch
    batch_resp = _rest_post(
        "/batches",
        payload={
            "input_file_id": file_id,
            "endpoint": VIDEO_GEN_ENDPOINT,
            "completion_window": "24h",
            "metadata": {"name": batch_name},
        },
    )
    batch_id = batch_resp.get("id")
    if not batch_id:
        raise RuntimeError(f"Batch creation failed: {batch_resp}")

    return batch_id


# ---------------------------------------------------------------------------
# Polling
# ---------------------------------------------------------------------------

def poll_batch(
    batch_id: str,
    *,
    client: Any = None,
    interval_s: int = DEFAULT_POLL_INTERVAL_S,
    timeout_s: int = DEFAULT_POLL_TIMEOUT_S,
    callback: Callable[[dict], None] | None = None,
) -> dict:
    """Poll batch status until complete, failed, or timeout.

    Returns final batch state dict. Callback fires each poll cycle.
    """
    deadline = time.monotonic() + timeout_s

    while time.monotonic() < deadline:
        if client is not None and hasattr(client, "batch"):
            try:
                state = client.batch.get(batch_id)
                state_dict = {
                    "id": state.id,
                    "status": state.status,
                    "request_counts": getattr(state, "request_counts", {}),
                }
            except Exception:
                state_dict = _rest_get(f"/batches/{batch_id}")
        else:
            state_dict = _rest_get(f"/batches/{batch_id}")

        status = state_dict.get("status", "unknown")
        if callback:
            callback(state_dict)

        if status in ("completed", "failed", "expired", "cancelled"):
            return state_dict

        time.sleep(interval_s)

    raise TimeoutError(f"Batch {batch_id} did not complete within {timeout_s}s")


# ---------------------------------------------------------------------------
# Result collection
# ---------------------------------------------------------------------------

def _download_video(url: str, dest: Path) -> None:
    """Download a video file from URL."""
    dest.parent.mkdir(parents=True, exist_ok=True)
    req = urllib.request.Request(url, headers={"User-Agent": "DAVID-batch/1.0"})
    with urllib.request.urlopen(req, timeout=300) as r:
        dest.write_bytes(r.read())


def collect_results(
    batch_id: str,
    shots_dir: Path,
    *,
    client: Any = None,
    download: bool = True,
) -> dict[str, dict]:
    """Retrieve batch results, optionally download videos.

    Returns {custom_id: {"url": ..., "path": ..., "status": ..., "error": ...}}

    IMPORTANT: Video URLs expire after 1 hour. Downloads happen immediately.
    """
    # Get results
    if client is not None and hasattr(client, "batch"):
        try:
            raw_results = client.batch.list_batch_results(batch_id)
            results_list = raw_results if isinstance(raw_results, list) else raw_results.get("results", [])
        except Exception:
            results_list = _get_results_rest(batch_id)
    else:
        results_list = _get_results_rest(batch_id)

    shots_dir.mkdir(parents=True, exist_ok=True)
    out: dict[str, dict] = {}

    for item in results_list:
        cid = item.get("custom_id", "unknown")
        response = item.get("response", {})
        status_code = response.get("status_code", 500)
        body = response.get("body", {})

        if status_code == 200:
            video_url = body.get("url") or body.get("video", {}).get("url", "")
            entry: dict[str, Any] = {
                "url": video_url,
                "status": "succeeded",
                "error": None,
                "path": None,
            }
            if download and video_url:
                # Derive filename from custom_id (strip "shot_" prefix)
                sid = cid.replace("shot_", "", 1)
                dest = shots_dir / f"{sid}.mp4"
                try:
                    _download_video(video_url, dest)
                    entry["path"] = str(dest)
                except Exception as exc:
                    entry["status"] = "download_failed"
                    entry["error"] = str(exc)
        else:
            entry = {
                "url": None,
                "status": "failed",
                "error": body.get("error", {}).get("message", f"HTTP {status_code}"),
                "path": None,
            }

        out[cid] = entry

    return out


def _get_results_rest(batch_id: str) -> list[dict]:
    """Fetch batch results via REST API."""
    # Get the batch to find output_file_id
    batch_info = _rest_get(f"/batches/{batch_id}")
    output_file_id = batch_info.get("output_file_id")
    if not output_file_id:
        raise RuntimeError(f"Batch {batch_id} has no output_file_id (status: {batch_info.get('status')})")

    # Download the output file (JSONL)
    url = f"{BATCH_API_BASE}/files/{output_file_id}/content"
    key = _api_key()
    req = urllib.request.Request(
        url,
        headers={"Authorization": f"Bearer {key}"},
        method="GET",
    )
    with urllib.request.urlopen(req, timeout=120) as resp:
        content = resp.read().decode("utf-8")

    results = []
    for line in content.strip().split("\n"):
        if line.strip():
            results.append(json.loads(line))
    return results


# ---------------------------------------------------------------------------
# Re-batch failures
# ---------------------------------------------------------------------------

def rebatch_failures(
    results: dict[str, dict],
    imagine_pack: dict[str, Any],
    output_path: Path,
    *,
    client: Any = None,
    model_override: str | None = None,
) -> str | None:
    """Re-submit failed shots as a new batch.

    Returns new batch_id or None if no failures.
    """
    failed_cids = {
        cid for cid, info in results.items()
        if info["status"] in ("failed", "download_failed")
    }

    if not failed_cids:
        return None

    # Map custom_ids back to shot_ids
    failed_sids = {cid.replace("shot_", "", 1) for cid in failed_cids}

    # Filter imagine_pack to only failed shots
    retry_pack = dict(imagine_pack)
    retry_pack["shots"] = [
        s for s in imagine_pack.get("shots", [])
        if s["shot_id"] in failed_sids
    ]

    if not retry_pack["shots"]:
        return None

    pack_to_jsonl(retry_pack, output_path, model_override=model_override)

    slug = imagine_pack.get("slug", "retry")
    batch_id = submit_batch(output_path, f"{slug}_retry", client=client)
    return batch_id


# ---------------------------------------------------------------------------
# Batch state persistence
# ---------------------------------------------------------------------------

def batch_state_path(prod_dir: Path) -> Path:
    """Standard location for batch state file."""
    return prod_dir / "batch_state.json"


def save_batch_state(prod_dir: Path, state: dict) -> None:
    """Persist batch submission state for --collect resume."""
    prod_dir.mkdir(parents=True, exist_ok=True)
    path = batch_state_path(prod_dir)
    state.setdefault("saved_at", datetime.now(timezone.utc).isoformat())
    path.write_text(json.dumps(state, indent=2, ensure_ascii=False), encoding="utf-8")


def load_batch_state(prod_dir: Path) -> dict | None:
    """Load saved batch state. Returns None if no state file exists."""
    path = batch_state_path(prod_dir)
    if not path.is_file():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


# ---------------------------------------------------------------------------
# Progress formatting
# ---------------------------------------------------------------------------

def format_progress(state: dict) -> str:
    """Human-readable one-liner from a poll state dict."""
    status = state.get("status", "unknown")
    counts = state.get("request_counts", {})
    total = counts.get("total", "?")
    completed = counts.get("completed", 0)
    failed = counts.get("failed", 0)
    return f"[batch] status={status}  completed={completed}/{total}  failed={failed}"


# ---------------------------------------------------------------------------
# Self-test
# ---------------------------------------------------------------------------

def _self_test() -> None:
    """Validate module loads, JSONL format is correct, state round-trips."""
    import tempfile

    print("[self-test] Testing pack_to_jsonl...")
    pack = {
        "slug": "test_project",
        "model_video": "grok-imagine-video-1.5",
        "resolution": "1080p",
        "aspect_ratio": "16:9",
        "shots": [
            {
                "shot_id": "b01",
                "duration": 8,
                "image_url": "https://example.com/frame1.png",
                "video_prompt": "A wide establishing shot of a Gothic cathedral",
                "speech_text": "In the beginning...",
            },
            {
                "shot_id": "b02",
                "duration": 6,
                "image_url": "https://example.com/frame2.png",
                "video_prompt": "Close-up of stained glass window",
                "speech_text": "The light filtered through...",
            },
            {
                "shot_id": "b03",
                "duration": 8,
                "image_url": None,
                "image_file_id": "file_abc123",
                "video_prompt": "Interior nave with candlelight",
                "speech_text": "",
            },
        ],
    }

    with tempfile.TemporaryDirectory() as td:
        td_path = Path(td)

        # Test JSONL generation
        jsonl_path = td_path / "batch.jsonl"
        result = pack_to_jsonl(pack, jsonl_path)
        assert result == jsonl_path, f"Expected {jsonl_path}, got {result}"
        assert jsonl_path.is_file(), "JSONL file not created"

        lines = jsonl_path.read_text(encoding="utf-8").strip().split("\n")
        assert len(lines) == 3, f"Expected 3 lines, got {len(lines)}"

        for i, line in enumerate(lines):
            obj = json.loads(line)
            assert "custom_id" in obj, f"Line {i}: missing custom_id"
            assert obj["method"] == "POST", f"Line {i}: method != POST"
            assert obj["url"] == VIDEO_GEN_ENDPOINT, f"Line {i}: wrong url"
            assert "body" in obj, f"Line {i}: missing body"
            body = obj["body"]
            assert body["model"] == "grok-imagine-video-1.5", f"Line {i}: wrong model"
            assert "prompt" in body, f"Line {i}: missing prompt"
            assert "duration" in body, f"Line {i}: missing duration"

        # Check image handling
        line0 = json.loads(lines[0])
        assert line0["body"]["image"]["url"] == "https://example.com/frame1.png"

        line2 = json.loads(lines[2])
        assert line2["body"]["image"]["file_id"] == "file_abc123"

        print(f"  JSONL: {len(lines)} lines, format OK")

        # Test seamless_first mode
        jsonl_sf = td_path / "batch_sf.jsonl"
        pack_to_jsonl(pack, jsonl_sf, mode="seamless_first")
        sf_lines = jsonl_sf.read_text(encoding="utf-8").strip().split("\n")
        assert len(sf_lines) == 1, f"seamless_first: expected 1 line, got {len(sf_lines)}"
        print("  seamless_first mode: 1 line OK")

        # Test state round-trip
        state = {
            "batch_id": "batch_test123",
            "batch_name": "test_project",
            "mode": "legacy",
            "shot_count": 3,
            "shot_ids": ["b01", "b02", "b03"],
            "status": "submitted",
        }
        save_batch_state(td_path, state)
        loaded = load_batch_state(td_path)
        assert loaded is not None, "State not loaded"
        assert loaded["batch_id"] == "batch_test123"
        assert loaded["shot_count"] == 3
        print("  State round-trip: OK")

        # Test rebatch with mock results
        mock_results = {
            "shot_b01": {"status": "succeeded", "url": "https://x.ai/v1", "path": "/tmp/b01.mp4", "error": None},
            "shot_b02": {"status": "failed", "url": None, "path": None, "error": "timeout"},
            "shot_b03": {"status": "succeeded", "url": "https://x.ai/v3", "path": "/tmp/b03.mp4", "error": None},
        }
        rebatch_jsonl = td_path / "rebatch.jsonl"
        # Can't actually submit without API, but can test JSONL generation
        failed_cids = {cid for cid, info in mock_results.items() if info["status"] == "failed"}
        failed_sids = {cid.replace("shot_", "", 1) for cid in failed_cids}
        retry_pack = dict(pack)
        retry_pack["shots"] = [s for s in pack["shots"] if s["shot_id"] in failed_sids]
        pack_to_jsonl(retry_pack, rebatch_jsonl)
        rb_lines = rebatch_jsonl.read_text(encoding="utf-8").strip().split("\n")
        assert len(rb_lines) == 1, f"Rebatch: expected 1 line (b02), got {len(rb_lines)}"
        rb_obj = json.loads(rb_lines[0])
        assert rb_obj["custom_id"] == "shot_b02"
        print("  Rebatch filter: OK")

        # Test format_progress
        progress = format_progress({
            "status": "in_progress",
            "request_counts": {"total": 42, "completed": 15, "failed": 1},
        })
        assert "15/42" in progress
        print(f"  Progress format: \"{progress}\"")

    print("[self-test] All checks passed.")


if __name__ == "__main__":
    if "--self-test" in sys.argv:
        _self_test()
    else:
        print("Usage: python grok_batch_adapter.py --self-test")
        print("  Or import from render_longform.py")
