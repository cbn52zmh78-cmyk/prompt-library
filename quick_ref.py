#!/usr/bin/env python3
from pathlib import Path

def generate():
    tools_dir = Path.home() / "prompt_library"
    tools = sorted([f.stem for f in tools_dir.glob("*.py") if f.stem != "__init__"])

    content = "# AI Systems - Quick Reference Card\n\n"
    content += f"Total tools: {len(tools)}\n\n"
    content += "## Available Tools\n\n"

    for tool in tools:
        content += f"- `{tool}.py`\n"

    content += "\n## Common Commands\n\n"
    content += "```bash\n"
    content += "~/prompt_library/nexus_status.py          # Overall system status\n"
    content += "~/prompt_library/decision_log.py list     # View logged decisions\n"
    content += "~/prompt_library/task_manager.py list     # View open tasks\n"
    content += "~/prompt_library/agent_health_monitor.py  # Check folder & prompt health\n"
    content += "```\n"

    output = tools_dir / "QUICK_REFERENCE.md"
    output.write_text(content, encoding="utf-8")
    print(f"Quick reference card generated: {output}")

if __name__ == "__main__":
    generate()