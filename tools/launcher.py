#!/usr/bin/env python3
import _bootstrap  # noqa: F401
import subprocess
import sys

from workspace_paths import TOOLS_DIR, WORKSPACE

PYTHON = sys.executable


def tool_script(name: str) -> str:
    return str(TOOLS_DIR / name)


print("\n=== GROK PROJECTS LAUNCHER ===\n")
print("Available Tools:\n")
print(' 1. dual_ai_helper.py workflow "task"')
print(" 2. nexus_status.py")
print(" 3. task_manager.py list")
print(" 4. decision_log.py list")
print(" 5. compliance_report.py <State>")
print(" 6. agent_health_monitor.py")
print(" 7. repo_sync_checker.py")
print(" 8. structure_validator.py")
print(" 9. weekly_summary.py")
print("10. launcher.py (this menu)")
print("\nType the number or full command you want to run.\n")

choice = input("Enter choice: ").strip()

commands = {
    "1": [PYTHON, tool_script("dual_ai_helper.py"), "workflow"],
    "2": [PYTHON, tool_script("nexus_status.py")],
    "3": [PYTHON, tool_script("task_manager.py"), "list"],
    "4": [PYTHON, tool_script("decision_log.py"), "list"],
    "5": [PYTHON, tool_script("compliance_report.py")],
    "6": [PYTHON, tool_script("agent_health_monitor.py")],
    "7": [PYTHON, tool_script("repo_sync_checker.py")],
    "8": [PYTHON, tool_script("structure_validator.py")],
    "9": [PYTHON, tool_script("weekly_summary.py")],
    "10": [PYTHON, tool_script("launcher.py")],
}

if choice in commands:
    cmd = commands[choice]
    if choice == "5":
        state = input("Enter state name (e.g. Pennsylvania): ").strip() or "Pennsylvania"
        cmd.append(state)
    print(f"\nRunning: {' '.join(cmd)}\n")
    subprocess.run(cmd, cwd=WORKSPACE, check=False)
else:
    print("Invalid choice.")