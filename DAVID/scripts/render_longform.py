#!/usr/bin/env python3
"""DAVID long-form video assembler — arbitrary shot-count concat pipeline.

Generalizes render_post*.py / render_sample_videos.py per
STUDIO/Techniques/STUDIO_LongForm_Video_Assembly_v1.md.

Usage:
    python render_longform.py <script.json>
    python render_longform.py <script.json> --concat-only
    python render_longform.py <script.json> --script-only
    python render_longform.py <script.json> --force-shot 03_host_pie_line

Input: script JSON with shots[] + config + provenance_card (imagine-pack schema).
Output: productions/<slug>/ → shots/, output/*.mp4, imagine_pack.json, qa_report.json
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import textwrap
import time
import urllib.request
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_LOCK = ROOT / "productions" / "host_identity_v1" / "david_identity_lock.json"
FFMPEG: str | None = None

SYNTHETIC_GUARD = "synthetic host only"
DEFAULT_VOICE_SUFFIX = (
    "mid-low resonant unhurried voice, precise diction, documentary gravitas, "
    "Attenborough-calm, accessible never stuffy, synthetic host only"
)
DEFAULT_CONTINUITY_PREFIX = (
    "CONTINUITY LOCK @David-001: identical host face, charcoal sweater, Archive desk, "
    "brass lamp, same eye-line — seamless continuation of prior take, zero jump cut."
)
DEFAULT_END_GUARD = (
    "Finish on gesture peak (hand motion or lean), never hold dead stillness or dead frame."
)
HOST_PERFORMANCE_NAME = "host_performance_extend.mp4"
API_PACE_S = 1.25  # xAI video rate limit ~1 req/s


def _load_grok_token() -> str:
    auth_path = Path.home() / ".grok" / "auth.json"
    if not auth_path.is_file():
        raise RuntimeError("No ~/.grok/auth.json — run grok login or set XAI_API_KEY")
    data = json.loads(auth_path.read_text(encoding="utf-8"))
    entry = next(iter(data.values()))
    token = entry.get("key") or entry.get("access_token")
    if not token:
        raise RuntimeError("Grok auth.json has no token")
    return token


def _ffmpeg_exe() -> str:
    global FFMPEG
    if FFMPEG:
        return FFMPEG
    try:
        import imageio_ffmpeg

        FFMPEG = imageio_ffmpeg.get_ffmpeg_exe()
    except ImportError:
        FFMPEG = "ffmpeg"
    return FFMPEG


def _download(url: str, dest: Path) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    req = urllib.request.Request(url, headers={"User-Agent": "DAVID-longform/1.0"})
    with urllib.request.urlopen(req, timeout=300) as r:
        dest.write_bytes(r.read())


def _api_pace() -> None:
    time.sleep(API_PACE_S)


def load_identity_lock(path: Path) -> dict[str, Any]:
    if not path.is_file():
        raise RuntimeError(f"Identity lock not found: {path}")
    lock = json.loads(path.read_text(encoding="utf-8"))
    if lock.get("status") != "LOCKED":
        raise RuntimeError(f"Identity lock status is not LOCKED: {path}")
    return lock


def _resolve_david_path(rel: str) -> Path:
    rel = str(rel).replace("\\", "/")
    if rel.startswith("DAVID/"):
        rel = rel[6:]
    p = Path(rel)
    return p if p.is_absolute() else (ROOT / p)


def _normalize_shot_list(shots: list[dict[str, Any]]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    t = 0
    for s in shots:
        shot = {**s}
        if "shot_id" in shot and "id" not in shot:
            shot["id"] = shot.pop("shot_id")
        timing = shot.pop("timing", None) or {}
        dur = shot.get("duration", 0)
        shot.setdefault("t_start", timing.get("start_s", t))
        shot.setdefault("t_end", timing.get("end_s", t + dur))
        t = int(shot["t_end"])
        speech = shot.get("speech_text", "")
        prompt = shot.get("video_prompt", "")
        if speech and speech not in prompt:
            shot["video_prompt"] = f'{prompt.rstrip()} Lip-synced, delivers: "{speech}"'
        out.append(shot)
    return out


def normalize_script(raw: dict[str, Any], script_path: Path) -> dict[str, Any]:
    """Accept longform schema, channel-intro shape, or legacy post01/sample script."""
    if "config" in raw and "shots" in raw:
        raw["shots"] = _normalize_shot_list(raw["shots"])
        return raw

    # Channel intro / alternate longform shape (shot_id, host_identity, closing_card)
    if "shots" in raw and any("shot_id" in s for s in raw["shots"]):
        slug = raw.get("slug", script_path.stem.replace("_script", ""))
        lock_rel = raw.get("host_identity") or raw.get("identity_lock", "productions/host_identity_v1/david_identity_lock.json")
        avatar_rel = (raw.get("avatar") or {}).get("reference", "")
        closing = raw.get("closing_card", {})
        voice = raw.get("voice_suffix", DEFAULT_VOICE_SUFFIX)
        if "synthetic" not in voice.lower():
            voice = f"{voice}, {SYNTHETIC_GUARD}"

        cfg: dict[str, Any] = {
            "model_video": raw.get("model_video", "grok-imagine-video-1.5"),
            "resolution": raw.get("resolution", "720p"),
            "aspect_ratio": raw.get("aspect_ratio", "16:9"),
            "identity_lock": str(_resolve_david_path(lock_rel)),
            "voice_suffix": voice,
        }
        if avatar_rel:
            cfg["avatar_reference"] = str(_resolve_david_path(avatar_rel))

        out: dict[str, Any] = {
            "slug": slug,
            "title": raw.get("title", slug),
            "target_seconds": raw.get("target_seconds"),
            "config": cfg,
            "shots": _normalize_shot_list(raw["shots"]),
            "provenance_card": {
                "enabled": closing.get("type") != "none",
                "card_type": "closing",
                "duration_s": closing.get("duration_s", 6),
                "banner": "",
                "title": closing.get("text", "DAVID · The Archive"),
                "subtitle": closing.get("subtext", ""),
                "lines": [],
                "footer": raw.get("cta", ""),
            },
            "guardrails": raw.get("guardrails", []),
            "qa_rules": {
                "require_identity_lock": True,
                "require_synthetic_guard": True,
                "require_reconstructed_labels": False,
                "min_shots": 1,
            },
        }
        if raw.get("seamless"):
            out["seamless"] = raw["seamless"]
            cfg["seamless"] = raw["seamless"]
        if raw.get("continuity_prefix"):
            out["continuity_prefix"] = raw["continuity_prefix"]
        if raw.get("end_guard"):
            out["end_guard"] = raw["end_guard"]
        if raw.get("compare_v1"):
            out["compare_v1"] = raw["compare_v1"]
        return out

    slug = raw.get("slug", script_path.stem)
    cfg: dict[str, Any] = {
        "model_video": "grok-imagine-video-1.5",
        "resolution": "720p",
        "aspect_ratio": "16:9",
        "identity_lock": str(raw.get("identity_lock", DEFAULT_LOCK)),
        "voice_suffix": DEFAULT_VOICE_SUFFIX,
    }
    if raw.get("host_reference"):
        cfg["avatar_reference"] = raw["host_reference"]

    prov = raw.get("provenance", {})
    title = raw.get("title", slug)
    banner = "RECONSTRUCTED — NOT ATTESTED"
    if raw.get("text_confidence") == "attested":
        banner = "ATTESTED TEXT · RECONSTRUCTED PRONUNCIATION"

    lines = []
    if prov.get("text"):
        lines.append(f"TEXT: {prov['text']}")
    if prov.get("pronunciation"):
        lines.append(f"PRONUNCIATION: {prov['pronunciation']}")
    if raw.get("line_ipa"):
        lines.append(f"IPA: {raw['line_ipa']}")
    if raw.get("translation"):
        lines.append(f"TRANSLATION: {raw['translation']}")
    if raw.get("reconstructed_text"):
        lines.append(f"LINE: {raw['reconstructed_text']}")
    if raw.get("attested_text"):
        lines.append(f"LINE: {raw['attested_text']}")
    if prov.get("citation"):
        lines.append(f"CITATION: {prov['citation']}")
    if prov.get("sources"):
        lines.append(f"SOURCES: {prov['sources']}")
    if prov.get("brain_scrape"):
        lines.append(f"BRAIN: {prov['brain_scrape']}")

    return {
        **{k: v for k, v in raw.items() if k not in ("shots", "provenance")},
        "slug": slug,
        "title": title,
        "config": cfg,
        "shots": _normalize_shot_list(raw.get("shots", [])),
        "provenance": prov,
        "provenance_card": {
            "enabled": True,
            "duration_s": 7,
            "banner": banner,
            "title": "DAVID · PROVENANCE",
            "subtitle": title,
            "lines": lines or [title],
            "footer": raw.get("on_screen_labels", {}).get("text", "DAVID"),
        },
        "qa_rules": {
            "require_identity_lock": True,
            "require_synthetic_guard": True,
            "min_shots": 1,
        },
    }


def resolve_production_dir(script: dict[str, Any]) -> Path:
    if script.get("production_dir"):
        p = Path(script["production_dir"])
        return p if p.is_absolute() else (ROOT / p)
    slug = script.get("slug", "longform")
    return ROOT / "productions" / f"{slug}_longform_v1"


def resolve_refs(script: dict[str, Any]) -> dict[str, Any]:
    cfg = script.setdefault("config", {})
    lock_raw = cfg.get("identity_lock", DEFAULT_LOCK)
    lock_path = Path(lock_raw) if Path(str(lock_raw)).is_absolute() else _resolve_david_path(str(lock_raw))
    lock = load_identity_lock(lock_path) if cfg.get("use_identity_lock", True) else {}

    avatar_url = cfg.get("avatar_url")
    avatar_file = cfg.get("avatar_reference")
    set_file = cfg.get("set_reference")
    voice_suffix = cfg.get("voice_suffix") or lock.get("voice", {}).get("prompt_suffix") or DEFAULT_VOICE_SUFFIX

    if lock:
        avatar_url = avatar_url or lock["references"]["david_avatar"].get("url")
        avatar_file = avatar_file or lock["references"]["david_avatar"].get("file")
        set_file = set_file or lock["references"]["archive_set"].get("file")
        if not avatar_url:
            raise RuntimeError(
                "Avatar URL missing from identity lock — re-run render_host_identity.py"
            )

    return {
        "lock": lock,
        "lock_path": lock_path,
        "avatar_url": avatar_url,
        "avatar_file": avatar_file,
        "set_file": set_file,
        "voice_suffix": voice_suffix,
        "model_video": cfg.get("model_video", "grok-imagine-video-1.5"),
        "resolution": cfg.get("resolution", "720p"),
    }


def ensure_voice_in_prompt(prompt: str, voice_suffix: str) -> str:
    if voice_suffix.lower() not in prompt.lower():
        prompt = f"{prompt.rstrip()} {voice_suffix}"
    if SYNTHETIC_GUARD.lower() not in prompt.lower():
        prompt = f"{prompt.rstrip()} {SYNTHETIC_GUARD}"
    return prompt


def build_imagine_pack(
    script: dict[str, Any],
    refs: dict[str, Any],
    seamless_opts: SeamlessOptions | None = None,
) -> dict[str, Any]:
    shots = script["shots"]
    prov = script.get("provenance_card", {})
    use_seamless = seamless_opts and seamless_opts.enabled
    return {
        "slug": script.get("slug"),
        "title": script.get("title"),
        "model_video": refs["model_video"],
        "resolution": refs["resolution"],
        "aspect_ratio": script.get("config", {}).get("aspect_ratio", "16:9"),
        "host_reference": refs.get("avatar_file"),
        "avatar_url": refs.get("avatar_url"),
        "set_reference": refs.get("set_file"),
        "voice_suffix": refs["voice_suffix"],
        "seamless": use_seamless,
        "shots": [
            {
                "shot_id": s["id"],
                "duration": clamp_shot_duration(s["duration"]) if use_seamless else s["duration"],
                "image_url": s.get("image_url") or refs.get("avatar_url"),
                "video_prompt": (
                    apply_seamless_prompt(s, refs, seamless_opts)
                    if use_seamless
                    else ensure_voice_in_prompt(s["video_prompt"], refs["voice_suffix"])
                ),
                "speech_text": s.get("speech_text", ""),
                "speech_ipa": s.get("speech_ipa"),
                "on_screen": s.get("on_screen", ""),
                "on_screen_labels": s.get("on_screen_labels", []),
                "timing": {
                    "start_s": s.get("t_start"),
                    "end_s": s.get("t_end"),
                },
            }
            for s in shots
        ],
        "provenance_shot": {
            "type": "code_rendered_png",
            "duration_s": prov.get("duration_s", 7),
            "enabled": prov.get("enabled", True),
        },
    }


def render_provenance_card(script: dict[str, Any], out_path: Path) -> None:
    from PIL import Image, ImageDraw, ImageFont

    prov = script.get("provenance_card", {})
    w, h = 1280, 720
    img = Image.new("RGB", (w, h), (12, 14, 20))
    draw = ImageDraw.Draw(img)
    try:
        title_font = ImageFont.truetype("arial.ttf", 40)
        warn_font = ImageFont.truetype("arialbd.ttf", 30)
        body_font = ImageFont.truetype("arial.ttf", 24)
        small_font = ImageFont.truetype("arial.ttf", 20)
    except OSError:
        title_font = warn_font = body_font = small_font = ImageFont.load_default()

    card_type = prov.get("card_type", "provenance")
    if card_type == "closing":
        draw.rectangle([(40, 40), (w - 40, h - 40)], outline=(180, 150, 90), width=3)
        title = prov.get("title", "DAVID · The Archive")
        subtitle = prov.get("subtitle", "")
        try:
            big_font = ImageFont.truetype("arial.ttf", 56)
        except OSError:
            big_font = title_font
        tw = draw.textlength(title, font=big_font)
        draw.text(((w - tw) / 2, h // 2 - 80), title, fill=(220, 190, 120), font=big_font)
        if subtitle:
            sw = draw.textlength(subtitle, font=body_font)
            draw.text(((w - sw) / 2, h // 2 + 10), subtitle, fill=(200, 205, 215), font=body_font)
        footer = prov.get("footer", "")
        if footer:
            for wrapped in textwrap.wrap(footer, width=60):
                fw = draw.textlength(wrapped, font=small_font)
                draw.text(((w - fw) / 2, h - 120), wrapped, fill=(255, 180, 90), font=small_font)
    else:
        draw.rectangle([(40, 40), (w - 40, h - 40)], outline=(200, 120, 50), width=4)
        banner = prov.get("banner", "")
        if banner:
            draw.rectangle([(55, 55), (w - 55, 110)], fill=(80, 45, 20))
            draw.text((70, 62), banner, fill=(255, 200, 120), font=warn_font)
            y_title = 130
        else:
            y_title = 70

        draw.text((70, y_title), prov.get("title", "DAVID · PROVENANCE"), fill=(220, 190, 120), font=title_font)
        if prov.get("subtitle"):
            draw.text((70, y_title + 50), prov["subtitle"], fill=(240, 240, 245), font=body_font)

        y = y_title + (100 if prov.get("subtitle") else 60)
        for line in prov.get("lines", []):
            for wrapped in textwrap.wrap(str(line), width=78):
                draw.text((70, y), wrapped, fill=(200, 205, 215), font=small_font)
                y += 28

        footer = prov.get("footer", "")
        if footer:
            draw.text((70, h - 70), footer, fill=(255, 180, 90), font=small_font)

    out_path.parent.mkdir(parents=True, exist_ok=True)
    img.save(out_path)


def provenance_to_video(png: Path, mp4: Path, duration: float) -> None:
    ff = _ffmpeg_exe()
    subprocess.run(
        [
            ff, "-y", "-loop", "1", "-i", str(png),
            "-c:v", "libx264", "-t", str(duration),
            "-pix_fmt", "yuv420p", "-vf", "scale=1280:720", str(mp4),
        ],
        check=True,
        capture_output=True,
    )


def concat_videos(parts: list[Path], out: Path) -> None:
    ff = _ffmpeg_exe()
    list_file = out.with_suffix(".txt")
    list_file.write_text(
        "\n".join(f"file '{p.resolve().as_posix()}'" for p in parts),
        encoding="utf-8",
    )
    subprocess.run(
        [ff, "-y", "-f", "concat", "-safe", "0", "-i", str(list_file), "-c", "copy", str(out)],
        check=True,
        capture_output=True,
    )
    list_file.unlink(missing_ok=True)


@dataclass
class SeamlessOptions:
    enabled: bool = False
    xfade_s: float = 0.2
    match_color: bool = False
    cut_on_motion: bool = False
    continuity_prefix: str = DEFAULT_CONTINUITY_PREFIX
    end_guard: str = DEFAULT_END_GUARD


def get_seamless_options(script: dict[str, Any], args: argparse.Namespace) -> SeamlessOptions:
    seam = script.get("seamless") or script.get("config", {}).get("seamless") or {}
    auto = seam.get("primary") in ("extend", "extend_chain", True)
    return SeamlessOptions(
        enabled=bool(getattr(args, "seamless", False) or auto),
        xfade_s=float(getattr(args, "xfade", None) or seam.get("xfade_s", 0.2)),
        match_color=getattr(args, "match_color", False) or bool(seam.get("match_color")),
        cut_on_motion=getattr(args, "cut_on_motion", False) or bool(seam.get("cut_on_motion")),
        continuity_prefix=script.get("continuity_prefix", DEFAULT_CONTINUITY_PREFIX),
        end_guard=script.get("end_guard", DEFAULT_END_GUARD),
    )


def clamp_shot_duration(duration: int, lo: int = 7, hi: int = 9) -> int:
    return max(lo, min(hi, int(duration)))


def apply_seamless_prompt(shot: dict[str, Any], refs: dict[str, Any], opts: SeamlessOptions) -> str:
    base = ensure_voice_in_prompt(shot.get("video_prompt", ""), refs["voice_suffix"])
    prefix = shot.get("continuity_prefix", opts.continuity_prefix)
    guard = shot.get("end_guard", opts.end_guard)
    speech = shot.get("speech_text", "")
    parts = [prefix, base]
    if speech and speech not in base:
        parts.append(f'Lip-synced, delivers: "{speech}"')
    parts.append(guard)
    return " ".join(p.strip() for p in parts if p.strip())


def probe_duration(video: Path) -> float:
    ff = _ffmpeg_exe()
    r = subprocess.run(
        [ff, "-i", str(video)],
        capture_output=True,
        text=True,
    )
    for line in (r.stderr or "").splitlines():
        if "Duration:" in line:
            t = line.split("Duration:", 1)[1].split(",")[0].strip()
            h, m, s = t.split(":")
            return int(h) * 3600 + int(m) * 60 + float(s)
    raise RuntimeError(f"cannot probe duration: {video}")


def extract_last_frame(video: Path, out_jpg: Path) -> Path:
    ff = _ffmpeg_exe()
    out_jpg.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        [
            ff, "-y", "-sseof", "-0.08", "-i", str(video),
            "-frames:v", "1", "-q:v", "2", "-update", "1", str(out_jpg),
        ],
        check=True,
        capture_output=True,
    )
    return out_jpg


def trim_tail_motion(video: Path, out: Path, trim_s: float = 0.15) -> Path:
    """Trim trailing stillness before a frame-chain join (--cut-on-motion)."""
    ff = _ffmpeg_exe()
    dur = probe_duration(video)
    keep = max(0.5, dur - trim_s)
    subprocess.run(
        [ff, "-y", "-i", str(video), "-t", f"{keep:.3f}", "-c", "copy", str(out)],
        check=True,
        capture_output=True,
    )
    return out


def upload_image_url(client: Any, image_path: Path) -> str:
    uploaded = client.files.upload(str(image_path))
    pub = client.files.create_public_url(uploaded.id)
    url = getattr(pub, "public_url", None) or pub.public_url
    if not url:
        raise RuntimeError(f"Failed to create public URL for {image_path}")
    return url


def match_color_segment(reference: Path, target: Path, out: Path) -> Path:
    """Histogram-match *target* to *reference* (STUDIO v1.1 pre-join)."""
    ff = _ffmpeg_exe()
    out.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        [
            ff, "-y", "-i", str(target), "-i", str(reference),
            "-filter_complex", "[0:v][1:v]histogrammatching=pattern=1:strength=0.55[outv]",
            "-map", "[outv]", "-map", "0:a?", "-c:v", "libx264", "-pix_fmt", "yuv420p",
            "-c:a", "copy", str(out),
        ],
        check=True,
        capture_output=True,
    )
    return out


def concat_xfade_two(
    left: Path,
    right: Path,
    out: Path,
    *,
    xfade_s: float = 0.2,
    match_color: bool = False,
    cut_on_motion: bool = False,
    work_dir: Path | None = None,
) -> Path:
    ff = _ffmpeg_exe()
    work = work_dir or out.parent
    a, b = left, right
    if cut_on_motion:
        trimmed = work / f"{left.stem}_trim.mp4"
        trim_tail_motion(left, trimmed)
        a = trimmed
    if match_color:
        matched = work / f"{right.stem}_matched.mp4"
        match_color_segment(a, right, matched)
        b = matched
    dur_a = probe_duration(a)
    offset = max(0.0, dur_a - xfade_s)
    out.parent.mkdir(parents=True, exist_ok=True)
    # Video xfade; audio optional (Grok clips often have no audio track)
    filter_v = f"[0:v][1:v]xfade=transition=fade:duration={xfade_s}:offset={offset:.3f}[vout]"
    cmd = [
        ff, "-y", "-i", str(a), "-i", str(b),
        "-filter_complex", filter_v,
        "-map", "[vout]", "-c:v", "libx264", "-pix_fmt", "yuv420p", str(out),
    ]
    r = subprocess.run(cmd, capture_output=True)
    if r.returncode != 0:
        # Retry without audio acrossfade
        subprocess.run(cmd, check=True, capture_output=True)
    return out


def build_side_by_side(left: Path, right: Path, out: Path, label_left: str = "v1", label_right: str = "v2") -> Path:
    ff = _ffmpeg_exe()
    out.parent.mkdir(parents=True, exist_ok=True)
    filt = (
        f"[0:v]scale=640:360,drawtext=text='{label_left}':fontsize=28:fontcolor=white:"
        f"x=20:y=20:box=1:boxcolor=black@0.5[left];"
        f"[1:v]scale=640:360,drawtext=text='{label_right}':fontsize=28:fontcolor=white:"
        f"x=20:y=20:box=1:boxcolor=black@0.5[right];"
        f"[left][right]hstack=inputs=2[vout]"
    )
    subprocess.run(
        [
            ff, "-y", "-i", str(left), "-i", str(right),
            "-filter_complex", filt, "-map", "[vout]",
            "-c:v", "libx264", "-pix_fmt", "yuv420p", "-t", str(min(probe_duration(left), probe_duration(right))),
            str(out),
        ],
        check=True,
        capture_output=True,
    )
    return out


def _extend_not_supported(exc: BaseException) -> bool:
    msg = str(exc).lower()
    return "not supported" in msg or "invalid_argument" in msg


def render_frame_chain_performance(
    shots: list[dict[str, Any]],
    client: Any,
    refs: dict[str, Any],
    opts: SeamlessOptions,
    shots_dir: Path,
    out_path: Path,
    *,
    concat_only: bool = False,
    force: bool = False,
    seed_segment: Path | None = None,
) -> tuple[Path, list[str], str]:
    """Fallback PRIMARY — last-frame → image-to-video chain (same take discipline)."""
    segments: list[Path] = []
    step_urls: list[str] = []
    model = refs["model_video"]
    frames_dir = shots_dir / "chain_frames"
    frames_dir.mkdir(parents=True, exist_ok=True)

    for i, shot in enumerate(shots):
        sid = shot["id"]
        seg_path = shots_dir / f"chain_{sid}.mp4"
        dur = clamp_shot_duration(shot.get("duration", 8))
        prompt = apply_seamless_prompt(shot, refs, opts)

        if seg_path.exists() and seg_path.stat().st_size > 10000 and not force:
            print(f"[seamless] reusing frame-chain {seg_path.name}")
            segments.append(seg_path)
            continue

        if concat_only:
            raise FileNotFoundError(f"--concat-only: missing frame-chain segment {seg_path}")

        if i == 0 and seed_segment and seed_segment.is_file() and not force:
            seed_segment.replace(seg_path)
            print(f"[seamless] frame-chain {i + 1}/{len(shots)} {sid} — reusing extend seed")
            segments.append(seg_path)
            continue

        image_url = refs["avatar_url"]
        if i > 0 and segments:
            frame_jpg = frames_dir / f"frame_after_{segments[-1].stem}.jpg"
            extract_last_frame(segments[-1], frame_jpg)
            _api_pace()
            image_url = upload_image_url(client, frame_jpg)
            print(f"[seamless] frame-chain {i + 1}/{len(shots)} {sid} ({dur}s) ← last frame")
        else:
            print(f"[seamless] frame-chain {i + 1}/{len(shots)} {sid} ({dur}s) ← David-001")

        _api_pace()
        resp = client.video.generate(
            prompt=prompt,
            model=model,
            image_url=image_url,
            duration=dur,
            resolution=refs["resolution"],
        )
        step_urls.append(resp.url)
        _download(resp.url, seg_path)
        segments.append(seg_path)

    if len(segments) == 1:
        segments[0].replace(out_path)
    else:
        concat_videos(segments, out_path)
    return out_path, step_urls, "frame_chain"


def render_extend_performance(
    shots: list[dict[str, Any]],
    client: Any,
    refs: dict[str, Any],
    opts: SeamlessOptions,
    out_path: Path,
    shots_dir: Path,
    *,
    concat_only: bool = False,
    force: bool = False,
) -> tuple[Path, list[str], str]:
    """PRIMARY path — Grok Imagine EXTEND when supported; else frame-chain fallback."""
    state_path = shots_dir / "extend_state.json"
    if out_path.exists() and out_path.stat().st_size > 10000 and not force:
        print(f"[seamless] reusing performance {out_path.name}")
        mode = "cached"
        if state_path.is_file():
            mode = json.loads(state_path.read_text()).get("mode", mode)
        return out_path, [], mode

    if concat_only:
        raise FileNotFoundError(f"--concat-only: missing performance {out_path}")

    gen_model = refs["model_video"]
    extend_model = refs.get("extend_model") or gen_model
    avatar_url = refs["avatar_url"]

    # First segment
    shot0 = shots[0]
    dur0 = clamp_shot_duration(shot0.get("duration", 8))
    prompt0 = apply_seamless_prompt(shot0, refs, opts)
    print(f"[seamless] extend step 1/{len(shots)} {shot0['id']} ({dur0}s)…")
    _api_pace()
    resp = client.video.generate(
        prompt=prompt0,
        model=gen_model,
        image_url=avatar_url,
        duration=dur0,
        resolution=refs["resolution"],
    )
    current_url = resp.url
    step_urls = [current_url]
    _download(current_url, out_path)

    if len(shots) == 1:
        state_path.write_text(json.dumps({"mode": "generate_only", "urls": step_urls}), encoding="utf-8")
        return out_path, step_urls, "generate_only"

    shot1 = shots[1]
    dur1 = clamp_shot_duration(shot1.get("duration", 8))
    prompt1 = apply_seamless_prompt(shot1, refs, opts)
    try:
        print(f"[seamless] extend step 2/{len(shots)} {shot1['id']} ({dur1}s)…")
        _api_pace()
        resp = client.video.extend(
            prompt=prompt1,
            model=extend_model,
            video_url=current_url,
            duration=dur1,
        )
        current_url = resp.url
        step_urls.append(current_url)
        _download(current_url, out_path)

        for i, shot in enumerate(shots[2:], start=3):
            sid = shot["id"]
            dur = clamp_shot_duration(shot.get("duration", 8))
            prompt = apply_seamless_prompt(shot, refs, opts)
            print(f"[seamless] extend step {i}/{len(shots)} {sid} ({dur}s)…")
            _api_pace()
            resp = client.video.extend(
                prompt=prompt,
                model=extend_model,
                video_url=current_url,
                duration=dur,
            )
            current_url = resp.url
            step_urls.append(current_url)
            _download(current_url, out_path)

        state_path.write_text(
            json.dumps({"mode": "extend", "model": extend_model, "urls": step_urls}),
            encoding="utf-8",
        )
        return out_path, step_urls, "extend"

    except Exception as exc:
        if not _extend_not_supported(exc):
            raise
        print("[seamless] EXTEND unavailable on grok-imagine-video-1.5 — frame-chain fallback (STUDIO v1.1 §2)")
        seed = shots_dir / f"chain_{shot0['id']}.mp4"
        if out_path.is_file():
            shutil.copy2(out_path, seed)
        result = render_frame_chain_performance(
            shots, client, refs, opts, shots_dir, out_path,
            concat_only=False, force=False,
            seed_segment=seed,
        )
        state_path.write_text(json.dumps({"mode": "frame_chain", "urls": result[1]}), encoding="utf-8")
        return result


def qa_check(
    script: dict[str, Any],
    refs: dict[str, Any],
    rendered: list[Path],
    *,
    seamless_opts: SeamlessOptions | None = None,
    extend_path: Path | None = None,
    comparison_path: Path | None = None,
    continuity_mode: str | None = None,
) -> dict[str, Any]:
    rules = script.get("qa_rules", {})
    issues: list[str] = []
    passes: list[str] = []

    if rules.get("require_identity_lock", True) and refs.get("lock"):
        if refs["lock"].get("status") == "LOCKED":
            passes.append("host identity lock LOADED")
        else:
            issues.append("host identity not LOCKED")

    shots = script.get("shots", [])
    min_shots = rules.get("min_shots", 1)
    if len(shots) >= min_shots:
        passes.append(f"shot count OK ({len(shots)} >= {min_shots})")
    else:
        issues.append(f"shot count {len(shots)} < min {min_shots}")

    if rules.get("require_synthetic_guard", True):
        voice = refs.get("voice_suffix", DEFAULT_VOICE_SUFFIX)
        bad = [
            s["id"]
            for s in shots
            if SYNTHETIC_GUARD.lower()
            not in ensure_voice_in_prompt(s.get("video_prompt", ""), voice).lower()
        ]
        if bad:
            issues.append(f"shots missing synthetic guard after patch: {bad}")
        else:
            passes.append("all shots carry synthetic host guard (incl. auto-patched)")

    pie_like = [s for s in shots if s.get("speech_lang", "").startswith("pie") or "RECONSTRUCTED" in str(s.get("on_screen_labels"))]
    for s in pie_like:
        labels = s.get("on_screen_labels", [])
        if any("RECONSTRUCTED" in lb for lb in labels):
            passes.append(f"{s['id']}: RECONSTRUCTED labels present")
        elif rules.get("require_reconstructed_labels"):
            issues.append(f"{s['id']}: missing RECONSTRUCTED labels")

    for p in rendered:
        if not p.is_file() or p.stat().st_size < 10000:
            issues.append(f"missing or tiny segment: {p.name}")

    total_dur = sum(s.get("duration", 0) for s in shots)
    prov_dur = script.get("provenance_card", {}).get("duration_s", 7)
    if script.get("provenance_card", {}).get("enabled", True):
        total_dur += prov_dur
    passes.append(f"target duration ~{total_dur}s")

    if seamless_opts and seamless_opts.enabled:
        passes.append("STUDIO v1.1 seamless mode ACTIVE")
        mode = continuity_mode or "unknown"
        passes.append(f"continuity mode: {mode}; card join xfade={seamless_opts.xfade_s}s")
        if mode == "extend":
            passes.append("PRIMARY Grok Imagine EXTEND chain")
        elif mode == "frame_chain":
            passes.append("frame-chain i2v fallback (extend unsupported on 1.5)")
        if seamless_opts.match_color:
            passes.append("match-color pre-join ENABLED")
        if seamless_opts.cut_on_motion:
            passes.append("cut-on-motion tail trim ENABLED")
        if extend_path and extend_path.is_file():
            passes.append(f"host performance: {extend_path.name} ({probe_duration(extend_path):.1f}s)")
        else:
            issues.append("missing host performance file")
        prefix = seamless_opts.continuity_prefix
        if "@David-001" in prefix:
            passes.append("David-001 continuity prefix locked")
        for s in shots:
            dur = s.get("duration", 0)
            if dur < 7 or dur > 9:
                issues.append(f"{s['id']}: duration {dur}s outside 7–9s seamless band")
        if comparison_path and comparison_path.is_file():
            passes.append(f"side-by-side: {comparison_path.name}")

    return {
        "slug": script.get("slug"),
        "qa_at": datetime.now(timezone.utc).isoformat(),
        "pass": len(issues) == 0,
        "passes": passes,
        "issues": issues,
        "shot_count": len(shots),
        "segment_count": len(rendered),
        "seamless": seamless_opts.enabled if seamless_opts else False,
    }


def render_longform(
    script: dict[str, Any],
    *,
    client: Any = None,
    concat_only: bool = False,
    force_shots: set[str] | None = None,
    seamless_opts: SeamlessOptions | None = None,
) -> dict[str, Any]:
    prod_dir = resolve_production_dir(script)
    shots_dir = prod_dir / "shots"
    shots_dir.mkdir(parents=True, exist_ok=True)

    refs = resolve_refs(script)
    opts = seamless_opts or SeamlessOptions()
    pack = build_imagine_pack(script, refs, opts if opts.enabled else None)
    pack_path = prod_dir / f"{script.get('slug', 'longform')}_imagine_pack.json"
    pack_path.write_text(json.dumps(pack, indent=2, ensure_ascii=False), encoding="utf-8")

    script_copy = prod_dir / f"{script.get('slug', 'longform')}_script.json"
    script_copy.write_text(json.dumps(script, indent=2, ensure_ascii=False), encoding="utf-8")

    slug = script.get("slug", "longform")
    final_mp4 = prod_dir / "output" / f"david_{slug}_longform_v1.mp4"
    final_mp4.parent.mkdir(parents=True, exist_ok=True)
    comparison_path: Path | None = None
    extend_path: Path | None = None

    if opts.enabled:
        scene_id = (script.get("seamless") or {}).get("performance_scene_id", "archive_performance")
        perf_shots = [s for s in script["shots"] if s.get("scene_id", scene_id) == scene_id]
        if not perf_shots:
            perf_shots = list(script["shots"])

        extend_path = shots_dir / HOST_PERFORMANCE_NAME
        force_extend = bool(force_shots)
        host_mp4, step_urls, continuity_mode = render_extend_performance(
            perf_shots,
            client,
            refs,
            opts,
            extend_path,
            shots_dir,
            concat_only=concat_only,
            force=force_extend,
        )

        prov_cfg = script.get("provenance_card", {})
        card_mp4: Path | None = None
        if prov_cfg.get("enabled", True):
            prov_png = prod_dir / "provenance_card.png"
            render_provenance_card(script, prov_png)
            card_mp4 = shots_dir / "provenance.mp4"
            provenance_to_video(prov_png, card_mp4, prov_cfg.get("duration_s", 6))

        host_join = host_mp4
        if opts.cut_on_motion:
            trimmed_host = shots_dir / "host_performance_trimmed.mp4"
            trim_tail_motion(host_mp4, trimmed_host)
            host_join = trimmed_host

        if card_mp4:
            seamless_out = prod_dir / "output" / f"david_{slug}_seamless_v1.mp4"
            concat_xfade_two(
                host_join,
                card_mp4,
                seamless_out,
                xfade_s=opts.xfade_s,
                match_color=opts.match_color,
                cut_on_motion=False,
                work_dir=shots_dir,
            )
            final_mp4 = seamless_out

        rendered = [p for p in [host_mp4, card_mp4] if p]
        print(f"[seamless] final → {final_mp4}")

        compare_v1 = script.get("compare_v1")
        if compare_v1:
            v1_path = _resolve_david_path(compare_v1)
            if v1_path.is_file():
                comparison_path = prod_dir / "output" / f"david_{slug}_v1_vs_v2.mp4"
                try:
                    build_side_by_side(v1_path, final_mp4, comparison_path, "v1 hard-cut", "v2 seamless")
                    print(f"[seamless] comparison → {comparison_path}")
                except subprocess.CalledProcessError:
                    comparison_path = prod_dir / "output" / f"david_{slug}_v1_vs_v2_nolabel.mp4"
                    subprocess.run(
                        [
                            _ffmpeg_exe(), "-y", "-i", str(v1_path), "-i", str(final_mp4),
                            "-filter_complex", "[0:v]scale=640:360[left];[1:v]scale=640:360[right];[left][right]hstack[vout]",
                            "-map", "[vout]", "-c:v", "libx264", "-pix_fmt", "yuv420p",
                            "-t", str(min(probe_duration(v1_path), probe_duration(final_mp4))),
                            str(comparison_path),
                        ],
                        check=True,
                        capture_output=True,
                    )
                    print(f"[seamless] comparison (no labels) → {comparison_path}")

        qa = qa_check(
            script, refs, rendered,
            seamless_opts=opts,
            extend_path=extend_path,
            comparison_path=comparison_path,
            continuity_mode=continuity_mode,
        )
        qa_path = prod_dir / "qa_report.json"
        qa_path.write_text(json.dumps(qa, indent=2, ensure_ascii=False), encoding="utf-8")

        return {
            "production_dir": str(prod_dir),
            "script": str(script_copy),
            "imagine_pack": str(pack_path),
            "output": str(final_mp4),
            "extend_performance": str(extend_path),
            "extend_steps": len(step_urls) if step_urls else "cached",
            "continuity_mode": continuity_mode,
            "comparison": str(comparison_path) if comparison_path else None,
            "qa": qa,
            "segments": [str(p) for p in rendered if p],
            "seamless": True,
        }

    rendered: list[Path] = []
    force_shots = force_shots or set()

    for shot in script["shots"]:
        sid = shot["id"]
        out = shots_dir / f"{sid}.mp4"
        reuse = (
            out.exists()
            and out.stat().st_size > 10000
            and sid not in force_shots
        )
        if reuse:
            print(f"[longform] reusing {out.name}")
            rendered.append(out)
            continue

        if concat_only:
            raise FileNotFoundError(
                f"--concat-only: missing cached shot {out} (generate first without --concat-only)"
            )

        if client is None:
            raise RuntimeError("API client required for shot generation")

        prompt = ensure_voice_in_prompt(shot["video_prompt"], refs["voice_suffix"])
        image_url = shot.get("image_url") or refs["avatar_url"]
        print(f"[longform] rendering {sid} ({shot['duration']}s)…")
        _api_pace()
        vid = client.video.generate(
            prompt=prompt,
            model=refs["model_video"],
            image_url=image_url,
            duration=shot["duration"],
            resolution=refs["resolution"],
        )
        _download(vid.url, out)
        rendered.append(out)

    prov_cfg = script.get("provenance_card", {})
    if prov_cfg.get("enabled", True):
        prov_png = prod_dir / "provenance_card.png"
        render_provenance_card(script, prov_png)
        prov_mp4 = shots_dir / "provenance.mp4"
        provenance_to_video(prov_png, prov_mp4, prov_cfg.get("duration_s", 7))
        rendered.append(prov_mp4)

    concat_videos(rendered, final_mp4)
    print(f"[longform] final → {final_mp4}")

    qa = qa_check(script, refs, rendered)
    qa_path = prod_dir / "qa_report.json"
    qa_path.write_text(json.dumps(qa, indent=2, ensure_ascii=False), encoding="utf-8")

    return {
        "production_dir": str(prod_dir),
        "script": str(script_copy),
        "imagine_pack": str(pack_path),
        "output": str(final_mp4),
        "qa": qa,
        "segments": [str(p) for p in rendered],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="DAVID long-form video assembler")
    parser.add_argument("script", type=Path, help="Path to script JSON")
    parser.add_argument("--concat-only", action="store_true", help="Reuse cached shots; no API calls")
    parser.add_argument("--script-only", action="store_true", help="Normalize + write imagine pack only")
    parser.add_argument("--force-shot", action="append", default=[], help="Regenerate specific shot id(s)")
    parser.add_argument("--seamless", action="store_true", help="STUDIO v1.1 extend-primary + xfade joins")
    parser.add_argument("--match-color", action="store_true", help="Histogram-match before frame-chain joins")
    parser.add_argument("--cut-on-motion", action="store_true", help="Trim tail stillness before card join")
    parser.add_argument("--xfade", type=float, default=None, help="Crossfade seconds (default 0.2)")
    args = parser.parse_args()

    script_path = args.script if args.script.is_absolute() else Path.cwd() / args.script
    if not script_path.is_file():
        script_path = Path(__file__).parent / "longform_scripts" / args.script.name
    if not script_path.is_file():
        raise SystemExit(f"Script not found: {args.script}")

    raw = json.loads(script_path.read_text(encoding="utf-8"))
    script = normalize_script(raw, script_path)

    if not script.get("shots"):
        raise SystemExit("Script has no shots[]")

    if args.script_only:
        refs = resolve_refs(script)
        pack = build_imagine_pack(script, refs)
        prod_dir = resolve_production_dir(script)
        prod_dir.mkdir(parents=True, exist_ok=True)
        out = prod_dir / f"{script.get('slug', 'longform')}_imagine_pack.json"
        out.write_text(json.dumps(pack, indent=2, ensure_ascii=False), encoding="utf-8")
        script_out = prod_dir / f"{script.get('slug', 'longform')}_script.json"
        script_out.write_text(json.dumps(script, indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"Script only → {script_out}")
        print(f"Imagine pack → {out}")
        return 0

    client = None
    if not args.concat_only:
        import xai_sdk

        token = os.environ.get("XAI_API_KEY") or _load_grok_token()
        os.environ["XAI_API_KEY"] = token
        client = xai_sdk.Client(api_key=token)

    seamless_opts = get_seamless_options(script, args)

    result = render_longform(
        script,
        client=client,
        concat_only=args.concat_only,
        force_shots=set(args.force_shot),
        seamless_opts=seamless_opts,
    )

    manifest = {
        "pipeline": "render_longform_seamless" if seamless_opts.enabled else "render_longform",
        "protocol": "STUDIO_Seamless_Continuity_Protocol_v1.1" if seamless_opts.enabled else None,
        "completed_at": datetime.now(timezone.utc).isoformat(),
        "script_source": str(script_path),
        "concat_only": args.concat_only,
        "seamless": seamless_opts.enabled,
        **result,
    }
    prod_dir = Path(result["production_dir"])
    manifest_path = prod_dir / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(manifest, indent=2, ensure_ascii=False))
    return 0 if result["qa"]["pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())