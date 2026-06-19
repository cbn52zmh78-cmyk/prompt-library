"""T1 #249 — intake trigger: valid / invalid / duplicate packet handling."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
NEXUS = ROOT / "Nexus"
sys.path.insert(0, str(NEXUS))

from nexus.identifiers import uuid7  # noqa: E402
from nexus.intake_trigger import (  # noqa: E402
    PacketIndex,
    build_job_spec,
    process_packet_bytes,
    validate_packet,
)
from nexus.jobs import JobStore  # noqa: E402
from nexus.qa_gate import QAGateQueue  # noqa: E402

V2_EXAMPLE = NEXUS / "Intake_Forms/examples/v2/editorial_coverage_filled_v2.json"


def _valid_submission(**overrides) -> dict:
    base = {
        "correlationId": uuid7(),
        "schemaVersion": "2.0.0",
        "serviceId": "editorial.coverage",
        "projectTitle": "Test Coverage Project",
        "clientContact": "test@example.com",
        "autoRoute": {
            "serviceId": "editorial.coverage",
            "lane": "Editorial",
            "tier": "Standard",
            "gates": ["editorial"],
            "ownerTerminals": ["editorial_engine"],
            "routingMapRow": 2,
        },
    }
    base.update(overrides)
    return base


def test_validate_packet_valid():
    ok, errors, sub = validate_packet(_valid_submission())
    assert ok is True
    assert not errors
    assert sub["correlationId"]
    assert sub["serviceId"] == "editorial.coverage"


def test_validate_packet_invalid_missing_required():
    ok, errors, _sub = validate_packet({"projectTitle": "orphan"})
    assert ok is False
    assert any("correlationId" in e or "serviceId" in e for e in errors)


def test_build_job_spec_contract_fields():
    sub = _valid_submission()
    _, _, migrated = validate_packet(sub)
    spec = build_job_spec(migrated)
    assert spec["correlationId"] == migrated["correlationId"]
    assert spec["serviceId"] == "editorial.coverage"
    assert spec["tier"] == "Standard"


def test_process_valid_packet_creates_job_and_qa_handoff(tmp_path: Path):
    sub = _valid_submission()
    raw = json.dumps(sub, separators=(",", ":")).encode("utf-8")
    jobs_path = tmp_path / "jobs.json"
    index_path = tmp_path / "packet_index.json"
    qa_path = tmp_path / "qa_queue.json"

    result = process_packet_bytes(
        raw,
        packet_path="inbox/test.json",
        jobs_store=JobStore(jobs_path),
        packet_index=PacketIndex(index_path),
        qa_queue=QAGateQueue(qa_path),
    )

    assert result.outcome == "accepted"
    assert result.job_id
    assert result.correlation_id == sub["correlationId"]
    assert result.service_id == "editorial.coverage"
    assert result.tier == "Standard"
    assert result.one_line().startswith("INTAKE_TRIGGER PASS")

    js = JobStore(jobs_path)
    row = js.get(result.job_id)
    assert row is not None
    assert row["submissionRef"] == sub["correlationId"]
    assert row["spec"]["serviceId"] == "editorial.coverage"

    qa = QAGateQueue(qa_path)
    assert len(qa.items) == 1
    assert qa.items[0]["jobId"] == result.job_id
    assert qa.items[0]["correlationId"] == sub["correlationId"]


def test_process_invalid_packet_no_job(tmp_path: Path):
    raw = json.dumps({"bad": True}).encode("utf-8")
    jobs_path = tmp_path / "jobs.json"
    index_path = tmp_path / "packet_index.json"
    qa_path = tmp_path / "qa_queue.json"

    result = process_packet_bytes(
        raw,
        packet_path="inbox/bad.json",
        jobs_store=JobStore(jobs_path),
        packet_index=PacketIndex(index_path),
        qa_queue=QAGateQueue(qa_path),
    )

    assert result.outcome == "rejected"
    assert result.job_id is None
    assert result.reasons
    assert result.one_line().startswith("INTAKE_TRIGGER FAIL:")
    assert JobStore(jobs_path).count() == 0
    assert QAGateQueue(qa_path).items == []


def test_duplicate_packet_is_no_op(tmp_path: Path):
    sub = _valid_submission()
    raw = json.dumps(sub).encode("utf-8")
    jobs_path = tmp_path / "jobs.json"
    index_path = tmp_path / "packet_index.json"
    qa_path = tmp_path / "qa_queue.json"
    kwargs = {
        "packet_path": "inbox/dup.json",
        "jobs_store": JobStore(jobs_path),
        "packet_index": PacketIndex(index_path),
        "qa_queue": QAGateQueue(qa_path),
    }

    first = process_packet_bytes(raw, **kwargs)
    second = process_packet_bytes(raw, **kwargs)

    assert first.outcome == "accepted"
    assert second.outcome == "duplicate"
    assert second.job_id == first.job_id
    assert second.one_line().startswith("INTAKE_TRIGGER DUPLICATE")
    assert JobStore(jobs_path).count() == 1
    assert len(QAGateQueue(qa_path).items) == 1


@pytest.mark.skipif(not V2_EXAMPLE.is_file(), reason="v2 example missing")
def test_v2_example_validates():
    payload = json.loads(V2_EXAMPLE.read_text(encoding="utf-8"))
    ok, errors, _ = validate_packet(payload)
    assert ok, errors