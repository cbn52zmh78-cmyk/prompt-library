#!/usr/bin/env python3
import _bootstrap  # noqa: F401
import sys
from workspace_paths import OUTPUTS_DIR

OUTPUT_DIR = OUTPUTS_DIR
OUTPUT_DIR.mkdir(exist_ok=True)


def optimize_for_grok(text):
    return f"""You are Grok — systems thinker, multi-agent orchestrator, and heavy tool user.

Task: {text}

Instructions:
- Think architecturally and modularly
- Prioritize scalability and long-term maintainability
- Use structured output (sections, bullets, tables)
- Be practical and bold
"""


def optimize_for_claude(text):
    return f"""You are Claude — precise, professional, and excellent at polished writing.

Task: {text}

Instructions:
- Make it clean, tight, and client-ready
- Use professional tone and structure
- Remove fluff, improve flow and clarity
- Output only the final polished version unless asked otherwise
"""


def save_output(name, content):
    file = OUTPUT_DIR / f"{name}.txt"
    file.write_text(content)
    print(f"Saved to: {file}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Commands: grok | claude | polish_grok | polish_claude | workflow")
        sys.exit(1)

    cmd = sys.argv[1].lower()
    text = " ".join(sys.argv[2:]) if len(sys.argv) > 2 else "Test task"

    if cmd == "grok":
        result = optimize_for_grok(text)
        print(result)
        save_output("grok_output", result)

    elif cmd == "claude":
        result = optimize_for_claude(text)
        print(result)
        save_output("claude_output", result)

    elif cmd == "workflow":
        print("=== GROK VERSION ===\n")
        print(optimize_for_grok(text))
        print("\n=== CLAUDE VERSION ===\n")
        print(optimize_for_claude(text))