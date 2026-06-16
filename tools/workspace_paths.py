#!/usr/bin/env python3
"""Canonical paths for the Grok Projects workspace."""

from pathlib import Path

WORKSPACE = Path.home() / "Videos" / "Grok Projects"
STONEBRIDGE_OPS = WORKSPACE / "Stonebridge" / "Operations"
FLASH = WORKSPACE / "FLASH"
CONTENT_PRODUCTION = WORKSPACE / "Content_Production"
CONTENT_PRODUCTION_PROJECTS = CONTENT_PRODUCTION / "Projects"

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

# Display name -> absolute path (for repo scanners / status tools)
REPO_PATHS: dict[str, Path] = {
    "Grok Projects": WORKSPACE,
    "Stonebridge_Operations": STONEBRIDGE_OPS,
    "FLASH": FLASH,
}