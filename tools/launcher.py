#!/usr/bin/env python3
import _bootstrap  # noqa: F401
import sys

print("\n=== AI SYSTEMS LAUNCHER ===\n")
print("1. tools/dual_ai_helper.py workflow \"task\"")
print("2. tools/nexus_status.py")
print("3. tools/task_manager.py list")
print("4. tools/decision_log.py list")
print("5. tools/compliance_report.py Pennsylvania")
print("6. tools/agent_health_monitor.py")
print("Type the number or command you want to run.")

if len(sys.argv) > 1:
    print(f"Running: {sys.argv[1]}")
    # You can expand this later to auto-run commands