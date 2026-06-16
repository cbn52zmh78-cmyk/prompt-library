#!/usr/bin/env python3
"""Nexus ecosystem status — Grok Projects repos + prompt library."""

from __future__ import annotations

import subprocess
from pathlib import Path
from datetime import datetime

HOME = Path.home()
GROK = HOME / "Videos" / "Grok Projects"

# (display name, path relative to home or absolute expander string)
REPOS: list[tuple[str, str]] = [
    ("prompt_library", "~/prompt_library"),
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


def check_repo(name: str, path_str: str) -> str:
    path = _resolve(path_str)
    if not path.exists():
        return f"❌ {name} — MISSING ({path})"

    branch = _git_branch(path)
    if branch:
        return f"✅ {name} — git:{branch}"
    if "junction" in name.lower():
        return f"✅ {name} — linked (no .git)"
    return f"⚠️  {name} — No .git folder"


def count_prompts() -> tuple[int, dict[str, int]]:
    prompt_dir = HOME / "prompt_library" / "prompts"
    by_cat: dict[str, int] = {}
    total = 0
    if prompt_dir.exists():
        for cat in ["system", "orchestration", "studio", "compliance"]:
            cat_path = prompt_dir / cat
            n = len(list(cat_path.glob("*.md"))) if cat_path.exists() else 0
            by_cat[cat] = n
            total += n
        for other in prompt_dir.iterdir():
            if other.is_dir() and other.name not in by_cat:
                n = len(list(other.glob("*.md")))
                by_cat[other.name] = n
                total += n
    return total, by_cat


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

    total, by_cat = count_prompts()
    print(f"\nPROMPTS: {total} total")
    for cat, n in sorted(by_cat.items()):
        print(f"  {cat}: {n}")

    print("\n=== Quick Actions ===")
    print("  Nexus status:       python ~/prompt_library/nexus_status.py")
    print("  Health check:       python ~/prompt_library/agent_health_monitor.py")
    print("  List prompts:       python ~/prompt_library/prompt_manager.py list")
    print("  Add prompt:         python ~/prompt_library/prompt_manager.py add <cat> <name>")


if __name__ == "__main__":
    main()