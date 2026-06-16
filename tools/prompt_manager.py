#!/usr/bin/env python3
import _bootstrap  # noqa: F401
import json
import sys
from workspace_paths import PROMPTS_DIR, TAGS_FILE

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

def get_prompt(category, name):
    path = PROMPTS_PATH / category / f"{name}.md"
    if path.exists():
        print(path.read_text())
    else:
        print(f"Not found: {category}/{name}")

def list_prompts(category=None):
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
        print("Usage: prompt_manager.py [add|get|list] ...")
        sys.exit(1)

    cmd = sys.argv[1]

    if cmd == "add" and len(sys.argv) >= 4:
        category = sys.argv[2]
        name = sys.argv[3]
        content = sys.stdin.read() if not sys.stdin.isatty() else input("Paste prompt content: ")
        add_prompt(category, name, content)

    elif cmd == "get" and len(sys.argv) >= 4:
        get_prompt(sys.argv[2], sys.argv[3])

    elif cmd == "list":
        category = sys.argv[2] if len(sys.argv) > 2 else None
        list_prompts(category)

    else:
        print("Unknown command or wrong arguments")