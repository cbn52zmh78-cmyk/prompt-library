"""Tests for STUDIO upload packaging pipeline."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
PIPELINE = ROOT / "STUDIO" / "Pipeline"
if str(PIPELINE) not in sys.path:
    sys.path.insert(0, str(PIPELINE))

from package_episode import (  # noqa: E402
    build_chapters,
    build_end_screen,
    build_seo,
    chapter_label,
    format_youtube_timestamp,
    package_production,
)

MOVIES_PROD = ROOT / "STUDIO/Productions/Narrative/movies_lane_sample_v1_longform_v1"


@pytest.fixture
def movies_script() -> dict:
    script_path = MOVIES_PROD / "movies_lane_sample_v1_script.json"
    if not script_path.is_file():
        pytest.skip("movies lane production not built")
    return json.loads(script_path.read_text(encoding="utf-8"))


def test_format_youtube_timestamp():
    assert format_youtube_timestamp(0) == "00:00"
    assert format_youtube_timestamp(65) == "01:05"
    assert format_youtube_timestamp(3661) == "1:01:01"


def test_chapter_label_prefers_speech():
    shot = {"id": "02_character_intro", "role": "character", "speech_text": "I came back for one file."}
    assert chapter_label(shot) == "I came back for one file."


def test_build_chapters_movies(movies_script):
    chapters = build_chapters(movies_script, xfade_s=0.2)
    assert len(chapters) >= 8
    assert chapters[0]["start_s"] == 0.0
    assert chapters[0]["youtube"].startswith("00:00")
    assert any(c["shot_id"] == "provenance_card" for c in chapters)


def test_build_seo_has_chapters_embedded(movies_script):
    chapters = build_chapters(movies_script, xfade_s=0.2)
    seo = build_seo(movies_script, chapters=chapters)
    assert "Warehouse Signal" in seo["title"]
    assert "Chapters" in seo["description"]
    assert "I came back for one file." in seo["description"]
    assert "short film" in seo["tags"]


def test_build_end_screen_trigger():
    end = build_end_screen({"publish": {}}, video_duration_s=57.5)
    assert end["trigger_at_s"] == 37.5
    assert len(end["elements"]) >= 3


def test_package_production_movies_lane():
    if not MOVIES_PROD.is_dir():
        pytest.skip("movies lane production not built")
    result = package_production(MOVIES_PROD)
    kit = Path(result["upload_kit"])
    assert kit.is_dir()
    assert (kit / "video").glob("*.mp4")
    assert (kit / "seo/title.txt").read_text(encoding="utf-8").strip()
    assert (kit / "chapters/youtube_chapters.txt").read_text(encoding="utf-8")
    assert json.loads((kit / "end_screen/end_screen.json").read_text(encoding="utf-8"))["elements"]
    assert (kit / "thumbnail/THUMBNAIL_BRIEF.json").is_file()
    assert (kit / "manifest.json").is_file()