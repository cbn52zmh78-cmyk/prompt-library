#!/usr/bin/env python3
"""DAVID host identity lock — Issue #69.

Generates locked Archive set + DAVID avatar reference, renders 15–20s host
test clip (signature beat), writes reuse manifest for all episodes.
"""
from __future__ import annotations

import json
import os
import subprocess
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
PROD = ROOT / "productions" / "host_identity_v1"
SCRIPTS = ROOT / "scripts"
FFMPEG: str | None = None

if str(SCRIPTS) not in __import__("sys").path:
    __import__("sys").path.insert(0, str(SCRIPTS))
from render_longform import ARCHIVE_ANTI_MAGENTA_GENERATION_LOCK  # noqa: E402

ARCHIVE_SET_PROMPT = (
    "The Archive — a deep scholarly study and library interior, 16:9 cinematic wide shot, "
    "no people. D65 neutral balanced 5000K ambient light — frame midtones R≈G≈B within 8%, "
    "real blue present in shadow neutrals; no purple/magenta ambient, no pink wall bounce, "
    "no violet wood bounce. Floor-to-ceiling shelves hold manuscripts, scrolls, and clay tablets "
    "from many cultures receding into soft blur. A long wooden worktable in the foreground holds "
    "an open illuminated codex, a cuneiform clay tablet, a rolled papyrus scroll, and one recurring "
    "brass desk lamp casting a tight localized 3200K amber pool on the desk surface and lamp shade "
    "only — NOT a global amber wash, zero magenta spill on walls or shelves. Documentary prestige "
    "aesthetic, rich wood and parchment textures, instant-recognition recurring TV host desk energy "
    "but ancient-archive themed, photoreal cinematic lighting with neutral white balance."
)

DAVID_AVATAR_PROMPT = (
    "DAVID — synthetic keeper-of-the-Archive host, chest-up medium shot seated at the Archive "
    "worktable, 16:9. Male, reads age 45–55, dark hair flecked with silver neatly kept, lined "
    "intelligent face, calm attentive eyes. Charcoal fine-texture sweater, deep navy undertones, "
    "reading glasses pushed up into his hair, subtle worn leather strap detail on shoulder. "
    "Modern understated wardrobe NOT period costume. Still grounded presence, hands resting near "
    "open codex. D65 neutral balanced 5000K key on face — skin R≈G≈B within 8%, natural blue in "
    "skin midtones; no magenta/pink skin cast, no purple ambient; brass desk lamp 3200K visible as "
    "localized amber accent on desk beside him, not washing his face; manuscript shelves soft "
    "behind. Documentary gravitas, trustworthy linguist host, no real person likeness, no celebrity "
    "resemblance, invented face only."
)

HOST_TEST_SPEECH = (
    "What did they actually say? … And how do we prove it?"
)

HOST_SHOT_A_PROMPT = (
    "The Archive keeper host speaks directly to camera with measured documentary gravitas, "
    "lip-synced, mid-low resonant unhurried voice, precise diction, Attenborough-calm. "
    "He asks: 'What did they actually say?' Medium shot, still grounded at worktable near "
    "open codex, D65 neutral 5000K key on face with blue intact — no magenta/pink skin cast; "
    "brass lamp amber accent on desk only, calm attentive eyes. Synthetic host only."
)

HOST_SHOT_B_PROMPT = (
    "The Archive keeper host continues speaking to camera, lip-synced, same mid-low resonant "
    "unhurried voice. After a brief thoughtful pause he asks: 'And how do we prove it?' "
    "Subtle slow push-in to medium-close, quiet conviction, hands still, D65 neutral 5000K skin key "
    "— no purple ambient; lamp amber on desk surface only, not face wash. Synthetic host only, "
    "documentary trust signal."
)

VOICE_LOCK = {
    "register": "mid-low",
    "pace": "measured, unhurried",
    "tone": "documentary gravitas, Attenborough-calm, accessible never stuffy",
    "diction": "precise, resonant",
    "delight": "subtle warmth when teaching — composure default",
    "signature_beat": HOST_TEST_SPEECH,
    "prompt_suffix": "mid-low resonant unhurried voice, precise diction, documentary gravitas",
}


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
    req = urllib.request.Request(url, headers={"User-Agent": "DAVID-host/1.0"})
    with urllib.request.urlopen(req, timeout=300) as r:
        dest.write_bytes(r.read())


def _load_ref_meta(path: Path) -> dict[str, Any]:
    meta_path = path.with_suffix(".json")
    if meta_path.is_file():
        return json.loads(meta_path.read_text(encoding="utf-8"))
    return {}


def _save_ref_meta(path: Path, data: dict[str, Any]) -> None:
    meta_path = path.with_suffix(".json")
    meta_path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


def generate_archive_set(client: Any, out_dir: Path, *, force: bool = False) -> dict[str, Any]:
    path = out_dir / "archive_set_reference.jpg"
    if not force and path.exists() and path.stat().st_size > 5000:
        meta = _load_ref_meta(path)
        if meta.get("url"):
            print("[archive] reusing existing set plate")
            return {**meta, "path": str(path), "reused": True}

    set_prompt = f"{ARCHIVE_ANTI_MAGENTA_GENERATION_LOCK} {ARCHIVE_SET_PROMPT}"
    print("[archive] generating set plate…")
    resp = client.image.sample(prompt=set_prompt, model="grok-imagine-image-quality")
    _download(resp.url, path)
    data = {
        "path": str(path),
        "url": resp.url,
        "prompt": set_prompt,
        "lighting_lock": (
            "LIGHTING LOCK @Set-Archive-001 (#243/#218): D65 neutral 5000K ambient key — "
            "blue preserved in shadows; no magenta/purple ambient; brass lamp 3200K localized "
            "amber desk pool only."
        ),
        "model": "grok-imagine-image-quality",
        "aspect_ratio": "16:9",
        "spec": "T243_neutral_lighting_prompt_spec.json",
        "status": "REGENERATED",
        "reused": False,
    }
    _save_ref_meta(path, data)
    return data


def generate_david_avatar(
    client: Any,
    archive: dict[str, Any],
    out_dir: Path,
    *,
    force: bool = False,
) -> dict[str, Any]:
    path = out_dir / "david_avatar_reference.jpg"
    if not force and path.exists() and path.stat().st_size > 5000:
        meta = _load_ref_meta(path)
        if meta.get("url"):
            print("[david] reusing existing avatar reference")
            return {**meta, "path": str(path), "reused": True}

    avatar_prompt = f"{ARCHIVE_ANTI_MAGENTA_GENERATION_LOCK} {DAVID_AVATAR_PROMPT}"
    print("[david] generating avatar in Archive (image edit on set)…")
    archive_url = archive.get("url")
    if not archive_url:
        # re-upload not available — regenerate combined
        print("[david] no set URL — generating avatar with embedded set description")
        resp = client.image.sample(prompt=avatar_prompt, model="grok-imagine-image-quality")
    else:
        resp = client.image.sample(
            prompt=avatar_prompt,
            model="grok-imagine-image-quality",
            image_url=archive_url,
        )
    _download(resp.url, path)
    data = {
        "path": str(path),
        "url": resp.url,
        "prompt": avatar_prompt,
        "lighting_lock": (
            "LIGHTING LOCK @David-001 (#243/#218): D65 neutral 5000K white key on face and sweater — "
            "natural skin R≈G≈B, blue channel intact (B≥40 mids); no magenta cast; brass lamp 3200K "
            "tight amber desk accent only."
        ),
        "model": "grok-imagine-image-quality",
        "base_set": archive["path"],
        "aspect_ratio": "16:9",
        "spec": "T243_neutral_lighting_prompt_spec.json",
        "status": "REGENERATED",
        "synthetic_only": True,
        "no_real_person_likeness": True,
        "reused": False,
    }
    _save_ref_meta(path, data)
    return data


def _render_shot(
    client: Any,
    avatar_url: str,
    prompt: str,
    duration: int,
    dest: Path,
    label: str,
) -> None:
    if dest.exists() and dest.stat().st_size > 10000:
        print(f"[host] reusing {label}")
        return
    print(f"[host] rendering {label} ({duration}s)…")
    vid = client.video.generate(
        prompt=prompt,
        model="grok-imagine-video-1.5",
        image_url=avatar_url,
        duration=duration,
        resolution="720p",
    )
    dest.parent.mkdir(parents=True, exist_ok=True)
    _download(vid.url, dest)


def _concat_videos(parts: list[Path], out: Path) -> None:
    ff = _ffmpeg_exe()
    list_file = out.with_suffix(".txt")
    list_file.write_text("\n".join(f"file '{p.resolve()}'" for p in parts), encoding="utf-8")
    subprocess.run(
        [ff, "-y", "-f", "concat", "-safe", "0", "-i", str(list_file), "-c", "copy", str(out)],
        check=True,
        capture_output=True,
    )
    list_file.unlink(missing_ok=True)


def render_host_test(client: Any, avatar: dict[str, Any], out_dir: Path) -> dict[str, Any]:
    shots_dir = out_dir / "shots"
    shot_a = shots_dir / "01_what_did_they_say.mp4"
    shot_b = shots_dir / "02_how_do_we_prove_it.mp4"
    final_path = out_dir / "output" / "david_host_test_signature_beat_v1.mp4"
    dur_a, dur_b = 8, 10
    total_duration = dur_a + dur_b

    avatar_url = avatar.get("url")
    if not avatar_url:
        raise RuntimeError("Avatar URL required for video — delete cached avatar to regenerate")

    _render_shot(client, avatar_url, HOST_SHOT_A_PROMPT, dur_a, shot_a, "shot A")
    _render_shot(client, avatar_url, HOST_SHOT_B_PROMPT, dur_b, shot_b, "shot B")

    final_path.parent.mkdir(parents=True, exist_ok=True)
    if not final_path.exists() or final_path.stat().st_size < 10000:
        _concat_videos([shot_a, shot_b], final_path)

    return {
        "path": str(final_path),
        "shots": [str(shot_a), str(shot_b)],
        "duration_s": total_duration,
        "speech": HOST_TEST_SPEECH,
        "shot_prompts": {
            "01_what_did_they_say": HOST_SHOT_A_PROMPT,
            "02_how_do_we_prove_it": HOST_SHOT_B_PROMPT,
        },
        "model": "grok-imagine-video-1.5",
        "on_screen_caption": "DAVID · The Archive",
    }


def sync_identity_lock_refs(archive: dict[str, Any], avatar: dict[str, Any]) -> Path:
    """#218-B — sync canonical david_identity_lock.json after refs-only regen."""
    path = PROD / "david_identity_lock.json"
    lock: dict[str, Any] = {}
    if path.is_file():
        lock = json.loads(path.read_text(encoding="utf-8"))
    lock.setdefault("issue", 69)
    lock["locked_at"] = datetime.now(timezone.utc).isoformat()
    lock["status"] = "LOCKED"
    lock.setdefault("character", {
        "name": "DAVID",
        "role": "keeper of the Archive",
        "core_question": "What did they actually say — and how do we prove it?",
        "age_read": "45-55",
        "wardrobe": "charcoal/deep navy modern understated — NOT period costume",
        "set_name": "The Archive",
    })
    lock.setdefault("voice", VOICE_LOCK)
    lock["references"] = {
        "archive_set": {
            "file": archive["path"],
            "url": archive.get("url"),
            "prompt": archive["prompt"],
            "lighting_lock": archive.get("lighting_lock"),
            "anti_magenta_lock": ARCHIVE_ANTI_MAGENTA_GENERATION_LOCK,
            "reuse": "environment plate @1 — same set every episode",
        },
        "david_avatar": {
            "file": avatar["path"],
            "url": avatar.get("url"),
            "prompt": avatar["prompt"],
            "lighting_lock": avatar.get("lighting_lock"),
            "anti_magenta_lock": ARCHIVE_ANTI_MAGENTA_GENERATION_LOCK,
            "reuse": "host reference @2 — image_to_video frame 1 every DAVID host shot",
        },
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(lock, indent=2, ensure_ascii=False), encoding="utf-8")
    return path


def write_identity_lock(
    archive: dict[str, Any],
    avatar: dict[str, Any],
    host_clip: dict[str, Any],
) -> Path:
    lock = {
        "issue": 69,
        "locked_at": datetime.now(timezone.utc).isoformat(),
        "status": "LOCKED",
        "character": {
            "name": "DAVID",
            "role": "keeper of the Archive",
            "core_question": "What did they actually say — and how do we prove it?",
            "age_read": "45-55",
            "wardrobe": "charcoal/deep navy modern understated — NOT period costume",
            "set_name": "The Archive",
        },
        "references": {
            "archive_set": {
                "file": archive["path"],
                "url": archive.get("url"),
                "prompt": archive["prompt"],
                "lighting_lock": archive.get("lighting_lock"),
                "anti_magenta_lock": ARCHIVE_ANTI_MAGENTA_GENERATION_LOCK,
                "reuse": "environment plate @1 — same set every episode",
            },
            "david_avatar": {
                "file": avatar["path"],
                "url": avatar.get("url"),
                "prompt": avatar["prompt"],
                "lighting_lock": avatar.get("lighting_lock"),
                "anti_magenta_lock": ARCHIVE_ANTI_MAGENTA_GENERATION_LOCK,
                "reuse": "host reference @2 — image_to_video frame 1 every DAVID host shot",
            },
        },
        "voice": VOICE_LOCK,
        "host_test_clip": host_clip,
        "episode_reuse": {
            "host_shots": "Always start image_to_video from david_avatar_reference.jpg",
            "set_shots": "Regenerate or composite from archive_set_reference.jpg for wide establishes",
            "voice_prompt_suffix": VOICE_LOCK["prompt_suffix"],
            "signature_beat": VOICE_LOCK["signature_beat"],
            "on_screen_label": "DAVID · The Archive · attested text / reconstructed pronunciation",
        },
        "guardrails": [
            "synthetic only — no real-person likeness",
            "attested vs reconstructed labeled on screen and in delivery",
            "CC-BY-SA attribution in video description",
        ],
        "models": {
            "image": "grok-imagine-image-quality",
            "video": "grok-imagine-video-1.5",
            "resolution": "720p",
            "aspect_ratio": "16:9",
        },
    }
    path = PROD / "david_identity_lock.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(lock, indent=2, ensure_ascii=False), encoding="utf-8")
    return path


def _report_generation_gate(archive_path: Path, avatar_path: Path) -> None:
    import numpy as np
    from PIL import Image

    from color_cast_qa import (  # noqa: WPS433
        generation_reference_breaches,
        generation_reference_passes,
        measure_color_cast,
        measure_set_shadow_blue_health,
    )
    from t243_pre_render_gate import probe_magenta_score_image  # noqa: WPS433

    with Image.open(avatar_path) as img:
        avatar_arr = np.asarray(img.convert("RGB"))
        avatar_m = measure_color_cast(avatar_arr)
        avatar_mag = probe_magenta_score_image(avatar_arr)
    with Image.open(archive_path) as img:
        set_arr = np.asarray(img.convert("RGB"))
        set_m = measure_set_shadow_blue_health(set_arr)
        set_mag = probe_magenta_score_image(set_arr)
    print(
        f"[gate] avatar Bμ={avatar_m['host_blue_mean']:.1f} "
        f"B/R={avatar_m['host_br_ratio']:.3f} "
        f"magenta={avatar_mag:.4f} "
        f"pass={generation_reference_passes(avatar_m, host=True)}"
    )
    print(
        f"[gate] set_shadow Bμ={set_m['host_blue_mean']:.1f} "
        f"B/R={set_m['host_br_ratio']:.3f} "
        f"magenta={set_mag:.4f} "
        f"pass={generation_reference_passes(set_m, host=False)}"
    )
    if avatar_mag >= 0.42 or set_mag >= 0.42:
        print(f"[gate] FAIL raw magenta must be <0.42 (avatar={avatar_mag:.4f} set={set_mag:.4f})")
    if not generation_reference_passes(avatar_m, host=True):
        print(f"[gate] avatar breaches: {generation_reference_breaches(avatar_m, host=True)}")
    if not generation_reference_passes(set_m, host=False):
        print(f"[gate] set breaches: {generation_reference_breaches(set_m, host=False)}")


def main() -> int:
    import argparse

    parser = argparse.ArgumentParser(description="DAVID host identity lock — Issue #69")
    parser.add_argument(
        "--force-refs",
        action="store_true",
        help="Regenerate archive set + avatar stills (T243 neutral lighting prompts)",
    )
    parser.add_argument(
        "--refs-only",
        action="store_true",
        help="Regenerate reference stills only; skip host test clip",
    )
    args = parser.parse_args()

    import xai_sdk

    token = os.environ.get("XAI_API_KEY") or _load_grok_token()
    os.environ["XAI_API_KEY"] = token
    client = xai_sdk.Client(api_key=token)

    refs_dir = PROD / "references"
    refs_dir.mkdir(parents=True, exist_ok=True)

    archive = generate_archive_set(client, refs_dir, force=args.force_refs)
    avatar = generate_david_avatar(client, archive, refs_dir, force=args.force_refs)
    _report_generation_gate(Path(archive["path"]), Path(avatar["path"]))
    if args.refs_only:
        lock_path = sync_identity_lock_refs(archive, avatar)
        print(f"[sync] canonical identity_lock → {lock_path}")
        print(json.dumps({
            "archive_set": archive["path"],
            "david_avatar": avatar["path"],
            "identity_lock": str(lock_path),
        }, indent=2))
        return 0
    host_clip = render_host_test(client, avatar, PROD)
    lock_path = write_identity_lock(archive, avatar, host_clip)

    manifest = {
        "issue": 69,
        "completed_at": datetime.now(timezone.utc).isoformat(),
        "identity_lock": str(lock_path),
        "archive_set": archive["path"],
        "david_avatar": avatar["path"],
        "host_test_clip": host_clip["path"],
    }
    manifest_path = PROD / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(manifest, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())