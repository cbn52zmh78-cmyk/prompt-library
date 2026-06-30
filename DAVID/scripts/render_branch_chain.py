#!/usr/bin/env python3
"""General branch chain — seed policy from script branch_chain.seed_handoff.

last_frame:
  b01 ← composite_first_frame; bN ← upload b(N-1) last frame as image_file_id seed.

last_frame_prompt_only:
  last frame = prompt staging only; star-seed from origin composite.

Usage:
  python render_branch_chain.py path/to/script.json [--force] [--from-branch N] [--stitch-only]

Duration:
  Default segment length = branch_chain.segment_s in script config (fallback: 15).
  Per-shot override: set shot.duration in the JSON.

  # NATIVE_LONG_SEGMENT: when xAI lifts the generation cap, replace the duration=
  # argument in _generate_origin / _generate_branch with shot.duration directly
  # (e.g. duration=300). The loop, staging, and stitch logic are unchanged.
"""
from __future__ import annotations

import argparse
import json
import subprocess
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
    MIN_XFADE_S,
    _api_pace,
    _download,
    _ffmpeg_exe,
    _load_grok_token,
    _resolve_composite_first_frame,
    analyze_handoff_frame,
    apply_grade_hold_light,
    apply_living_room_skin_recovery,
    concat_xfade_chain,
    generate_baked_composite_video,
    generate_branch_handoff_video,
    mandatory_extract_last_frame,
    normalize_script,
    probe_magenta_score,
    resolve_branch_chain_seed_handoff,
    probe_duration,
    resolve_refs,
    _resolve_composite_first_frame,
)

EYELINE = (
    "EYE LINE LOCK: pupils centered on camera lens throughout — never off-camera left/right, "
    "never interview eyeline, never downstage void"
)
PERSONA = (
    "VOICE PERSONA LOCK: MATILDA — relaxed laid-back friendly inviting host; soft gentle warm "
    "voice; NATIVE Münchner Bayerisch accent on every English and German word; Munich-born "
    "rhythm and vowels; genuinely enjoys her work; must NOT sound American, NOT General "
    "American, NOT network news anchor, NOT CNN, NOT corporate commander"
)
RELAXED_HOST = (
    "RELAXED HOST LOCK: conversational hospitality — warm, inviting, easygoing business host "
    "who enjoys selling Stonebridge; NOT authoritative, NOT intense, NOT commanding, NOT flirtatious"
)
TIMING = (
    "TIMING LOCK: spoken lines complete by {wrap}s; tail {wrap}–{seg}s gentle alive hold "
    "with subtle micro-expression — NOT frozen mannequin stillness, NOT audible exhale or sigh"
)
PAUSE = (
    "PAUSE LOCK: brief micro-pauses only (~0.3s) between statements — NOT sighs, NOT audible "
    "exhales, NOT dramatic waits, NOT dead air; b01: ZERO open pause — lip-sync from frame one; "
    "b01 tail: NO heavy sigh, NO breathy exhale, NO falling pause at end; "
    "branches 2-N may use brief connector pause before first word only"
)
FACE = (
    "FACE LIFE LOCK: warm alive documentary host — natural micro-expressions, subtle eyebrow "
    "and smile shifts, organic breathing; NOT robotic, NOT uptight, NOT mannequin, NOT "
    "statue frozen hold"
)
WARDROBE = (
    "WARDROBE LOCK: identical outfit entire episode per Plates/2.jpg — gray sleeveless "
    "jumpsuit with sweetheart neckline and wide-leg trousers, black belt with silver "
    "rectangular buckle, black ankle boots, large silver filigree statement earrings, "
    "blonde hair in low ponytail — ONE piece gray jumpsuit only; NO black dress, NO "
    "sweater, NO cardigan, NO separate top layer; match chain seed pixels exactly; ZERO "
    "wardrobe change, ZERO outfit swap"
)
GRADE_CONTINUITY = (
    "GRADE CONTINUITY LOCK: skin tone and lighting must match kitchen branches b01-b04 exactly — "
    "same natural warm-neutral key light, same fair skin midtones; no color cast shift of any kind; "
    "no beauty filter; do NOT shift cool, do NOT shift blue, do NOT desaturate skin"
)
SKIN_GRADE_LATE = (
    "SKIN GRADE LOCK: skin and walls match kitchen b01-b04 grade exactly — "
    "same warm-neutral key light, same natural fair complexion; no pink cast, no purple cast, "
    "no cool shift, no blue shift; continuous grade from kitchen branches"
)
MUTE_SCORE = (
    "AUDIO SILENCE LOCK: zero music, zero score, zero underscore, zero sting, zero bed — "
    "voice only through entire branch including tail"
)
ANTI_DOWNSTAGE = (
    "ANTI-DOWNSTAGE LOCK: living room is UPSTAGE STAGE-LEFT behind her — NEVER walk toward "
    "camera, NEVER walk downstage, NEVER into downstage void; path is stage-left then upstage "
    "to sofa against back wall"
)


def _shot_duration(shot: dict, default: int) -> int:
    """Per-shot duration with fallback to segment default.

    # NATIVE_LONG_SEGMENT: remove the min() clamp below once xAI lifts the cap.
    # Native call: client.video.generate(duration=shot.get("duration") or default, ...)
    """
    return int(shot.get("duration") or default)


def _timing_lock(seg_s: int) -> str:
    wrap = max(1, seg_s - 3)
    return TIMING.format(wrap=wrap, seg=seg_s)


def _prod_dir(script: dict) -> Path:
    slug = script.get("slug", "branch_chain")
    return ROOT / "productions" / f"{slug}_longform_v1"


def _enrich_prompt(prompt: str, *, relaxed_host: bool = True, seg_s: int = 15) -> str:
    clauses = [EYELINE, PERSONA, FACE, PAUSE, MUTE_SCORE, _timing_lock(seg_s)]
    if relaxed_host:
        clauses.append(RELAXED_HOST)
    for clause in clauses:
        if clause not in prompt:
            prompt = f"{prompt} ; {clause}"
    return prompt


def _wardrobe_lock(script: dict) -> str:
    cfg = script.get("config") or {}
    return str(cfg.get("wardrobe_lock") or WARDROBE)


def _enrich_shot_barebones(shot: dict, seg_s: int, script: dict | None = None) -> dict:
    shot_enriched = dict(shot)
    bb = dict(shot_enriched.get("barebones") or {})
    sc = str(bb.get("scene") or "")
    timing = _timing_lock(seg_s)
    wardrobe = _wardrobe_lock(script or {})
    setting = str(shot.get("setting") or "")
    scene_bits = [sc] if sc else []
    for clause in (wardrobe, EYELINE, timing):
        if clause not in sc:
            scene_bits.append(clause)
    if setting == "transition_kitchen_to_living" and ANTI_DOWNSTAGE not in sc:
        scene_bits.append(ANTI_DOWNSTAGE)
    bb["scene"] = "; ".join(scene_bits)
    st = str(bb.get("style") or "")
    if setting in ("transition_kitchen_to_living", "living_room") and GRADE_CONTINUITY not in st:
        bb["style"] = f"{st}; {GRADE_CONTINUITY}" if st else GRADE_CONTINUITY
    shot_id = str(shot.get("id") or "")
    if shot_id in ("b07_network", "b08_close_de"):
        if SKIN_GRADE_LATE not in st:
            bb["style"] = f"{bb.get('style') or st}; {SKIN_GRADE_LATE}"
    amb = bb.get("audio") if isinstance(bb.get("audio"), dict) else {}
    amb_str = str(amb.get("ambient") or "")
    if MUTE_SCORE.split(":")[0] not in amb_str:
        amb = dict(amb)
        amb["ambient"] = f"{amb_str}; {MUTE_SCORE}" if amb_str else MUTE_SCORE
        bb["audio"] = amb
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
    seg_s: int,
) -> tuple[str, Path, dict]:
    dur = _shot_duration(shot, seg_s)
    shot_enriched = _enrich_shot_barebones(shot, dur, script)
    _api_pace()
    resp, req = generate_baked_composite_video(
        client, shot_enriched, refs, script, prod_dir, composite,
        duration=dur,  # NATIVE_LONG_SEGMENT: swap with native cap when available
    )
    prompt = _enrich_prompt(req.get("prompt") or "", seg_s=dur)
    out_mp4.with_suffix(".prompt.txt").write_text(prompt, encoding="utf-8")
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
    seg_s: int,
    seed_mode: str,
) -> tuple[str, Path, dict]:
    dur = _shot_duration(shot, seg_s)
    staging_meta = (
        analyze_handoff_frame(handoff_frame)
        if seed_mode == BRANCH_CHAIN_STAGING_MODE
        else {}
    )
    shot_enriched = _enrich_shot_barebones(shot, dur, script)
    _api_pace()
    resp, req = generate_branch_handoff_video(
        client,
        shot_enriched,
        refs,
        script,
        prod_dir,
        handoff_frame=handoff_frame,
        prev_shot_id=prev_shot_id,
        duration=dur,  # NATIVE_LONG_SEGMENT: swap with native cap when available
        origin_video_url=origin_video_url,
        origin_composite=origin_composite,
        seed_mode=seed_mode,
    )
    prompt = _enrich_prompt(req.get("prompt") or "", seg_s=dur)
    out_mp4.with_suffix(".prompt.txt").write_text(prompt, encoding="utf-8")
    handoff_audit = {
        **staging_meta,
        "seed_mode": seed_mode,
        "handoff_from": prev_shot_id,
        "handoff_frame_local": str(handoff_frame),
    }
    if seed_mode == BRANCH_CHAIN_STAGING_MODE:
        handoff_audit["origin_video_url"] = origin_video_url
    out_mp4.with_suffix(".staging_meta.json").write_text(
        json.dumps(handoff_audit, indent=2), encoding="utf-8"
    )
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


def _concat_reencode(segments: list[Path], out: Path) -> None:
    """Re-encode concat via FFmpeg concat filter — eliminates first-frame flash
    that occurs with stream-copy hard cuts between Grok-generated clips."""
    ff = _ffmpeg_exe()
    n = len(segments)
    inputs: list[str] = []
    for seg in segments:
        inputs += ["-i", str(seg)]
    video_chain = "".join(f"[{i}:v]" for i in range(n))
    audio_chain = "".join(f"[{i}:a]" for i in range(n))
    filtergraph = (
        f"{video_chain}concat=n={n}:v=1:a=0[vout];"
        f"{audio_chain}concat=n={n}:v=0:a=1[aout]"
    )
    subprocess.run(
        [
            ff, "-y", *inputs,
            "-filter_complex", filtergraph,
            "-map", "[vout]", "-map", "[aout]",
            "-c:v", "libx264", "-preset", "fast", "-crf", "18",
            "-c:a", "aac", "-b:a", "192k",
            str(out),
        ],
        check=True,
        capture_output=True,
    )


def _resolve_color_anchor(
    prod_dir: Path,
    script: dict,
    branch_cfg: dict,
) -> Path | None:
    """Grade anchor — explicit shot last frame (e.g. b04 kitchen) or composite for b01."""
    frames_dir = prod_dir / "branch_frames"
    anchor_shot = str(branch_cfg.get("color_anchor_shot") or "b01_intro")

    if anchor_shot != "b01_intro":
        direct = frames_dir / f"{anchor_shot}_last_frame.jpg"
        if direct.is_file():
            return direct
        matches = sorted(frames_dir.glob(f"{anchor_shot}*_last_frame.jpg"))
        if matches:
            return matches[0]

    composite = _resolve_composite_first_frame(script, prod_dir)
    if composite and composite.is_file():
        return composite
    direct = frames_dir / f"{anchor_shot}_last_frame.jpg"
    if direct.is_file():
        return direct
    matches = sorted(frames_dir.glob(f"{anchor_shot}*_last_frame.jpg"))
    return matches[0] if matches else None


def _should_clamp_branch(sid: str, branch_cfg: dict) -> bool:
    if branch_cfg.get("color_clamp_all") or branch_cfg.get("color_hold") == "all":
        return True
    clamp_ids = branch_cfg.get("color_clamp_shots")
    if clamp_ids is None:
        return False
    return sid in clamp_ids


def _maybe_clamp_branch_color(
    shot: dict,
    mp4: Path,
    prod_dir: Path,
    branch_cfg: dict,
    script: dict,
) -> None:
    """Light grade hold — living-room branches only, histogram pull to kitchen anchor."""
    sid = str(shot.get("id") or "")
    if not _should_clamp_branch(sid, branch_cfg):
        return
    anchor = _resolve_color_anchor(prod_dir, script, branch_cfg)
    if anchor is None or not anchor.is_file():
        print(f"[clamp] skip {sid}: color anchor missing", flush=True)
        return
    before = probe_magenta_score(mp4)
    tmp = mp4.with_name(f"{mp4.stem}_clamped.mp4")
    recovery_ids = branch_cfg.get("color_recovery_shots") or []
    if sid in recovery_ids:
        apply_living_room_skin_recovery(mp4, tmp, anchor)
    else:
        apply_grade_hold_light(mp4, tmp, anchor)
    tmp.replace(mp4)
    after = probe_magenta_score(mp4)
    print(
        f"[clamp] {sid} anchor={anchor.name} magenta {before:.3f}→{after:.3f}",
        flush=True,
    )


def _restore_branches_from_api(
    shots: list[dict],
    prod_dir: Path,
    segment_s: int,
) -> None:
    """Re-download raw Grok MP4s from branch_chain_state — undoes destructive local clamp."""
    state_path = prod_dir / "branch_chain_state.json"
    if not state_path.is_file():
        raise SystemExit("--restore-api: branch_chain_state.json missing")
    state = json.loads(state_path.read_text(encoding="utf-8"))
    branch_dir = prod_dir / "branches"
    for shot in shots:
        sid = shot["id"]
        api_url = str((state.get(sid) or {}).get("api_url") or "")
        if not api_url:
            raise SystemExit(f"--restore-api: no api_url for {sid}")
        dur = _shot_duration(shot, segment_s)
        mp4 = branch_dir / f"{sid}_{dur}s.mp4"
        print(f"[restore] {sid} ← api", flush=True)
        _download(api_url, mp4)
        for marker in branch_dir.glob(f"{sid}_{dur}s*.clamp244.json"):
            marker.unlink(missing_ok=True)


def _clamp_existing_branches(
    shots: list[dict],
    prod_dir: Path,
    branch_cfg: dict,
    segment_s: int,
    script: dict,
) -> None:
    branch_dir = prod_dir / "branches"
    for shot in shots:
        sid = shot["id"]
        if not _should_clamp_branch(sid, branch_cfg):
            continue
        dur = _shot_duration(shot, segment_s)
        mp4 = branch_dir / f"{sid}_{dur}s.mp4"
        if not mp4.is_file():
            raise SystemExit(f"--clamp-only: missing branch {mp4}")
        _maybe_clamp_branch_color(shot, mp4, prod_dir, branch_cfg, script)
        handoff = prod_dir / "branch_frames" / f"{sid}_last_frame.jpg"
        mandatory_extract_last_frame(mp4, handoff)


def _loudnorm_pass(path: Path) -> None:
    """EBU R128 loudness normalization on the final stitched file (audio-only re-encode).
    Fixes per-branch audio level variance from Grok generation (audio blasts at stitch points)."""
    ff = _ffmpeg_exe()
    tmp = path.parent / (path.stem + "_loudnorm_tmp" + path.suffix)
    subprocess.run(
        [
            ff, "-y", "-i", str(path),
            "-c:v", "copy",
            "-af", "loudnorm=I=-16:TP=-1.5:LRA=11",
            "-c:a", "aac", "-b:a", "192k",
            str(tmp),
        ],
        check=True,
        capture_output=True,
    )
    tmp.replace(path)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Branch chain pipeline — arbitrary shot count, staging-guide policy."
    )
    parser.add_argument("script", help="Path to branch chain script JSON")
    parser.add_argument(
        "--from-branch", type=int, default=1,
        help="Resume from branch N (1-indexed, default: 1)",
    )
    parser.add_argument("--stitch-only", action="store_true")
    parser.add_argument(
        "--clamp-only",
        action="store_true",
        help="FFmpeg grade-hold configured branches to kitchen anchor, then stitch",
    )
    parser.add_argument(
        "--restore-api",
        action="store_true",
        help="Re-download raw Grok branches from branch_chain_state (undo local clamp)",
    )
    parser.add_argument("--force", action="store_true", help="Regenerate all branches (ignore cache)")
    args = parser.parse_args()

    script_path = Path(args.script)
    if not script_path.is_absolute():
        script_path = Path.cwd() / script_path
    if not script_path.is_file():
        raise SystemExit(f"Script not found: {script_path}")

    script = normalize_script(json.loads(script_path.read_text(encoding="utf-8")), script_path)
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

    # Default segment duration from script config; per-shot override via shot.duration
    segment_s: int = int(branch_cfg.get("segment_s") or 15)

    shots = script["shots"]
    n_shots = len(shots)
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
        dur = _shot_duration(shot, segment_s)
        seg = branch_dir / f"{shot['id']}_{dur}s.mp4"
        if seg.is_file() and seg.stat().st_size > 10000:
            segments.append(seg)

    if args.restore_api:
        _restore_branches_from_api(shots, prod_dir, segment_s)
        frames_dir = prod_dir / "branch_frames"
        for shot in shots:
            sid = shot["id"]
            dur = _shot_duration(shot, segment_s)
            mp4 = branch_dir / f"{sid}_{dur}s.mp4"
            mandatory_extract_last_frame(mp4, frames_dir / f"{sid}_last_frame.jpg")
        print("[restore] all branches + handoff frames refreshed from API", flush=True)

    if args.clamp_only:
        anchor = _resolve_color_anchor(prod_dir, script, branch_cfg)
        if anchor is None:
            raise SystemExit("--clamp-only: color anchor missing (b04 last frame or composite)")
        clamp_targets = [s["id"] for s in shots if _should_clamp_branch(s["id"], branch_cfg)]
        print(
            f"[clamp] grade hold {clamp_targets or 'none'} → anchor {anchor.name}",
            flush=True,
        )
        _clamp_existing_branches(shots, prod_dir, branch_cfg, segment_s, script)
        args.stitch_only = True

    if args.stitch_only:
        if len(segments) < n_shots:
            raise SystemExit(f"--stitch-only: need {n_shots} branches, have {len(segments)}")
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

        b01_last_frame_path = frames_dir / f"{shots[0]['id']}_last_frame.jpg"

        start_idx = max(0, args.from_branch - 1)
        for i, shot in enumerate(shots[start_idx:], start=start_idx):
            sid = shot["id"]
            dur = _shot_duration(shot, segment_s)
            out_mp4 = branch_dir / f"{sid}_{dur}s.mp4"

            if not args.force and out_mp4.is_file() and out_mp4.stat().st_size > 10000:
                print(
                    f"[branch] reuse {out_mp4.name} ({probe_duration(out_mp4):.2f}s)", flush=True
                )
                if i == 0 and not locked_origin_url:
                    locked_origin_url = str((state.get(sid) or {}).get("api_url") or "")
                    origin_video_url = locked_origin_url
                if i + 1 < n_shots:
                    handoff = frames_dir / f"{sid}_last_frame.jpg"
                    mandatory_extract_last_frame(out_mp4, handoff)
                    staging_frame = handoff
                if len(segments) <= i:
                    segments.append(out_mp4)
                continue

            branch_meta: dict = {}
            if i == 0:
                print(
                    f"[branch] {i + 1}/{n_shots} ORIGIN {sid} ({dur}s) ← composite",
                    flush=True,
                )
                api_url, out_mp4, branch_meta = _generate_origin(
                    client, shot, refs, script, prod_dir,
                    composite=composite, out_mp4=out_mp4, seg_s=segment_s,
                )
                locked_origin_url = api_url
                origin_video_url = locked_origin_url
                # Extract B01 last frame — B02 staging guide (prompt only, not image seed).
                mandatory_extract_last_frame(out_mp4, b01_last_frame_path)
                print(
                    f"[branch]   b01 last frame extracted → B02 staging: {b01_last_frame_path.name}",
                    flush=True,
                )
            else:
                prev = shots[i - 1]["id"]
                prev_dur = _shot_duration(shots[i - 1], segment_s)
                prev_mp4 = branch_dir / f"{prev}_{prev_dur}s.mp4"
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
                if not staging_frame.is_file():
                    raise SystemExit(
                        f"handoff frame missing: {staging_frame} — "
                        "previous branch must complete before this one"
                    )
                if seed_mode == BRANCH_CHAIN_LAST_FRAME_MODE:
                    print(
                        f"[branch] {i + 1}/{n_shots} BRANCH {sid} ({dur}s) "
                        f"← seed {staging_frame.name} (prev {prev} last frame)",
                        flush=True,
                    )
                else:
                    print(
                        f"[branch] {i + 1}/{n_shots} BRANCH {sid} ({dur}s) "
                        f"← staging {staging_frame.name} → prompt; "
                        f"seed={composite.name}; origin={locked_origin_url[:56]}…",
                        flush=True,
                    )
                api_url, out_mp4, branch_meta = _generate_branch(
                    client, shot, refs, script, prod_dir,
                    handoff_frame=staging_frame,
                    origin_video_url=locked_origin_url,
                    origin_composite=composite if seed_mode == BRANCH_CHAIN_STAGING_MODE else None,
                    prev_shot_id=prev,
                    out_mp4=out_mp4,
                    seg_s=segment_s,
                    seed_mode=seed_mode,
                )

            _maybe_clamp_branch_color(shot, out_mp4, prod_dir, branch_cfg, script)
            actual_dur = probe_duration(out_mp4)
            handoff = frames_dir / f"{sid}_last_frame.jpg"
            mandatory_extract_last_frame(out_mp4, handoff)
            staging_frame = handoff
            state[sid] = {
                "api_url": api_url,
                "duration_s": actual_dur,
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
            print(f"[branch]   done {actual_dur:.2f}s → {out_mp4.name}", flush=True)
            if len(segments) <= i:
                segments.append(out_mp4)
            else:
                segments[i] = out_mp4

    # Rebuild segment list in shot order (handles partial cache + force combos)
    segments = [branch_dir / f"{s['id']}_{_shot_duration(s, segment_s)}s.mp4" for s in shots]
    for p in segments:
        if not p.is_file():
            raise SystemExit(f"missing branch: {p}")

    ver = branch_cfg.get("output_version", "v1")
    final = out_dir / f"{script['slug']}_branch_chain_{n_shots}x{segment_s}s_{ver}.mp4"
    work = branch_dir / "stitch_work"
    work.mkdir(parents=True, exist_ok=True)
    join_mode = "hard_cut" if xfade_s < MIN_XFADE_S else "xfade"
    print(f"[stitch] joining {n_shots} branches mode={join_mode} xfade={xfade_s}s", flush=True)
    if xfade_s < MIN_XFADE_S:
        _concat_reencode(segments, final)
    else:
        concat_xfade_chain(segments, final, xfade_s=xfade_s, magenta_clamp=False, work_dir=work)
    print("[stitch] loudnorm pass…", flush=True)
    _loudnorm_pass(final)
    total = probe_duration(final)

    total_seg_s = sum(_shot_duration(s, segment_s) for s in shots)
    expected_s = total_seg_s - xfade_s * (n_shots - 1)

    report = {
        "at": datetime.now(timezone.utc).isoformat(),
        "slug": script["slug"],
        "n_shots": n_shots,
        "segment_s_default": segment_s,
        "branches": [str(p) for p in segments],
        "xfade_s": xfade_s,
        "join_mode": join_mode,
        "output": str(final),
        "duration_s": round(total, 3),
        "expected_s": round(expected_s, 3),
        "seed_mode": seed_mode,
        "staging_policy": (
            "prev branch last frame → upload → image_file_id chain seed"
            if seed_mode == BRANCH_CHAIN_LAST_FRAME_MODE
            else "last frame → analyze locally → prompt only → b01 composite image seed"
        ),
        "topology": (
            "sequential_last_frame"
            if seed_mode == BRANCH_CHAIN_LAST_FRAME_MODE
            else "star_from_origin_composite"
        ),
        "script": str(script_path),
    }
    (prod_dir / "branch_chain_report.json").write_text(
        json.dumps(report, indent=2), encoding="utf-8"
    )
    print(f"[stitch] → {final} ({total:.2f}s)", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
