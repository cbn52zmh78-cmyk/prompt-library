"""Smoke tests for the artifacts Studio production pipeline."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
ARTIFACTS = ROOT / "artifacts"
TOOLS = ROOT / "tools"
for entry in (str(ROOT), str(TOOLS), str(ARTIFACTS), str(ARTIFACTS / "profile")):
    if entry not in sys.path:
        sys.path.insert(0, entry)

from workspace_paths import STUDIO_DIR, studio_path  # noqa: E402


@pytest.fixture
def profile_name() -> str:
    return "Test_Editorial"


def test_studio_path_creates_parent():
    path = studio_path("Model_Profiles", "_smoke_test_marker")
    assert path.parent == STUDIO_DIR / "Model_Profiles"
    assert path.parent.exists()


def test_model_profile_manager_loads_profile(profile_name):
    from profile.model_profile_manager import ModelProfileManager

    mgr = ModelProfileManager()
    names = mgr.list_profile_names()
    if profile_name not in names:
        pytest.skip(f"Profile {profile_name} not present in Studio/Model_Profiles")

    data = mgr.get_profile_data(profile_name)
    assert data is not None
    assert "visual" in data


def test_batch_prompt_generator_from_json(tmp_path, profile_name):
    from profile.model_profile_manager import ModelProfileManager
    from prompts.batch_prompt_generator import BatchPromptGenerator

    mgr = ModelProfileManager()
    if profile_name not in mgr.list_profile_names():
        pytest.skip(f"Profile {profile_name} not present")

    spec = {
        "base_prompt": "[SUBJECT] in editorial frame, [MOOD]",
        "variations": [{"MOOD": "confident"}, {"MOOD": "contemplative"}],
    }
    spec_file = tmp_path / "batch_spec.json"
    spec_file.write_text(json.dumps(spec), encoding="utf-8")

    gen = BatchPromptGenerator(output_dir=tmp_path)
    out = gen.generate_from_json(str(spec_file), profile_name=profile_name)
    assert out.exists()
    payload = json.loads(out.read_text(encoding="utf-8"))
    assert len(payload["prompts"]) == 2
    assert profile_name.replace("_", " ") in payload["prompts"][0]["prompt"] or "striking" in payload["prompts"][0]["prompt"]


def test_integration_utils_inject_profile(profile_name):
    from core.integration_utils import inject_profile_into_prompt, load_profile

    profile = load_profile(profile_name)
    if profile is None:
        pytest.skip(f"Profile {profile_name} not present")

    enhanced, ok = inject_profile_into_prompt("editorial portrait", profile_name)
    assert ok is True
    assert profile["visual"] in enhanced


def test_visual_asset_catalog_init_db(tmp_path, monkeypatch):
    from catalog import visual_asset_catalog as vac

    monkeypatch.setattr(vac, "db_path", lambda: tmp_path / "visual_assets.db")
    path = vac.init_db()
    assert path.exists()