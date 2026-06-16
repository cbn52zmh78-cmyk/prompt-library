#!/usr/bin/env python3
"""Call Sheet Manager v1.0 — log every Director session."""

from __future__ import annotations

import json
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from lib.bootstrap import ensure_paths

ensure_paths()
from lib.studio_paths import producers_path


class CallSheetManager:
    def __init__(self) -> None:
        self.dir = producers_path("Call_Sheets")
        self.logs = producers_path("Session_Logs")
        self.dir.mkdir(parents=True, exist_ok=True)
        self.logs.mkdir(parents=True, exist_ok=True)

    def open_day(self, project_id: str, director: str = "Director") -> Path:
        stamp = datetime.now().strftime("%Y-%m-%d")
        path = self.dir / f"{stamp}_{project_id}_call_sheet.json"
        if path.exists():
            return path
        payload = {
            "date": stamp,
            "project_id": project_id,
            "director": director,
            "producer": "Producer",
            "legal_gate": "pending",
            "agency_cleared_talent": [],
            "scenes": [],
            "disposition": {},
            "notes": "",
        }
        path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        return path

    def log_scene(self, project_id: str, scene: str, medium: str, talent: list[str], legal: str, disposition: str, notes: str = "") -> None:
        legal_upper = legal.upper()
        if legal_upper in ("RED", "PENDING", ""):
            raise ValueError(
                f"Cannot log scene without Gate 0 clearance. Legal status '{legal}' blocked. "
                "Run legal_gate.py first."
            )
        stamp = datetime.now().strftime("%Y-%m-%d")
        path = self.dir / f"{stamp}_{project_id}_call_sheet.json"
        if not path.exists():
            self.open_day(project_id)
        data = json.loads(path.read_text(encoding="utf-8"))
        entry = {
            "time": datetime.now().isoformat(),
            "scene": scene,
            "medium": medium,
            "talent": talent,
            "legal_gate": legal,
            "disposition": disposition,
            "notes": notes,
        }
        data["scenes"].append(entry)
        path.write_text(json.dumps(data, indent=2), encoding="utf-8")
        log_path = self.logs / f"{stamp}_{project_id}.md"
        with open(log_path, "a", encoding="utf-8") as f:
            f.write(f"\n## {entry['time']}\n- Scene: {scene}\n- Talent: {', '.join(talent)}\n- Legal: {legal}\n- Out: {disposition}\n- Notes: {notes}\n")
        print(f"✅ Logged: {scene} → {disposition}")


def main() -> int:
    import argparse

    parser = argparse.ArgumentParser(description="Call Sheet Manager v1.0")
    parser.add_argument("command", choices=["open", "log"])
    parser.add_argument("--project", required=True)
    parser.add_argument("--scene", default="")
    parser.add_argument("--medium", default="video")
    parser.add_argument("--talent", default="")
    parser.add_argument("--legal", default="GREEN")
    parser.add_argument("--disposition", default="review")
    parser.add_argument("--notes", default="")
    args = parser.parse_args()

    mgr = CallSheetManager()
    if args.command == "open":
        p = mgr.open_day(args.project)
        print(f"✅ Call sheet: {p}")
        return 0
    talent = [t.strip() for t in args.talent.split(",") if t.strip()]
    mgr.log_scene(args.project, args.scene, args.medium, talent, args.legal, args.disposition, args.notes)
    return 0


if __name__ == "__main__":
    sys.exit(main())