"""Canonical Studio output paths — always under Grok Projects/Studio."""

from pathlib import Path

ARTIFACTS_DIR = Path(__file__).resolve().parents[1]
GROK_PROJECTS = ARTIFACTS_DIR.parent
STUDIO_DIR = GROK_PROJECTS / "Studio"


def studio_path(*parts: str) -> Path:
    path = STUDIO_DIR.joinpath(*parts)
    path.parent.mkdir(parents=True, exist_ok=True)
    return path