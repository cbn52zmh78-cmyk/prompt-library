#!/usr/bin/env python3
"""Unified ecosystem launcher — Nexus ops tools + Studio artifacts pipeline."""

import _bootstrap  # noqa: F401
import subprocess
import sys

from workspace_paths import ARTIFACTS_DIR, TOOLS_DIR, WORKSPACE

PYTHON = sys.executable


def tool_script(name: str) -> str:
    return str(TOOLS_DIR / name)


def run_cmd(cmd: list[str]) -> None:
    print(f"\nRunning: {' '.join(cmd)}\n")
    subprocess.run(cmd, cwd=WORKSPACE, check=False)


def nexus_menu() -> None:
    print("\n=== NEXUS OPS TOOLS ===\n")
    print(" 1. nexus_status.py")
    print(" 2. agent_health_monitor.py")
    print(" 3. repo_sync_checker.py")
    print(" 4. structure_validator.py")
    print(" 5. task_manager.py list")
    print(" 6. decision_log.py list")
    print(" 7. prompt_manager.py list --all")
    print(" 8. dual_ai_helper.py workflow")
    print(" 9. weekly_summary.py")
    print("10. compliance_report.py")
    print(" 0. Back\n")

    choice = input("Enter choice: ").strip()
    commands = {
        "1": [PYTHON, tool_script("nexus_status.py")],
        "2": [PYTHON, tool_script("agent_health_monitor.py")],
        "3": [PYTHON, tool_script("repo_sync_checker.py")],
        "4": [PYTHON, tool_script("structure_validator.py")],
        "5": [PYTHON, tool_script("task_manager.py"), "list"],
        "6": [PYTHON, tool_script("decision_log.py"), "list"],
        "7": [PYTHON, tool_script("prompt_manager.py"), "list", "--all"],
        "8": [PYTHON, tool_script("dual_ai_helper.py"), "workflow"],
        "9": [PYTHON, tool_script("weekly_summary.py")],
        "10": [PYTHON, tool_script("compliance_report.py")],
    }
    if choice == "0":
        return
    if choice not in commands:
        print("Invalid choice.")
        return
    cmd = commands[choice]
    if choice == "8":
        task = input('Task description: ').strip() or "status check"
        cmd.append(task)
    if choice == "10":
        state = input("State name (e.g. Pennsylvania): ").strip() or "Pennsylvania"
        cmd.append(state)
    run_cmd(cmd)


def studio_menu() -> None:
    studio_launcher = ARTIFACTS_DIR / "core" / "master_launcher.py"
    if not studio_launcher.exists():
        print(f"❌ Studio launcher not found: {studio_launcher}")
        return
    run_cmd([PYTHON, str(studio_launcher)])


def main() -> None:
    while True:
        print("\n=== GROK PROJECTS ECOSYSTEM LAUNCHER ===\n")
        print(" 1. Nexus ops tools")
        print(" 2. Studio production pipeline (artifacts)")
        print(" 3. Quick: nexus_status")
        print(" 4. Quick: repo_sync_checker")
        print(" 0. Exit\n")

        choice = input("Enter choice: ").strip()
        if choice == "0":
            print("Exiting.")
            break
        if choice == "1":
            nexus_menu()
        elif choice == "2":
            studio_menu()
        elif choice == "3":
            run_cmd([PYTHON, tool_script("nexus_status.py")])
        elif choice == "4":
            run_cmd([PYTHON, tool_script("repo_sync_checker.py")])
        else:
            print("Invalid choice.")


if __name__ == "__main__":
    main()