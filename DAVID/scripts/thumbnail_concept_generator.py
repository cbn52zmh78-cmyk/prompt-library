#!/usr/bin/env python3
"""DAVID dead-language corpus thumbnail concept generator — Issue #140.

Builds 1280×720 thumbnail specs from locked David-001 identity plates,
defines title-text zone + brand look, and optionally renders PIL composites.

Usage:
    python thumbnail_concept_generator.py --specs-only
    python thumbnail_concept_generator.py --render
    python thumbnail_concept_generator.py --slug david_latin_corpus_v1 --render
"""
from __future__ import annotations

import argparse
import json
import textwrap
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
WORKSPACE = ROOT.parent
DEFAULT_LOCK = ROOT / "productions" / "host_identity_v1" / "david_identity_lock.json"
DEFAULT_OUT = ROOT / "productions" / "thumbnails" / "dead_language_corpus_v1"

CANVAS_W, CANVAS_H = 1280, 720

BRAND: dict[str, Any] = {
    "issue": 140,
    "canvas_px": [CANVAS_W, CANVAS_H],
    "aspect_ratio": "16:9",
    "wordmark": "DAVID · The Archive",
    "tagline": "Dead languages, actually pronounced.",
    "actor_id": "David-001",
    "set_id": "@Set-Archive-001",
    "colors": {
        "bg": "#0C0E14",
        "bg_rgb": [12, 14, 20],
        "gold_title": "#DCBE78",
        "gold_title_rgb": [220, 190, 120],
        "gold_footer": "#FFB45A",
        "gold_footer_rgb": [255, 180, 90],
        "parchment": "#F5F0E6",
        "parchment_rgb": [245, 240, 230],
        "umber_dark": "#3D2B1F",
        "umber_mid": "#5C4033",
        "shadow_warm": "#2A2520",
        "body_text": "#C8CDD7",
        "body_text_rgb": [200, 205, 215],
        "banner_fill": "#502D14",
        "banner_fill_rgb": [80, 45, 20],
        "attested": "#6BBF8A",
        "attested_rgb": [107, 191, 138],
        "reconstructed": "#E8A84C",
        "reconstructed_rgb": [232, 168, 76],
    },
    "lighting": "Warm brass desk lamp 3200K key — amber pool, no magenta, no cool fill",
    "title_zone": {
        "x": 0,
        "y": 420,
        "w": 742,
        "h": 260,
        "safe_margin_px": 48,
        "youtube_safe": "left 58% bottom 38% — face stays right; title never overlaps host eyes",
    },
    "host_crop": {
        "source": "david_avatar_reference.jpg",
        "x": 520,
        "y": 0,
        "w": 760,
        "h": 720,
        "anchor": "right-center",
        "notes": "Chest-up from locked host plate; vignette left edge into title zone",
    },
    "set_plate": {
        "source": "archive_set_reference.jpg",
        "blend": "darken 65% under host crop for depth",
    },
    "fonts": {
        "wordmark": {"family": "Arial", "weight": "regular", "size_px": 22},
        "hook_title": {"family": "Arial", "weight": "bold", "size_px": 72, "max_lines": 2},
        "hook_subtitle": {"family": "Arial", "weight": "regular", "size_px": 28},
        "excerpt": {"family": "Arial", "weight": "regular", "size_px": 20, "style": "italic"},
        "badge": {"family": "Arial", "weight": "bold", "size_px": 18},
    },
    "guardrails": [
        "synthetic host only — David-001 locked plate",
        "attested vs reconstructed badge on every thumbnail",
        "no real-person likeness",
        "export PNG 1280×720 under 2MB",
    ],
}

EPISODE_REGISTRY: dict[str, dict[str, Any]] = {
    "david_latin_corpus_v1": {
        "title": "DAVID — Why Latin Never Really Died",
        "language": "Latin",
        "hook_title": "LATIN\nNEVER DIED",
        "hook_subtitle": "Who kept speaking it?",
        "excerpt": "Gallia est omnis divisa in partes tres",
        "excerpt_script": "Latin",
        "artifact": "illuminated codex + Roman grammarian marginalia",
        "attestation_primary": "ATTESTED",
        "attestation_secondary": "RECONSTRUCTED PRONUNCIATION",
        "attestation_note": "Liturgy & law continuous; classical vowel length from meter",
        "accent_hex": "#C9A227",
    },
    "david_gothic_corpus_v1": {
        "title": "DAVID — Gothic: A Language Saved by One Bible",
        "language": "Gothic",
        "hook_title": "ONE\nBIBLE",
        "hook_subtitle": "Wulfila's witness",
        "excerpt": "Atta unsar, thu in himinam",
        "excerpt_script": "Gothic",
        "artifact": "Codex Argenteus silver manuscript fragment",
        "attestation_primary": "ATTESTED TEXT",
        "attestation_secondary": "RECONSTRUCTED PRONUNCIATION",
        "attestation_note": "Gospel spellings attested; vowel timbre reconstructed",
        "accent_hex": "#8B7355",
    },
    "david_ancient_greek_corpus_v1": {
        "title": "DAVID — Ancient Greek: Restoring the Pitch Accent",
        "language": "Ancient Greek",
        "hook_title": "GREEK\nPITCH ACCENT",
        "hook_subtitle": "Pitch, not just letters",
        "excerpt": "ἄνδρα μοι ἔννεπε, μοῦσα",
        "excerpt_script": "Greek",
        "artifact": "Homeric papyrus with accent marks",
        "attestation_primary": "ATTESTED NOTATION",
        "attestation_secondary": "RECONSTRUCTED PRONUNCIATION",
        "attestation_note": "Accent marks in manuscripts; peak pitch reconstructed",
        "accent_hex": "#2E6B9E",
    },
    "david_old_english_corpus_v1": {
        "title": "DAVID — Old English: Beowulf's Tongue in Manuscript",
        "language": "Old English",
        "hook_title": "BEFORE\nENGLISH",
        "hook_subtitle": "Manuscript vs mouth",
        "excerpt": "Hwæt, we gar-Dena in geardagum",
        "excerpt_script": "Anglo-Saxon",
        "artifact": "Beowulf manuscript folio (Cotton Vitellius)",
        "attestation_primary": "ATTESTED MANUSCRIPT",
        "attestation_secondary": "RECONSTRUCTED PRONUNCIATION",
        "attestation_note": "West Saxon graphs attested; unstressed vowels reconstructed",
        "accent_hex": "#7A4E2D",
    },
    "david_old_norse_corpus_v1": {
        "title": "DAVID — Old Norse: Runes Attested, Sagas Reconstructed",
        "language": "Old Norse",
        "hook_title": "RUNES\nSPEAK",
        "hook_subtitle": "Stone attests · verse reconstructs",
        "excerpt": "Haraldr konungr sigrsæll",
        "excerpt_script": "Younger Futhark / Latin transliteration",
        "artifact": "Jelling runestone rubbing",
        "attestation_primary": "ATTESTED",
        "attestation_secondary": "RECONSTRUCTED",
        "attestation_note": "Jelling inscription attested; skaldic delivery reconstructed",
        "accent_hex": "#5A6E7A",
    },
    "david_sumerian_corpus_v1": {
        "title": "DAVID — Sumerian: The First Written Language",
        "language": "Sumerian",
        "hook_title": "FIRST\nLANGUAGE",
        "hook_subtitle": "Clay outlived voice",
        "excerpt": "dnin-ĝir-su-ka",
        "excerpt_script": "cuneiform transliteration",
        "artifact": "Lagash administrative clay tablet",
        "attestation_primary": "ATTESTED SYLLABLES",
        "attestation_secondary": "RECONSTRUCTED VOWELS",
        "attestation_note": "Syllabic values from scribes; open-syllable vowels reconstructed",
        "accent_hex": "#B85C38",
    },
}


def load_identity_lock(lock_path: Path) -> dict[str, Any]:
    lock = json.loads(lock_path.read_text(encoding="utf-8"))
    if lock.get("status") != "LOCKED":
        raise RuntimeError(f"Identity lock not LOCKED: {lock_path}")
    return lock


def _rel(path: Path) -> str:
    path = path.resolve()
    for base in (ROOT, WORKSPACE):
        try:
            return path.relative_to(base).as_posix()
        except ValueError:
            continue
    return str(path)


def _resolve_ref(stored: str) -> Path:
    p = Path(stored)
    if p.is_file():
        return p
    for base in (ROOT, WORKSPACE):
        candidate = base / stored
        if candidate.is_file():
            return candidate
    return ROOT / stored


def build_image_prompt(ep: dict[str, Any], lock: dict[str, Any]) -> str:
    avatar = lock["references"]["david_avatar"]["prompt"]
    archive = lock["references"]["archive_set"]["prompt"]
    return (
        f"YouTube thumbnail 1280×720, cinematic documentary prestige, high contrast readable at small size. "
        f"LEFT THIRD: bold title-safe negative space for text overlay — gold hook title "
        f"\"{ep['hook_title'].replace(chr(10), ' ')}\" and subtitle \"{ep['hook_subtitle']}\". "
        f"RIGHT TWO-THIRDS: {avatar} "
        f"Background depth from {archive} "
        f"Foreground artifact prop: {ep['artifact']}. "
        f"Excerpt strip in {ep.get('excerpt_script', ep['language'])} script: \"{ep['excerpt']}\". "
        f"On-screen badges: {ep['attestation_primary']} + {ep['attestation_secondary']}. "
        f"Brand wordmark top-left: DAVID · The Archive. "
        f"COLOR LOCK Archive: amber 3200K brass lamp, burnt umber wood, parchment cream, warm shadow — "
        f"no blue fill, no magenta, no teal. "
        f"Synthetic host David-001 only, no real person likeness, no celebrity resemblance, SFW."
    )


def build_spec(
    slug: str,
    ep: dict[str, Any],
    lock: dict[str, Any],
    *,
    lock_path: Path,
) -> dict[str, Any]:
    refs = lock["references"]
    avatar_path = Path(refs["david_avatar"]["file"])
    set_path = Path(refs["archive_set"]["file"])

    return {
        "slug": slug,
        "issue": 140,
        "title": ep["title"],
        "language": ep["language"],
        "actor_id": BRAND["actor_id"],
        "canvas_px": BRAND["canvas_px"],
        "brand": {
            "wordmark": BRAND["wordmark"],
            "tagline": BRAND["tagline"],
            "colors": BRAND["colors"],
            "lighting": BRAND["lighting"],
        },
        "plates": {
            "identity_lock": _rel(lock_path),
            "host_reference": _rel(avatar_path),
            "set_reference": _rel(set_path),
            "host_reuse": refs["david_avatar"]["reuse"],
            "set_reuse": refs["archive_set"]["reuse"],
        },
        "layout": {
            "title_zone": BRAND["title_zone"],
            "host_crop": BRAND["host_crop"],
            "set_plate": BRAND["set_plate"],
            "fonts": BRAND["fonts"],
        },
        "copy": {
            "hook_title": ep["hook_title"],
            "hook_subtitle": ep["hook_subtitle"],
            "excerpt": ep["excerpt"],
            "excerpt_script": ep.get("excerpt_script", ep["language"]),
            "artifact": ep["artifact"],
        },
        "attestation": {
            "primary_badge": ep["attestation_primary"],
            "secondary_badge": ep["attestation_secondary"],
            "note": ep["attestation_note"],
            "accent_hex": ep.get("accent_hex", BRAND["colors"]["gold_title"]),
        },
        "imagine_prompt": build_image_prompt(ep, lock),
        "delivery": {
            "filename": f"{slug}_thumbnail_1280x720.jpg",
            "format": "JPEG",
            "quality": 92,
            "max_bytes": 2_097_152,
        },
        "design_notes": [
            "Composite from locked david_avatar_reference.jpg — never substitute another face",
            "Title in left title_zone; host eyes remain in right crop",
            "Primary attestation badge above excerpt strip; secondary badge below",
            f"Artifact cue: {ep['artifact']}",
            "Compatible with Studio/Pipeline/package_episode.py THUMBNAIL_BRIEF handoff",
        ],
    }


def _load_fonts() -> dict[str, Any]:
    from PIL import ImageFont

    def truetype(name: str, size: int, *, bold: bool = False) -> Any:
        candidates = (
            [f"C:/Windows/Fonts/{name}bd.ttf" if bold else f"C:/Windows/Fonts/{name}.ttf"]
            if bold
            else [f"C:/Windows/Fonts/{name}.ttf", f"C:/Windows/Fonts/{name}bd.ttf"]
        )
        for path in candidates:
            try:
                return ImageFont.truetype(path, size)
            except OSError:
                continue
        return ImageFont.load_default()

    return {
        "wordmark": truetype("arial", 22),
        "hook_title": truetype("arial", 64, bold=True),
        "hook_subtitle": truetype("arial", 26),
        "excerpt": truetype("arial", 20),
        "badge": truetype("arial", 16, bold=True),
        "badge_sm": truetype("arial", 14, bold=True),
    }


def _hex_rgb(hex_color: str) -> tuple[int, int, int]:
    h = hex_color.lstrip("#")
    return (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16))


def _paste_host(img: Any, avatar_path: Path, crop: dict[str, Any]) -> None:
    from PIL import Image, ImageDraw, ImageEnhance, ImageFilter

    host = Image.open(avatar_path).convert("RGB")
    tw, th = crop["w"], crop["h"]
    sw, sh = host.size
    scale = max(tw / sw, th / sh)
    resized = host.resize((int(sw * scale), int(sh * scale)), Image.Resampling.LANCZOS)
    rw, rh = resized.size
    left = max(0, (rw - tw) // 2)
    top = max(0, (rh - th) // 3)
    cropped = resized.crop((left, top, left + tw, top + th))

    mask = Image.new("L", (tw, th), 0)
    mdraw = ImageDraw.Draw(mask)
    mdraw.rectangle([(int(tw * 0.15), 0), (tw, th)], fill=255)
    mdraw.rectangle([(0, 0), (int(tw * 0.35), th)], fill=80)

    dark = ImageEnhance.Brightness(cropped).enhance(0.92)
    dark = dark.filter(ImageFilter.GaussianBlur(radius=0.3))
    img.paste(dark, (crop["x"], crop["y"]), mask)


def _paste_set_bg(img: Any, set_path: Path) -> None:
    from PIL import Image, ImageEnhance

    bg = Image.open(set_path).convert("RGB")
    bg = bg.resize((CANVAS_W, CANVAS_H), Image.Resampling.LANCZOS)
    bg = ImageEnhance.Brightness(bg).enhance(0.35)
    bg = ImageEnhance.Contrast(bg).enhance(1.1)
    img.paste(bg, (0, 0))


def render_composite(spec: dict[str, Any], out_path: Path) -> None:
    from PIL import Image, ImageDraw

    colors = spec["brand"]["colors"]
    ep_slug = spec["slug"]
    ep = EPISODE_REGISTRY[ep_slug]
    lock = load_identity_lock(_resolve_ref(spec["plates"]["identity_lock"]))
    avatar_path = Path(lock["references"]["david_avatar"]["file"])
    set_path = Path(lock["references"]["archive_set"]["file"])

    img = Image.new("RGB", (CANVAS_W, CANVAS_H), tuple(colors["bg_rgb"]))
    _paste_set_bg(img, set_path)
    _paste_host(img, avatar_path, BRAND["host_crop"])

    draw = ImageDraw.Draw(img)
    fonts = _load_fonts()
    margin = BRAND["title_zone"]["safe_margin_px"]

    draw.rectangle([(0, 380), (760, CANVAS_H)], fill=(*colors["bg_rgb"],))
    draw.rectangle([(margin, margin), (margin + 340, margin + 36)], fill=tuple(colors["banner_fill_rgb"]))
    draw.text((margin + 12, margin + 6), BRAND["wordmark"], fill=tuple(colors["gold_title_rgb"]), font=fonts["wordmark"])

    tz = BRAND["title_zone"]
    y = tz["y"] + 20
    for line in spec["copy"]["hook_title"].split("\n"):
        draw.text((margin, y), line, fill=tuple(colors["gold_title_rgb"]), font=fonts["hook_title"])
        y += 68

    draw.text(
        (margin, y + 8),
        spec["copy"]["hook_subtitle"],
        fill=tuple(colors["body_text_rgb"]),
        font=fonts["hook_subtitle"],
    )

    strip_y = CANVAS_H - 130
    accent = _hex_rgb(spec["attestation"]["accent_hex"])
    draw.rectangle([(margin, strip_y), (CANVAS_W - margin - 280, strip_y + 90)], fill=accent, outline=tuple(colors["gold_title_rgb"]), width=2)
    draw.rectangle([(margin + 8, strip_y + 8), (margin + 200, strip_y + 32)], fill=tuple(colors["banner_fill_rgb"]))
    draw.text(
        (margin + 14, strip_y + 10),
        spec["attestation"]["primary_badge"],
        fill=tuple(colors["attested_rgb"]) if "ATTESTED" in spec["attestation"]["primary_badge"] else tuple(colors["reconstructed_rgb"]),
        font=fonts["badge"],
    )
    draw.text((margin + 14, strip_y + 40), spec["copy"]["excerpt"], fill=tuple(colors["parchment_rgb"]), font=fonts["excerpt"])
    draw.text(
        (margin + 14, strip_y + 64),
        spec["attestation"]["secondary_badge"],
        fill=tuple(colors["reconstructed_rgb"]),
        font=fonts["badge_sm"],
    )

    artifact = spec["copy"]["artifact"]
    for i, line in enumerate(textwrap.wrap(artifact, width=28)[:2]):
        draw.text((CANVAS_W - margin - 260, strip_y + 12 + i * 22), line, fill=tuple(colors["body_text_rgb"]), font=fonts["badge_sm"])

    out_path.parent.mkdir(parents=True, exist_ok=True)
    img.save(out_path, "JPEG", quality=spec["delivery"]["quality"], optimize=True)


def generate_all(
    *,
    lock_path: Path = DEFAULT_LOCK,
    out_dir: Path = DEFAULT_OUT,
    slugs: list[str] | None = None,
    render: bool = False,
) -> dict[str, Any]:
    lock = load_identity_lock(lock_path)
    targets = slugs or list(EPISODE_REGISTRY.keys())
    specs: list[dict[str, Any]] = []

    for slug in targets:
        if slug not in EPISODE_REGISTRY:
            raise KeyError(f"Unknown slug: {slug}")
        spec = build_spec(slug, EPISODE_REGISTRY[slug], lock, lock_path=lock_path)
        specs.append(spec)
        if render:
            jpg = out_dir / spec["delivery"]["filename"]
            render_composite(spec, jpg)
            spec["rendered_path"] = _rel(jpg)

    payload = {
        "issue": 140,
        "task": "T2 thumbnail system — dead-language corpus v1",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "brand_system": BRAND,
        "identity_lock": _rel(lock_path),
        "identity_status": lock.get("status"),
        "episode_count": len(specs),
        "episodes": specs,
    }

    out_dir.mkdir(parents=True, exist_ok=True)
    specs_path = out_dir / "thumbnail_specs.json"
    specs_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    payload["specs_path"] = _rel(specs_path)
    return payload


def main() -> None:
    parser = argparse.ArgumentParser(description="DAVID thumbnail concept generator (#140)")
    parser.add_argument("--specs-only", action="store_true", help="Write thumbnail_specs.json only")
    parser.add_argument("--render", action="store_true", help="Also render JPEG composites")
    parser.add_argument("--slug", action="append", dest="slugs", help="Limit to slug(s)")
    parser.add_argument("--lock", type=Path, default=DEFAULT_LOCK)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    args = parser.parse_args()

    if not args.render and not args.specs_only:
        args.specs_only = True

    payload = generate_all(
        lock_path=args.lock,
        out_dir=args.out,
        slugs=args.slugs,
        render=args.render,
    )
    print(json.dumps({"specs_path": payload["specs_path"], "episode_count": payload["episode_count"]}, indent=2))


if __name__ == "__main__":
    main()