#!/usr/bin/env python3
"""4×15s branch chain — seed policy from script branch_chain.seed_handoff.

last_frame (default for Matilda 60s):
  b01 ← composite_first_frame
  b02 ← upload b01 last frame → image_file_id
  b03 ← upload b02 last frame → image_file_id
  … sequential chain → xfade/hard-cut stitch

last_frame_prompt_only (optional):
  last frame analyzed for prompt staging only; star-seed from origin composite.
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import xai_sdk  # noqa: E402
from render_longform import (  # noqa: E402
    BRANCH_CHAIN_LAST_FRAME_MODE,
    BRANCH_CHAIN_STAGING_MODE,
    _api_pace,
    _download,
    _load_grok_token,
    _resolve_composite_first_frame,
    analyze_handoff_frame,
    concat_xfade_chain,
    generate_baked_composite_video,
    generate_branch_handoff_video,
    mandatory_extract_last_frame,
    normalize_script,
    probe_duration,
    resolve_branch_chain_seed_handoff,
    resolve_refs,
)

SCRIPT_PATH = ROOT / "scripts/longform_scripts/matilda_stonebridge_kitchen_60s_4branch_script.json"
DURATION_S = 15
EYELINE = (
    "EYE LINE LOCK: pupils centered on camera lens throughout — never off-camera left/right, "
    "never interview eyeline, never downstage void"
)
PERSONA = (
    "VOICE PERSONA LOCK: MATILDA — relaxed laid-back friendly inviting host; soft gentle warm "
    "voice; native Bavarian/Munich accent; genuinely enjoys her work; must NOT sound American "
    "investigative journalist, NOT corporate commander, NOT network anchor"
)
RELAXED_HOST = (
    "RELAXED HOST LOCK: conversational hospitality — warm, inviting, easygoing business host "
    "who enjoys selling Stonebridge; NOT authoritative, NOT intense, NOT commanding, NOT flirtatious"
)
TIMING = (
    "TIMING LOCK: spoken lines complete by 12.5 seconds; tail 12.5-15.0s gentle alive hold "
    "with subtle micro-expression — NOT frozen mannequin stillness, NOT audible exhale or sigh"
)
PAUSE = (
    "PAUSE LOCK: brief micro-pauses only (~0.3s) between statements — NOT sighs, NOT audible "
    "exhales, NOT dramatic waits, NOT dead air; b01: ZERO open pause — lip-sync Grüß Gott from "
    "frame one; b01 tail: NO heavy sigh, NO breathy exhale, NO falling pause at end; branches "
    "2-4 may use brief connector pause before first word only"
)
FACE = (
    "FACE LIFE LOCK: warm alive documentary host — natural micro-expressions, subtle eyebrow "
    "and smile shifts, organic breathing; NOT robotic, NOT uptight, NOT mannequin, NOT "
    "statue frozen hold"
)
B01_TAIL_BODY = (
    "B01 TAIL BODY LOCK: after final word upper body frozen — ZERO shrug, ZERO shoulder roll, "
    "ZERO shoulder drop, ZERO shoulder lift, ZERO gesture, ZERO repositioning; shoulders "
    "squared and still through handoff"
)
B01_TAIL_AUDIO = (
    "B01 TAIL AUDIO LOCK: lips closed after last word — ZERO sigh, ZERO breathy exhale, "
    "ZERO audible release, ZERO vocal fry, ZERO chest breath sound"
)


def _prod_dir(script: dict) -> Path:
    slug = script.get("slug", "branch_chain")
    return ROOT / "productions" / f"{slug}_longform_v1"


def _enrich_prompt(prompt: str, *, relaxed_host: bool = True, shot_id: str = "") -> str:
    if shot_id == "b01_intro":
        clauses = [EYELINE, PERSONA, B01_TAIL_BODY, B01_TAIL_AUDIO, PAUSE]
    else:
        clauses = [EYELINE, PERSONA, FACE, PAUSE, TIMING]
    if relaxed_host:
        clauses.append(RELAXED_HOST)
    for clause in clauses:
        if clause not in prompt:
            prompt = f"{prompt} ; {clause}"
    return prompt


def _timing_lock_for_shot(shot_id: str) -> str:
    if shot_id == "b01_intro":
        return (
            "TIMING LOCK: spoken lines complete by 12.5s; tail 12.5-15.0s frozen composed hold "
            "— NO sigh, NO shrug, NO shoulder movement, NO gesture at end"
        )
    if shot_id == "b02_role":
        return (
            "TIMING LOCK: spoken lines complete by 11.0s; tail 11.0-11.5s micro-hold only "
            "~0.5s then cut-ready — NOT 1s pause, NOT long end linger before b03; "
            "OPEN EXPRESSION LOCK: NO laugh, NO chuckle, NO giggle at branch open"
        )
    if shot_id == "b03_services":
        return (
            "TIMING LOCK: spoken lines complete by 12.5s; final beat subtle head shake into "
            "handoff — carry pose to b04"
        )
    return TIMING


def _enrich_shot_barebones(shot: dict) -> dict:
    shot_enriched = dict(shot)
    bb = dict(shot_enriched.get("barebones") or {})
    sc = str(bb.get("scene") or "")
    timing = _timing_lock_for_shot(str(shot.get("id") or ""))
    if EYELINE not in sc:
        bb["scene"] = f"{sc}; {EYELINE}; {timing}" if sc else f"{EYELINE}; {timing}"
    shot_enriched["barebones"] = bb
    return shot_enriched


def _generate_origin(
    client: Any,
    shot: dict,
    refs: dict,
    script: dict,
    prod_dir: Path,
    *,
    composite: Path,
    out_mp4: Path,
) -> tuple[str, Path, dict]:
    shot_enriched = _enrich_shot_barebones(shot)
    _api_pace()
    resp, req = generate_baked_composite_video(
        client, shot_enriched, refs, script, prod_dir, composite, duration=DURATION_S,
    )
    prompt = _enrich_prompt(req.get("prompt") or "", shot_id=str(shot.get("id") or ""))
    prompt_path = out_mp4.with_suffix(".prompt.txt")
    prompt_path.write_text(prompt, encoding="utf-8")
    _download(resp.url, out_mp4)
    return resp.url, out_mp4, {"prompt": prompt, "binding": req.get("binding")}


def _generate_branch(
    client: Any,
    shot: dict,
    refs: dict,
    script: dict,
    prod_dir: Path,
    *,
    handoff_frame: Path,
    origin_video_url: str,
    origin_composite: Path | None,
    prev_shot_id: str,
    out_mp4: Path,
    seed_mode: str,
) -> tuple[str, Path, dict]:
    shot_enriched = _enrich_shot_barebones(shot)
    staging_meta = (
        analyze_handoff_frame(handoff_frame)
        if seed_mode == BRANCH_CHAIN_STAGING_MODE
        else {}
    )
    _api_pace()
    resp, req = generate_branch_handoff_video(
        client,
        shot_enriched,
        refs,
        script,
        prod_dir,
        handoff_frame=handoff_frame,
        prev_shot_id=prev_shot_id,
        duration=DURATION_S,
        origin_video_url=origin_video_url,
        origin_composite=origin_composite,
        seed_mode=seed_mode,
    )
    prompt = _enrich_prompt(req.get("prompt") or "", shot_id=str(shot.get("id") or ""))
    prompt_path = out_mp4.with_suffix(".prompt.txt")
    prompt_path.write_text(prompt, encoding="utf-8")
    meta_path = out_mp4.with_suffix(".staging_meta.json")
    handoff_audit = {
        **staging_meta,
        "seed_mode": seed_mode,
        "handoff_from": prev_shot_id,
        "handoff_frame_local": str(handoff_frame),
    }
    if seed_mode == BRANCH_CHAIN_STAGING_MODE:
        handoff_audit["origin_video_url"] = origin_video_url
    meta_path.write_text(json.dumps(handoff_audit, indent=2), encoding="utf-8")
    _download(resp.url, out_mp4)
    binding = req.get("binding") or {}
    uploaded = binding.get("handoff_frame_uploaded", binding.get("staging_frame_uploaded", False))
    return resp.url, out_mp4, {
        "prompt": prompt,
        "binding": binding,
        "staging_meta": staging_meta or None,
        "handoff_frame_local": str(handoff_frame),
        "handoff_from": prev_shot_id,
        "handoff_frame_uploaded": uploaded,
        "seed_mode": seed_mode,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--from-branch", type=int, default=1, help="Resume from branch N (1-4)")
    parser.add_argument("--stitch-only", action="store_true")
    parser.add_argument("--force", action="store_true", help="Regenerate all branches (ignore cache)")
    args = parser.parse_args()

    script = normalize_script(json.loads(SCRIPT_PATH.read_text(encoding="utf-8")), SCRIPT_PATH)
    branch_cfg = script.get("config", {}).get("branch_chain") or {}
    seed_mode = resolve_branch_chain_seed_handoff(script)
    if seed_mode == BRANCH_CHAIN_STAGING_MODE and branch_cfg.get("staging_guide") not in (
        None,
        BRANCH_CHAIN_STAGING_MODE,
    ):
        raise SystemExit(
            f"branch_chain.staging_guide must be {BRANCH_CHAIN_STAGING_MODE!r} "
            f"(got {branch_cfg.get('staging_guide')!r})"
        )
    print(f"[branch] seed policy: {seed_mode}", flush=True)

    shots = script["shots"]
    prod_dir = _prod_dir(script)
    branch_dir = prod_dir / "branches"
    frames_dir = prod_dir / "branch_frames"
    out_dir = prod_dir / "output"
    branch_dir.mkdir(parents=True, exist_ok=True)
    frames_dir.mkdir(parents=True, exist_ok=True)
    out_dir.mkdir(parents=True, exist_ok=True)

    xfade_s = float(branch_cfg.get("xfade_s", 0.35))
    segments: list[Path] = []

    for shot in shots:
        seg = branch_dir / f"{shot['id']}_{DURATION_S}s.mp4"
        if seg.is_file() and seg.stat().st_size > 10000:
            segments.append(seg)

    if args.stitch_only:
        if len(segments) < len(shots):
            raise SystemExit(f"--stitch-only: need {len(shots)} branches, have {len(segments)}")
    else:
        client = xai_sdk.Client(api_key=_load_grok_token())
        refs = resolve_refs(script, client=client)
        composite = _resolve_composite_first_frame(script, prod_dir)
        if not composite:
            raise SystemExit("composite_first_frame missing for origin (b01)")

        state_path = prod_dir / "branch_chain_state.json"
        state: dict = {}
        if state_path.is_file():
            state = json.loads(state_path.read_text(encoding="utf-8"))

        locked_origin_url = str(state.get("origin_video_url") or "")
        if not locked_origin_url:
            b01_id = shots[0]["id"]
            locked_origin_url = str((state.get(b01_id) or {}).get("api_url") or "")
        origin_video_url = locked_origin_url
        staging_frame: Path | None = None

        start_idx = max(0, args.from_branch - 1)
        for i, shot in enumerate(shots[start_idx:], start=start_idx):
            sid = shot["id"]
            out_mp4 = branch_dir / f"{sid}_{DURATION_S}s.mp4"
            if (
                not args.force
                and out_mp4.is_file()
                and out_mp4.stat().st_size > 10000
            ):
                print(f"[branch] reuse {out_mp4.name} ({probe_duration(out_mp4):.2f}s)", flush=True)
                if i == 0 and not locked_origin_url:
                    locked_origin_url = str((state.get(sid) or {}).get("api_url") or "")
                    origin_video_url = locked_origin_url
                if i + 1 < len(shots):
                    handoff = frames_dir / f"{sid}_last_frame.jpg"
                    mandatory_extract_last_frame(out_mp4, handoff)
                    staging_frame = handoff
                if len(segments) <= i:
                    segments.append(out_mp4)
                continue

            branch_meta: dict = {}
            if i == 0:
                print(f"[branch] {i + 1}/4 ORIGIN {sid} ({DURATION_S}s) ← composite", flush=True)
                api_url, out_mp4, branch_meta = _generate_origin(
                    client, shot, refs, script, prod_dir,
                    composite=composite, out_mp4=out_mp4,
                )
                locked_origin_url = api_url
                origin_video_url = locked_origin_url
            else:
                prev = shots[i - 1]["id"]
                prev_mp4 = branch_dir / f"{prev}_{DURATION_S}s.mp4"
                staging_frame = frames_dir / f"{prev}_last_frame.jpg"
                mandatory_extract_last_frame(prev_mp4, staging_frame)
                if not locked_origin_url:
                    locked_origin_url = str(state.get("origin_video_url") or "")
                    if not locked_origin_url:
                        locked_origin_url = str(
                            (state.get(shots[0]["id"]) or {}).get("api_url") or ""
                        )
                if seed_mode == BRANCH_CHAIN_STAGING_MODE and not locked_origin_url:
                    raise SystemExit("MANDATORY origin_video_url missing — run b01 first")
                if seed_mode == BRANCH_CHAIN_LAST_FRAME_MODE:
                    print(
                        f"[branch] {i + 1}/4 BRANCH {sid} ({DURATION_S}s) "
                        f"← seed {staging_frame.name} (prev {prev} last frame)",
                        flush=True,
                    )
                else:
                    print(
                        f"[branch] {i + 1}/4 BRANCH {sid} ({DURATION_S}s) "
                        f"← staging {staging_frame.name} → prompt; "
                        f"origin={locked_origin_url[:56]}…",
                        flush=True,
                    )
                api_url, out_mp4, branch_meta = _generate_branch(
                    client, shot, refs, script, prod_dir,
                    handoff_frame=staging_frame,
                    origin_video_url=locked_origin_url,
                    origin_composite=composite if seed_mode == BRANCH_CHAIN_STAGING_MODE else None,
                    prev_shot_id=prev,
                    out_mp4=out_mp4,
                    seed_mode=seed_mode,
                )

            dur = probe_duration(out_mp4)
            handoff = frames_dir / f"{sid}_last_frame.jpg"
            mandatory_extract_last_frame(out_mp4, handoff)
            staging_frame = handoff
            state[sid] = {
                "api_url": api_url,
                "duration_s": dur,
                "handoff_frame_local": str(handoff),
                "branch_mode": seed_mode,
                **branch_meta,
            }
            if seed_mode == BRANCH_CHAIN_STAGING_MODE:
                state[sid]["origin_video_url"] = locked_origin_url
            if i == 0:
                state["origin_video_url"] = locked_origin_url
            elif (
                seed_mode == BRANCH_CHAIN_STAGING_MODE
                and state[sid].get("origin_video_url") != state.get("origin_video_url")
            ):
                raise SystemExit(
                    f"origin UUID drift on {sid}: branch origin != locked origin "
                    f"(star topology violated)"
                )
            state_path.write_text(json.dumps(state, indent=2), encoding="utf-8")
            print(f"[branch]   done {dur:.2f}s → {out_mp4.name}", flush=True)
            if len(segments) <= i:
                segments.append(out_mp4)
            else:
                segments[i] = out_mp4

    segments = [branch_dir / f"{s['id']}_{DURATION_S}s.mp4" for s in shots]
    for p in segments:
        if not p.is_file():
            raise SystemExit(f"missing branch: {p}")

    ver = branch_cfg.get("output_version", "v1")
    final = out_dir / f"{script['slug']}_branch_chain_4x15s_{ver}.mp4"
    work = branch_dir / "stitch_work"
    work.mkdir(parents=True, exist_ok=True)
    print(f"[stitch] joining {len(segments)} branches xfade={xfade_s}s", flush=True)
    concat_xfade_chain(segments, final, xfade_s=xfade_s, magenta_clamp=False, work_dir=work)
    total = probe_duration(final)

    report = {
        "at": datetime.now(timezone.utc).isoformat(),
        "slug": script["slug"],
        "branches": [str(p) for p in segments],
        "xfade_s": xfade_s,
        "output": str(final),
        "duration_s": round(total, 3),
        "expected_s": DURATION_S * len(shots) - xfade_s * (len(shots) - 1),
        "seed_mode": seed_mode,
        "staging_policy": (
            "prev branch last frame → upload → image_file_id chain seed"
            if seed_mode == BRANCH_CHAIN_LAST_FRAME_MODE
            else "last frame → analyze locally → prompt only → star composite seed"
        ),
        "topology": (
            "sequential_last_frame"
            if seed_mode == BRANCH_CHAIN_LAST_FRAME_MODE
            else "star_from_origin_composite"
        ),
    }
    (prod_dir / "branch_chain_report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(f"[stitch] → {final} ({total:.2f}s)", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())