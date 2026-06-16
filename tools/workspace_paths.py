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
DAVID_DIR = WORKSPACE / "DAVID"
HISTORY_DIR = WORKSPACE / "History"
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

# Producer layout zones (Studio repo — June 2026)
STUDIO_PRODUCERS_OFFICE = "Producers_Office"
STUDIO_PIPELINE = "Pipeline"
STUDIO_PRODUCTIONS = "Productions"
STUDIO_CAST = "Cast"
STUDIO_TALENT_AGENCY = f"{STUDIO_CAST}/Talent_Agency"
STUDIO_MAGAZINE = "MAGAZINE"
STUDIO_REFERENCE_LIBRARY = "Reference_Library"
STUDIO_PROMPT_LIBRARY = "Prompt_Library"
STUDIO_DEVELOPMENT = "Development"

STUDIO_FOLDERS: tuple[str, ...] = (
    f"{STUDIO_PIPELINE}/Model_Profiles",
    f"{STUDIO_PIPELINE}/Prompt_Versions",
    f"{STUDIO_PIPELINE}/Prompt_Templates",
    f"{STUDIO_PIPELINE}/ShotLists",
    f"{STUDIO_PIPELINE}/Video_Prompts",
    f"{STUDIO_PIPELINE}/OneTake_Prompts",
    f"{STUDIO_PIPELINE}/Fashion_Prompts",
    f"{STUDIO_PIPELINE}/Grok_Video_Packs",
    f"{STUDIO_PIPELINE}/Negative_Prompts",
    f"{STUDIO_PIPELINE}/Refined_Prompts",
    f"{STUDIO_PIPELINE}/Physics_Lighting_Blocks",
    f"{STUDIO_PIPELINE}/Batch_Outputs",
    f"{STUDIO_PRODUCERS_OFFICE}/Compliance_Reports",
    f"{STUDIO_PRODUCERS_OFFICE}/Tool_Logs",
    f"{STUDIO_PRODUCERS_OFFICE}/Release_Tracker",
    f"{STUDIO_REFERENCE_LIBRARY}/Asset_Metadata",
    f"{STUDIO_REFERENCE_LIBRARY}/plates",
    f"{STUDIO_REFERENCE_LIBRARY}/assets",
    "Canons/Bibles",
    f"{STUDIO_PRODUCTIONS}/Narrative",
    f"{STUDIO_PRODUCTIONS}/History",
    f"{STUDIO_PRODUCTIONS}/GFE",
    f"{STUDIO_PRODUCTIONS}/Editorial",
    f"{STUDIO_PRODUCTIONS}/_Scene_Production_Kit",
    f"{STUDIO_MAGAZINE}/Editorial/Models",
    f"{STUDIO_MAGAZINE}/Film/Features",
    f"{STUDIO_MAGAZINE}/Video/Features",
    f"{STUDIO_MAGAZINE}/Runway/Shows",
    f"{STUDIO_MAGAZINE}/Promos/Trailers",
    f"{STUDIO_MAGAZINE}/Profiles/Actors",
    f"{STUDIO_MAGAZINE}/History/Features",
    f"{STUDIO_MAGAZINE}/_Catalog",
    f"{STUDIO_MAGAZINE}/scripts",
    f"{STUDIO_TALENT_AGENCY}/Performance_Studies",
    f"{STUDIO_TALENT_AGENCY}/Scoring_Rubrics",
    f"{STUDIO_TALENT_AGENCY}/Reports",
    f"{STUDIO_TALENT_AGENCY}/Pairing_Notes",
    "renders/approved",
    "renders/review",
    "renders/rejected",
)

PROMPT_SOURCES: dict[str, Path] = {
    "central": PROMPTS_DIR,
    "studio": STUDIO_DIR / STUDIO_PROMPT_LIBRARY,
    "david": DAVID_DIR / "prompts",
}

DAVID_FOLDERS: tuple[str, ...] = (
    "data",
    "languages",
    "scripts",
    "prompts",
    "training_packs",
    "research",
    "reports",
    "brain",
)

REPO_PATHS: dict[str, Path] = {
    "Grok Projects": WORKSPACE,
    "Stonebridge_Operations": STONEBRIDGE_OPS,
    "FLASH": FLASH,
    "DAVID": DAVID_DIR,
}

NESTED_REPOS: dict[str, Path] = {
    "AI": WORKSPACE / "AI",
    "History": WORKSPACE / "History",
    "Stonebridge": WORKSPACE / "Stonebridge",
    "Studio": WORKSPACE / "Studio",
    "Nexus": WORKSPACE / "Nexus",
    "Science": WORKSPACE / "Science",
    "GFE": WORKSPACE / "GFE",
    "MAGAZINE": WORKSPACE / "Studio" / "MAGAZINE",
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


def pipeline_path(*parts: str) -> Path:
    return studio_path(STUDIO_PIPELINE, *parts)


def producers_path(*parts: str) -> Path:
    return studio_path(STUDIO_PRODUCERS_OFFICE, *parts)


def reference_path(*parts: str) -> Path:
    return studio_path(STUDIO_REFERENCE_LIBRARY, *parts)


def magazine_path(*parts: str) -> Path:
    return studio_path(STUDIO_MAGAZINE, *parts)


def count_prompt_files(root: Path, *, exclude_readme: bool = True) -> int:
    if not root.exists():
        return 0
    total = 0
    for path in root.rglob("*.md"):
        if exclude_readme and path.name.upper() == "README.MD":
            continue
        total += 1
    return total