"""Discover talent across Cast rosters and extract performance-relevant metadata."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

from lib.studio_paths import STUDIO_DIR, studio_path

CAST_ROOT = STUDIO_DIR / "Cast"
ACTORS_ROSTER = CAST_ROOT / "actors_roster"
GFE_ROOT = CAST_ROOT / "GFE"
MAGAZINE_MODELS = STUDIO_DIR / "MAGAZINE" / "Editorial" / "Models"
CONCEPTS_ROOT = CAST_ROOT / "CONCEPTS"


def slugify(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", name.lower()).strip("_")


@dataclass
class TalentRecord:
    talent_id: str
    display_name: str
    roster_source: str
    roster_path: str
    gender: str = ""
    world_region: str = ""
    age_locked: int | None = None
    archetypes: list[str] = field(default_factory=list)
    performance_style: str = ""
    voice_notes: str = ""
    has_profile_md: bool = False
    has_casting_jpg: bool = False
    has_clips: bool = False
    profile_excerpt: str = ""


def _parse_profile_md(text: str) -> dict:
    out: dict = {"archetypes": [], "age_locked": None, "performance_style": "", "voice_notes": ""}
    age_match = re.search(r"Age \(locked\)\s*\|\s*\*\*(\d+)\*\*", text)
    if age_match:
        out["age_locked"] = int(age_match.group(1))
    style_match = re.search(r"## Performance Style\s*\n(.+?)(?=\n##|\Z)", text, re.S)
    if style_match:
        out["performance_style"] = style_match.group(1).strip()
    voice_match = re.search(r"## Voice Notes\s*\n(.+?)(?=\n##|\Z)", text, re.S)
    if voice_match:
        out["voice_notes"] = voice_match.group(1).strip()
    arch_block = re.search(r"## Archetypes\s*\n((?:- .+\n?)+)", text)
    if arch_block:
        out["archetypes"] = [
            line.lstrip("- ").strip()
            for line in arch_block.group(1).splitlines()
            if line.strip().startswith("-")
        ]
    return out


def _has_casting_jpg(folder: Path) -> bool:
    patterns = ("01_casting_shots", "CASTING", "casting_shots")
    for pat in patterns:
        casting = folder / pat
        if casting.is_dir() and any(casting.glob("*.jpg")):
            return True
    return any(folder.rglob("*casting*.jpg")) or any(folder.rglob("*turnaround*.jpg"))


def _scan_actors_roster() -> list[TalentRecord]:
    records: list[TalentRecord] = []
    if not ACTORS_ROSTER.is_dir():
        return records
    for profile in ACTORS_ROSTER.rglob("actor_profile.md"):
        folder = profile.parent
        parts = folder.relative_to(ACTORS_ROSTER).parts
        gender = parts[0] if len(parts) >= 1 else ""
        region = parts[1] if len(parts) >= 2 else ""
        name = folder.name.replace("_", " ")
        text = profile.read_text(encoding="utf-8", errors="replace")
        parsed = _parse_profile_md(text)
        records.append(
            TalentRecord(
                talent_id=slugify(name),
                display_name=name,
                roster_source="actors_roster",
                roster_path=str(folder),
                gender=gender,
                world_region=region,
                age_locked=parsed["age_locked"],
                archetypes=parsed["archetypes"],
                performance_style=parsed["performance_style"],
                voice_notes=parsed["voice_notes"],
                has_profile_md=True,
                has_casting_jpg=_has_casting_jpg(folder),
                profile_excerpt=parsed["performance_style"][:200],
            )
        )
    return records


def _scan_gfe() -> list[TalentRecord]:
    records: list[TalentRecord] = []
    if not GFE_ROOT.is_dir():
        return records
    for folder in sorted(GFE_ROOT.iterdir()):
        if not folder.is_dir() or folder.name.startswith("."):
            continue
        clips_dir = folder / "CLIPS"
        records.append(
            TalentRecord(
                talent_id=f"gfe_{slugify(folder.name)}",
                display_name=folder.name,
                roster_source="gfe",
                roster_path=str(folder),
                has_profile_md=(folder / "actor_profile.md").exists(),
                has_casting_jpg=_has_casting_jpg(folder),
                has_clips=clips_dir.is_dir() and any(clips_dir.glob("*.txt")),
            )
        )
    return records


def _scan_magazine_models() -> list[TalentRecord]:
    records: list[TalentRecord] = []
    if not MAGAZINE_MODELS.is_dir():
        return records
    for folder in sorted(MAGAZINE_MODELS.iterdir()):
        if not folder.is_dir():
            continue
        records.append(
            TalentRecord(
                talent_id=f"mag_{slugify(folder.name)}",
                display_name=folder.name,
                roster_source="magazine_editorial",
                roster_path=str(folder),
                has_casting_jpg=_has_casting_jpg(folder),
            )
        )
    return records


def discover_all_talent() -> list[TalentRecord]:
    return _scan_actors_roster() + _scan_gfe() + _scan_magazine_models()


def agency_root() -> Path:
    return studio_path("Cast", "Talent_Agency")