#!/usr/bin/env python3
"""DAVID dead-language pronunciation proof — 480p with code-burned overlays.

Validates the channel value prop: DAVID speaks attested/reconstructed dead language
with on-screen labels, IPA captions, and code-rendered provenance card.
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
SCRIPTS = Path(__file__).resolve().parent / "longform_scripts"
FFMPEG: str | None = None

# 480p 16:9
PROOF_W, PROOF_H = 854, 480

LABEL_COLORS = {
    "ATTESTED TEXT": (34, 110, 72, 230),
    "RECONSTRUCTED PRONUNCIATION": (140, 88, 28, 230),
    "RECONSTRUCTED": (140, 88, 28, 230),
    "NOT ATTESTED": (160, 55, 30, 230),
}


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
    req = urllib.request.Request(url, headers={"User-Agent": "DAVID-dead-language-proof/1.0"})
    with urllib.request.urlopen(req, timeout=300) as r:
        dest.write_bytes(r.read())


def resolve_corpus_path(language: str) -> Path | None:
    """Locate known_texts.json for a language id under languages/dead or languages/extinct."""
    lang = (language or "").strip()
    if not lang:
        return None
    for bucket in ("dead", "extinct", "reconstructed", "undeciphered"):
        candidate = ROOT / "languages" / bucket / lang / "corpus" / "known_texts.json"
        if candidate.is_file():
            return candidate
    return None


def load_identity_lock(path: Path) -> dict[str, Any]:
    lock = json.loads(path.read_text(encoding="utf-8"))
    if lock.get("status") != "LOCKED":
        raise RuntimeError(f"Identity lock not LOCKED: {path}")
    return lock


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


def _fonts() -> tuple[Any, Any, Any, Any]:
    from PIL import ImageFont

    try:
        title = ImageFont.truetype("arialbd.ttf", 22)
        body = ImageFont.truetype("arial.ttf", 20)
        ipa_font = ImageFont.truetype("arial.ttf", 18)
        small = ImageFont.truetype("arial.ttf", 16)
    except OSError:
        title = body = ipa_font = small = ImageFont.load_default()
    return title, body, ipa_font, small


def render_shot_overlay_png(shot: dict[str, Any], out_path: Path) -> Path:
    """Burn-ready RGBA overlay: label chips + lower-third text + IPA."""
    from PIL import Image, ImageDraw

    w, h = PROOF_W, PROOF_H
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    title_font, body_font, ipa_font, small_font = _fonts()

    # Header channel caption
    draw.rectangle([(16, 12), (w - 16, 44)], fill=(18, 20, 28, 210))
    draw.text((28, 16), "DAVID · The Archive", fill=(220, 190, 120, 255), font=small_font)

    # Attested / reconstructed label chips
    labels = shot.get("on_screen_labels") or []
    x = 16
    y = 52
    for label in labels:
        color = LABEL_COLORS.get(label, (60, 60, 80, 220))
        tw = draw.textlength(label, font=small_font)
        pad = 10
        draw.rounded_rectangle(
            [(x, y), (x + tw + pad * 2, y + 28)],
            radius=6,
            fill=color,
        )
        draw.text((x + pad, y + 5), label, fill=(255, 255, 255, 255), font=small_font)
        x += tw + pad * 2 + 8

    detail = shot.get("overlay_detail")
    if detail:
        tw = draw.textlength(detail, font=body_font)
        draw.rounded_rectangle([(16, y + 34), (16 + tw + 20, y + 64)], radius=6, fill=(40, 48, 62, 220))
        draw.text((26, y + 40), detail, fill=(230, 235, 245, 255), font=body_font)

    # Lower third — attested Latin line
    on_screen = (shot.get("on_screen") or "").strip()
    ipa = (shot.get("speech_ipa") or "").strip()
    if on_screen or ipa:
        bar_h = 110 if ipa and shot.get("overlay_ipa") else 72
        draw.rectangle([(0, h - bar_h), (w, h)], fill=(0, 0, 0, 185))
        ty = h - bar_h + 12
        if on_screen:
            for i, line in enumerate(textwrap.wrap(on_screen, width=48)[:2]):
                draw.text((24, ty + i * 26), line, fill=(245, 242, 235, 255), font=body_font)
            ty += 52 if len(textwrap.wrap(on_screen, width=48)) > 0 else 0
        if ipa and shot.get("overlay_ipa"):
            draw.text((24, h - 38), f"IPA {ipa}", fill=(180, 210, 255, 255), font=ipa_font)

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


def render_provenance_card(script: dict[str, Any], out_path: Path) -> None:
    from PIL import Image, ImageDraw

    corpus = script.get("corpus", {})
    prov_cfg = script.get("provenance_card", {})
    hf = script.get("historical_figure", {})
    card_type = prov_cfg.get("card_type", "provenance")
    w, h = PROOF_W, PROOF_H
    img = Image.new("RGB", (w, h), (12, 14, 20))
    draw = ImageDraw.Draw(img)
    title_font, body_font, _, small_font = _fonts()

    draw.rectangle([(24, 24), (w - 24, h - 24)], outline=(180, 150, 90), width=2)
    draw.rectangle([(36, 36), (w - 36, 78)], fill=(34, 110, 72))
    draw.text((48, 44), "ATTESTED TEXT", fill=(255, 255, 255), font=small_font)
    draw.rectangle([(200, 36), (w - 36, 78)], fill=(140, 88, 28))
    draw.text((212, 44), "RECONSTRUCTED PRONUNCIATION", fill=(255, 255, 255), font=small_font)

    if card_type == "sources" and hf:
        title = prov_cfg.get("title") or f"DAVID · SOURCES · {hf.get('name', '')}"
        subtitle = prov_cfg.get("subtitle") or f"{hf.get('era', '')} · d. {hf.get('death_year', '')}"
    else:
        title = prov_cfg.get("title", "DAVID · PROVENANCE")
        subtitle = prov_cfg.get("subtitle", "")

    draw.text((48, 92), title, fill=(220, 190, 120), font=title_font)
    draw.text((48, 122), subtitle, fill=(240, 240, 245), font=body_font)

    corpus_rel = ""
    corpus_file = resolve_corpus_path(corpus.get("language", ""))
    if corpus_file:
        try:
            corpus_rel = str(corpus_file.relative_to(ROOT)).replace("\\", "/")
        except ValueError:
            corpus_rel = str(corpus_file)

    lines: list[str] = []
    if hf:
        lines.append(f"FIGURE: {hf.get('name', '')} ({hf.get('figure_id', '')})")
    lines.extend([
        f"TEXT [attested]: {corpus.get('text_source', '')}",
        f"LINE: {corpus.get('attested_text', '')}",
        f"IPA [reconstructed]: {corpus.get('line_ipa', '')}",
        f"MODEL: {corpus.get('pronunciation_model', '')}",
        f"TRANSLATION: {corpus.get('translation', '')}",
    ])
    if card_type == "sources":
        for src in (prov_cfg.get("sources") or hf.get("sources") or [])[:3]:
            cite = str(src.get("citation", "")).strip()
            if cite:
                lines.append(f"SOURCE: {cite}")
    else:
        lines.append("SOURCES: Wikipedia / Wiktionary (CC BY-SA), Wikidata (CC0)")
    if corpus_rel:
        lines.append(f"CORPUS: {corpus_rel} · {corpus.get('corpus_id', '')}")

    y = 158
    for line in lines:
        for wrapped in textwrap.wrap(line, width=58):
            if y > h - 72:
                break
            draw.text((48, y), wrapped, fill=(200, 205, 215), font=small_font)
            y += 22

    footer = prov_cfg.get("footer", "attested text · reconstructed pronunciation")
    draw.text((48, h - 48), footer, fill=(220, 190, 120), font=body_font)
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
    x = min(40, w - 1)
    y = min(60, h - 1)
    return img.getpixel((x, y))


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
    corpus = script.get("corpus", {})
    issues: list[str] = []
    passes: list[str] = []

    if lock.get("status") == "LOCKED":
        passes.append("host identity lock LOADED (@David-001)")
    else:
        issues.append("host identity not LOCKED")

    speech_lang = corpus.get("language") or script["shots"][0].get("speech_lang", "")
    lang_shots = [s for s in script["shots"] if s.get("speech_lang") == speech_lang]
    min_shots = rules.get("min_shots", 3)
    if len(lang_shots) >= min_shots:
        passes.append(f"{speech_lang} demonstration shots: {len(lang_shots)}")
    else:
        issues.append(f"fewer than {min_shots} {speech_lang} speech shots")

    english_period_langs = {"tudor-english", "early-modern-english", "old-english", "middle-english"}
    for s in lang_shots:
        speech = s.get("speech_text", "")
        if speech_lang not in english_period_langs and re.search(
            r"\b(the|and|is|what|how)\b", speech, re.I
        ):
            issues.append(f"{s['id']}: English function words in speech_text")
        if not s.get("speech_ipa"):
            issues.append(f"{s['id']}: missing speech_ipa")
        labels = s.get("on_screen_labels", [])
        if rules.get("require_reconstructed_labels"):
            if any("RECONSTRUCTED" in lb for lb in labels):
                passes.append(f"{s['id']}: RECONSTRUCTED label present")
            else:
                issues.append(f"{s['id']}: missing RECONSTRUCTED label")
            if any("ATTESTED" in lb for lb in labels) or "RECONSTRUCTED PRONUNCIATION" in labels:
                passes.append(f"{s['id']}: attested/pronunciation honesty chips")
        timing = s.get("t_end", 0) - s.get("t_start", 0)
        if abs(timing - s.get("duration", 0)) > 0.5:
            issues.append(f"{s['id']}: timing mismatch t_start/t_end vs duration")

    corpus_path = resolve_corpus_path(corpus.get("language", ""))
    if corpus_path and corpus_path.is_file():
        known = json.loads(corpus_path.read_text(encoding="utf-8"))
        entry = next((t for t in known.get("texts", []) if t.get("id") == corpus.get("corpus_id")), None)
        if entry and entry.get("transliteration") == corpus.get("attested_text"):
            passes.append(f"attested_text matches corpus transliteration ({corpus.get('corpus_id')})")
        elif entry:
            issues.append("attested_text mismatch vs corpus")
        if entry and entry.get("confidence") == "attested":
            passes.append("corpus entry confidence: attested")
        if entry and entry.get("type") == "meta":
            issues.append("corpus_id points to meta entry — not speakable attested line")
    else:
        issues.append("corpus file missing")

    if corpus.get("line_ipa", "").startswith("["):
        passes.append("line IPA bracketed (reconstructed pronunciation)")

    if rules.get("require_overlay_burn"):
        if len(overlay_manifest) == len(script["shots"]):
            passes.append(f"overlay manifest complete ({len(overlay_manifest)} shots)")
        else:
            issues.append("overlay manifest incomplete")
        for entry in overlay_manifest:
            if not Path(entry["overlay_png"]).is_file():
                issues.append(f"missing overlay PNG: {entry['shot_id']}")
            if not Path(entry["burned_mp4"]).is_file():
                issues.append(f"missing burned MP4: {entry['shot_id']}")

        if burned_paths:
            raw = burned_paths[0].with_name(burned_paths[0].stem.replace("_burned", "_raw") + ".mp4")
            if raw.is_file():
                mid = probe_duration(raw) * 0.5
                raw_jpg = raw.with_suffix(".qa_raw.jpg")
                burned_jpg = burned_paths[0].with_suffix(".qa_burned.jpg")
                extract_frame(raw, mid, raw_jpg)
                extract_frame(burned_paths[0], mid, burned_jpg)
                raw_px = _label_bar_pixel(raw_jpg)
                burned_px = _label_bar_pixel(burned_jpg)
                if raw_px != burned_px:
                    passes.append("overlay burn verified (label region pixel change)")
                else:
                    issues.append("overlay burn not detected in label region")
                if _lower_third_dark(burned_jpg):
                    passes.append("lower-third IPA bar visible on burned frame")
                else:
                    issues.append("lower-third bar not detected on burned frame")
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
        card_label = prov.get("card_type", "provenance")
        passes.append(f"{card_label} card enabled ({prov.get('duration_s', 5)}s)")
        if prov.get("card_type") == "sources":
            src_count = len(prov.get("sources") or script.get("historical_figure", {}).get("sources") or [])
            if src_count >= 2:
                passes.append(f"sources card entries: {src_count}")
            else:
                issues.append("sources card missing citations")

    hf = script.get("historical_figure", {})
    if hf.get("figure_id"):
        passes.append(f"historical figure: {hf.get('figure_id')}")

    return {
        "slug": script.get("slug"),
        "qa_at": datetime.now(timezone.utc).isoformat(),
        "pass": len(issues) == 0,
        "passes": passes,
        "issues": issues,
        "corpus_id": corpus.get("corpus_id"),
        "attested_text": corpus.get("attested_text"),
        "line_ipa": corpus.get("line_ipa"),
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
    if not avatar_url:
        raise RuntimeError("Avatar URL missing — re-run render_host_identity.py")

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
            print(f"[proof] rendering {sid} ({shot['duration']}s, {resolution})…")
            resp = client.video.generate(
                prompt=shot["video_prompt"],
                model=model,
                image_url=avatar_url,
                duration=shot["duration"],
                resolution=resolution,
            )
            _download(resp.url, raw_path)
        elif concat_only and not raw_path.is_file():
            raise FileNotFoundError(f"--concat-only: missing {raw_path}")

        render_shot_overlay_png(shot, overlay_png)
        burn_overlay(raw_path, overlay_png, burned_path)
        print(f"[proof] burned overlays → {burned_path.name}")

        overlay_manifest.append({
            "shot_id": sid,
            "t_start": shot.get("t_start"),
            "t_end": shot.get("t_end"),
            "on_screen": shot.get("on_screen"),
            "on_screen_labels": shot.get("on_screen_labels", []),
            "speech_ipa": shot.get("speech_ipa"),
            "overlay_png": str(overlay_png),
            "raw_mp4": str(raw_path),
            "burned_mp4": str(burned_path),
        })
        burned_parts.append(burned_path)

    prov_png = prod_dir / "provenance_card.png"
    render_provenance_card(script, prov_png)
    prov_dur = float(script.get("provenance_card", {}).get("duration_s", 5))
    prov_mp4 = shots_dir / "provenance.mp4"
    provenance_to_video(prov_png, prov_mp4, prov_dur)
    burned_parts.append(prov_mp4)

    out_name = cfg.get("output_filename") or f"{slug}_480p_v1.mp4"
    final_mp4 = out_dir / out_name
    concat_videos(burned_parts, final_mp4)
    print(f"[proof] final → {final_mp4}")

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
        "provenance_card": str(prov_png),
        "qa": qa,
        "overlay_manifest": overlay_manifest,
    }


def main() -> int:
    import argparse

    parser = argparse.ArgumentParser(description="DAVID dead-language pronunciation proof (480p)")
    parser.add_argument(
        "script",
        nargs="?",
        default=SCRIPTS / "david_latin_pronunciation_proof_v1_script.json",
        type=Path,
    )
    parser.add_argument("--concat-only", action="store_true", help="Reuse cached raw shots; re-burn overlays")
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
        "pipeline": "render_dead_language_proof",
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