"""Re-export canonical workspace paths (single source: tools/workspace_paths.py)."""

from __future__ import annotations

import sys
from pathlib import Path

_TOOLS = Path(__file__).resolve().parents[2] / "tools"
if str(_TOOLS) not in sys.path:
    sys.path.insert(0, str(_TOOLS))

from workspace_paths import (  # noqa: E402
    ARTIFACTS_DIR,
    GROK_PROJECTS,
    STUDIO_CAST,
    STUDIO_DIR,
    STUDIO_DEVELOPMENT,
    STUDIO_FOLDERS,
    STUDIO_PIPELINE,
    STUDIO_PRODUCTIONS,
    STUDIO_PROMPT_LIBRARY,
    STUDIO_PRODUCERS_OFFICE,
    STUDIO_REFERENCE_LIBRARY,
    WORKSPACE,
    pipeline_path,
    producers_path,
    reference_path,
    studio_path,
)

__all__ = [
    "ARTIFACTS_DIR",
    "GROK_PROJECTS",
    "STUDIO_CAST",
    "STUDIO_DIR",
    "STUDIO_DEVELOPMENT",
    "STUDIO_FOLDERS",
    "STUDIO_PIPELINE",
    "STUDIO_PRODUCTIONS",
    "STUDIO_PROMPT_LIBRARY",
    "STUDIO_PRODUCERS_OFFICE",
    "STUDIO_REFERENCE_LIBRARY",
    "WORKSPACE",
    "pipeline_path",
    "producers_path",
    "reference_path",
    "studio_path",
]