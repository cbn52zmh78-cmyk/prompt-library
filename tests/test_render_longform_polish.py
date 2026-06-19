"""#193 — render_longform exit code + science loudness-tighten wiring."""

from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

ROOT = Path(__file__).resolve().parents[1]
DAVID_SCRIPTS = ROOT / "DAVID" / "scripts"
if str(DAVID_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(DAVID_SCRIPTS))

import render_longform as rl  # noqa: E402
from render_longform import (  # noqa: E402
    DEFAULT_XFADE_S,
    MIN_XFADE_S,
    SeamlessOptions,
    resolve_render_exit_code,
    resolve_xfade_s,
)

STAR_SCRIPT = (
    ROOT
    / "DAVID/batches/T4_181_science_astro/scripts/science_star_lifecycle_v1_480p_script.json"
)
STAR_PROD = ROOT / "STUDIO/Productions/Editorial/science_star_lifecycle_v1_longform_v1"
RENDER = DAVID_SCRIPTS / "render_longform.py"


def test_resolve_xfade_s_floors_legacy_0_2():
    assert resolve_xfade_s(cli=None, script_seam={"xfade_s": 0.2}) == MIN_XFADE_S
    assert resolve_xfade_s(cli=0.2, script_seam={}) == MIN_XFADE_S
    assert resolve_xfade_s(cli=None, script_seam={}) == DEFAULT_XFADE_S


def test_write_seamless_final_uses_host_join_not_raw_host(tmp_path: Path):
    host = tmp_path / "host_performance_extend.mp4"
    trimmed = tmp_path / "host_performance_trimmed.mp4"
    out = tmp_path / "david_slug_seamless_v1.mp4"
    host.write_bytes(b"raw" * 5_000)
    trimmed.write_bytes(b"trim" * 5_000)
    opts = SeamlessOptions(enabled=True, xfade_s=DEFAULT_XFADE_S)

    rl._write_seamless_final(trimmed, None, out, opts=opts, color_ref=None, shots_dir=tmp_path)
    assert out.read_bytes() == trimmed.read_bytes()
    assert out.read_bytes() != host.read_bytes()


def test_stale_host_without_xfade_state_forces_frame_chain(tmp_path: Path):
    shots_dir = tmp_path / "shots"
    shots_dir.mkdir()
    shots = [
        {"id": "01_hook", "duration": 8, "video_prompt": "CONTINUITY LOCK @David-001"},
        {"id": "02_stakes", "duration": 9, "video_prompt": "CONTINUITY LOCK @David-001"},
    ]
    host = shots_dir / "host_performance_extend.mp4"
    host.write_bytes(b"stale-ungraded" * 800)
    out_path = host
    opts = SeamlessOptions(enabled=True, loudnorm=True)
    refs = {
        "avatar_file": str(ROOT / "STUDIO/Pipeline/references/seamless_neutral_reference.jpg"),
        "avatar_url": "https://example.invalid/avatar.jpg",
        "model_video": "grok-imagine-video-1.5",
        "resolution": "480p",
        "voice_suffix": "voice synthetic host only",
        "set_file": str(ROOT / "DAVID/productions/host_identity_v1/references/archive_set_reference.jpg"),
    }

    with (
        patch.object(rl, "resolve_color_reference", return_value=None),
        patch.object(rl, "render_frame_chain_performance", return_value=(out_path, [], "frame_chain")) as fc,
    ):
        rl.render_extend_performance(
            shots,
            client=None,
            refs=refs,
            opts=opts,
            out_path=out_path,
            shots_dir=shots_dir,
            concat_only=False,
        )
    fc.assert_called_once()


def test_apply_grade_policy_disables_lamp_lock_for_clinical_neutral():
    script = {
        "format_id": "science-explainer",
        "config": {"seamless": {"lamp_lock": True, "neutral_grade": True}},
    }
    refs = {
        "set_file": str(ROOT / "STUDIO/Pipeline/references/seamless_neutral_reference.jpg"),
    }
    opts = SeamlessOptions(enabled=True, lamp_lock=True, match_color=True)
    graded = rl._apply_grade_policy(script, refs, opts)
    assert graded.lamp_lock is False
    assert graded.neutral_grade is True
    assert graded.match_color is True


def test_process_shot_segment_uses_neutral_grade_not_lamp_clamp(tmp_path: Path):
    video = tmp_path / "chain_01_hook.mp4"
    out = tmp_path / "chain_01_hook_processed.mp4"
    video.write_bytes(b"x" * 20_000)
    shot = {"id": "01_hook", "duration": 8}
    refs = {
        "set_file": str(ROOT / "STUDIO/Pipeline/references/seamless_neutral_reference.jpg"),
    }
    opts = SeamlessOptions(
        enabled=True, match_color=True, magenta_clamp=True,
        neutral_grade=True, lamp_lock=False,
    )
    color_ref = ROOT / "STUDIO/Pipeline/references/seamless_neutral_reference.jpg"

    def _write_neutral(_v: Path, o: Path, _ref: Path) -> Path:
        o.write_bytes(b"x" * 20_000)
        return o

    with (
        patch.object(rl, "apply_neutral_white_balance_grade", side_effect=_write_neutral) as neutral,
        patch.object(rl, "apply_per_shot_magenta_clamp") as lamp_clamp,
        patch.object(rl, "pin_av_to_duration", side_effect=lambda src, dst, _d: shutil.copy2(src, dst)),
        patch.object(
            rl, "loudnorm_two_pass",
            side_effect=lambda src, dst, **kwargs: shutil.copy2(src, dst),
        ),
    ):
        rl.process_shot_segment(video, out, shot, refs, opts, tmp_path, color_ref)

    neutral.assert_called_once()
    lamp_clamp.assert_not_called()


def test_assemble_xfade_chain_threads_neutral_grade(tmp_path: Path):
    seg_a = tmp_path / "chain_01_hook_processed.mp4"
    seg_b = tmp_path / "chain_02_phenomenon_processed.mp4"
    seg_a.write_bytes(b"x" * 20_000)
    seg_b.write_bytes(b"x" * 20_000)
    out = tmp_path / "host_performance_extend.mp4"
    shots = [{"id": "01_hook", "duration": 8}, {"id": "02_phenomenon", "duration": 9}]
    opts = SeamlessOptions(enabled=True, loudnorm=False, neutral_grade=True, match_color=True)

    with patch.object(rl, "concat_xfade_chain") as xfade:
        rl._assemble_xfade_chain(
            [seg_a, seg_b], shots, out, opts=opts, shots_dir=tmp_path, color_ref=None,
        )
    _args, kwargs = xfade.call_args
    assert kwargs.get("neutral_grade") is True


def test_resolve_render_exit_code_pass():
    assert resolve_render_exit_code({"qa": {"pass": True}}) == 0


def test_resolve_render_exit_code_fail():
    assert resolve_render_exit_code({"qa": {"pass": False}}) == 1
    assert resolve_render_exit_code({}) == 1


def test_parse_render_manifest_from_stdout():
    if str(DAVID_SCRIPTS) not in sys.path:
        sys.path.insert(0, str(DAVID_SCRIPTS))
    from batch_runner import parse_render_manifest, qa_from_render_output  # noqa: WPS433

    blob = (
        'log line\n'
        '{"completed_at": "2026-01-01T00:00:00+00:00", '
        '"slug": "x", "qa": {"pass": true, "issues": []}}'
    )
    manifest = parse_render_manifest(blob)
    assert manifest is not None
    assert manifest["slug"] == "x"
    qa = qa_from_render_output(blob)
    assert qa is not None
    assert qa["pass"] is True


def test_assemble_xfade_chain_calls_tighten_when_loudnorm(tmp_path: Path):
    seg_a = tmp_path / "chain_01_hook_processed.mp4"
    seg_b = tmp_path / "chain_02_phenomenon_processed.mp4"
    seg_a.write_bytes(b"x" * 20_000)
    seg_b.write_bytes(b"x" * 20_000)
    out = tmp_path / "host_performance_extend.mp4"
    shots = [
        {"id": "01_hook", "duration": 8},
        {"id": "02_phenomenon", "duration": 9},
    ]
    opts = SeamlessOptions(enabled=True, loudnorm=True)
    tightened = [seg_a, seg_b]

    with (
        patch.object(rl, "tighten_chain_loudness", return_value=tightened) as tighten,
        patch.object(rl, "concat_xfade_chain") as xfade,
    ):
        rl._assemble_xfade_chain(
            [seg_a, seg_b],
            shots,
            out,
            opts=opts,
            shots_dir=tmp_path,
            color_ref=None,
            label="test",
        )
    tighten.assert_called_once()
    xfade.assert_called_once()


def test_multi_segment_reconcat_refuses_hard_cut_without_seamless(tmp_path: Path):
    seg_a = tmp_path / "a.mp4"
    seg_b = tmp_path / "b.mp4"
    seg_a.write_bytes(b"x" * 20_000)
    seg_b.write_bytes(b"x" * 20_000)
    out = tmp_path / "out.mp4"
    shots = [{"id": "01_hook", "duration": 8}, {"id": "02_phenomenon", "duration": 9}]
    opts = SeamlessOptions(enabled=False, loudnorm=False)

    with pytest.raises(RuntimeError, match="requires seamless xfade"):
        rl._assemble_xfade_chain(
            [seg_a, seg_b],
            shots,
            out,
            opts=opts,
            shots_dir=tmp_path,
            color_ref=None,
        )


def test_partial_chain_routes_to_frame_chain_not_stale_host(tmp_path: Path):
    shots_dir = tmp_path / "shots"
    shots_dir.mkdir()
    shots = [
        {"id": "01_hook", "duration": 8, "video_prompt": "CONTINUITY LOCK @Julian-001"},
        {"id": "02_phenomenon", "duration": 9, "video_prompt": "CONTINUITY LOCK @Julian-001"},
    ]
    # Only first segment cached — partial chain
    proc = shots_dir / "chain_01_hook_processed.mp4"
    proc.write_bytes(b"x" * 20_000)
    host = shots_dir / "host_performance_extend.mp4"
    host.write_bytes(b"stale" * 5_000)

    out_path = host
    opts = SeamlessOptions(enabled=True, loudnorm=True)
    refs = {
        "avatar_file": str(ROOT / "STUDIO/Pipeline/references/seamless_neutral_reference.jpg"),
        "avatar_url": "https://example.invalid/avatar.jpg",
        "model_video": "grok-imagine-video-1.5",
        "resolution": "480p",
        "voice_suffix": "science voice synthetic host only",
        "set_file": str(ROOT / "STUDIO/Pipeline/references/seamless_neutral_reference.jpg"),
    }

    with (
        patch.object(rl, "resolve_color_reference", return_value=None),
        patch.object(rl, "render_frame_chain_performance", return_value=(out_path, [], "frame_chain")) as fc,
    ):
        rl.render_extend_performance(
            shots,
            client=None,
            refs=refs,
            opts=opts,
            out_path=out_path,
            shots_dir=shots_dir,
            concat_only=False,
        )
    fc.assert_called_once()


def test_have_chain_reassembly_wires_tighten(tmp_path: Path):
    shots_dir = tmp_path / "shots"
    shots_dir.mkdir()
    shots = [
        {"id": "01_hook", "duration": 8, "video_prompt": "CONTINUITY LOCK @Julian-001 hook"},
        {"id": "02_phenomenon", "duration": 9, "video_prompt": "CONTINUITY LOCK @Julian-001 phenomenon"},
    ]
    for shot in shots:
        raw = shots_dir / f"chain_{shot['id']}.mp4"
        proc = shots_dir / f"chain_{shot['id']}_processed.mp4"
        raw.write_bytes(b"x" * 20_000)
        proc.write_bytes(b"x" * 20_000)

    out_path = shots_dir / "host_performance_extend.mp4"
    opts = SeamlessOptions(enabled=True, loudnorm=True)
    refs = {
        "avatar_file": str(ROOT / "STUDIO/Pipeline/references/seamless_neutral_reference.jpg"),
        "avatar_url": "https://example.invalid/avatar.jpg",
        "model_video": "grok-imagine-video-1.5",
        "resolution": "480p",
        "voice_suffix": "science voice synthetic host only",
        "set_file": str(ROOT / "STUDIO/Pipeline/references/seamless_neutral_reference.jpg"),
    }

    with (
        patch.object(rl, "resolve_color_reference", return_value=None),
        patch.object(rl, "_reconcat_seamless_chain", return_value=out_path) as assemble,
    ):
        rl.render_extend_performance(
            shots,
            client=None,
            refs=refs,
            opts=opts,
            out_path=out_path,
            shots_dir=shots_dir,
            concat_only=False,
        )
    assemble.assert_called_once()
    _args, kwargs = assemble.call_args
    assert kwargs.get("label") == "cached reassembly"
    assert kwargs["opts"].loudnorm is True


@pytest.mark.skipif(not STAR_SCRIPT.is_file(), reason="star_lifecycle batch script missing")
def test_concat_only_seamless_grade_rejected_by_cli():
    """#194 — concat-only + seamless must hard-fail (prevents false-pass re-grade)."""
    proc = subprocess.run(
        [
            sys.executable,
            str(RENDER),
            str(STAR_SCRIPT),
            "--concat-only",
            "--seamless",
            "--match-color",
            "--cut-on-motion",
        ],
        cwd=str(ROOT),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    assert proc.returncode != 0
    assert "cannot grade or re-seam" in (proc.stderr or "") + (proc.stdout or "")