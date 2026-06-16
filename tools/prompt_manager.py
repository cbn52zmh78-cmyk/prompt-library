#!/usr/bin/env python3
"""
Prompt manager — central orchestration prompts live in prompts/.
Studio production prompts live in Studio/prompts/ (read-only via this tool).
"""
from __future__ import annotations

import _bootstrap  # noqa: F401
import json
import sys

from workspace_paths import PROMPT_SOURCES, PROMPTS_DIR, TAGS_FILE, count_prompt_files

PROMPTS_PATH = PROMPTS_DIR


def load_tags():
    if TAGS_FILE.exists():
        return json.loads(TAGS_FILE.read_text())
    return {}


def save_tags(tags):
    TAGS_FILE.write_text(json.dumps(tags, indent=2))


def add_prompt(category, name, content):
    path = PROMPTS_PATH / category / f"{name}.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content)
    print(f"Added: {category}/{name}")


def get_prompt(category, name, source: str = "central"):
    if source == "studio":
        root = PROMPT_SOURCES["studio"]
        matches = list(root.rglob(f"{name}.md"))
        if matches:
            print(matches[0].read_text(encoding="utf-8"))
            return
        print(f"Not found in Studio/prompts: {name}")
        return

    path = PROMPTS_PATH / category / f"{name}.md"
    if path.exists():
        print(path.read_text(encoding="utf-8"))
    else:
        print(f"Not found: {category}/{name}")


def list_prompts(category=None, show_all: bool = False):
    if show_all:
        print("\n=== Prompt sources ===\n")
        for label, root in PROMPT_SOURCES.items():
            n = count_prompt_files(root)
            print(f"{label}: {n} file(s) under {root}")
            if root.exists():
                for path in sorted(root.rglob("*.md")):
                    if path.name.upper() == "README.MD":
                        continue
                    rel = path.relative_to(root)
                    print(f"  {label}/{rel.as_posix()}")
        return

    if category:
        path = PROMPTS_PATH / category
        if path.exists():
            for f in path.glob("*.md"):
                print(f"{category}/{f.stem}")
        else:
            print(f"No prompts in {category}")
    else:
        for cat in ["system", "orchestration", "studio", "compliance"]:
            path = PROMPTS_PATH / cat
            if path.exists():
                for f in path.glob("*.md"):
                    print(f"{cat}/{f.stem}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage:")
        print("  prompt_manager.py add <category> <name>")
        print("  prompt_manager.py get <category> <name> [--studio]")
        print("  prompt_manager.py list [category] [--all]")
        sys.exit(1)

    cmd = sys.argv[1]
    args = sys.argv[2:]
    show_all = "--all" in args
    args = [a for a in args if a != "--all"]
    studio_src = "--studio" in args
    args = [a for a in args if a != "--studio"]

    if cmd == "add" and len(args) >= 2:
        category, name = args[0], args[1]
        content = sys.stdin.read() if not sys.stdin.isatty() else input("Paste prompt content: ")
        add_prompt(category, name, content)

    elif cmd == "get" and len(args) >= 2:
        if studio_src:
            get_prompt(None, args[1], source="studio")
        else:
            get_prompt(args[0], args[1])

    elif cmd == "list":
        category = args[0] if args else None
        list_prompts(category, show_all=show_all)

    elif cmd == "sources":
        for label, root in PROMPT_SOURCES.items():
            print(f"{label}: {root} ({count_prompt_files(root)} prompts)")

    else:
        print("Unknown command or wrong arguments")