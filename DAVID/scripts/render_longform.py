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
import subprocess
import sys
import textwrap
import urllib.request
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


def load_identity_lock(path: Path) -> dict[str, Any]:
    if not path.is_file():
        raise RuntimeError(f"Identity lock not found: {path}")
    lock = json.loads(path.read_text(encoding="utf-8"))
    if lock.get("status") != "LOCKED":
        raise RuntimeError(f"Identity lock status is not LOCKED: {path}")
    return lock


def normalize_script(raw: dict[str, Any], script_path: Path) -> dict[str, Any]:
    """Accept longform schema or legacy post01/sample script shape."""
    if "config" in raw and "shots" in raw:
        return raw

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
        "shots": raw.get("shots", []),
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
    lock_path = Path(cfg.get("identity_lock", DEFAULT_LOCK))
    if not lock_path.is_absolute():
        lock_path = ROOT / lock_path
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


def build_imagine_pack(script: dict[str, Any], refs: dict[str, Any]) -> dict[str, Any]:
    shots = script["shots"]
    prov = script.get("provenance_card", {})
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
        "shots": [
            {
                "shot_id": s["id"],
                "duration": s["duration"],
                "image_url": s.get("image_url") or refs.get("avatar_url"),
                "video_prompt": ensure_voice_in_prompt(s["video_prompt"], refs["voice_suffix"]),
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


def qa_check(script: dict[str, Any], refs: dict[str, Any], rendered: list[Path]) -> dict[str, Any]:
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
        bad = [s["id"] for s in shots if SYNTHETIC_GUARD.lower() not in s.get("video_prompt", "").lower()]
        if bad:
            issues.append(f"shots missing synthetic guard (auto-patched in pack): {bad}")
        else:
            passes.append("all shots carry synthetic host guard")

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

    return {
        "slug": script.get("slug"),
        "qa_at": datetime.now(timezone.utc).isoformat(),
        "pass": len(issues) == 0,
        "passes": passes,
        "issues": issues,
        "shot_count": len(shots),
        "segment_count": len(rendered),
    }


def render_longform(
    script: dict[str, Any],
    *,
    client: Any = None,
    concat_only: bool = False,
    force_shots: set[str] | None = None,
) -> dict[str, Any]:
    prod_dir = resolve_production_dir(script)
    shots_dir = prod_dir / "shots"
    shots_dir.mkdir(parents=True, exist_ok=True)

    refs = resolve_refs(script)
    pack = build_imagine_pack(script, refs)
    pack_path = prod_dir / f"{script.get('slug', 'longform')}_imagine_pack.json"
    pack_path.write_text(json.dumps(pack, indent=2, ensure_ascii=False), encoding="utf-8")

    script_copy = prod_dir / f"{script.get('slug', 'longform')}_script.json"
    script_copy.write_text(json.dumps(script, indent=2, ensure_ascii=False), encoding="utf-8")

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

    slug = script.get("slug", "longform")
    final_mp4 = prod_dir / "output" / f"david_{slug}_longform_v1.mp4"
    final_mp4.parent.mkdir(parents=True, exist_ok=True)
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

    result = render_longform(
        script,
        client=client,
        concat_only=args.concat_only,
        force_shots=set(args.force_shot),
    )

    manifest = {
        "pipeline": "render_longform",
        "completed_at": datetime.now(timezone.utc).isoformat(),
        "script_source": str(script_path),
        "concat_only": args.concat_only,
        **result,
    }
    prod_dir = Path(result["production_dir"])
    manifest_path = prod_dir / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(manifest, indent=2, ensure_ascii=False))
    return 0 if result["qa"]["pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())