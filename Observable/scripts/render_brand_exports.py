#!/usr/bin/env python3
"""Observable brand export renderer — task #180 / intro sting #197.

Generates wordmark PNG, monogram avatar, YouTube banner, channel avatar,
4s intro sting MP4, and template plates from asset_specs.json + Julian-001.

Usage:
    python Observable/scripts/render_brand_exports.py
    python Observable/scripts/render_brand_exports.py --only wordmark banner avatar
    python Observable/scripts/render_brand_exports.py --only intro_sting
"""
from __future__ import annotations

import argparse
import json
import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BRAND = ROOT / "Observable" / "brand"
EXPORT = BRAND / "export"
TEMPLATES = BRAND / "templates"
SPECS = json.loads((BRAND / "asset_specs.json").read_text(encoding="utf-8"))

COLORS = SPECS["channel"]["colors"]
CASTING = ROOT / "STUDIO" / "Cast" / "actors_roster" / "male" / "north_america" / "Julian_Cross" / "01_casting_shots" / "casting_turnaround_v1.jpg"


def _rgb(token: str) -> tuple[int, int, int]:
    h = COLORS[token].lstrip("#")
    return (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16))


def _fonts() -> dict:
    from PIL import ImageFont

    def tt(name: str, size: int, *, bold: bool = False):
        paths = [f"C:/Windows/Fonts/{name}bd.ttf"] if bold else [f"C:/Windows/Fonts/{name}.ttf", f"C:/Windows/Fonts/{name}bd.ttf"]
        for p in paths:
            try:
                return ImageFont.truetype(p, size)
            except OSError:
                continue
        return ImageFont.load_default()

    return {
        "wordmark": tt("segoeui", 96, bold=True),
        "tagline": tt("segoeui", 32),
        "small": tt("segoeui", 22),
        "mono": tt("consola", 18),
        "chip": tt("segoeui", 16, bold=True),
        "cta": tt("segoeui", 28),
        "parent": tt("segoeui", 18),
    }


def _gradient_vertical(size: tuple[int, int], top: str, bottom: str):
    from PIL import Image

    w, h = size
    img = Image.new("RGB", size)
    t, b = _rgb(top), _rgb(bottom)
    for y in range(h):
        ratio = y / max(h - 1, 1)
        row = tuple(int(t[i] + (b[i] - t[i]) * ratio) for i in range(3))
        for x in range(w):
            img.putpixel((x, y), row)
    return img


def _front_panel_crop(host_path: Path):
    from PIL import Image

    host = Image.open(host_path).convert("RGB")
    w, h = host.size
    panel_w = w // 3
    front = host.crop((panel_w, 0, panel_w * 2, h))
    return front


def _paste_chest_up(base, host_path: Path, box: tuple[int, int, int, int], *, vignette_left: bool = True) -> None:
    from PIL import Image, ImageDraw, ImageEnhance, ImageFilter

    front = _front_panel_crop(host_path)
    x, y, tw, th = box
    sw, sh = front.size
    scale = max(tw / sw, th / sh)
    resized = front.resize((int(sw * scale), int(sh * scale)), Image.Resampling.LANCZOS)
    rw, rh = resized.size
    left = max(0, (rw - tw) // 2)
    top = max(0, int((rh - th) * 0.12))
    cropped = resized.crop((left, top, left + tw, top + th))
    cropped = ImageEnhance.Brightness(cropped).enhance(0.97)
    cropped = cropped.filter(ImageFilter.GaussianBlur(radius=0.2))

    if vignette_left:
        mask = Image.new("L", (tw, th), 255)
        mdraw = ImageDraw.Draw(mask)
        for col in range(int(tw * 0.35)):
            alpha = int(255 * (col / max(int(tw * 0.35), 1)))
            mdraw.line([(col, 0), (col, th)], fill=alpha)
        base.paste(cropped, (x, y), mask)
    else:
        base.paste(cropped, (x, y))


def render_wordmark_png() -> Path:
    from PIL import Image, ImageDraw

    out = EXPORT / "observable_wordmark_1x.png"
    img = Image.new("RGBA", (640, 160), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    fonts = _fonts()
    accent = _rgb("obs-accent")
    title = _rgb("obs-title")
    body = _rgb("obs-body")

    draw.ellipse((8, 28, 68, 88), outline=accent, width=4)
    draw.text((78, 24), "bservable", fill=title, font=fonts["wordmark"])
    draw.text((12, 118), "Evidence before wonder.", fill=body, font=fonts["tagline"])
    img.save(out, "PNG")
    return out


def render_monogram() -> Path:
    from PIL import Image, ImageDraw

    out = EXPORT / "observable_monogram_O_800.png"
    size = 800
    img = Image.new("RGB", (size, size), _rgb("obs-bg"))
    draw = ImageDraw.Draw(img)
    accent = _rgb("obs-accent")
    draw.ellipse((120, 120, 680, 680), outline=accent, width=12)
    img.save(out, "PNG")
    return out


def render_channel_avatar() -> Path:
    from PIL import Image, ImageDraw

    out = EXPORT / "channel_avatar_800.png"
    size = 800
    img = Image.new("RGB", (size, size), _rgb("obs-bg"))
    if CASTING.is_file():
        _paste_chest_up(img, CASTING, (40, 40, 720, 720), vignette_left=False)
    else:
        render_monogram()
        mono = Image.open(EXPORT / "observable_monogram_O_800.png").convert("RGB")
        img.paste(mono, (0, 0))

    draw = ImageDraw.Draw(img)
    draw.ellipse((8, 8, 792, 792), outline=_rgb("obs-accent"), width=4)
    img.save(out, "PNG")
    return out


def render_banner() -> Path:
    from PIL import Image, ImageDraw

    out = EXPORT / "youtube_banner_2560x1440.jpg"
    w, h = 2560, 1440
    img = _gradient_vertical((w, h), "obs-seamless", "obs-bg")
    draw = ImageDraw.Draw(img)
    fonts = _fonts()

    if CASTING.is_file():
        _paste_chest_up(img, CASTING, (w - 1100, 80, 1000, 1280))

    wm = Image.open(render_wordmark_png()).convert("RGBA")
    wm = wm.resize((720, 180), Image.Resampling.LANCZOS)
    img.paste(wm, (180, h - 320), wm)

    parent = _rgb("ut-gold") if "ut-gold" in COLORS else (201, 168, 76)
    draw.text((w - 420, h - 48), "Upon Tyne Productions", fill=parent, font=fonts["parent"])
    img.save(out, "JPEG", quality=92)
    return out


def render_lower_third() -> Path:
    from PIL import Image, ImageDraw

    out = TEMPLATES / "lower_third_master_1920x1080.png"
    img = Image.new("RGBA", (1920, 1080), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    fonts = _fonts()
    surface = _rgb("obs-surface")
    title = _rgb("obs-title")
    accent = _rgb("obs-accent-bright")

    draw.rounded_rectangle((48, 48, 280, 92), radius=8, fill=surface)
    draw.text((64, 56), "Observable", fill=title, font=fonts["small"])

    draw.rounded_rectangle((48, 920, 1100, 1000), radius=10, fill=(*surface, 230))
    draw.text((72, 936), "How Atoms Share Electrons", fill=title, font=fonts["tagline"])
    draw.text((72, 972), "@Sci-ChemBond-001 · MODEL · NOT TO SCALE", fill=accent, font=fonts["mono"])

    for i, (label, color_key) in enumerate([("OBSERVED", "label-observed"), ("MODEL", "label-model"), ("NOT TO SCALE", "label-not-to-scale")]):
        x = 1150 + i * 220
        draw.rounded_rectangle((x, 936, x + 200, 972), radius=6, fill=_rgb(color_key))
        draw.text((x + 14, 944), label, fill=(255, 255, 255), font=fonts["chip"])

    img.save(out, "PNG")
    return out


def render_end_card(kind: str) -> Path:
    from PIL import Image, ImageDraw

    name = f"end_card_{kind}_1920x1080.png"
    out = TEMPLATES / name
    img = Image.new("RGB", (1920, 1080), _rgb("obs-bg"))
    draw = ImageDraw.Draw(img)
    fonts = _fonts()
    title_c = _rgb("obs-title")
    body_c = _rgb("obs-body")
    cta_c = _rgb("obs-cta")

    draw.text((960, 280), "Observable", fill=title_c, font=fonts["wordmark"], anchor="mm")
    draw.text((960, 380), "Evidence before wonder.", fill=body_c, font=fonts["tagline"], anchor="mm")

    if kind == "closing":
        draw.text((960, 520), "Follow Observable — one measurement at a time.", fill=cta_c, font=fonts["cta"], anchor="mm")
        draw.text(
            (960, 900),
            "Upon Tyne Productions · Synthetic presenter · AI disclosure in description",
            fill=body_c,
            font=fonts["small"],
            anchor="mm",
        )
    else:
        draw.text((960, 480), "Sources — Covalent bonding in H₂O", fill=title_c, font=fonts["tagline"], anchor="mm")
        lines = [
            "NIST Chemistry WebBook — bond geometry (H₂O)",
            "Pauling — shared electron pair model",
            "OpenStax Chemistry 2e, Ch. 7",
        ]
        y = 560
        for line in lines:
            draw.text((960, y), line, fill=body_c, font=fonts["small"], anchor="mm")
            y += 44
        draw.text((960, 900), "Chemistry · COV-BOND-001", fill=body_c, font=fonts["mono"], anchor="mm")

    img.save(out, "PNG")
    return out


def _lerp(a: float, b: float, t: float) -> float:
    return a + (b - a) * max(0.0, min(1.0, t))


def _fade_alpha(frame_i: int, fps: int, start_s: float, end_s: float) -> float:
    t = frame_i / fps
    if t < start_s:
        return 0.0
    if t >= end_s:
        return 1.0
    return (t - start_s) / max(end_s - start_s, 1e-6)


def render_intro_sting() -> Path:
    """4s 1080p bumper — obs-bg fade → seamless neutral + Julian → wordmark."""
    from PIL import Image, ImageDraw, ImageEnhance

    out = EXPORT / "intro_sting_4s_1080p.mp4"
    w, h = 1920, 1080
    fps = 24
    duration_s = 4.0
    total_frames = int(duration_s * fps)
    fonts = _fonts()
    bg = _rgb("obs-bg")
    seamless_top = _rgb("obs-seamless")
    seamless_bot = _rgb("obs-bg")
    title_c = _rgb("obs-title")
    body_c = _rgb("obs-body")

    wm_path = render_wordmark_png()
    wordmark = Image.open(wm_path).convert("RGBA")

    with tempfile.TemporaryDirectory(prefix="obs_intro_") as tmp:
        tmp_dir = Path(tmp)
        for i in range(total_frames):
            t = i / fps
            img = Image.new("RGB", (w, h), bg)

            # 0.0–0.5 s: obs-bg hold; 0.5–3.0 s: seamless neutral wide + Julian
            host_alpha = _fade_alpha(i, fps, 0.35, 0.55)
            if host_alpha > 0:
                wide = _gradient_vertical((w, h), "obs-seamless", "obs-bg")
                img = wide.copy()
                if CASTING.is_file():
                    _paste_chest_up(img, CASTING, (w // 2 - 280, 120, 560, 840))
                    img = ImageEnhance.Brightness(img).enhance(0.98)
                overlay = Image.new("RGBA", (w, h), (0, 0, 0, 0))
                if t < 0.5:
                    fade = int(255 * (1.0 - t / 0.5))
                    overlay = Image.new("RGBA", (w, h), (*bg, fade))
                img = img.convert("RGBA")
                img = Image.alpha_composite(img, overlay).convert("RGB")
                if t < 0.5:
                    bg_layer = Image.new("RGB", (w, h), bg)
                    blend = _lerp(1.0, 0.0, t / 0.5)
                    img = Image.blend(bg_layer, img, 1.0 - blend)

            # 3.0–4.0 s: wordmark + tagline on obs-bg
            end_alpha = _fade_alpha(i, fps, 3.0, 3.25)
            if end_alpha > 0:
                end_card = Image.new("RGB", (w, h), bg)
                draw = ImageDraw.Draw(end_card)
                wm = wordmark.resize((900, 225), Image.Resampling.LANCZOS)
                end_card.paste(wm, ((w - 900) // 2, 360), wm)
                draw.text((w // 2, 640), "Evidence before wonder.", fill=body_c, font=fonts["tagline"], anchor="mm")
                if host_alpha > 0 and end_alpha < 1.0:
                    img = Image.blend(img, end_card, end_alpha)
                else:
                    img = end_card

            img.save(tmp_dir / f"frame_{i:04d}.png")

        import imageio_ffmpeg

        ffmpeg = imageio_ffmpeg.get_ffmpeg_exe()
        proc = subprocess.run(
            [
                ffmpeg, "-y",
                "-framerate", str(fps),
                "-i", str(tmp_dir / "frame_%04d.png"),
                "-c:v", "libx264",
                "-pix_fmt", "yuv420p",
                "-movflags", "+faststart",
                "-t", str(duration_s),
                str(out),
            ],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
        if proc.returncode != 0:
            raise RuntimeError(f"intro sting encode failed: {proc.stderr[-800:]}")

    return out


RENDERERS = {
    "wordmark": lambda: (render_wordmark_png(), render_monogram()),
    "avatar": render_channel_avatar,
    "banner": render_banner,
    "intro_sting": render_intro_sting,
    "lower_third": render_lower_third,
    "end_closing": lambda: render_end_card("closing"),
    "end_sources": lambda: render_end_card("sources"),
}


def main() -> int:
    parser = argparse.ArgumentParser(description="Render Observable brand exports (#180)")
    parser.add_argument("--only", nargs="*", choices=list(RENDERERS), help="Subset of assets")
    args = parser.parse_args()

    EXPORT.mkdir(parents=True, exist_ok=True)
    TEMPLATES.mkdir(parents=True, exist_ok=True)

    keys = args.only or list(RENDERERS)
    for key in keys:
        result = RENDERERS[key]()
        if isinstance(result, tuple):
            for path in result:
                print(f"Wrote {path.relative_to(ROOT)}")
        else:
            print(f"Wrote {result.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())