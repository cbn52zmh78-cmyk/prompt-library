#!/usr/bin/env python3
import _bootstrap  # noqa: F401
import json
import sys
from datetime import datetime
from workspace_paths import TASKS_FILE

def load_tasks():
    if TASKS_FILE.exists():
        return json.loads(TASKS_FILE.read_text())
    return []

def save_tasks(tasks):
    TASKS_FILE.write_text(json.dumps(tasks, indent=2))

def add_task(description, assigned_to=""):
    tasks = load_tasks()
    task = {
        "id": len(tasks) + 1,
        "date": datetime.now().strftime("%Y-%m-%d"),
        "description": description,
        "assigned_to": assigned_to,
        "status": "open"
    }
    tasks.append(task)
    save_tasks(tasks)
    print(f"Task #{task['id']} added: {description}")

def list_tasks(status=None):
    tasks = load_tasks()
    if not tasks:
        print("No tasks found.")
        return

    filtered = tasks
    if status:
        filtered = [t for t in tasks if t["status"] == status]

    for t in filtered:
        status_icon = "✅" if t["status"] == "done" else ""
        assigned = f" → {t['assigned_to']}" if t['assigned_to'] else ""
        print(f"{status_icon} #{t['id']} [{t['date']}] {t['description']}{assigned}")

def mark_done(task_id):
    tasks = load_tasks()
    for t in tasks:
        if t["id"] == task_id:
            t["status"] = "done"
            save_tasks(tasks)
            print(f"Task #{task_id} marked as done.")
            return
    print(f"Task #{task_id} not found.")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Commands: add | list | done")
        sys.exit(1)

    cmd = sys.argv[1]

    if cmd == "add" and len(sys.argv) >= 3:
        assigned = sys.argv[3] if len(sys.argv) > 3 else ""
        add_task(sys.argv[2], assigned)

    elif cmd == "list":
        status = sys.argv[2] if len(sys.argv) > 2 else None
        list_tasks(status)

    elif cmd == "done" and len(sys.argv) >= 3:
        try:
            mark_done(int(sys.argv[2]))
        except ValueError:
            print("Task ID must be a number.")

    else:
        print("Unknown command or wrong arguments")