"""NEXUS intake router (#217) — workflow templates + PI_Story dispatch validation."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
NEXUS = ROOT / "Nexus"
sys.path.insert(0, str(NEXUS))

from nexus.intake_router import (  # noqa: E402
    build_dispatch_plan,
    load_auto_route_schema,
    load_workflow_template,
    parse_auto_route_block,
    route_intake_form,
    service_required_fields,
    validate_auto_route_schema,
    validate_completeness,
)

EDITORIAL_FORM = NEXUS / "Intake_Forms/md/editorial_screenplay_manuscript_dev_intake_v1.md"
PI_STORY_FILLED = NEXUS / "Intake_Forms/examples/pi_story_editorial_filled_v1.json"
VIDEO_FILLED = NEXUS / "Intake_Forms/examples/video_explainer_filled_v1.json"
STONEBRIDGE_FILLED = NEXUS / "Intake_Forms/examples/stonebridge_compliance_filled_v1.json"
SCHEMA_FILE = NEXUS / "Intake_Forms/schema/auto_route.schema.json"
TEMPLATES = NEXUS / "Workflows/templates"
INDEX = NEXUS / "Workflows/INDEX.json"
ROUTER = NEXUS / "nexus/intake_router.py"


def test_workflow_index_has_eleven_services():
    assert INDEX.is_file()
    data = json.loads(INDEX.read_text(encoding="utf-8"))
    assert data["template_count"] == 11
    ids = {s["service_id"] for s in data["services"]}
    assert "editorial.screenplay_dev" in ids
    assert "science.moa_viz" in ids
    assert "stonebridge.compliance_records" in ids


def test_parse_auto_route_from_editorial_form_md():
    text = EDITORIAL_FORM.read_text(encoding="utf-8")
    route = parse_auto_route_block(text)
    assert route["service_id"] == "editorial.screenplay_dev"
    assert route["lane"] == "Editorial"
    assert route["routing_map_row"] == "1"
    assert "editorial" in route["gates"]


def test_pi_story_dispatch_reproduces_editorial_pipeline():
    if not PI_STORY_FILLED.is_file():
        pytest.skip("PI_Story filled form missing")
    payload = json.loads(PI_STORY_FILLED.read_text(encoding="utf-8"))
    plan = build_dispatch_plan(payload["auto_route"], form_context=payload)

    assert plan["service_id"] == "editorial.screenplay_dev"
    assert plan["routing_map_row"] == 1
    assert plan["lane"] == "Editorial"

    step_ids = [s["step"] for s in plan["steps"]]
    assert step_ids.index("03_ingest_story_materials") < step_ids.index("06_draft_screenplay")
    assert step_ids.index("06_draft_screenplay") < step_ids.index("07_coverage")
    assert "04_architecture" in step_ids
    assert "05_development" in step_ids
    assert "02_editorial_gate_intake" in step_ids
    assert step_ids.count("editorial") == 0  # gate is field, not step id

    gates_at_steps = [s["gate"] for s in plan["steps"] if s.get("gate")]
    assert "editorial" in gates_at_steps
    assert "gate_0" in gates_at_steps

    assert "10_studio_storyboard" in step_ids
    assert "11_studio_proof_scene" in step_ids
    assert step_ids.index("09_gate_0_legal") < step_ids.index("10_studio_storyboard")
    assert step_ids.index("09_gate_0_legal") < step_ids.index("11_studio_proof_scene")

    ingest = next(s for s in plan["steps"] if s["step"] == "03_ingest_story_materials")
    assert "story_bible" in ingest["input"]
    assert plan["form_context"]["project_id"] == "pi_story"


def test_route_intake_form_from_md_plus_context():
    if not EDITORIAL_FORM.is_file():
        pytest.skip("editorial form md missing")
    ctx = {
        "project_id": "pi_story",
        "tier": "Full development + STUDIO proof scene",
        "deliverables": ["Full script", "Coverage report", "Storyboard (key sequence)", "Filmed proof scene (STUDIO add-on)"],
    }
    plan = route_intake_form(EDITORIAL_FORM, form_context=ctx)
    assert plan["service_id"] == "editorial.screenplay_dev"
    assert len(plan["steps"]) >= 10


def test_coverage_template_skips_studio_steps():
    tpl = load_workflow_template("editorial.coverage", templates_dir=TEMPLATES)
    plan = build_dispatch_plan({"service_id": "editorial.coverage"}, form_context={})
    step_ids = [s["step"] for s in plan["steps"]]
    assert "07_coverage" not in step_ids
    assert "04_coverage" in step_ids
    assert "gate_0" not in [s.get("gate") for s in plan["steps"]]
    assert tpl["routing_map_row"] == 2


def test_science_template_has_science_and_gate_0():
    plan = build_dispatch_plan({"service_id": "science.moa_viz"}, form_context={})
    gates = [s["gate"] for s in plan["steps"] if s.get("gate")]
    assert "science_gate" in gates
    assert "gate_0" in gates
    owners = [s["owner_terminal"] for s in plan["steps"]]
    assert "T2_plates" in owners
    assert "C2_fact_check" in owners


def test_stonebridge_compliance_has_money_gate():
    plan = build_dispatch_plan({"service_id": "stonebridge.compliance_records"}, form_context={})
    gates = [s["gate"] for s in plan["steps"] if s.get("gate")]
    assert "gate_0_legal" in gates
    assert "money_gate" in gates


def test_cli_emits_dispatch_json(tmp_path: Path):
    if not PI_STORY_FILLED.is_file():
        pytest.skip("PI_Story filled form missing")
    out = tmp_path / "dispatch.json"
    proc = subprocess.run(
        [sys.executable, str(ROUTER), str(PI_STORY_FILLED), "-o", str(out)],
        cwd=str(ROOT),
        capture_output=True,
        text=True,
    )
    assert proc.returncode == 0, proc.stderr
    assert out.is_file()
    plan = json.loads(out.read_text(encoding="utf-8"))
    assert plan["message_type"] == "dispatch_plan"
    assert plan["steps"][-1]["step"] == "12_package_deliverable"


# ===================================================== #217 schema + validation

def test_auto_route_schema_is_wellformed_with_service_enum():
    schema = load_auto_route_schema(schema_path=SCHEMA_FILE)
    assert schema["type"] == "object"
    assert schema["required"] == ["service_id"]
    enum = schema["properties"]["service_id"]["enum"]
    assert len(enum) == 11
    assert "editorial.screenplay_dev" in enum and "stonebridge.compliance_records" in enum


def test_schema_accepts_valid_auto_route():
    good = {
        "service_id": "video.explainer_ugc_ad",
        "lane": "STUDIO",
        "gates": ["gate_0"],
        "owner_terminals": ["production_intake", "T1"],
        "routing_map_row": 6,
        "form_version": "v1",
    }
    res = validate_auto_route_schema(good, schema_path=SCHEMA_FILE)
    assert res["valid"] is True and res["errors"] == []


def test_schema_rejects_bad_service_unknown_key_and_gate():
    bad = {
        "service_id": "video.not_a_service",   # not in enum
        "gates": ["made_up_gate"],             # not in gate enum
        "routing_map_row": 99,                 # out of range
        "mystery_field": "x",                  # additionalProperties: false
    }
    res = validate_auto_route_schema(bad, schema_path=SCHEMA_FILE)
    assert res["valid"] is False
    joined = " ".join(res["errors"])
    assert "service_id" in joined and "gates[0]" in joined
    assert "routing_map_row" in joined and "mystery_field" in joined


def test_schema_requires_service_id():
    res = validate_auto_route_schema({"lane": "Editorial"}, schema_path=SCHEMA_FILE)
    assert res["valid"] is False
    assert any("service_id" in e for e in res["errors"])


def test_incomplete_submission_is_flagged_with_missing_fields():
    payload = json.loads(VIDEO_FILLED.read_text(encoding="utf-8"))
    # Drop a required service field + a master-envelope field.
    payload.pop("call_to_action", None)
    payload.pop("deadline", None)
    ctx = {k: v for k, v in payload.items() if k != "auto_route"}
    val = validate_completeness(payload["auto_route"], ctx)
    assert val["complete"] is False
    assert "call_to_action" in val["missing_service_fields"]
    assert "deadline" in val["missing_envelope"]

    plan = build_dispatch_plan(payload["auto_route"], form_context=ctx)
    assert plan["status"] == "BLOCKED_INCOMPLETE"
    assert plan["dispatch_authorization"]["ready_to_dispatch"] is False
    assert plan["dispatch_authorization"]["block_reasons"]


def test_service_required_fields_lookup():
    req = service_required_fields("video.explainer_ugc_ad")
    assert "project_title" in req["master_envelope"]
    assert "call_to_action" in req["service"]


def test_three_dry_run_routes_complete_and_no_auto_execute():
    for filled, service_id, lane, last_step in [
        (PI_STORY_FILLED, "editorial.screenplay_dev", "Editorial", "12_package_deliverable"),
        (VIDEO_FILLED, "video.explainer_ugc_ad", "STUDIO", "06_package_upload_kit"),
        (STONEBRIDGE_FILLED, "stonebridge.compliance_records", "Stonebridge", "06_package_deliverable"),
    ]:
        if not filled.is_file():
            pytest.skip(f"{filled.name} missing")
        plan = route_intake_form(filled)
        assert plan["service_id"] == service_id
        assert plan["lane"] == lane
        assert plan["status"] in ("READY", "READY_WITH_WARNINGS")
        assert plan["validation"]["auto_route_schema"]["valid"] is True
        assert plan["validation"]["complete"] is True
        assert plan["steps"][-1]["step"] == last_step
        # No auto-execution — every plan awaits human approval (#217 dry-run discipline).
        auth = plan["dispatch_authorization"]
        assert auth["auto_execute"] is False and auth["requires_human_approval"] is True


def test_stonebridge_route_carries_money_and_legal_gates():
    if not STONEBRIDGE_FILLED.is_file():
        pytest.skip("stonebridge filled form missing")
    plan = route_intake_form(STONEBRIDGE_FILLED)
    gates = [s["gate"] for s in plan["steps"] if s.get("gate")]
    assert "gate_0_legal" in gates and "money_gate" in gates


def test_emitted_dispatch_plans_exist_and_are_well_formed():
    dispatches = NEXUS / "Workflows/dispatches"
    for name in ("pi_story_editorial", "video_explainer", "stonebridge_compliance"):
        path = dispatches / f"{name}_dispatch_v1.json"
        assert path.is_file(), f"missing dispatch: {path}"
        plan = json.loads(path.read_text(encoding="utf-8"))
        assert plan["message_type"] == "dispatch_plan"
        assert plan["dispatch_authorization"]["auto_execute"] is False
        assert plan["validation"]["auto_route_schema"]["valid"] is True