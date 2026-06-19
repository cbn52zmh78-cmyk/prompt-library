#!/usr/bin/env python3
"""DAVID science explainer proof — 480p with code-burned overlays.

Validates the science lane value prop: narration + on-screen honesty labels
(ILLUSTRATIVE / NOT TO SCALE) + NASA/EHT sources card.
"""
from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import textwrap
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
WORKSPACE = ROOT.parent
PIPELINE_DIR = WORKSPACE / "STUDIO" / "Pipeline"
if str(PIPELINE_DIR) not in sys.path:
    sys.path.insert(0, str(PIPELINE_DIR))

from shot_duration import (  # noqa: E402
    av_sync_drift_label,
    check_shot_duration_band,
    effective_shot_duration,
    seamless_chain_enabled,
)

SCRIPTS = Path(__file__).resolve().parent / "longform_scripts"
FFMPEG: str | None = None

PROOF_W, PROOF_H = 854, 480

LABEL_COLORS = {
    "ILLUSTRATIVE": (140, 88, 28, 230),
    "NOT TO SCALE": (160, 55, 30, 230),
    "SCIENCE VISUALIZATION": (34, 72, 110, 230),
    "HOW WE KNOW": (34, 110, 72, 230),
    "MEASUREMENT": (60, 90, 130, 230),
}

SCIENCE_VOICE_RECOMMENDED = (
    "clear enthusiastic science communicator voice, precise but accessible diction, "
    "wonder without hype, synthetic presenter only"
)

DAVID_SCIENCE_VOICE = (
    "measured clear science narration voice, mid-low resonant precise diction, "
    "wonder without hype, documentary trust, accessible never stuffy, synthetic host only"
)


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


def _download(url: str, dest: Path) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    req = urllib.request.Request(url, headers={"User-Agent": "DAVID-science-proof/1.0"})
    with urllib.request.urlopen(req, timeout=300) as r:
        dest.write_bytes(r.read())


def load_identity_lock(path: Path) -> dict[str, Any]:
    lock = json.loads(path.read_text(encoding="utf-8"))
    if lock.get("status") != "LOCKED":
        raise RuntimeError(f"Identity lock not LOCKED: {path}")
    return lock


def resolve_science_subject(subject_id: str) -> Path | None:
    sid = (subject_id or "").strip().replace("-", "_")
    for candidate in (
        ROOT / "science" / "subjects" / f"{sid}.json",
        ROOT / "science" / "subjects" / f"{subject_id}.json",
    ):
        if candidate.is_file():
            return candidate
    return None


def probe_duration(video: Path) -> float:
    ff = _ffmpeg_exe()
    r = subprocess.run([ff, "-i", str(video)], capture_output=True, text=True)
    for line in (r.stderr or "").splitlines():
        if "Duration:" in line:
            t = line.split("Duration:", 1)[1].split(",")[0].strip()
            h, m, s = t.split(":")
            return int(h) * 3600 + int(m) * 60 + float(s)
    raise RuntimeError(f"cannot probe duration: {video}")


def extract_frame(video: Path, at_s: float, out_jpg: Path) -> Path:
    ff = _ffmpeg_exe()
    out_jpg.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        [ff, "-y", "-ss", f"{at_s:.3f}", "-i", str(video), "-frames:v", "1", str(out_jpg)],
        check=True,
        capture_output=True,
    )
    return out_jpg


def _fonts() -> tuple[Any, Any, Any]:
    from PIL import ImageFont

    try:
        title = ImageFont.truetype("arialbd.ttf", 22)
        body = ImageFont.truetype("arial.ttf", 20)
        small = ImageFont.truetype("arial.ttf", 16)
    except OSError:
        title = body = small = ImageFont.load_default()
    return title, body, small


def render_shot_overlay_png(shot: dict[str, Any], script: dict[str, Any], out_path: Path) -> Path:
    from PIL import Image, ImageDraw

    w, h = PROOF_W, PROOF_H
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    title_font, body_font, small_font = _fonts()

    brand = script.get("brand", {}).get("title", "DAVID · Science")
    draw.rectangle([(16, 12), (w - 16, 44)], fill=(18, 20, 28, 210))
    draw.text((28, 16), brand, fill=(180, 210, 255, 255), font=small_font)

    labels = shot.get("on_screen_labels") or []
    x = 16
    y = 52
    for label in labels:
        color = LABEL_COLORS.get(label, (60, 60, 80, 220))
        tw = draw.textlength(label, font=small_font)
        pad = 10
        draw.rounded_rectangle([(x, y), (x + tw + pad * 2, y + 28)], radius=6, fill=color)
        draw.text((x + pad, y + 5), label, fill=(255, 255, 255, 255), font=small_font)
        x += tw + pad * 2 + 8

    detail = shot.get("overlay_detail")
    if detail:
        tw = draw.textlength(detail, font=body_font)
        draw.rounded_rectangle([(16, y + 34), (16 + tw + 20, y + 64)], radius=6, fill=(40, 48, 62, 220))
        draw.text((26, y + 40), detail, fill=(230, 235, 245, 255), font=body_font)

    on_screen = (shot.get("on_screen") or "").strip()
    if on_screen:
        bar_h = 72
        draw.rectangle([(0, h - bar_h), (w, h)], fill=(0, 0, 0, 185))
        for i, line in enumerate(textwrap.wrap(on_screen, width=52)[:2]):
            draw.text((24, h - bar_h + 12 + i * 26), line, fill=(245, 242, 235, 255), font=body_font)

    out_path.parent.mkdir(parents=True, exist_ok=True)
    img.save(out_path)
    return out_path


def burn_overlay(video: Path, overlay_png: Path, out: Path) -> Path:
    ff = _ffmpeg_exe()
    out.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        [
            ff, "-y",
            "-i", str(video),
            "-i", str(overlay_png),
            "-filter_complex", "[0:v][1:v]overlay=0:0:format=auto,format=yuv420p[v]",
            "-map", "[v]", "-map", "0:1?",
            "-c:v", "libx264", "-pix_fmt", "yuv420p",
            "-c:a", "aac", "-b:a", "128k",
            str(out),
        ],
        check=True,
        capture_output=True,
    )
    return out


def render_sources_card(script: dict[str, Any], out_path: Path) -> None:
    from PIL import Image, ImageDraw

    ss = script.get("science_subject", {})
    prov_cfg = script.get("provenance_card", {})
    w, h = PROOF_W, PROOF_H
    img = Image.new("RGB", (w, h), (10, 14, 22))
    draw = ImageDraw.Draw(img)
    title_font, body_font, small_font = _fonts()

    draw.rectangle([(24, 24), (w - 24, h - 24)], outline=(100, 150, 200), width=2)
    draw.rectangle([(36, 36), (w - 36, 78)], fill=(34, 72, 110))
    draw.text((48, 44), "ILLUSTRATIVE", fill=(255, 255, 255), font=small_font)
    draw.rectangle([(200, 36), (w - 36, 78)], fill=(140, 88, 28))
    draw.text((212, 44), "NOT TO SCALE", fill=(255, 255, 255), font=small_font)

    title = prov_cfg.get("title") or f"Sources — {ss.get('phenomenon', 'Science')}"
    subtitle = prov_cfg.get("subtitle") or ss.get("domain", "")
    draw.text((48, 92), title, fill=(180, 210, 255), font=title_font)
    draw.text((48, 122), subtitle, fill=(240, 240, 245), font=body_font)

    lines: list[str] = [
        f"SUBJECT: {ss.get('subject_id', '')}",
        f"PHENOMENON: {ss.get('phenomenon', '')}",
        f"MEASUREMENT: {ss.get('key_measurement', '')}",
        f"PRINCIPLE SET: {ss.get('principle_set', '')}",
    ]
    sources = prov_cfg.get("sources") or ss.get("sources") or []
    for src in sources[:3]:
        cite = str(src.get("citation", "")).strip()
        if cite:
            lines.append(f"SOURCE: {cite}")

    y = 158
    for line in lines:
        for wrapped in textwrap.wrap(line, width=58):
            if y > h - 72:
                break
            draw.text((48, y), wrapped, fill=(200, 205, 215), font=small_font)
            y += 22

    footer = prov_cfg.get("footer", "illustrative visualization · sources on file")
    draw.text((48, h - 48), footer, fill=(180, 210, 255), font=body_font)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    img.save(out_path)


def provenance_to_video(png: Path, mp4: Path, duration: float) -> None:
    ff = _ffmpeg_exe()
    subprocess.run(
        [
            ff, "-y", "-loop", "1", "-i", str(png),
            "-c:v", "libx264", "-t", str(duration),
            "-pix_fmt", "yuv420p", "-vf", f"scale={PROOF_W}:{PROOF_H}", str(mp4),
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


def _label_bar_pixel(img_path: Path) -> tuple[int, int, int]:
    from PIL import Image

    img = Image.open(img_path).convert("RGB")
    w, h = img.size
    return img.getpixel((min(40, w - 1), min(60, h - 1)))


def _lower_third_dark(img_path: Path) -> bool:
    from PIL import Image

    img = Image.open(img_path).convert("RGB")
    w, h = img.size
    r, g, b = img.getpixel((w // 2, max(0, h - 40)))
    return (r + g + b) / 3 < 80


def qa_check(
    script: dict[str, Any],
    lock: dict[str, Any],
    *,
    final_path: Path,
    overlay_manifest: list[dict[str, Any]],
    burned_paths: list[Path],
) -> dict[str, Any]:
    rules = script.get("qa_rules", {})
    ss = script.get("science_subject", {})
    issues: list[str] = []
    passes: list[str] = []

    if lock.get("status") == "LOCKED":
        passes.append("host identity lock LOADED (@David-001)")
    else:
        issues.append("host identity not LOCKED")

    narration_shots = [s for s in script["shots"] if s.get("role") in ("host", "presenter")]
    min_shots = rules.get("min_shots", 3)
    if len(script["shots"]) >= min_shots:
        passes.append(f"science proof shots: {len(script['shots'])}")
    else:
        issues.append(f"fewer than {min_shots} shots")

    seamless = seamless_chain_enabled(script.get("config", {}).get("seamless"))
    for s in script["shots"]:
        if band := check_shot_duration_band(s, seamless=seamless):
            issues.append(band)

    for s in narration_shots:
        if not s.get("speech_text"):
            issues.append(f"{s['id']}: missing speech_text narration")
        timing = s.get("t_end", 0) - s.get("t_start", 0)
        if abs(timing - s.get("duration", 0)) > 0.5:
            issues.append(f"{s['id']}: timing mismatch")

    if seamless and burned_paths:
        sync_bad = []
        for shot, path in zip(script["shots"], burned_paths):
            if path.is_file():
                label = av_sync_drift_label(shot, probe_duration(path), seamless=True)
                if label:
                    sync_bad.append(label)
        if sync_bad:
            issues.append(f"A/V sync drift: {sync_bad}")
        else:
            passes.append("tight A/V sync per shot (script-clamped duration)")

    viz_shots = [s for s in script["shots"] if s.get("role") == "visualization"]
    if viz_shots:
        for vs in viz_shots:
            labels = [lb.upper() for lb in (vs.get("on_screen_labels") or [])]
            if "ILLUSTRATIVE" in labels:
                passes.append(f"{vs['id']}: ILLUSTRATIVE label present")
            else:
                issues.append(f"{vs['id']}: missing ILLUSTRATIVE label")
            if any("NOT TO SCALE" in lb for lb in labels):
                passes.append(f"{vs['id']}: NOT TO SCALE label present")
            else:
                issues.append(f"{vs['id']}: missing NOT TO SCALE label")
    else:
        issues.append("no visualization payoff shot")

    voice = script.get("config", {}).get("voice_suffix", "")
    if voice:
        passes.append("science narration voice configured")
    if script.get("config", {}).get("voice_recommendation"):
        passes.append("voice_recommendation documented in script")

    subject_path = resolve_science_subject(ss.get("subject_id", ""))
    if subject_path and subject_path.is_file():
        known = json.loads(subject_path.read_text(encoding="utf-8"))
        if known.get("subject_id") == ss.get("subject_id"):
            passes.append(f"science_subject matches registry ({ss.get('subject_id')})")
        else:
            issues.append("science_subject id mismatch vs registry")
    elif ss.get("subject_id"):
        issues.append("science subject registry file missing")

    sources = script.get("provenance_card", {}).get("sources") or ss.get("sources") or []
    cites = " ".join(str(s.get("citation", "")) for s in sources).lower()
    if "eht" in cites or "event horizon" in cites:
        passes.append("EHT source cited")
    else:
        issues.append("missing EHT source citation")
    if "nasa" in cites:
        passes.append("NASA source cited")
    else:
        issues.append("missing NASA source citation")

    if rules.get("require_overlay_burn"):
        if len(overlay_manifest) == len(script["shots"]):
            passes.append(f"overlay manifest complete ({len(overlay_manifest)} shots)")
        else:
            issues.append("overlay manifest incomplete")
        if burned_paths:
            raw = burned_paths[0].with_name(burned_paths[0].stem.replace("_burned", "_raw") + ".mp4")
            if raw.is_file():
                mid = probe_duration(raw) * 0.5
                raw_jpg = raw.with_suffix(".qa_raw.jpg")
                burned_jpg = burned_paths[0].with_suffix(".qa_burned.jpg")
                extract_frame(raw, mid, raw_jpg)
                extract_frame(burned_paths[0], mid, burned_jpg)
                if _label_bar_pixel(raw_jpg) != _label_bar_pixel(burned_jpg):
                    passes.append("overlay burn verified (label region pixel change)")
                else:
                    issues.append("overlay burn not detected in label region")
                raw_jpg.unlink(missing_ok=True)
                burned_jpg.unlink(missing_ok=True)

    if final_path.is_file():
        dur = probe_duration(final_path)
        lo = rules.get("duration_lo_s", 20)
        hi = rules.get("duration_hi_s", 32)
        if lo <= dur <= hi:
            passes.append(f"target duration OK ({dur:.1f}s in {lo}–{hi}s band)")
        else:
            issues.append(f"duration {dur:.1f}s outside {lo}–{hi}s band")
        passes.append(f"proof MP4: {final_path.name}")
    else:
        issues.append("missing final proof MP4")

    prov = script.get("provenance_card", {})
    if prov.get("enabled"):
        passes.append(f"sources card enabled ({prov.get('duration_s', 5)}s)")
        if len(sources) >= 2:
            passes.append(f"sources card entries: {len(sources)}")
        else:
            issues.append("sources card missing citations")

    if ss.get("principle_set") == "astrophysics_fidelity":
        passes.append("principle_set: astrophysics_fidelity")

    return {
        "slug": script.get("slug"),
        "qa_at": datetime.now(timezone.utc).isoformat(),
        "pass": len(issues) == 0,
        "passes": passes,
        "issues": issues,
        "science_subject_id": ss.get("subject_id"),
        "phenomenon": ss.get("phenomenon"),
        "voice_recommendation": script.get("config", {}).get("voice_recommendation", {}),
        "overlay_manifest": overlay_manifest,
    }


def render_proof(
    script: dict[str, Any],
    *,
    client: Any = None,
    concat_only: bool = False,
) -> dict[str, Any]:
    slug = script["slug"]
    prod_dir = ROOT / "productions" / f"{slug}_longform_v1"
    shots_dir = prod_dir / "shots"
    out_dir = prod_dir / "output"
    shots_dir.mkdir(parents=True, exist_ok=True)
    out_dir.mkdir(parents=True, exist_ok=True)

    lock_path = ROOT / script["config"]["identity_lock"]
    lock = load_identity_lock(lock_path)
    avatar_url = lock["references"]["david_avatar"].get("url")

    cfg = script["config"]
    model = cfg.get("model_video", "grok-imagine-video-1.5")
    resolution = cfg.get("resolution", "480p")

    script_copy = prod_dir / f"{slug}_script.json"
    script_copy.write_text(json.dumps(script, indent=2, ensure_ascii=False), encoding="utf-8")

    overlay_manifest: list[dict[str, Any]] = []
    burned_parts: list[Path] = []

    for shot in script["shots"]:
        sid = shot["id"]
        raw_path = shots_dir / f"{sid}_raw.mp4"
        overlay_png = shots_dir / f"{sid}_overlay.png"
        burned_path = shots_dir / f"{sid}_burned.mp4"
        if not (raw_path.is_file() and raw_path.stat().st_size > 10000) and not concat_only:
            if client is None:
                raise RuntimeError("API client required for video generation")
            seamless = seamless_chain_enabled(cfg.get("seamless"))
            api_dur = effective_shot_duration(shot, seamless=seamless)
            print(f"[science-proof] rendering {sid} ({api_dur}s, {resolution})…")
            image_url = shot.get("image_url") or avatar_url
            if not image_url:
                raise RuntimeError("image_url required — re-run render_host_identity.py")
            kwargs: dict[str, Any] = {
                "prompt": shot["video_prompt"],
                "model": model,
                "duration": api_dur,
                "resolution": resolution,
                "image_url": image_url,
            }
            resp = client.video.generate(**kwargs)
            _download(resp.url, raw_path)
        elif concat_only and not raw_path.is_file():
            raise FileNotFoundError(f"--concat-only: missing {raw_path}")

        render_shot_overlay_png(shot, script, overlay_png)
        burn_overlay(raw_path, overlay_png, burned_path)
        print(f"[science-proof] burned overlays → {burned_path.name}")

        overlay_manifest.append({
            "shot_id": sid,
            "t_start": shot.get("t_start"),
            "t_end": shot.get("t_end"),
            "on_screen": shot.get("on_screen"),
            "on_screen_labels": shot.get("on_screen_labels", []),
            "overlay_png": str(overlay_png),
            "raw_mp4": str(raw_path),
            "burned_mp4": str(burned_path),
        })
        burned_parts.append(burned_path)

    prov_png = prod_dir / "sources_card.png"
    render_sources_card(script, prov_png)
    prov_dur = float(script.get("provenance_card", {}).get("duration_s", 5))
    prov_mp4 = shots_dir / "sources.mp4"
    provenance_to_video(prov_png, prov_mp4, prov_dur)
    burned_parts.append(prov_mp4)

    out_name = cfg.get("output_filename") or f"{slug}_480p_v1.mp4"
    final_mp4 = out_dir / out_name
    concat_videos(burned_parts, final_mp4)
    print(f"[science-proof] final → {final_mp4}")

    qa = qa_check(
        script, lock,
        final_path=final_mp4,
        overlay_manifest=overlay_manifest,
        burned_paths=burned_parts[: len(script["shots"])],
    )
    qa_path = prod_dir / "qa_report.json"
    qa_path.write_text(json.dumps(qa, indent=2, ensure_ascii=False), encoding="utf-8")

    return {
        "production_dir": str(prod_dir),
        "script": str(script_copy),
        "output": str(final_mp4),
        "sources_card": str(prov_png),
        "qa": qa,
        "overlay_manifest": overlay_manifest,
    }


def main() -> int:
    import argparse

    parser = argparse.ArgumentParser(description="DAVID science explainer proof (480p)")
    parser.add_argument(
        "script",
        nargs="?",
        default=SCRIPTS / "david_black_hole_science_proof_v1_script.json",
        type=Path,
    )
    parser.add_argument("--concat-only", action="store_true")
    args = parser.parse_args()

    script_path = args.script if args.script.is_absolute() else SCRIPTS / args.script.name
    if not script_path.is_file():
        script_path = Path(args.script)
    if not script_path.is_file():
        raise SystemExit(f"Script not found: {args.script}")

    script = json.loads(script_path.read_text(encoding="utf-8"))

    client = None
    if not args.concat_only:
        import xai_sdk

        token = os.environ.get("XAI_API_KEY") or _load_grok_token()
        os.environ["XAI_API_KEY"] = token
        client = xai_sdk.Client(api_key=token)

    result = render_proof(script, client=client, concat_only=args.concat_only)
    manifest = {
        "pipeline": "render_science_proof",
        "completed_at": datetime.now(timezone.utc).isoformat(),
        "resolution": "480p",
        "concat_only": args.concat_only,
        **result,
    }
    manifest_path = Path(result["production_dir"]) / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(manifest, indent=2, ensure_ascii=False))
    return 0 if result["qa"]["pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())