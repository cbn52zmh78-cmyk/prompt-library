"""Locked performance study rubric v1.0 — Talent Agency."""

from __future__ import annotations

RUBRIC_VERSION = "1.0"

# 0–10 scale per dimension; None = not yet studied
PERFORMANCE_DIMENSIONS: tuple[str, ...] = (
    "emotional_range",
    "physical_continuity",
    "camera_presence",
    "voice_direct_address",
    "archetype_clarity",
    "movement_physics",
)

DIMENSION_LABELS: dict[str, str] = {
    "emotional_range": "Emotional range & believability",
    "physical_continuity": "Face/body/wardrobe continuity across takes",
    "camera_presence": "Eye line, stillness, motivated reaction",
    "voice_direct_address": "Direct-to-camera / dialogue delivery",
    "archetype_clarity": "Archetype reads clearly on first frame",
    "movement_physics": "Gesture, fabric, weight — physical truth",
}

AGENCY_STATUSES: tuple[str, ...] = (
    "development",
    "plate_locked",
    "performance_review",
    "agency_ready",
    "represented",
)

STATUS_GUIDANCE: dict[str, str] = {
    "development": "Profile exists; casting plate not locked — not cleared for hero production.",
    "plate_locked": "3-view or hero plate locked; performance study not complete.",
    "performance_review": "Scene studies logged; scores being finalized by agency team.",
    "agency_ready": "Performance rubric passed; cleared for slate casting.",
    "represented": "Active on producer slate — priority representation.",
}

ROSTER_SOURCES: tuple[str, ...] = (
    "actors_roster",
    "gfe",
    "magazine_editorial",
    "concepts",
)

AGENCY_READY_THRESHOLD = 7.0
MIN_SCORED_DIMENSIONS = 4