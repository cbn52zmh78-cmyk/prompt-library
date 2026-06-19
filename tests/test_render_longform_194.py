"""#194 — archive neutral color + pronunciation chip overlay."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
DAVID_SCRIPTS = ROOT / "DAVID" / "scripts"
if str(DAVID_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(DAVID_SCRIPTS))

import render_longform as rl  # noqa: E402


def test_archive_neutral_clamp_excludes_global_lamp():
    vf = rl._magenta_clamp_vf(dark_scene=False, lamp_lock=True, archive_neutral=True)
    assert rl.LAMP_LOCK_VF not in vf
    assert vf == rl.MAGENTA_SATURATION_CLAMP_VF


def test_non_archive_lamp_lock_still_global():
    vf = rl._magenta_clamp_vf(dark_scene=False, lamp_lock=True, archive_neutral=False)
    assert rl.LAMP_LOCK_VF in vf


def test_shot_needs_label_chip_burn():
    assert rl._shot_needs_label_chip_burn({"on_screen": "RECONSTRUCTED PRONUNCIATION · Classical Latin"})
    assert not rl._shot_needs_label_chip_burn({"on_screen": "Who kept speaking it?"})


def test_render_pronunciation_chip_overlay(tmp_path: Path):
    shot = {"id": "07_demonstration", "on_screen": "RECONSTRUCTED PRONUNCIATION · Classical Latin"}
    out = tmp_path / "chip.png"
    rl.render_pronunciation_chip_overlay(shot, out, width=1280, height=720)
    assert out.is_file()
    assert out.stat().st_size > 500


def test_concat_only_seamless_grade_rejected():
    opts = rl.SeamlessOptions(enabled=True, match_color=True, magenta_clamp=True)
    with pytest.raises(SystemExit, match="cannot grade or re-seam"):
        rl.reject_concat_only_seamless_grade(
            concat_only=True,
            seamless_opts=opts,
            match_color=True,
            cut_on_motion=True,
            seamless_flag=True,
        )


def test_neutral_generation_lock_injected_for_archive():
    opts = rl.SeamlessOptions(neutral_generation=True, lamp_lock=True)
    refs = {"set_file": "archive_set_reference.jpg", "voice_suffix": "calm documentary voice"}
    shot = {"video_prompt": "Host at desk.", "speech_text": "Hello."}
    out = rl.apply_seamless_prompt(shot, refs, opts)
    assert rl.ARCHIVE_NEUTRAL_GENERATION_LOCK.split(".")[0] in out
    assert "5000K" in out


def test_concat_only_plain_concat_allowed():
    opts = rl.SeamlessOptions(enabled=False, magenta_clamp=False, neutral_grade=False)
    rl.reject_concat_only_seamless_grade(
        concat_only=True,
        seamless_opts=opts,
        match_color=False,
        cut_on_motion=False,
        seamless_flag=False,
    )