"""Unit tests for render_longform dark/high-contrast magenta convergence (480p fixtures)."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
DAVID_SCRIPTS = ROOT / "DAVID" / "scripts"
if str(DAVID_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(DAVID_SCRIPTS))

import render_longform as rl  # noqa: E402
from render_longform import SeamlessOptions  # noqa: E402

RES_480P = "480p"


@pytest.fixture
def warehouse_refs() -> dict:
    return {
        "set_file": str(ROOT / "STUDIO/Pipeline/references/warehouse_industrial_reference.jpg"),
        "format_id": "narrative-short-film",
        "production_meta": {"identity_anchor": "@Amara-001"},
        "resolution": RES_480P,
    }


@pytest.fixture
def clinical_refs() -> dict:
    return {
        "set_file": str(ROOT / "STUDIO/Pipeline/references/seamless_neutral_reference.jpg"),
        "format_id": "explainer-ad",
        "production_meta": {"identity_anchor": "@Amara-001"},
        "resolution": RES_480P,
    }


@pytest.fixture
def warehouse_shot() -> dict:
    return {
        "id": "02_character_intro",
        "video_prompt": (
            "CONTINUITY LOCK @Amara-001. @Set-Warehouse-Industrial-001 dusk industrial loft, "
            "dramatic side key 4800K, deep shadow pockets, high-contrast thriller."
        ),
    }


@pytest.fixture
def seamless_opts() -> SeamlessOptions:
    return SeamlessOptions(
        enabled=True,
        reground_interval=2,
        magenta_clamp=True,
    )


def test_is_dark_scene_warehouse_set_file(warehouse_refs):
    assert rl._is_dark_scene(warehouse_refs) is True


def test_is_dark_scene_clinical_neutral(clinical_refs):
    assert rl._is_dark_scene(clinical_refs) is False


def test_should_magenta_reroll_skips_clinical(clinical_refs):
    script = {"format_id": clinical_refs["format_id"]}
    assert rl._should_magenta_reroll(script, clinical_refs) is False


def test_should_magenta_reroll_enables_movies_dark(warehouse_refs):
    script = {"format_id": warehouse_refs["format_id"]}
    assert rl._should_magenta_reroll(script, warehouse_refs) is True


def test_use_avatar_reground_every_shot_on_dark(
    warehouse_refs, warehouse_shot, seamless_opts
):
    for i in range(3):
        assert rl._use_avatar_reground(warehouse_refs, warehouse_shot, i, seamless_opts) is True


def test_use_avatar_reground_interval_on_clinical(
    clinical_refs, seamless_opts
):
    shot = {"id": "01_hook", "video_prompt": "Clinical cyclorama explainer."}
    assert rl._use_avatar_reground(clinical_refs, shot, 0, seamless_opts) is True
    assert rl._use_avatar_reground(clinical_refs, shot, 1, seamless_opts) is False
    assert rl._use_avatar_reground(clinical_refs, shot, 2, seamless_opts) is True


def test_effective_reground_interval_dark_is_one(
    warehouse_refs, warehouse_shot, seamless_opts
):
    assert rl._effective_reground_interval(seamless_opts, warehouse_refs, warehouse_shot) == 1


def test_magenta_reroll_attempts_dark_vs_neutral(warehouse_refs, warehouse_shot, clinical_refs):
    neutral_shot = {"id": "01_hook", "video_prompt": "Bright studio interior."}
    assert rl._magenta_reroll_attempts(warehouse_refs, warehouse_shot) == 5
    assert rl._magenta_reroll_attempts(clinical_refs, neutral_shot) == 3


def test_kelvin_lock_injects_warehouse_prompt(warehouse_refs):
    base = "CONTINUITY LOCK @Set-Warehouse-Industrial-001: industrial loft."
    lock = rl._kelvin_lock_for_prompt(base, warehouse_refs)
    assert lock is not None
    assert "4800K" in lock
    assert "magenta" in lock.lower()


def test_kelvin_lock_skips_when_kelvin_baked(warehouse_refs):
    base = "Industrial window 4800K directional key locked — zero hue drift."
    assert rl._kelvin_lock_for_prompt(base, warehouse_refs) is None


def test_use_magenta_hue_qa_movies_not_clinical(warehouse_refs, clinical_refs):
    movies_script = {"format_id": "narrative-short-film"}
    clinical_script = {"format_id": "explainer-ad"}
    assert rl._use_magenta_hue_qa(movies_script, warehouse_refs) is True
    assert rl._use_magenta_hue_qa(clinical_script, clinical_refs) is False


def test_movies_script_resolution_480p():
    import json

    script_path = (
        ROOT
        / "STUDIO/Productions/Narrative/movies_lane_sample_v1/movies_lane_sample_v1_script.json"
    )
    script = json.loads(script_path.read_text(encoding="utf-8"))
    assert script["config"]["resolution"] == RES_480P
    assert script["config"]["seamless"]["reground_interval"] == 1
    assert script["production_meta"]["identity_anchor"] == "@Amara-001"