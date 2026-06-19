"""T243-B — pre-render gate checklist + one-line emitter."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from unittest.mock import patch

import numpy as np
import pytest
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
DAVID_SCRIPTS = ROOT / "DAVID" / "scripts"
if str(DAVID_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(DAVID_SCRIPTS))

import render_longform as rl  # noqa: E402
import t243_pre_render_gate as gate  # noqa: E402

LATIN_SCRIPT = DAVID_SCRIPTS / "longform_scripts" / "david_latin_corpus_v1_script.json"
GATE_SPEC = ROOT / "Nexus" / "gates" / "T243_pre_render_gate.json"


def _archive_opts() -> rl.SeamlessOptions:
    return rl.SeamlessOptions(
        enabled=True,
        match_color=True,
        magenta_clamp=True,
        neutral_generation=True,
        lamp_lock=False,
    )


def test_gate_spec_exists():
    assert GATE_SPEC.is_file()
    spec = json.loads(GATE_SPEC.read_text(encoding="utf-8"))
    assert spec["gate"] == "T243_PRE_RENDER"
    assert len(spec["checklist"]) == 4


def test_plumbing_audit_passes_on_current_render_longform():
    source = (DAVID_SCRIPTS / "render_longform.py").read_text(encoding="utf-8")
    passes, failures = gate._audit_plumbing(source)
    assert not failures, failures
    assert any("clamp_idempotent" in p for p in passes)
    assert any("single_pass_confirmed" in p for p in passes)


def test_refs_neutral_fails_blue_starved_avatar(tmp_path: Path):
    avatar = tmp_path / "avatar.jpg"
    arr = np.zeros((720, 1280, 3), dtype=np.uint8)
    arr[:, :, 0] = 220
    arr[:, :, 1] = 215
    arr[:, :, 2] = 8
    Image.fromarray(arr).save(avatar)
    set_ref = tmp_path / "set.jpg"
    Image.fromarray(arr).save(set_ref)

    script = {"format_id": "documentary-host", "config": {"seamless": {"neutral_generation": True}}}
    refs = {
        "set_file": str(set_ref),
        "avatar_file": str(avatar),
    }
    passes, failures = gate._check_refs_neutral(
        script, refs, seamless_opts=_archive_opts(), magenta_max=0.42,
    )
    assert failures
    assert any("blue-channel FAIL" in f for f in failures)


def test_refs_neutral_passes_balanced_stills(tmp_path: Path):
    avatar = tmp_path / "avatar.jpg"
    arr = np.zeros((720, 1280, 3), dtype=np.uint8)
    arr[:, :, 0] = 120
    arr[:, :, 1] = 115
    arr[:, :, 2] = 110
    Image.fromarray(arr).save(avatar)
    set_ref = tmp_path / "set.jpg"
    Image.fromarray(arr).save(set_ref)

    script = {"format_id": "documentary-host", "config": {"seamless": {"neutral_generation": True}}}
    refs = {
        "set_file": str(set_ref),
        "avatar_file": str(avatar),
    }
    passes, failures = gate._check_refs_neutral(
        script, refs, seamless_opts=_archive_opts(), magenta_max=0.42,
    )
    assert not failures
    assert any("raw magenta" in p for p in passes)


def test_xfade_seam_config_passes_latin_script():
    script = json.loads(LATIN_SCRIPT.read_text(encoding="utf-8"))
    refs = rl.resolve_refs(script)
    opts = rl.get_seamless_options(script, type("A", (), {"seamless": True})())
    opts = rl._apply_grade_policy(script, refs, opts)
    passes, failures = gate._check_xfade_seam(script, opts, None, xfade_min=0.35)
    assert not failures
    assert any("xfade_s=" in p for p in passes)


def test_one_line_emitter_pass_and_fail():
    ok = gate.format_one_line({"pass": True})
    assert ok == gate.PASS_LINE
    bad = gate.format_one_line({"pass": False, "failures": ["refs_neutral: avatar missing"]})
    assert bad.startswith(gate.FAIL_PREFIX)
    assert "avatar missing" in bad


@pytest.mark.skipif(not LATIN_SCRIPT.is_file(), reason="latin script missing")
def test_cli_one_line_latin_script():
    import subprocess

    proc = subprocess.run(
        [sys.executable, str(DAVID_SCRIPTS / "t243_pre_render_gate.py"), "--script", str(LATIN_SCRIPT)],
        cwd=str(ROOT),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    line = (proc.stdout or "").strip().splitlines()[-1]
    assert line.startswith("T243_PRE_RENDER_GATE")
    # Current refs likely FAIL blue-channel until regen; plumbing + xfade should be evaluable
    if proc.returncode == 0:
        assert line == gate.PASS_LINE
    else:
        assert line.startswith(gate.FAIL_PREFIX)