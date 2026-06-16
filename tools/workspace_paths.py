#!/usr/bin/env python3
"""Canonical paths for the Grok Projects workspace."""

from __future__ import annotations

from pathlib import Path

WORKSPACE = Path.home() / "Videos" / "Grok Projects"
GROK_PROJECTS = WORKSPACE
STONEBRIDGE_OPS = WORKSPACE / "Stonebridge" / "Operations"
FLASH = WORKSPACE / "FLASH"
CONTENT_PRODUCTION = WORKSPACE / "Content_Production"
CONTENT_PRODUCTION_PROJECTS = CONTENT_PRODUCTION / "Projects"
STUDIO_DIR = WORKSPACE / "Studio"
ARTIFACTS_DIR = WORKSPACE / "artifacts"
ARTIFACTS_LIB = ARTIFACTS_DIR / "lib"

TOOLS_DIR = WORKSPACE / "tools"
DATA_DIR = WORKSPACE / "data"
DOCS_DIR = WORKSPACE / "docs"
PROMPTS_DIR = WORKSPACE / "prompts"
OUTPUTS_DIR = WORKSPACE / "outputs"
NOTES_DIR = WORKSPACE / "notes"
VERSIONS_DIR = WORKSPACE / "versions"

CONFIG_FILE = DATA_DIR / "config.json"
CHANGELOG_FILE = DATA_DIR / "changelog.json"
DECISIONS_FILE = DATA_DIR / "decisions.json"
ERRORS_FILE = DATA_DIR / "errors.json"
TASKS_FILE = DATA_DIR / "tasks.json"
PROJECT_INDEX_FILE = DATA_DIR / "project_index.json"
TAGS_FILE = DATA_DIR / "tags.json"
X_QUEUE_FILE = DATA_DIR / "x_queue.json"
X_DM_QUEUE_FILE = DATA_DIR / "x_dm_queue.json"
CLIENT_EMAIL_MANIFEST = DATA_DIR / "client_email_manifest.json"
ENV_FILE = WORKSPACE / ".env"
ENV_EXAMPLE_FILE = WORKSPACE / ".env.example"
QUICK_REF_FILE = DOCS_DIR / "QUICK_REFERENCE.md"

STUDIO_FOLDERS: tuple[str, ...] = (
    "Model_Profiles",
    "Prompt_Versions",
    "Prompt_Templates",
    "ShotLists",
    "Video_Prompts",
    "OneTake_Prompts",
    "Fashion_Prompts",
    "Grok_Video_Packs",
    "Negative_Prompts",
    "Asset_Metadata",
    "References",
    "Compliance_Reports",
    "Batch_Outputs",
    "Canons_Bibles",
    "Refined_Prompts",
    "Physics_Lighting_Blocks",
    "Tool_Logs",
)

PROMPT_SOURCES: dict[str, Path] = {
    "central": PROMPTS_DIR,
    "studio": STUDIO_DIR / "prompts",
}

# Display name -> absolute path (for repo scanners / status tools)
REPO_PATHS: dict[str, Path] = {
    "Grok Projects": WORKSPACE,
    "Stonebridge_Operations": STONEBRIDGE_OPS,
    "FLASH": FLASH,
}

NESTED_REPOS: dict[str, Path] = {
    "AI": WORKSPACE / "AI",
    "History": WORKSPACE / "History",
    "Stonebridge": WORKSPACE / "Stonebridge",
    "Studio": WORKSPACE / "Studio",
    "Nexus": WORKSPACE / "Nexus",
    "Science": WORKSPACE / "Science",
    "GFE": WORKSPACE / "GFE",
    "MAGAZINE": WORKSPACE / "MAGAZINE",
}

SUBMODULE_PATHS: dict[str, Path] = {
    "AI": WORKSPACE / "AI",
    "History": WORKSPACE / "History",
    "Stonebridge": WORKSPACE / "Stonebridge",
    "Studio": WORKSPACE / "Studio",
}


def studio_path(*parts: str) -> Path:
    path = STUDIO_DIR.joinpath(*parts)
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


def count_prompt_files(root: Path, *, exclude_readme: bool = True) -> int:
    if not root.exists():
        return 0
    total = 0
    for path in root.rglob("*.md"):
        if exclude_readme and path.name.upper() == "README.MD":
            continue
        total += 1
    return total