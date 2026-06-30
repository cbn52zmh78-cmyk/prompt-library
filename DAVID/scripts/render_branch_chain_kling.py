#!/usr/bin/env python3
"""Branch-chain renderer — Kling AI API backend.

Drop-in alternative to the Grok-backed renderers. Reads the SAME script JSON
format, produces the SAME directory structure, uses the SAME stitching pipeline.
Only the video generation calls differ.

Works for any content (MATILDA, black hole, etc.) — no content-specific locks
baked in. Those belong in the script JSON or a content-specific wrapper.

Kling limits:
  - Duration: 5 or 10 seconds per generation (extend endpoint for longer)
  - Resolution: up to 1080p (model-dependent)
  - Models: kling-v2.6-pro, kling-v2.5-turbo, kling-video-o1, etc.
  - API is async: submit task → poll → download

Usage:
  python render_branch_chain_kling.py path/to/script.json
  python render_branch_chain_kling.py path/to/script.json --from-clip 3
  python render_branch_chain_kling.py path/to/script.json --stitch-only
  python render_branch_chain_kling.py path/to/script.json --model kling-video-o1
  python render_branch_chain_kling.py path/to/script.json --duration 5

Env vars:
  KLING_API_KEY        — required, your Kling developer API key
  KLING_API_BASE       — optional, override API base URL
                         (default: https://api.klingai.com)
"""
from __future__ import annotations

import argparse
import base64
import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import requests

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
ROOT = Path(__file__).resolve().parents[1]          # DAVID/
WORKSPACE = ROOT.parent                             # Grok Projects/
sys.path.insert(0, str(ROOT / "scripts"))

from render_longform import (  # noqa: E402
    _resolve_workspace_path,
    compile_barebones_prose_prompt,
    concat_xfade_chain,
    extract_last_frame,
    normalize_script,
    probe_duration,
)

# ---------------------------------------------------------------------------
# Kling API config
# ---------------------------------------------------------------------------
KLING_API_BASE = os.environ.get("KLING_API_BASE", "https://api.klingai.com")
KLING_DEFAULT_MODEL = "kling-v2.6-pro"
KLING_VALID_DURATIONS = (5, 10)
KLING_POLL_INTERVAL = 5          # seconds between status checks
KLING_POLL_TIMEOUT = 300         # 5 min max wait per clip
KLING_MAX_RETRIES = 2            # retry on transient failures


def _load_kling_key() -> str:
    key = os.environ.get("KLING_API_KEY", "").strip()
    if not key:
        raise SystemExit(
            "KLING_API_KEY env var not set. "
            "Get your key from https://kling.ai/dev and set it in your environment."
        )
    return key


def _headers(api_key: str) -> dict:
    return {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }


# ---------------------------------------------------------------------------
# Image encoding
# ---------------------------------------------------------------------------
def _encode_image_base64(path: Path) -> str:
    """Encode a local image as a data-URI string for the API payload."""
    suffix = path.suffix.lower().lstrip(".")
    mime = {"jpg": "image/jpeg", "jpeg": "image/jpeg", "png": "image/png"}.get(
        suffix, "image/jpeg"
    )
    raw = path.read_bytes()
    b64 = base64.b64encode(raw).decode("ascii")
    return f"data:{mime};base64,{b64}"


# ---------------------------------------------------------------------------
# Kling API calls
# ---------------------------------------------------------------------------
def _submit_image2video(
    api_key: str,
    image_path: Path,
    prompt: str,
    *,
    tail_image_path: Path | None = None,
    duration: int = 10,
    aspect_ratio: str = "16:9",
    model: str = KLING_DEFAULT_MODEL,
    mode: str = "professional",
    negative_prompt: str | None = None,
) -> str:
    """Submit an image-to-video task. Returns generation ID.

    Kling accepts base64 data-URIs in image_url / tail_image_url, so no
    external hosting is needed for local seed frames.

    tail_image_path: optional last-frame lock — Kling will target this as the
    exit frame, giving us deterministic handoff instead of hoping the last
    frame is usable.
    """
    payload: dict[str, Any] = {
        "model": model,
        "prompt": prompt,
        "image_url": _encode_image_base64(image_path),
        "duration": duration,
        "aspect_ratio": aspect_ratio,
        "mode": mode,
    }
    if tail_image_path and tail_image_path.is_file():
        payload["tail_image_url"] = _encode_image_base64(tail_image_path)
    if negative_prompt:
        payload["negative_prompt"] = negative_prompt

    resp = requests.post(
        f"{KLING_API_BASE}/v1/videos/image2video",
        headers=_headers(api_key),
        json=payload,
        timeout=60,
    )
    resp.raise_for_status()
    data = resp.json()
    gen_id = data.get("id") or data.get("task_id") or data.get("data", {}).get("task_id")
    if not gen_id:
        raise RuntimeError(f"No generation ID in Kling response: {data}")
    return gen_id


def _submit_text2video(
    api_key: str,
    prompt: str,
    *,
    duration: int = 10,
    aspect_ratio: str = "16:9",
    model: str = KLING_DEFAULT_MODEL,
    mode: str = "professional",
    negative_prompt: str | None = None,
) -> str:
    """Submit a text-to-video task (no seed image). Returns generation ID."""
    payload: dict[str, Any] = {
        "model": model,
        "prompt": prompt,
        "duration": duration,
        "aspect_ratio": aspect_ratio,
        "mode": mode,
    }
    if negative_prompt:
        payload["negative_prompt"] = negative_prompt

    resp = requests.post(
        f"{KLING_API_BASE}/v1/videos/text2video",
        headers=_headers(api_key),
        json=payload,
        timeout=60,
    )
    resp.raise_for_status()
    data = resp.json()
    gen_id = data.get("id") or data.get("task_id") or data.get("data", {}).get("task_id")
    if not gen_id:
        raise RuntimeError(f"No generation ID in Kling response: {data}")
    return gen_id


def _poll_task(api_key: str, gen_id: str) -> dict:
    """Poll until task completes or fails. Returns response data with video URL.

    Handles both direct Kling API (GET /v1/videos/{id}) and AIML-style
    (GET /v1/videos?generation_id=...) response shapes.
    """
    deadline = time.time() + KLING_POLL_TIMEOUT
    last_status = ""
    while time.time() < deadline:
        # Try path-param style first (direct Kling API)
        resp = requests.get(
            f"{KLING_API_BASE}/v1/videos/{gen_id}",
            headers=_headers(api_key),
            timeout=30,
        )
        resp.raise_for_status()
        data = resp.json()

        # Handle both flat and nested response shapes
        task_data = data.get("data", data)
        status = (
            task_data.get("status")
            or task_data.get("task_status")
            or ""
        ).lower()

        if status != last_status:
            print(f"[kling]   status: {status}", flush=True)
            last_status = status

        if status in ("completed", "succeed", "success"):
            return task_data
        if status in ("failed", "error"):
            err = task_data.get("error") or {}
            msg = err.get("message") if isinstance(err, dict) else str(err)
            raise RuntimeError(
                f"Kling task {gen_id} failed: {msg or data}"
            )

        time.sleep(KLING_POLL_INTERVAL)

    raise TimeoutError(f"Kling task {gen_id} timed out after {KLING_POLL_TIMEOUT}s")


def _extract_video_url(task_data: dict) -> str:
    """Pull the video download URL from a completed task response.

    Kling's documented shape: {"video": {"url": "..."}}
    Also handles other common patterns from reseller wrappers.
    """
    # Primary: Kling's documented shape
    video = task_data.get("video")
    if isinstance(video, dict) and video.get("url"):
        return video["url"]
    # Flat keys
    for key in ("video_url", "url", "output_url", "result_url"):
        val = task_data.get(key)
        if val:
            return val
    # Array shape: works[0].resource.resource (official Kling SDK pattern)
    works = task_data.get("works") or task_data.get("videos") or []
    if works and isinstance(works, list):
        v = works[0]
        url = (
            v.get("url")
            or v.get("video_url")
            or (v.get("resource") or {}).get("resource")
        )
        if url:
            return url
    raise RuntimeError(f"Cannot find video URL in Kling response: {task_data}")


def _download_video(url: str, out_path: Path) -> None:
    """Download video from URL to local file."""
    print(f"[kling]   downloading -> {out_path.name}", flush=True)
    resp = requests.get(url, stream=True, timeout=120)
    resp.raise_for_status()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "wb") as f:
        for chunk in resp.iter_content(chunk_size=65536):
            f.write(chunk)


# ---------------------------------------------------------------------------
# Script helpers (shared with Grok renderers)
# ---------------------------------------------------------------------------
def _prod_dir(script: dict) -> Path:
    raw = script.get("production_dir")
    if raw:
        p = Path(str(raw))
        return p if p.is_absolute() else WORKSPACE / p
    slug = script.get("slug", "kling_render")
    return WORKSPACE / "DAVID" / "productions" / f"{slug}_kling_v1"


def _resolve_origin(shot: dict) -> Path:
    rel = shot.get("origin_composite") or ""
    p = _resolve_workspace_path(rel)
    if not p.is_file():
        raise SystemExit(f"origin composite missing for {shot['id']}: {p}")
    return p


def _build_prompt(shot: dict, script: dict) -> str:
    """Compile a prompt from the shot's barebones fields."""
    bb = shot.get("barebones") or {}
    parts = []
    for key in ("scene", "camera", "action", "dialogue"):
        val = bb.get(key)
        if val:
            parts.append(str(val).strip())
    prompt = "; ".join(parts) if parts else shot.get("prompt", "")

    # Append any script-level prompt suffix
    suffix = (script.get("config") or {}).get("prompt_suffix", "")
    if suffix and suffix not in prompt:
        prompt = f"{prompt}; {suffix}"
    return prompt


def _build_negative_prompt(shot: dict, script: dict) -> str | None:
    """Build a negative prompt from shot and script config."""
    parts = []
    # Shot-level
    neg = shot.get("negative_prompt") or (shot.get("barebones") or {}).get("negative")
    if neg:
        parts.append(str(neg).strip())
    # Script-level
    cfg_neg = (script.get("config") or {}).get("negative_prompt")
    if cfg_neg:
        parts.append(str(cfg_neg).strip())
    return "; ".join(parts) if parts else None


# ---------------------------------------------------------------------------
# Branch generation
# ---------------------------------------------------------------------------
def _generate_branch(
    api_key: str,
    shot: dict,
    script: dict,
    *,
    seed_image: Path | None,
    out_mp4: Path,
    duration: int,
    model: str,
    aspect_ratio: str,
) -> Path:
    """Generate one branch clip via Kling API."""
    prompt = _build_prompt(shot, script)
    negative = _build_negative_prompt(shot, script)

    # Save prompt for debugging
    out_mp4.with_suffix(".prompt.txt").write_text(prompt, encoding="utf-8")
    if negative:
        out_mp4.with_suffix(".negative.txt").write_text(negative, encoding="utf-8")

    for attempt in range(1, KLING_MAX_RETRIES + 2):
        try:
            if seed_image is not None and seed_image.is_file():
                print(f"[kling]   image2video <- {seed_image.name}", flush=True)
                task_id = _submit_image2video(
                    api_key, seed_image, prompt,
                    duration=duration, aspect_ratio=aspect_ratio,
                    model=model, negative_prompt=negative,
                )
            else:
                print("[kling]   text2video (no seed image)", flush=True)
                task_id = _submit_text2video(
                    api_key, prompt,
                    duration=duration, aspect_ratio=aspect_ratio,
                    model=model, negative_prompt=negative,
                )

            print(f"[kling]   task_id: {task_id}", flush=True)
            result = _poll_task(api_key, task_id)
            video_url = _extract_video_url(result)
            _download_video(video_url, out_mp4)
            return out_mp4

        except (requests.RequestException, RuntimeError, TimeoutError) as exc:
            if attempt <= KLING_MAX_RETRIES:
                wait = 10 * attempt
                print(f"[kling]   attempt {attempt} failed: {exc}", flush=True)
                print(f"[kling]   retrying in {wait}s...", flush=True)
                time.sleep(wait)
            else:
                raise


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main() -> int:
    parser = argparse.ArgumentParser(
        description="Branch-chain renderer — Kling AI backend"
    )
    parser.add_argument("script", help="Path to script JSON")
    parser.add_argument("--from-clip", dest="from_clip", type=int, default=1,
                        help="Resume from clip N (1-based)")
    parser.add_argument("--stitch-only", action="store_true",
                        help="Skip generation, just re-stitch existing clips")
    parser.add_argument("--force", action="store_true",
                        help="Regenerate even if clip already exists")
    parser.add_argument("--model", default=None,
                        help=f"Kling model (default: script config or {KLING_DEFAULT_MODEL})")
    parser.add_argument("--duration", type=int, default=None,
                        help="Clip duration in seconds (5 or 10, default: script config or 10)")
    parser.add_argument("--aspect-ratio", dest="aspect_ratio", default=None,
                        help="Aspect ratio (default: script config or 16:9)")
    args = parser.parse_args()

    # ── Load script ──────────────────────────────────────────────────────
    script_path = Path(args.script)
    if not script_path.is_absolute():
        script_path = Path.cwd() / script_path
    if not script_path.is_file():
        raise SystemExit(f"script not found: {script_path}")

    script = normalize_script(
        json.loads(script_path.read_text(encoding="utf-8")), script_path
    )
    shots = script["shots"]
    cfg = script.get("config") or {}
    bc = cfg.get("branch_chain") or {}

    # ── Resolve settings (CLI > script config > defaults) ────────────────
    model = args.model or cfg.get("kling_model") or cfg.get("model_video") or KLING_DEFAULT_MODEL
    aspect_ratio = args.aspect_ratio or cfg.get("aspect_ratio") or "16:9"

    duration = args.duration or cfg.get("kling_duration") or bc.get("segment_s")
    if duration is None:
        duration = 10
    duration = int(duration)
    # Clamp to Kling-valid durations
    if duration not in KLING_VALID_DURATIONS:
        orig = duration
        duration = min(KLING_VALID_DURATIONS, key=lambda d: abs(d - orig))
        print(f"[kling] duration {orig}s not supported, clamped to {duration}s", flush=True)

    xfade_s = float(bc.get("xfade_s", 0.35))

    # ── Directories ──────────────────────────────────────────────────────
    prod_dir = _prod_dir(script)
    branch_dir = prod_dir / "branches"
    frames_dir = prod_dir / "branch_frames"
    out_dir = prod_dir / "output"
    for d in (branch_dir, frames_dir, out_dir):
        d.mkdir(parents=True, exist_ok=True)

    print(f"[kling] script: {script_path.name}", flush=True)
    print(f"[kling] model:  {model}", flush=True)
    print(f"[kling] clips:  {len(shots)} × {duration}s", flush=True)
    print(f"[kling] output: {prod_dir}", flush=True)

    # ── Stitch-only mode ─────────────────────────────────────────────────
    if args.stitch_only:
        segments = [branch_dir / f"{s['id']}_{duration}s.mp4" for s in shots]
        for p in segments:
            if not p.is_file():
                raise SystemExit(f"missing branch: {p}")
    else:
        # ── Generate clips ───────────────────────────────────────────────
        api_key = _load_kling_key()
        seed_frame: Path | None = None
        state_path = prod_dir / "branch_chain_state.json"
        state: dict = {}
        if state_path.is_file():
            state = json.loads(state_path.read_text(encoding="utf-8"))

        start_idx = max(0, args.from_clip - 1)
        for i, shot in enumerate(shots[start_idx:], start=start_idx):
            sid = shot["id"]
            out_mp4 = branch_dir / f"{sid}_{duration}s.mp4"

            # Skip existing clips unless --force
            if (
                not args.force
                and out_mp4.is_file()
                and out_mp4.stat().st_size > 10_000
            ):
                dur = probe_duration(out_mp4)
                print(f"[clip] reuse {out_mp4.name} ({dur:.2f}s)", flush=True)
                handoff = frames_dir / f"{sid}_last_frame.jpg"
                extract_last_frame(out_mp4, handoff)
                seed_frame = handoff
                continue

            print(f"[clip] {i + 1}/{len(shots)} generate {sid} ({duration}s)",
                  flush=True)

            # Determine seed image for this clip
            use_origin = bool(shot.get("new_origin")) or i == 0
            if use_origin and shot.get("origin_composite"):
                seed_image = _resolve_origin(shot)
                print(f"[clip]   origin <- {seed_image.name}", flush=True)
            elif seed_frame is not None and seed_frame.is_file():
                seed_image = seed_frame
                print(f"[clip]   seed <- {seed_frame.name}", flush=True)
            else:
                # No seed available — try extracting from previous clip
                if i > 0:
                    prev_sid = shots[i - 1]["id"]
                    prev_mp4 = branch_dir / f"{prev_sid}_{duration}s.mp4"
                    if prev_mp4.is_file():
                        seed_frame = frames_dir / f"{prev_sid}_last_frame.jpg"
                        extract_last_frame(prev_mp4, seed_frame)
                        seed_image = seed_frame
                        print(f"[clip]   recovered seed <- {seed_frame.name}",
                              flush=True)
                    else:
                        seed_image = None
                        print("[clip]   WARNING: no seed, falling back to text2video",
                              flush=True)
                else:
                    seed_image = None

            # Generate
            _generate_branch(
                api_key, shot, script,
                seed_image=seed_image,
                out_mp4=out_mp4,
                duration=duration,
                model=model,
                aspect_ratio=aspect_ratio,
            )

            # Extract last frame for handoff
            dur = probe_duration(out_mp4)
            handoff = frames_dir / f"{sid}_last_frame.jpg"
            extract_last_frame(out_mp4, handoff)
            seed_frame = handoff

            # Update state
            state[sid] = {
                "duration_s": dur,
                "handoff_frame": str(handoff),
                "origin": shot.get("origin_composite"),
                "new_origin": shot.get("new_origin"),
                "model": model,
                "backend": "kling",
            }
            state_path.write_text(json.dumps(state, indent=2), encoding="utf-8")
            print(f"[clip]   done {dur:.2f}s -> {out_mp4.name}", flush=True)

        segments = [branch_dir / f"{s['id']}_{duration}s.mp4" for s in shots]

    # ── Stitch ───────────────────────────────────────────────────────────
    ver = bc.get("output_version", "v1")
    final = out_dir / f"{script['slug']}_kling_{len(shots)}x{duration}s_{ver}.mp4"
    work = branch_dir / "stitch_work"
    work.mkdir(parents=True, exist_ok=True)
    print(f"[stitch] joining {len(segments)} clips xfade={xfade_s}s", flush=True)
    concat_xfade_chain(
        segments, final, xfade_s=xfade_s, magenta_clamp=False, work_dir=work
    )
    total = probe_duration(final)

    # ── Report ───────────────────────────────────────────────────────────
    report = {
        "at": datetime.now(timezone.utc).isoformat(),
        "slug": script["slug"],
        "backend": "kling",
        "model": model,
        "clips": len(shots),
        "clip_duration_s": duration,
        "branches": [str(p) for p in segments],
        "xfade_s": xfade_s,
        "output": str(final),
        "duration_s": round(total, 3),
        "expected_s": duration * len(shots) - xfade_s * (len(shots) - 1),
    }
    report_path = prod_dir / "branch_chain_report.json"
    report_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(f"[stitch] -> {final} ({total:.2f}s)", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
