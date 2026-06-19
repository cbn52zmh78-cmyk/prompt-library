"""Tests for STUDIO production templates → render_longform schema mapping."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
ARTIFACTS = ROOT / "artifacts"
TOOLS = ROOT / "tools"
for entry in (str(ROOT), str(TOOLS), str(ARTIFACTS)):
    if entry not in sys.path:
        sys.path.insert(0, entry)

from production.production_templates import (  # noqa: E402
    build_longform_script,
    compose_video_prompt,
    get_format,
    list_formats,
    select_format,
)


@pytest.fixture
def documentary_beats() -> list[dict]:
    return [
        {
            "id": "01_cold_open",
            "speech_text": "I am DAVID. I bring dead languages back.",
            "action_prompt": "Host seated at Archive worktable, warm lamplight.",
        },
        {
            "id": "02_stakes",
            "speech_text": "When a language died, its voice died with it.",
        },
    ]


def test_list_formats_has_four_templates():
    formats = list_formats()
    assert len(formats) == 4
    assert "documentary-host" in formats
    assert "narrative-short-film" in formats
    assert "conversational-companion" in formats
    assert "explainer-ad" in formats


def test_select_format_companion():
    result = select_format("warm daily check-in companion message, supportive and gentle")
    assert result["format_id"] == "conversational-companion"


def test_select_format_documentary():
    result = select_format("BBC-style host explains attested pronunciation from the corpus")
    assert result["format_id"] == "documentary-host"


def test_select_format_narrative():
    result = select_format("short film character arc with cinematic twist ending")
    assert result["format_id"] == "narrative-short-film"


def test_select_format_explainer_ad():
    result = select_format("30 second product ad with clear CTA sign up now")
    assert result["format_id"] == "explainer-ad"


def test_compose_video_prompt_has_prefix_and_end_guard():
    prompt = compose_video_prompt(
        action_prompt="Host speaks to camera.",
        speech_text="Hello world.",
        role="host",
        set_id="@Set-Archive-001",
        style_id="@Style-Documentary-Prestige-001",
        identity_continuity_lock="CONTINUITY LOCK @David-001: identical host face.",
        voice_suffix="documentary gravitas, synthetic host only",
    )
    assert "CONTINUITY LOCK @David-001" in prompt
    assert "CONTINUITY LOCK @Set-Archive-001" in prompt
    assert "STYLE LOCK @Style-Documentary-Prestige-001" in prompt
    assert 'Lip-synced, delivers: "Hello world."' in prompt
    assert "gesture peak" in prompt.lower()
    assert "synthetic" in prompt.lower()


def test_build_longform_script_canonical_shape(documentary_beats):
    script = build_longform_script(
        "documentary-host",
        concept="Channel intro",
        slug="test_intro",
        beats=documentary_beats,
    )
    assert script["slug"] == "test_intro"
    assert "config" in script
    assert "shots" in script
    assert "provenance_card" in script
    assert "qa_rules" in script
    assert script["config"]["seamless"]["primary"] == "extend"
    assert script["config"]["seamless"]["xfade_s"] == 0.2

    shot = script["shots"][0]
    for key in ("id", "duration", "t_start", "t_end", "video_prompt", "speech_text", "role"):
        assert key in shot

    assert shot["t_start"] == 0
    assert shot["t_end"] == shot["duration"]
    assert "@David-001" in shot["video_prompt"]
    assert "gesture peak" in shot["video_prompt"].lower()

    assert len(script["guardrails"]) >= 5
    assert script["production_meta"]["set_id"] == "@Set-Archive-001"


def test_companion_guardrails_sfw():
    fmt = get_format("conversational-companion")
    joined = " ".join(fmt["guardrails"]).lower()
    assert "sfw" in joined
    assert "no explicit" in joined or "pg" in joined


def test_shot_timings_are_contiguous():
    script = build_longform_script("explainer-ad", concept="SaaS launch")
    prev_end = 0
    for shot in script["shots"]:
        assert shot["t_start"] == prev_end
        assert shot["t_end"] == shot["t_start"] + shot["duration"]
        prev_end = shot["t_end"]


def test_b_roll_omits_lip_sync():
    prompt = compose_video_prompt(
        action_prompt="Wide establishing shot of warehouse.",
        speech_text="",
        role="b_roll",
        set_id="@Set-Warehouse-Industrial-001",
        style_id="@Style-Cinematic-001",
        identity_continuity_lock="CONTINUITY LOCK @Talent-001: same character.",
        voice_suffix="synthetic talent only",
        include_lip_sync=False,
    )
    assert "Lip-synced" not in prompt
    assert "gesture peak" in prompt.lower() or "dead stillness" in prompt.lower()


def test_script_roundtrip_json(documentary_beats, tmp_path):
    script = build_longform_script("documentary-host", concept="Roundtrip", beats=documentary_beats)
    out = tmp_path / "script.json"
    out.write_text(json.dumps(script, indent=2), encoding="utf-8")
    loaded = json.loads(out.read_text(encoding="utf-8"))
    assert loaded["shots"][0]["speech_text"] == documentary_beats[0]["speech_text"]