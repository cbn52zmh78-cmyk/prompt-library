#!/usr/bin/env python3
"""DAVID Post 1 — PIE hybrid host format (Issue #70).

Format proof #2: DAVID hosts in the Archive → reconstructed PIE line (heavy
RECONSTRUCTED labels) → comparative-method explainer → provenance card.

Requires locked host identity from render_host_identity.py (Issue #69).
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import textwrap
import urllib.request
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
HOST_PROD = ROOT / "productions" / "host_identity_v1"
PROD = ROOT / "productions" / "post_01_pie_hybrid_v1"
FFMPEG: str | None = None

VOICE_SUFFIX = (
    "mid-low resonant unhurried voice, precise diction, documentary gravitas, "
    "Attenborough-calm, accessible never stuffy, synthetic host only"
)


@dataclass
class PieHybridSpec:
    slug: str = "proto-indo-european"
    status: str = "reconstructed"
    title: str = "Post 1 — The Mother Tongue of English (Proto-Indo-European)"
    corpus_id: str = "schleicher-fable-opener"
    reconstructed_text: str = "*h₂éwis, h₁éḱwōs h₁éḱontes"
    reconstructed_text_spoken: str = "h₂éwis, h₁éḱwōs h₁éḱontes"
    translation: str = "The sheep and the horses (were) going…"
    text_confidence: str = "reconstructed"
    pronunciation_model: str = "reconstructed late PIE phonology (laryngeal theory)"
    pronunciation_confidence: str = "moderate — scholarly consensus with debated laryngeal detail"
    line_ipa: str = "[ˈh₂é.wis ˈh₁é.kʷoːs ˈh₁é.kʷon.tes]"
    text_source: str = (
        "August Schleicher, Compendium der vergleichenden Grammatik (1861/62); "
        "modern recension Schleicher's Fable"
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
    req = urllib.request.Request(url, headers={"User-Agent": "DAVID-post01/1.0"})
    with urllib.request.urlopen(req, timeout=300) as r:
        dest.write_bytes(r.read())


def load_identity_lock() -> dict[str, Any]:
    lock_path = HOST_PROD / "david_identity_lock.json"
    if not lock_path.is_file():
        raise RuntimeError(
            f"Host identity not locked — run: python DAVID/scripts/render_host_identity.py\n"
            f"Expected: {lock_path}"
        )
    lock = json.loads(lock_path.read_text(encoding="utf-8"))
    if lock.get("status") != "LOCKED":
        raise RuntimeError(f"Host identity lock status is not LOCKED: {lock_path}")
    return lock


def _load_scrape() -> dict[str, Any]:
    path = ROOT / "languages" / "reconstructed" / "proto-indo-european" / "research" / "brain" / "latest_scrape.json"
    return json.loads(path.read_text(encoding="utf-8"))


def build_shots(spec: PieHybridSpec) -> list[dict[str, Any]]:
    cold_open_speech = (
        "Before Latin. Before Greek. Before anything was written down — "
        "there was one language. No one ever recorded it. "
        "And yet we can rebuild it… from its children."
    )
    question_speech = "What did they actually say? … And how do we prove it?"
    method_speech = (
        "We compare its daughters — Latin, Sanskrit, Old English — "
        "and work backward to the sound that must have stood behind them all. "
        "That's the comparative method. It's reconstruction, not a recording — "
        "and we'll always tell you which is which."
    )
    tagline_speech = "Bring the dead tongues back — one attestation at a time. DAVID."

    return [
        {
            "id": "01_host_cold_open",
            "role": "host",
            "t_start": 0,
            "t_end": 6,
            "duration": 6,
            "on_screen": "DAVID · The Archive · 🔶 RECONSTRUCTED",
            "on_screen_labels": ["RECONSTRUCTED language"],
            "video_prompt": (
                f"The Archive keeper host speaks directly to camera in English, lip-synced, "
                f"measured documentary gravitas, {VOICE_SUFFIX}. "
                f'Delivers slowly: "{cold_open_speech}" '
                f"Subtle slow push-in, warm brass lamp on face, hands near open codex on worktable."
            ),
            "speech_text": cold_open_speech,
            "speech_lang": "en",
            "pace": "slow",
        },
        {
            "id": "02_host_question",
            "role": "host",
            "t_start": 6,
            "t_end": 11,
            "duration": 5,
            "on_screen": "What did they actually say?",
            "on_screen_labels": [],
            "video_prompt": (
                f"Host push-in medium-close, speaks signature beat in English, lip-synced, "
                f"thoughtful pause between clauses, {VOICE_SUFFIX}. "
                f'Delivers: "{question_speech}" Still grounded, trustworthy delivery.'
            ),
            "speech_text": question_speech,
            "speech_lang": "en",
            "pace": "measured",
        },
        {
            "id": "03_host_pie_line",
            "role": "host_pie",
            "t_start": 11,
            "t_end": 26,
            "duration": 15,
            "on_screen": (
                f"{spec.reconstructed_text}\n{spec.line_ipa}\n"
                "RECONSTRUCTED — NOT ATTESTED"
            ),
            "on_screen_labels": [
                "RECONSTRUCTED text",
                "RECONSTRUCTED pronunciation",
                "NOT ATTESTED",
            ],
            "video_prompt": (
                "The same Archive host now speaks reconstructed Proto-Indo-European slowly and "
                "clearly, lip-synced, scholarly documentary tone, never claiming it is a recording. "
                f'PIE line: "{spec.reconstructed_text_spoken}" '
                f"IPA target {spec.line_ipa}. "
                "On-screen feel: bold RECONSTRUCTED warning tags, asterisk forms visible. "
                f"{VOICE_SUFFIX}. Steady medium shot, lamp light, deliberate pace."
            ),
            "speech_text": spec.reconstructed_text_spoken,
            "speech_ipa": spec.line_ipa,
            "speech_lang": "pie-reconstructed",
            "pace": "slow-didactic",
        },
        {
            "id": "04_host_comparative_method",
            "role": "host",
            "t_start": 26,
            "t_end": 36,
            "duration": 10,
            "on_screen": "Comparative method · Latin ovis ← *h₂éwis · Sanskrit ávi- · English ewe",
            "on_screen_labels": ["RECONSTRUCTED inference"],
            "video_prompt": (
                f"Host back in Archive, gestures toward manuscripts on table while explaining in "
                f"English, lip-synced, {VOICE_SUFFIX}. "
                f'Delivers: "{method_speech}" '
                "Educational hand gesture toward codex, calm authority, honesty about uncertainty."
            ),
            "speech_text": method_speech,
            "speech_lang": "en",
            "pace": "didactic",
        },
        {
            "id": "05_tagline_vo",
            "role": "host",
            "t_start": 36,
            "t_end": 42,
            "duration": 6,
            "on_screen": "DAVID",
            "on_screen_labels": [],
            "video_prompt": (
                f"Host warm close, speaks tagline in English, lip-synced, {VOICE_SUFFIX}. "
                f'Delivers: "{tagline_speech}" Slight smile of quiet wonder, medium close-up.'
            ),
            "speech_text": tagline_speech,
            "speech_lang": "en",
            "pace": "warm",
        },
    ]


def finalize_script(spec: PieHybridSpec, shots: list[dict[str, Any]], scrape: dict[str, Any], lock: dict[str, Any]) -> dict[str, Any]:
    return {
        "issue": 70,
        "format": "hybrid_host",
        "format_proof": 2,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "slug": spec.slug,
        "title": spec.title,
        "post_number": 1,
        "channel_title": "The Mother Tongue of English — Reconstructed",
        "reconstructed_text": spec.reconstructed_text,
        "translation": spec.translation,
        "text_confidence": spec.text_confidence,
        "pronunciation_model": spec.pronunciation_model,
        "pronunciation_confidence": spec.pronunciation_confidence,
        "line_ipa": spec.line_ipa,
        "line_ipa_derivation": {
            "method": "reconstructed late PIE from Schleicher fable recension + laryngeal theory",
            "not_from_scrape": "Wiktionary scrape holds English name IPA only, not excerpt IPA",
            "language_ipa_from_scrape": scrape.get("wiktionary", {}).get("ipa_entries", []),
            "wikipedia_url": scrape.get("wikipedia", {}).get("url"),
        },
        "on_screen_labels": {
            "text": "RECONSTRUCTED — NOT ATTESTED",
            "pronunciation": "RECONSTRUCTED pronunciation",
        },
        "identity_lock": str(HOST_PROD / "david_identity_lock.json"),
        "host_reference": lock["references"]["david_avatar"]["file"],
        "shots": shots,
        "total_duration_target_s": 49,
        "provenance": {
            "text": f"{spec.text_source}. Reconstructed — not attested.",
            "pronunciation": f"{spec.pronunciation_model}; {spec.pronunciation_confidence}.",
            "citation": "https://en.wikipedia.org/wiki/Schleicher%27s_fable",
            "sources": "Wikipedia / Wiktionary (CC BY-SA), Wikidata (CC0), retrieved 2026-06-18.",
            "brain_scrape": "languages/reconstructed/proto-indo-european/research/brain/latest_scrape.json",
            "scrape_at": scrape.get("scraped_at", ""),
        },
    }


def render_provenance_card(spec: PieHybridSpec, script: dict[str, Any], out_path: Path) -> None:
    from PIL import Image, ImageDraw, ImageFont

    w, h = 1280, 720
    img = Image.new("RGB", (w, h), (12, 14, 20))
    draw = ImageDraw.Draw(img)
    try:
        title_font = ImageFont.truetype("arial.ttf", 40)
        warn_font = ImageFont.truetype("arialbd.ttf", 32)
        body_font = ImageFont.truetype("arial.ttf", 24)
        small_font = ImageFont.truetype("arial.ttf", 20)
    except OSError:
        title_font = ImageFont.load_default()
        warn_font = title_font
        body_font = title_font
        small_font = title_font

    draw.rectangle([(40, 40), (w - 40, h - 40)], outline=(200, 120, 50), width=4)
    draw.rectangle([(55, 55), (w - 55, 110)], fill=(80, 45, 20))
    draw.text((70, 62), "RECONSTRUCTED — NOT ATTESTED", fill=(255, 200, 120), font=warn_font)
    draw.text((70, 130), "DAVID · PROVENANCE · Post 1", fill=(220, 190, 120), font=title_font)
    draw.text((70, 180), spec.title, fill=(240, 240, 245), font=body_font)

    lines = [
        f"TEXT [reconstructed]: {script['provenance']['text']}",
        f"PRONUNCIATION [reconstructed]: {script['provenance']['pronunciation']}",
        f"LINE: {spec.reconstructed_text}",
        f"IPA: {spec.line_ipa}",
        f"TRANSLATION: {spec.translation}",
        f"CITATION: {script['provenance']['citation']}",
        f"SOURCES: {script['provenance']['sources']}",
        f"BRAIN: {script['provenance']['brain_scrape']}",
    ]
    y = 230
    for line in lines:
        for wrapped in textwrap.wrap(line, width=78):
            draw.text((70, y), wrapped, fill=(200, 205, 215), font=small_font)
            y += 28

    draw.text(
        (70, h - 70),
        "reconstructed text · reconstructed pronunciation · comparative method",
        fill=(255, 180, 90),
        font=small_font,
    )
    out_path.parent.mkdir(parents=True, exist_ok=True)
    img.save(out_path)


def provenance_to_video(png: Path, mp4: Path, duration: float = 7.0) -> None:
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
    list_file.write_text("\n".join(f"file '{p.resolve()}'" for p in parts), encoding="utf-8")
    subprocess.run(
        [ff, "-y", "-f", "concat", "-safe", "0", "-i", str(list_file), "-c", "copy", str(out)],
        check=True,
        capture_output=True,
    )
    list_file.unlink(missing_ok=True)


def qa_check(spec: PieHybridSpec, script: dict[str, Any], lock: dict[str, Any]) -> dict[str, Any]:
    issues: list[str] = []
    passes: list[str] = []

    if lock.get("status") == "LOCKED":
        passes.append("host identity lock LOADED")
    else:
        issues.append("host identity not LOCKED")

    if spec.text_confidence == "reconstructed":
        passes.append("text labeled reconstructed")
    if spec.line_ipa.startswith("[") and "h₂" in spec.line_ipa:
        passes.append("line IPA bracketed with laryngeal notation")

    pie_shot = next(s for s in script["shots"] if s["id"] == "03_host_pie_line")
    labels = pie_shot.get("on_screen_labels", [])
    if any("RECONSTRUCTED" in lb for lb in labels) and any("NOT ATTESTED" in lb for lb in labels):
        passes.append("PIE shot has heavy RECONSTRUCTED + NOT ATTESTED labels")
    else:
        issues.append("PIE shot missing required honesty labels")

    if len(script["shots"]) == 5:
        passes.append("hybrid host shot structure complete (5 host + provenance)")

    return {
        "issue": 70,
        "slug": spec.slug,
        "qa_at": datetime.now(timezone.utc).isoformat(),
        "pass": len(issues) == 0,
        "passes": passes,
        "issues": issues,
    }


def render_post(client: Any, *, render_video: bool = True) -> dict[str, Any]:
    lock = load_identity_lock()
    avatar_url = lock["references"]["david_avatar"].get("url")
    if not avatar_url:
        raise RuntimeError(
            "Avatar URL missing from identity lock — delete cached avatar and re-run "
            "render_host_identity.py to regenerate with URL"
        )

    scrape = _load_scrape()
    spec = PieHybridSpec()
    clip_dir = PROD
    shots_dir = clip_dir / "shots"
    shots_dir.mkdir(parents=True, exist_ok=True)

    shots = build_shots(spec)
    script = finalize_script(spec, shots, scrape, lock)
    script_path = clip_dir / "post01_pie_script_final.json"
    script_path.write_text(json.dumps(script, indent=2, ensure_ascii=False), encoding="utf-8")

    pack = {
        "issue": 70,
        "format": "hybrid_host",
        "model_video": "grok-imagine-video-1.5",
        "resolution": "720p",
        "aspect_ratio": "16:9",
        "host_reference": lock["references"]["david_avatar"]["file"],
        "avatar_url": avatar_url,
        "shots": [
            {
                "shot_id": s["id"],
                "duration": s["duration"],
                "image_url": avatar_url,
                "video_prompt": s["video_prompt"],
                "speech_text": s["speech_text"],
                "on_screen": s["on_screen"],
                "on_screen_labels": s.get("on_screen_labels", []),
                "timing": {"start_s": s["t_start"], "end_s": s["t_end"]},
            }
            for s in script["shots"]
        ],
        "provenance_shot": {"type": "code_rendered_png", "duration_s": 7},
    }
    pack_path = clip_dir / "post01_pie_imagine_pack.json"
    pack_path.write_text(json.dumps(pack, indent=2, ensure_ascii=False), encoding="utf-8")

    rendered: list[Path] = []
    if render_video:
        for shot in script["shots"]:
            out = shots_dir / f"{shot['id']}.mp4"
            if out.exists() and out.stat().st_size > 10000:
                print(f"[post01] reusing {out.name}")
                rendered.append(out)
                continue
            print(f"[post01] rendering {shot['id']} ({shot['duration']}s)…")
            vid = client.video.generate(
                prompt=shot["video_prompt"],
                model="grok-imagine-video-1.5",
                image_url=avatar_url,
                duration=shot["duration"],
                resolution="720p",
            )
            _download(vid.url, out)
            rendered.append(out)

    prov_png = clip_dir / "provenance_card.png"
    render_provenance_card(spec, script, prov_png)
    prov_mp4 = shots_dir / "06_provenance.mp4"
    provenance_to_video(prov_png, prov_mp4, duration=7.0)
    rendered.append(prov_mp4)

    final_mp4 = clip_dir / "output" / "david_post01_pie_hybrid_v1.mp4"
    final_mp4.parent.mkdir(parents=True, exist_ok=True)
    concat_videos(rendered, final_mp4)
    print(f"[post01] final → {final_mp4}")

    qa = qa_check(spec, script, lock)
    qa_path = clip_dir / "qa_report.json"
    qa_path.write_text(json.dumps(qa, indent=2, ensure_ascii=False), encoding="utf-8")

    return {
        "script": str(script_path),
        "imagine_pack": str(pack_path),
        "provenance_card": str(prov_png),
        "output": str(final_mp4),
        "qa": qa,
    }


def main() -> int:
    import xai_sdk

    script_only = "--script-only" in sys.argv
    token = os.environ.get("XAI_API_KEY") or _load_grok_token()
    os.environ["XAI_API_KEY"] = token

    if script_only:
        lock = load_identity_lock()
        scrape = _load_scrape()
        spec = PieHybridSpec()
        script = finalize_script(spec, build_shots(spec), scrape, lock)
        out = PROD / "post01_pie_script_final.json"
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(script, indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"Script only → {out}")
        return 0

    client = xai_sdk.Client(api_key=token)
    result = render_post(client)

    manifest = {
        "issue": 70,
        "format": "hybrid_host",
        "format_proof": 2,
        "completed_at": datetime.now(timezone.utc).isoformat(),
        "production_dir": str(PROD),
        "post": result,
    }
    manifest_path = PROD / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(manifest, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())