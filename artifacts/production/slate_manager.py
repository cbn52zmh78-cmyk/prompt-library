#!/usr/bin/env python3
"""Production Slate Manager v1.0 — locked active titles (max 10)."""

from __future__ import annotations

import json
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from lib.bootstrap import ensure_paths

ensure_paths()
from lib.studio_paths import producers_path

SLATE_FILE = "SLATE/slate.json"
MAX_SLATE = 10
STATUSES = ("development", "pre_production", "talent_study", "production", "post", "released", "hold", "killed")


def _slate_path() -> Path:
    p = producers_path("SLATE", "slate.json")
    p.parent.mkdir(parents=True, exist_ok=True)
    return p


def load_slate() -> dict:
    path = _slate_path()
    if not path.exists():
        return {"version": "1.0", "updated": None, "projects": []}
    return json.loads(path.read_text(encoding="utf-8"))


def save_slate(data: dict) -> None:
    data["updated"] = datetime.now().isoformat()
    _slate_path().write_text(json.dumps(data, indent=2), encoding="utf-8")


def add_project(project_id: str, title: str, medium: str, rating: str, status: str = "development", notes: str = "") -> None:
    data = load_slate()
    if any(p["id"] == project_id for p in data["projects"]):
        raise ValueError(f"Slate ID {project_id} already exists")
    if len(data["projects"]) >= MAX_SLATE:
        raise ValueError(f"Slate full ({MAX_SLATE} max). Kill or release a title first.")
    data["projects"].append({
        "id": project_id,
        "title": title,
        "medium": medium,
        "target_rating": rating,
        "status": status,
        "legal_gate": "pending",
        "agency_clearance": "pending",
        "notes": notes,
        "created": datetime.now().isoformat(),
    })
    save_slate(data)
    print(f"✅ Added to slate: {title} ({project_id})")


def update_status(project_id: str, status: str, **kwargs) -> None:
    if status not in STATUSES:
        raise ValueError(f"Invalid status. Use: {STATUSES}")
    data = load_slate()
    for p in data["projects"]:
        if p["id"] == project_id:
            p["status"] = status
            p.update(kwargs)
            save_slate(data)
            print(f"✅ {project_id} → {status}")
            return
    raise ValueError(f"Not on slate: {project_id}")


def list_slate() -> None:
    data = load_slate()
    print(f"\nPRODUCTION SLATE ({len(data['projects'])}/{MAX_SLATE})\n")
    for p in data["projects"]:
        print(f"  [{p['status'].upper():16}] {p['id']:20} {p['title']} — {p['medium']} ({p['target_rating']}) gate:{p.get('legal_gate','?')} agency:{p.get('agency_clearance','?')}")


def seed_default_slate() -> None:
    path = _slate_path()
    if path.exists() and json.loads(path.read_text())["projects"]:
        return
    defaults = [
        ("henry_ii_council", "Henry II — Bad News Council", "narrative", "PG-13", "talent_study"),
        ("valentina_editorial", "Valentina Rossi — Cover Editorial", "magazine_editorial", "R", "talent_study"),
        ("gfe_vesper_scene1", "GFE Vesper — Scene 1", "gfe", "R", "talent_study"),
        ("history_marcus_aurelius", "History — Marcus Aurelius", "documentary", "PG", "development"),
        ("pi_story_beat1", "PI Story — Lieutenant Scene", "narrative", "R", "development"),
    ]
    for pid, title, medium, rating, status in defaults:
        try:
            add_project(pid, title, medium, rating, status)
        except ValueError:
            pass


def main() -> int:
    import argparse

    parser = argparse.ArgumentParser(description="Production Slate Manager v1.0")
    parser.add_argument("command", choices=["list", "add", "update", "seed"])
    parser.add_argument("--id", help="project id")
    parser.add_argument("--title", help="project title")
    parser.add_argument("--medium", default="narrative")
    parser.add_argument("--rating", default="PG-13")
    parser.add_argument("--status", default="development")
    parser.add_argument("--notes", default="")
    parser.add_argument("--legal-gate", dest="legal_gate")
    parser.add_argument("--agency", dest="agency_clearance")
    args = parser.parse_args()

    if args.command == "seed":
        seed_default_slate()
        list_slate()
        return 0
    if args.command == "list":
        list_slate()
        return 0
    if args.command == "add":
        add_project(args.id, args.title, args.medium, args.rating, args.status, args.notes)
        return 0
    if args.command == "update":
        kw = {}
        if args.legal_gate:
            kw["legal_gate"] = args.legal_gate
        if args.agency_clearance:
            kw["agency_clearance"] = args.agency_clearance
        update_status(args.id, args.status, **kw)
        return 0
    return 1


if __name__ == "__main__":
    sys.exit(main())