"""NEXUS #250 + #283 — dispatch execution: folder, plan emission, correlationId."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
NEXUS = ROOT / "Nexus"
TOOLS = ROOT / "tools"
sys.path.insert(0, str(NEXUS))
sys.path.insert(0, str(TOOLS))

import output_registry as reg  # noqa: E402
from nexus import dispatch_execution as de  # noqa: E402
from nexus import intake_v2 as v2  # noqa: E402
from nexus import job_paths  # noqa: E402
from nexus.dispatch_execution import EXECUTION_AUTO, EXECUTION_HUMAN  # noqa: E402
from nexus.identifiers import ULID_RE  # noqa: E402
from nexus.lifecycle import JobStore  # noqa: E402
from nexus.submissions import SubmissionStore  # noqa: E402

EXAMPLES = NEXUS / "Intake_Forms" / "examples"
PI_STORY = EXAMPLES / "pi_story_editorial_filled_v1.json"
VIDEO_CREATOR = EXAMPLES / "video_creator_channel_filled_v1.json"


def _qa_passed_receipt(tmp_path, payload):
    store = SubmissionStore(tmp_path / "sot.json")
    receipt = v2.ingest_and_create_job(
        payload, store=store, jobs_root=tmp_path / "Jobs"
    )
    assert receipt["releaseToDispatch"] is True
    return receipt, store


def test_jobs_root_resolves_via_registry():
    p = job_paths.jobs_root(mkdirs=False)
    assert reg.rel_canonical(p) == "Nexus/Jobs"
    assert reg.classify(p) == "nexus_jobs"


def test_job_folder_resolves_via_registry():
    p = job_paths.job_folder("validated", "01ARZ3NDEKTSV4RRFFQ69G5FAV", mkdirs=False)
    assert reg.rel_canonical(p) == "Nexus/Jobs/validated/01ARZ3NDEKTSV4RRFFQ69G5FAV"


def test_editorial_auto_creates_folder_emits_plan_and_correlation_id(tmp_path):
    payload = json.loads(PI_STORY.read_text(encoding="utf-8"))
    receipt, store = _qa_passed_receipt(tmp_path, payload)

    result = de.execute_dispatch(
        receipt["correlationId"],
        submission=receipt["submission"],
        store=store,
        jobs_root=tmp_path / "Jobs",
    )

    assert result["executionMode"] == EXECUTION_AUTO
    assert result["dispatchStatus"] == "dispatched"
    assert result["packetCount"] == result["dispatchPlan"]["step_count"]
    assert result["packetCount"] > 0

    jid = result["jobId"]
    assert ULID_RE.match(jid)
    folder = tmp_path / "Jobs" / "dispatched" / jid
    assert folder.is_dir()
    assert (folder / "manifest.json").is_file()
    assert (folder / "dispatch_plan.json").is_file()
    assert (folder / "dispatch_state.json").is_file()

    state = json.loads((folder / "dispatch_state.json").read_text(encoding="utf-8"))
    assert state["correlationId"] == receipt["correlationId"]
    assert state["executionMode"] == EXECUTION_AUTO

    packets_dir = folder / "artifacts" / "dispatch_packets"
    packet_files = sorted(packets_dir.glob("*.json"))
    assert len(packet_files) == result["packetCount"]

    for pkt in result["packets"]:
        assert pkt["correlationId"] == receipt["correlationId"]
        assert pkt["jobId"] == jid
        assert pkt["dispatch"]["task_id"] == receipt["correlationId"]
        assert pkt["dispatch"]["context"]["correlationId"] == receipt["correlationId"]

    row = store.get(receipt["correlationId"])
    assert row["status"] == "dispatched"


def test_video_human_gated_pending_approval(tmp_path):
    if not VIDEO_CREATOR.is_file():
        pytest.skip("video creator example missing")
    payload = json.loads(VIDEO_CREATOR.read_text(encoding="utf-8"))
    receipt, store = _qa_passed_receipt(tmp_path, payload)

    result = de.execute_dispatch(
        receipt["correlationId"],
        submission=receipt["submission"],
        store=store,
        jobs_root=tmp_path / "Jobs",
    )

    assert result["executionMode"] == EXECUTION_HUMAN
    assert result["dispatchStatus"] == "pending_approval"
    assert result["stage"] == "validated"
    assert all(p["status"] == "pending_approval" for p in result["packets"])
    assert all(p["correlationId"] == receipt["correlationId"] for p in result["packets"])

    jid = result["jobId"]
    folder = tmp_path / "Jobs" / "validated" / jid
    assert (folder / "dispatch_state.json").is_file()
    assert store.get(receipt["correlationId"])["status"] == "routed"


def test_resolve_execution_mode_policy():
    editorial = {"lane": "Editorial", "service_id": "editorial.coverage", "deliverable": "report"}
    video = {"lane": "STUDIO", "service_id": "video.creator_channel", "deliverable": "channel pack"}
    website = {"lane": "Stonebridge", "service_id": "stonebridge.due_diligence",
               "deliverable": "website compliance audit"}

    assert de.resolve_execution_mode(editorial) == EXECUTION_AUTO
    assert de.resolve_execution_mode(video) == EXECUTION_HUMAN
    assert de.resolve_execution_mode(website) == EXECUTION_HUMAN


def test_dispatch_rejects_non_qa_passed(tmp_path):
    store = SubmissionStore(tmp_path / "sot.json")
    incomplete = {
        "serviceId": "editorial.coverage",
        "autoRoute": {
            "serviceId": "editorial.coverage",
            "lane": "Editorial",
            "gates": ["editorial"],
            "routingMapRow": 2,
        },
    }
    receipt = v2.ingest_submission(incomplete, store=store)
    assert receipt["releaseToDispatch"] is False
    with pytest.raises(de.DispatchError, match="not qa_passed"):
        de.execute_dispatch(
            receipt["correlationId"],
            submission=receipt["submission"],
            store=store,
            jobs_root=tmp_path / "Jobs",
        )


def test_execute_from_receipt_end_to_end(tmp_path):
    payload = json.loads(PI_STORY.read_text(encoding="utf-8"))
    receipt, store = _qa_passed_receipt(tmp_path, payload)

    result = de.execute_from_receipt(
        receipt, store=store, jobs_root=tmp_path / "Jobs"
    )
    assert result["correlationId"] == receipt["correlationId"]
    assert result["packetCount"] == len(result["packets"])
    assert JobStore(tmp_path / "Jobs").get(result["jobId"])["stage"] == "dispatched"