"""
render_longform_ARCHITECTURE_EXCERPT.py
========================================
Trimmed architecture excerpt from render_longform.py (full file: 3,944 lines).

Purpose: paste into Grok Heavy browser for pipeline review.
Source:  DAVID/scripts/render_longform.py  (commit ~578a7ba, 2026-06-28)

OMITTED FROM FULL FILE (still exist in production):
  - ffmpeg post-processing (magenta clamp, loudnorm, xfade assembly, label chips)
  - seamless extend + frame-chain performance paths (~800 lines)
  - PromptDirector / qa_gate wiring details
  - generation reference gate (T243 blue-channel)
  - package_episode upload kit stage
  - pronunciation chip overlays, science @2 viz swap proofs

REFERENCE SLOT MODEL (ELEANOR-DAVID / MATILDA)
----------------------------------------------
  @1  Environment zone plate — EMPTY SET ONLY (no people, no props)
      → productions/<slug>/plates/@1_plate.jpg (copied from Set_Library)
      → NEVER composited with @2 — pre-composite destroys identity / ages face
      → NOT passed to video.generate — set continuity is in video_prompt only

  @2  Talent casting reference — isolated presenter still (white-bg turntable)
      → config.avatar_reference → uploaded as avatar_url
      → THIS is the video.generate image_url seed for host shots
      → Grok places @2 into @Set-* from prompt; do not bake presenter into @1

  @2 (science)  visualization_url — locked science plate for viz shots

IMAGE SEED PRIORITY (resolve_shot_image_url):
  1. shot.image_url (explicit override)
  2. visualization_url  (science @2 viz)
  3. avatar_url         (host @2 casting — ALWAYS for MATILDA/DAVID-style host)
  4. @N zone plate URL   (fallback only if no avatar_url — rarely used)

PIPELINE FLOW
-------------
  script.json
    → normalize_script()
    → assert_gate_0_cleared()          # human_signoff, music row_2 PASS
    → resolve_refs()                 # avatar_url, set_file, voice_suffix
    → ensure_zone_plates()           # if use_zone_plates + set_reference
    → build_imagine_pack()           # audit manifest per shot
    → FOR EACH shot:
         resolve_shot_image_url()     # @2 avatar casting seed
         client.video.generate(prompt, image_url=..., duration=...)
    → concat_videos() → output/*.mp4
    → qa_check() → qa_report.json

CLI
---
  python render_longform.py <script.json>
  python render_longform.py <script.json> --force-plates --force-all
  python render_longform.py <script.json> --seamless
  python render_longform.py <script.json> --concat-only
  python render_longform.py <script.json> --script-only --package

EXAMPLE SCRIPT CONFIG (MATILDA baseline):
  use_identity_lock: false
  use_zone_plates: true
  avatar_reference: AI/ELEANOR/.../grok-image-d25e8689....jpg   # @2 casting
  set_reference: STUDIO/Pipeline/references/warehouse_industrial_reference.jpg  # @1 source
"""

from __future__ import annotations

# --- imports (abbreviated) ---
import argparse
import json
import re
import shutil
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
WORKSPACE = ROOT.parent
SET_LIBRARY_PATH = WORKSPACE / "Studio" / "Pipeline" / "Set_Library_v1.json"
DEFAULT_VOICE_SUFFIX = "mid-low resonant unhurried voice, synthetic host only"
SYNTHETIC_GUARD = "synthetic host only"


def _log(*args: Any, **kwargs: Any) -> None:
    kwargs.setdefault("file", sys.stderr)
    print(*args, **kwargs)


def _resolve_workspace_path(rel: str) -> Path:
    rel = str(rel).replace("\\", "/")
    if rel.split("/", 1)[0].lower() == "studio":
        return WORKSPACE / rel
    return WORKSPACE / rel if "/" in rel else ROOT / rel


def upload_image_url(client: Any, image_path: Path) -> str:
    uploaded = client.files.upload(str(image_path))
    pub = client.files.create_public_url(uploaded.id)
    return getattr(pub, "public_url", None) or pub.public_url


def _api_pace() -> None:
    import time
    time.sleep(1.25)


# ===========================================================================
# ZONE PLATES (@1 empty environment)
# ===========================================================================

def _shot_uses_viz_reference(shot: dict[str, Any]) -> bool:
    slots = shot.get("reference_slots") or {}
    if slots.get("@2") == "visualization":
        return True
    return shot.get("role") == "visualization" or shot.get("use_avatar") is False


def _extract_zone(text: str) -> str | None:
    if not text:
        return None
    m = re.search(r"\(@(\d+)", text)
    if m:
        return f"@{m.group(1)}"
    m = re.search(r"@(\d+)\b", text)
    return f"@{m.group(1)}" if m else None


def _shot_zone(shot: dict[str, Any]) -> str | None:
    raw = shot.get("zone")
    if raw:
        z = str(raw).strip()
        return z if z.startswith("@") else f"@{z}"
    return _extract_zone(shot.get("video_prompt", ""))


def _needs_zone_plates(script: dict[str, Any], refs: dict[str, Any]) -> bool:
    """MATILDA-style: isolated @2 casting ref + set_reference → seed video from @1 empty set."""
    cfg = script.get("config") or {}
    if cfg.get("use_zone_plates") is False:
        return False
    if not refs.get("set_file"):
        return False
    if cfg.get("use_zone_plates") is True:
        return True
    if cfg.get("avatar_in_set"):
        return False
    lock = refs.get("lock") or {}
    talent = (lock.get("references") or {}).get("talent_avatar") or {}
    if cfg.get("use_identity_lock", True) and talent.get("url"):
        return False  # DAVID Archive: avatar already composited in set
    return bool(refs.get("avatar_file") or refs.get("avatar_url"))


def _load_plate_sidecar(path: Path) -> dict[str, Any]:
    meta = path.with_suffix(".json")
    if not meta.is_file():
        return {}
    return json.loads(meta.read_text(encoding="utf-8"))


def _save_plate_sidecar(path: Path, data: dict[str, Any]) -> None:
    path.with_suffix(".json").write_text(
        json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8"
    )


def _load_set_library() -> dict[str, Any]:
    return json.loads(SET_LIBRARY_PATH.read_text(encoding="utf-8"))


def _extract_set_id(text: str) -> str | None:
    m = re.search(r"@Set-[\w-]+", text)
    return m.group(0) if m else None


def _resolve_environment_plate_file(
    script: dict[str, Any],
    refs: dict[str, Any],
) -> tuple[Path, str | None]:
    set_id = _extract_set_id(
        str(refs.get("set_file") or "")
        + " " + json.dumps(script.get("intake") or {})
        + " " + json.dumps(script.get("config") or {})
    )
    candidates: list[Path] = []
    if refs.get("set_file"):
        sf = Path(str(refs["set_file"]))
        if sf.is_file():
            candidates.append(sf)
    if set_id:
        ref_file = ((_load_set_library().get("sets") or {}).get(set_id) or {}).get("reference_file")
        if ref_file:
            rp = _resolve_workspace_path(str(ref_file))
            if rp.is_file() and rp not in candidates:
                candidates.append(rp)
    if not candidates:
        raise RuntimeError(f"No empty environment plate for set {set_id}")
    return candidates[0], set_id


def generate_zone_plate(
    zone_id: str,
    client: Any,
    refs: dict[str, Any],
    plates_dir: Path,
    script: dict[str, Any],
    *,
    force: bool = False,
) -> dict[str, Any]:
    """@1 = empty environment only. No talent composite. No Grok image generation."""
    plates_dir.mkdir(parents=True, exist_ok=True)
    plate_path = plates_dir / f"{zone_id}_plate.jpg"
    meta = _load_plate_sidecar(plate_path)
    if (
        not force
        and plate_path.is_file()
        and meta.get("plate_type") == "environment_empty"
        and meta.get("no_people") is True
        and meta.get("url")
    ):
        _log(f"[zone] reusing empty {zone_id} environment plate")
        return {**meta, "path": str(plate_path), "reused": True}

    source_path, set_id = _resolve_environment_plate_file(script, refs)
    if source_path.resolve() != plate_path.resolve():
        shutil.copy2(source_path, plate_path)
    _log(f"[zone] locking empty {zone_id} environment plate from {source_path.name}")
    plate_url = upload_image_url(client, plate_path)

    data = {
        "zone_id": zone_id,
        "plate_type": "environment_empty",
        "no_people": True,
        "path": str(plate_path),
        "url": plate_url,
        "source_file": str(source_path),
        "set_id": set_id,
        "avatar_reference": refs.get("avatar_url"),
        "note": "@1 empty set — performer from @2 casting ref + video prompt",
        "status": "LOCKED",
        "reused": False,
    }
    _save_plate_sidecar(plate_path, data)
    return data


def ensure_zone_plates(
    script: dict[str, Any],
    refs: dict[str, Any],
    client: Any,
    plates_dir: Path,
    *,
    force: bool = False,
) -> None:
    if not _needs_zone_plates(script, refs):
        return
    zones: set[str] = set()
    for shot in script.get("shots", []):
        if shot.get("role", "host") == "card" or _shot_uses_viz_reference(shot):
            continue
        if z := _shot_zone(shot):
            zones.add(z)
    if not zones:
        zones.add("@1")
    for zone_id in sorted(zones):
        plate = generate_zone_plate(zone_id, client, refs, plates_dir, script, force=force)
        refs[f"{zone_id}_plate_url"] = plate["url"]
        refs[f"{zone_id}_plate_file"] = plate["path"]


def get_pure_character_seed(
    shot: dict[str, Any],
    refs: dict[str, Any],
    *,
    use_avatar: bool = True,
) -> str:
    """@2-only seed — avatar_url or visualization_url; never @1 zone plates."""
    if shot.get("image_url"):
        return str(shot["image_url"])
    if _shot_uses_viz_reference(shot) or not use_avatar:
        if refs.get("visualization_url"):
            return str(refs["visualization_url"])
    if not refs.get("avatar_url"):
        raise RuntimeError(f"Shot {shot.get('id')}: no @2 avatar_url")
    return str(refs["avatar_url"])


def resolve_shot_image_url(shot: dict[str, Any], refs: dict[str, Any]) -> str:
    use_avatar = not _shot_uses_viz_reference(shot)
    return get_pure_character_seed(shot, refs, use_avatar=use_avatar)


# ===========================================================================
# GATE 0 + REF RESOLUTION
# ===========================================================================

def assert_gate_0_cleared(script: dict[str, Any]) -> None:
    intake = script.get("intake") or {}
    gate = intake.get("gate_0") or {}
    if not gate:
        return
    if gate.get("blocked") or gate.get("verdict") == "RED":
        raise SystemExit(f"Gate 0 RED — render blocked. Report: {gate.get('report_path')}")
    if gate.get("requires_human_signoff") and not gate.get("human_signoff"):
        raise SystemExit("Gate 0 — human sign-off required")
    if gate.get("music_bed_id") and gate.get("row_2_music_sync") != "PASS":
        raise SystemExit(
            f"Gate 0 row 2 music/sync FAIL for {gate.get('music_bed_id')}"
        )


def resolve_production_dir(script: dict[str, Any]) -> Path:
    slug = script.get("slug", "longform")
    return ROOT / "productions" / f"{slug}_longform_v1"


def resolve_refs(script: dict[str, Any], *, client: Any = None) -> dict[str, Any]:
    cfg = script.setdefault("config", {})
    avatar_url = cfg.get("avatar_url")
    avatar_file = cfg.get("avatar_reference")
    set_file = cfg.get("set_reference")

    if avatar_file:
        ap = _resolve_workspace_path(str(avatar_file))
        if ap.is_file():
            avatar_file = str(ap)
    if set_file:
        sp = _resolve_workspace_path(str(set_file))
        if sp.is_file():
            set_file = str(sp)

    if not avatar_url and avatar_file and client:
        avatar_url = upload_image_url(client, Path(avatar_file))
        cfg["avatar_url"] = avatar_url

    return {
        "avatar_url": avatar_url,
        "avatar_file": avatar_file,
        "set_file": set_file,
        "voice_suffix": cfg.get("voice_suffix", DEFAULT_VOICE_SUFFIX),
        "model_video": cfg.get("model_video", "grok-imagine-video-1.5"),
        "resolution": cfg.get("resolution", "720p"),
        "lock": {},
    }


def ensure_voice_in_prompt(prompt: str, voice_suffix: str) -> str:
    if voice_suffix.lower() not in prompt.lower():
        prompt = f"{prompt.rstrip()} {voice_suffix}"
    if "synthetic" not in prompt.lower():
        prompt = f"{prompt.rstrip()} {SYNTHETIC_GUARD}"
    return prompt


def build_imagine_pack(script: dict[str, Any], refs: dict[str, Any]) -> dict[str, Any]:
    return {
        "slug": script.get("slug"),
        "avatar_url": refs.get("avatar_url"),
        "set_reference": refs.get("set_file"),
        "zone_plates": {
            k.replace("_plate_url", ""): v
            for k, v in refs.items()
            if k.endswith("_plate_url")
        },
        "shots": [
            {
                "shot_id": s["id"],
                "duration": s["duration"],
                "image_url": resolve_shot_image_url(s, refs),
                "video_prompt": ensure_voice_in_prompt(s["video_prompt"], refs["voice_suffix"]),
                "speech_text": s.get("speech_text", ""),
            }
            for s in script["shots"]
        ],
    }


# ===========================================================================
# RENDER LOOP (hard-cut path — non --seamless)
# ===========================================================================

def render_longform(
    script: dict[str, Any],
    *,
    client: Any = None,
    force_all: bool = False,
    force_plates: bool = False,
) -> dict[str, Any]:
    prod_dir = resolve_production_dir(script)
    shots_dir = prod_dir / "shots"
    shots_dir.mkdir(parents=True, exist_ok=True)

    refs = resolve_refs(script, client=client)
    plates_dir = prod_dir / "plates"
    if _needs_zone_plates(script, refs) and client:
        ensure_zone_plates(
            script, refs, client, plates_dir,
            force=force_plates or force_all,
        )

    pack_path = prod_dir / f"{script.get('slug')}_imagine_pack.json"
    pack_path.write_text(
        json.dumps(build_imagine_pack(script, refs), indent=2), encoding="utf-8"
    )

    final_mp4 = prod_dir / "output" / f"david_{script.get('slug')}_longform_v1.mp4"
    final_mp4.parent.mkdir(parents=True, exist_ok=True)
    rendered: list[Path] = []

    for shot in script["shots"]:
        sid = shot["id"]
        out = shots_dir / f"{sid}.mp4"
        if out.exists() and out.stat().st_size > 10000 and not force_all:
            _log(f"[longform] reusing {out.name}")
            rendered.append(out)
            continue

        prompt = ensure_voice_in_prompt(shot["video_prompt"], refs["voice_suffix"])
        image_url = resolve_shot_image_url(shot, refs)
        _log(f"[longform] rendering {sid} ({shot['duration']}s) seed={image_url[:60]}…")
        _api_pace()
        vid = client.video.generate(
            prompt=prompt,
            model=refs["model_video"],
            image_url=image_url,
            duration=shot["duration"],
            resolution=refs["resolution"],
        )
        # _download(vid.url, out)  # omitted — see full render_longform.py
        rendered.append(out)

    # concat_videos(rendered, final_mp4)  # omitted
    _log(f"[longform] final → {final_mp4}")
    return {"output": str(final_mp4), "production_dir": str(prod_dir)}


# ===========================================================================
# CLI
# ===========================================================================

def main() -> int:
    parser = argparse.ArgumentParser(description="DAVID long-form video assembler")
    parser.add_argument("script", type=Path)
    parser.add_argument("--concat-only", action="store_true")
    parser.add_argument("--script-only", action="store_true")
    parser.add_argument("--force-all", action="store_true")
    parser.add_argument("--force-plates", action="store_true",
                        help="Re-lock @1 zone plates (empty environment from set_reference)")
    parser.add_argument("--seamless", action="store_true",
                        help="extend-primary + xfade chain (see full file)")
    args = parser.parse_args()

    script = json.loads(args.script.read_text(encoding="utf-8"))
    assert_gate_0_cleared(script)

    import xai_sdk
    client = xai_sdk.Client()
    render_longform(
        script,
        client=client,
        force_all=args.force_all,
        force_plates=args.force_plates,
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())


# ===========================================================================
# EXAMPLE script.json config block (MATILDA baseline 30s)
# ===========================================================================
EXAMPLE_CONFIG = """
{
  "slug": "matilda_baseline_30s",
  "format_id": "documentary-host",
  "intake": {
    "actor_id": "Matilda-001",
    "set_id": "@Set-Warehouse-Industrial-001",
    "gate_0": {
      "verdict": "GREEN",
      "human_signoff": true,
      "music_bed_id": "BED-DOC-001",
      "row_2_music_sync": "PASS"
    }
  },
  "config": {
    "model_video": "grok-imagine-video-1.5",
    "resolution": "480p",
    "use_identity_lock": false,
    "use_zone_plates": true,
    "avatar_reference": "AI/ELEANOR/products/model_variants/OTHER/grok-image-d25e8689-....jpg",
    "set_reference": "STUDIO/Pipeline/references/warehouse_industrial_reference.jpg"
  },
  "shots": [
    {
      "id": "01_intro",
      "duration": 7,
      "role": "host",
      "speech_text": "I'm MATILDA. I'm a synthetic presenter — generated, not filmed.",
      "video_prompt": "CONTINUITY LOCK @Matilda-001: ... (@1, warehouse loft — window grid camera-left) ..."
    }
  ]
}
"""