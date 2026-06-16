#!/usr/bin/env python3
"""Nexus ecosystem status — Grok Projects repos."""

from __future__ import annotations

import _bootstrap  # noqa: F401
import subprocess
from datetime import datetime
from pathlib import Path

from workspace_paths import NESTED_REPOS, PROMPT_SOURCES, PROMPTS_DIR, WORKSPACE, count_prompt_files

HOME = Path.home()

REPOS: list[tuple[str, str]] = [
    ("Grok Projects", "~/Videos/Grok Projects"),
    ("Nexus", "~/Videos/Grok Projects/Nexus"),
    ("SCIENCE", "~/Videos/Grok Projects/Science"),
    ("STUDIO", "~/Videos/Grok Projects/Studio"),
    ("GFE", "~/Videos/Grok Projects/GFE"),
    ("MAGAZINE", "~/Videos/Grok Projects/MAGAZINE"),
    ("Stonebridge-Security-Consultants", "~/Videos/Grok Projects/Stonebridge"),
    ("Stonebridge_Operations (junction)", "~/Stonebridge_Operations"),
]


def _resolve(path_str: str) -> Path:
    return Path(path_str).expanduser()


def _git_branch(path: Path) -> str | None:
    if not (path / ".git").exists():
        return None
    try:
        r = subprocess.run(
            ["git", "-C", str(path), "rev-parse", "--abbrev-ref", "HEAD"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        if r.returncode == 0:
            return r.stdout.strip()
    except (OSError, subprocess.TimeoutExpired):
        pass
    return None


def _dirty_count(path: Path) -> int:
    if not (path / ".git").exists():
        return 0
    try:
        r = subprocess.run(
            ["git", "-C", str(path), "status", "--porcelain"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        if r.returncode == 0 and r.stdout.strip():
            return len(r.stdout.strip().splitlines())
    except (OSError, subprocess.TimeoutExpired):
        pass
    return 0


def check_repo(name: str, path_str: str) -> str:
    path = _resolve(path_str)
    if not path.exists():
        return f"❌ {name} — MISSING ({path})"

    branch = _git_branch(path)
    dirty = _dirty_count(path)
    dirty_note = f", {dirty} dirty" if dirty else ""

    if branch:
        return f"✅ {name} — git:{branch}{dirty_note}"
    if "junction" in name.lower():
        return f"✅ {name} — linked (no .git)"
    return f"⚠️  {name} — No .git folder"


def count_prompts() -> tuple[int, dict[str, int]]:
    by_source: dict[str, int] = {}
    total = 0

    for label, root in PROMPT_SOURCES.items():
        n = count_prompt_files(root)
        by_source[label] = n
        total += n

    if PROMPTS_DIR.exists():
        for cat in ["system", "orchestration", "studio", "compliance"]:
            cat_path = PROMPTS_DIR / cat
            n = len(list(cat_path.glob("*.md"))) if cat_path.exists() else 0
            by_source[f"central/{cat}"] = n

    return total, by_source


def main() -> None:
    print(f"\n=== NEXUS STATUS — {datetime.now().strftime('%Y-%m-%d %H:%M')} ===\n")

    print("GROK PROJECTS REPOS:")
    ok = 0
    for name, path_str in REPOS:
        line = check_repo(name, path_str)
        print(f"  {line}")
        if line.startswith("✅"):
            ok += 1

    print(f"\n  {ok}/{len(REPOS)} paths OK")

    print("\nSUBMODULES (AI, History, Stonebridge, Studio):")
    for name, path in NESTED_REPOS.items():
        if name in {"AI", "History", "Stonebridge", "Studio"}:
            print(f"  {check_repo(name, str(path))}")

    total, by_source = count_prompts()
    print(f"\nPROMPTS: {total} total (central + Studio/prompts)")
    for key, n in sorted(by_source.items()):
        print(f"  {key}: {n}")

    print("\n=== Quick Actions ===")
    print("  Nexus status:       python tools/nexus_status.py")
    print("  Health check:       python tools/agent_health_monitor.py")
    print("  Repo sync:          python tools/repo_sync_checker.py")
    print("  Ecosystem launcher: python tools/launcher.py")
    print("  Studio launcher:    python artifacts/core/master_launcher.py")
    print("  List prompts:       python tools/prompt_manager.py list --all")


if __name__ == "__main__":
    main()