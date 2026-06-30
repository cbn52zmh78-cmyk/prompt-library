#!/usr/bin/env python3
"""Black hole branch chain — composite seed + last-frame handoff.

Usage:
  python render_branch_chain_black_hole.py                          # default 24x15s script
  python render_branch_chain_black_hole.py path/to/script.json      # any black-hole script
  python render_branch_chain_black_hole.py --from-clip 5            # resume from clip 5
  python render_branch_chain_black_hole.py --stitch-only            # re-stitch existing clips
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
WORKSPACE = ROOT.parent
DEFAULT_SCRIPT_PATH = (
    WORKSPACE
    / "Stonebridge/Products/CANNON/VIDEOS/RESEARCH/INTERSTELLAR/BLACK_HOLES"
    / "black_hole_journey_24x15s_script.json"
)
DURATION_S = 15

COLOR = (
    "COLOR DNA LOCK: disk tilt 35deg; left approaching cyan-white hot; right receding "
    "orange-red dim; NOT mirror symmetric -- match locked origin palette"
)
AUDIO = "AUDIO LOCK: absolute silence mute generate"
PHYSICS = "PHYSICS LOCK: no luminous sphere no waterfall no fire jets no interior"
CONTINUITY = "CONTINUITY LOCK: match seed frame mass scale tilt color LUT exposure"
TIMING = "TIMING LOCK: continuous motion full 15s cut-ready no dead end hold"
PURE_VISUAL_HOST_LOCK = (
    "NO HOST LOCK: zero people zero presenter zero talent zero on-screen narrator — "
    "pure astrophysics phenomenon visual only"
)
PURE_VISUAL_PROMPT_TEMPLATE = "Studio/prompts/MASTER_PureVisual_v1.json"

sys.path.insert(0, str(ROOT / "scripts"))

import xai_sdk  # noqa: E402
from render_longform import (  # noqa: E402
    _api_pace,
    _download,
    _load_grok_token,
    _resolve_workspace_path,
    compile_barebones_prose_prompt,
    concat_xfade_chain,
    extract_last_frame,
    generate_baked_chain_video,
    generate_baked_composite_video,
    normalize_script,
    probe_duration,
    resolve_refs,
    upload_and_capture_id,
)


def _prod_dir(script: dict) -> Path:
    raw = script.get("production_dir")
    if raw:
        p = Path(str(raw))
        return p if p.is_absolute() else WORKSPACE / p
    slug = script.get("slug", "black_hole_journey")
    return WORKSPACE / "DAVID" / "productions" / f"{slug}_v1"


def _resolve_origin(shot: dict) -> Path:
    rel = shot.get("origin_composite") or ""
    p = _resolve_workspace_path(rel)
    if not p.is_file():
        raise SystemExit(f"origin composite missing for {shot['id']}: {p}")
    return p


def _apply_pure_visual_config(script: dict) -> None:
    """Force VO-in-post astrophysics mode — never seed Matilda / identity lock."""
    cfg = script.setdefault("config", {})
    script["format_id"] = "science-pure-visual"
    cfg["format_id"] = "science-pure-visual"
    cfg["narration"] = False
    cfg["use_identity_lock"] = False
    cfg["use_zone_plates"] = False
    cfg.setdefault("prompt_mode", "barebones")
    cfg.setdefault("prompt_template", PURE_VISUAL_PROMPT_TEMPLATE)
    cfg.setdefault("model_video", "grok-imagine-video-1.5")
    cfg.setdefault("resolution", "480p")
    cfg.setdefault("aspect_ratio", "16:9")
    branch = cfg.setdefault("branch_chain", {})
    if branch.get("output_version") == "v1":
        branch["output_version"] = "v2"


def _enrich_prompt(prompt: str) -> str:
    for clause in (PURE_VISUAL_HOST_LOCK, COLOR, AUDIO, PHYSICS, CONTINUITY, TIMING):
        if clause not in prompt:
            prompt = f"{prompt} ; {clause}"
    return prompt


def _generate_branch(
    client: Any,
    shot: dict,
    refs: dict,
    script: dict,
    prod_dir: Path,
    *,
    composite: Path | None,
    seed_frame: Path | None,
    out_mp4: Path,
) -> tuple[str, Path]:
    if composite is not None:
        shot_enriched = dict(shot)
        bb = dict(shot_enriched.get("barebones") or {})
        for key in ("scene", "camera"):
            val = str(bb.get(key) or "")
            if TIMING not in val:
                bb[key] = f"{val}; {TIMING}"
        shot_enriched["barebones"] = bb
        _api_pace()
        resp, req = generate_baked_composite_video(
            client, shot_enriched, refs, script, prod_dir, composite, duration=DURATION_S,
        )
        prompt = _enrich_prompt(req.get("prompt") or "")
    else:
        assert seed_frame is not None
        _api_pace()
        chain_url, chain_fid = upload_and_capture_id(
            client, seed_frame, friendly=f"branch_seed_{shot['id']}",
        )
        shot_enriched = dict(shot)
        bb = dict(shot_enriched.get("barebones") or {})
        sc = str(bb.get("scene") or "")
        if CONTINUITY not in sc:
            bb["scene"] = f"{sc}; {CONTINUITY}; {TIMING}"
        shot_enriched["barebones"] = bb
        prompt = _enrich_prompt(
            compile_barebones_prose_prompt(
                shot_enriched, refs, prod_dir, script,
                image_url=chain_url, seed_slot="@1", talent_baked_in=True,
            )
        )
        _api_pace()
        resp, req = generate_baked_chain_video(
            client, shot_enriched, refs, script, prod_dir,
            chain_image_file_id=chain_fid,
            chain_image_url=chain_url,
            duration=DURATION_S,
        )

    prompt_path = out_mp4.with_suffix(".prompt.txt")
    prompt_path.write_text(prompt, encoding="utf-8")
    _download(resp.url, out_mp4)
    return resp.url, out_mp4


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("script", nargs="?", default=None,
                        help="Path to script JSON (default: 24x15s black hole journey)")
    parser.add_argument("--from-clip", dest="from_clip", type=int, default=1,
                        help="Resume from clip N (1-based)")
    parser.add_argument("--stitch-only", action="store_true")
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()

    script_path = Path(args.script) if args.script else DEFAULT_SCRIPT_PATH
    if not script_path.is_absolute():
        script_path = Path.cwd() / script_path
    if not script_path.is_file():
        raise SystemExit(f"script not found: {script_path}")

    script = normalize_script(json.loads(script_path.read_text(encoding="utf-8")), script_path)
    _apply_pure_visual_config(script)
    shots = script["shots"]
    prod_dir = _prod_dir(script)
    branch_dir = prod_dir / "branches"
    frames_dir = prod_dir / "branch_frames"
    out_dir = prod_dir / "output"
    for d in (branch_dir, frames_dir, out_dir):
        d.mkdir(parents=True, exist_ok=True)

    xfade_s = float((script.get("config", {}).get("branch_chain") or {}).get("xfade_s", 0.35))

    if args.stitch_only:
        segments = [branch_dir / f"{s['id']}_{DURATION_S}s.mp4" for s in shots]
        for p in segments:
            if not p.is_file():
                raise SystemExit(f"missing branch: {p}")
    else:
        client = xai_sdk.Client(api_key=_load_grok_token())
        refs = resolve_refs(script, client=client)
        seed_frame: Path | None = None
        state_path = prod_dir / "branch_chain_state.json"
        state: dict = {}
        if state_path.is_file():
            state = json.loads(state_path.read_text(encoding="utf-8"))

        start_idx = max(0, args.from_clip - 1)
        for i, shot in enumerate(shots[start_idx:], start=start_idx):
            sid = shot["id"]
            out_mp4 = branch_dir / f"{sid}_{DURATION_S}s.mp4"
            if (
                not args.force
                and out_mp4.is_file()
                and out_mp4.stat().st_size > 10000
            ):
                print(f"[clip] reuse {out_mp4.name} ({probe_duration(out_mp4):.2f}s)", flush=True)
                handoff = frames_dir / f"{sid}_last_frame.jpg"
                extract_last_frame(out_mp4, handoff)
                seed_frame = handoff
                continue

            use_composite = bool(shot.get("new_origin")) or i == 0
            print(f"[clip] {i + 1}/{len(shots)} generate {sid} ({DURATION_S}s)", flush=True)

            if use_composite:
                composite = _resolve_origin(shot)
                print(f"[clip]   origin <- {composite.name}", flush=True)
                api_url, out_mp4 = _generate_branch(
                    client, shot, refs, script, prod_dir,
                    composite=composite, seed_frame=None, out_mp4=out_mp4,
                )
            else:
                if seed_frame is None or not seed_frame.is_file():
                    prev = shots[i - 1]["id"]
                    prev_mp4 = branch_dir / f"{prev}_{DURATION_S}s.mp4"
                    seed_frame = frames_dir / f"{prev}_last_frame.jpg"
                    extract_last_frame(prev_mp4, seed_frame)
                print(f"[clip]   seed <- {seed_frame.name}", flush=True)
                api_url, out_mp4 = _generate_branch(
                    client, shot, refs, script, prod_dir,
                    composite=None, seed_frame=seed_frame, out_mp4=out_mp4,
                )

            dur = probe_duration(out_mp4)
            handoff = frames_dir / f"{sid}_last_frame.jpg"
            extract_last_frame(out_mp4, handoff)
            seed_frame = handoff
            state[sid] = {
                "api_url": api_url,
                "duration_s": dur,
                "handoff_frame": str(handoff),
                "origin": shot.get("origin_composite"),
                "new_origin": shot.get("new_origin"),
            }
            state_path.write_text(json.dumps(state, indent=2), encoding="utf-8")
            print(f"[clip]   done {dur:.2f}s -> {out_mp4.name}", flush=True)

        segments = [branch_dir / f"{s['id']}_{DURATION_S}s.mp4" for s in shots]

    ver = (script.get("config", {}).get("branch_chain") or {}).get("output_version", "v1")
    final = out_dir / f"{script['slug']}_branch_chain_{len(shots)}x15s_{ver}.mp4"
    work = branch_dir / "stitch_work"
    work.mkdir(parents=True, exist_ok=True)
    print(f"[stitch] joining {len(segments)} clips xfade={xfade_s}s", flush=True)
    concat_xfade_chain(segments, final, xfade_s=xfade_s, magenta_clamp=False, work_dir=work)
    total = probe_duration(final)

    report = {
        "at": datetime.now(timezone.utc).isoformat(),
        "slug": script["slug"],
        "clips": len(shots),
        "branches": [str(p) for p in segments],
        "xfade_s": xfade_s,
        "output": str(final),
        "duration_s": round(total, 3),
        "expected_s": DURATION_S * len(shots) - xfade_s * (len(shots) - 1),
        "audio_post": "chandra_perseus_sonification",
    }
    (prod_dir / "branch_chain_report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(f"[stitch] -> {final} ({total:.2f}s)", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
