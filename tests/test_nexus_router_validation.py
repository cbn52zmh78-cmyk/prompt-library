"""NEXUS intake router (#217) — completeness validation + INDEX cross-match coverage."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
NEXUS = ROOT / "Nexus"
sys.path.insert(0, str(NEXUS))

from nexus.intake_router import (  # noqa: E402
    build_dispatch_plan,
    match_service_index,
    route_intake_form,
    validate_completeness,
)

EX = NEXUS / "Intake_Forms/examples"
BLANK_EDITORIAL_MD = NEXUS / "Intake_Forms/md/editorial_screenplay_manuscript_dev_intake_v1.md"


# --------------------------------------------------------------------------- INDEX match
def test_index_match_registered_clean():
    route = {"service_id": "editorial.screenplay_dev", "lane": "Editorial",
             "routing_map_row": 1, "gates": ["editorial"]}
    m = match_service_index(route)
    assert m["registered"] is True
    assert m["mismatches"] == []
    assert m["warnings"] == []


def test_index_match_unregistered_service():
    m = match_service_index({"service_id": "editorial.nope"})
    assert m["registered"] is False
    assert m["mismatches"]


def test_index_match_flags_lane_and_row_mismatch():
    route = {"service_id": "editorial.screenplay_dev", "lane": "STUDIO", "routing_map_row": 99,
             "gates": ["editorial"]}
    m = match_service_index(route)
    assert m["registered"] is True
    assert any("lane" in x for x in m["mismatches"])
    assert any("routing_map_row" in x for x in m["mismatches"])


def test_index_match_gate_alias_is_warning_not_mismatch():
    # Stonebridge form uses adr_0002_money_gate; INDEX uses money_gate — same after aliasing.
    route = {"service_id": "stonebridge.compliance_records", "lane": "Stonebridge",
             "routing_map_row": 9, "gates": ["gate_0_legal", "adr_0002_money_gate"]}
    m = match_service_index(route)
    assert m["mismatches"] == []
    assert any("alias drift" in w for w in m["warnings"])


# --------------------------------------------------------------------------- completeness
def test_completeness_blocks_missing_auto_route_keys():
    v = validate_completeness({"service_id": "video.explainer_ugc_ad"}, {}, require_envelope=False)
    assert v["complete"] is False
    assert set(v["missing_auto_route"]) >= {"lane", "gates", "routing_map_row"}


def test_completeness_detects_placeholder_tier():
    route = {"service_id": "video.explainer_ugc_ad", "lane": "STUDIO",
             "routing_map_row": 6, "gates": ["gate_0"], "tier": "________"}
    v = validate_completeness(route, {}, require_envelope=False)
    assert "tier" in v["placeholder_fields"]
    assert v["complete"] is False


# --------------------------------------------------------------------------- end-to-end
def test_filled_examples_are_ready():
    for name, expected in [
        ("pi_story_editorial_filled_v1.json", "READY"),
        ("video_explainer_filled_v1.json", "READY"),
        ("stonebridge_compliance_filled_v1.json", "READY_WITH_WARNINGS"),
    ]:
        path = EX / name
        if not path.is_file():
            continue
        plan = route_intake_form(path)
        assert plan["status"] == expected, f"{name}: {plan['status']}"
        assert plan["validation"]["complete"] is True


def test_blank_md_form_is_blocked_incomplete():
    plan = route_intake_form(BLANK_EDITORIAL_MD)
    assert plan["status"] == "BLOCKED_INCOMPLETE"
    assert plan["validation"]["missing_envelope"]


def test_dispatch_plan_carries_validation_and_index_blocks():
    plan = build_dispatch_plan(
        {"service_id": "science.moa_viz", "lane": "Observable",
         "routing_map_row": 8, "gates": ["science_gate", "gate_0"]},
        form_context={},
    )
    assert "validation" in plan and "index_match" in plan and "status" in plan
    assert plan["index_match"]["registered"] is True
