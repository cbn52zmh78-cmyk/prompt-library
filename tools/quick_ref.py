#!/usr/bin/env python3
import _bootstrap  # noqa: F401
from workspace_paths import QUICK_REF_FILE, TOOLS_DIR, WORKSPACE


def generate():
    tools = sorted(
        f.stem
        for f in TOOLS_DIR.glob("*.py")
        if f.stem not in {"__init__", "_bootstrap"}
    )

    content = "# AI Systems - Quick Reference Card\n\n"
    content += f"Total tools: {len(tools)}\n\n"
    content += "## Available Tools\n\n"

    for tool in tools:
        content += f"- `tools/{tool}.py`\n"

    content += "\n## Common Commands\n\n"
    content += "```bash\n"
    content += "python ~/Videos/Grok\\ Projects/tools/nexus_status.py          # Overall system status\n"
    content += "python ~/Videos/Grok\\ Projects/tools/decision_log.py list     # View logged decisions\n"
    content += "python ~/Videos/Grok\\ Projects/tools/task_manager.py list     # View open tasks\n"
    content += "python ~/Videos/Grok\\ Projects/tools/agent_health_monitor.py  # Check folder & prompt health\n"
    content += "```\n"

    QUICK_REF_FILE.parent.mkdir(parents=True, exist_ok=True)
    QUICK_REF_FILE.write_text(content, encoding="utf-8")
    print(f"Quick reference card generated: {QUICK_REF_FILE}")


if __name__ == "__main__":
    generate()