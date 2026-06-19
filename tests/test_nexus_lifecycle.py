"""NEXUS job lifecycle file system (#258) — folder-flow state machine tests."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
NEXUS = ROOT / "Nexus"
sys.path.insert(0, str(NEXUS))

from nexus.lifecycle import (  # noqa: E402
    ALL_STAGES,
    FLOW,
    JobError,
    JobStore,
    can_transition,
    create_from_receipt,
)
from nexus.identifiers import ULID_RE  # noqa: E402


def _store(tmp_path: Path) -> JobStore:
    s = JobStore(tmp_path / "Jobs")
    s.ensure_scaffold()
    return s


def test_scaffold_creates_all_stage_dirs(tmp_path: Path):
    s = _store(tmp_path)
    for stage in ALL_STAGES:
        assert (s.root / stage).is_dir()
    assert s.index_path.is_file()


def test_create_mints_ulid_folder_in_intake(tmp_path: Path):
    s = _store(tmp_path)
    m = s.create(service_id="video.explainer_ugc_ad", lane="STUDIO", project_title="Demo")
    jid = m["jobId"]
    assert ULID_RE.match(jid)
    assert (s.root / "intake" / jid / "manifest.json").is_file()
    assert (s.root / "intake" / jid / "artifacts").is_dir()
    assert m["stage"] == "intake" and m["status"] == "active"


def test_full_flow_moves_folder_each_stage(tmp_path: Path):
    s = _store(tmp_path)
    jid = s.create(service_id="editorial.coverage", lane="Editorial")["jobId"]
    seen = ["intake"]
    for nxt in FLOW[1:]:
        m = s.advance(jid)
        seen.append(m["stage"])
        # folder physically present only in the new stage dir
        assert (s.root / m["stage"] / jid).is_dir()
        for other in ALL_STAGES:
            if other != m["stage"]:
                assert not (s.root / other / jid).exists()
    assert seen == list(FLOW)
    final = s.get(jid)
    assert final["stage"] == "delivered" and final["status"] == "terminal"
    assert [h["stage"] for h in final["history"]] == list(FLOW)


def test_illegal_skip_is_blocked(tmp_path: Path):
    s = _store(tmp_path)
    jid = s.create(service_id="x")["jobId"]
    with pytest.raises(JobError):
        s.advance(jid, "delivered")


def test_reject_from_any_active_stage(tmp_path: Path):
    s = _store(tmp_path)
    jid = s.create(service_id="x")["jobId"]
    s.advance(jid)  # validated
    m = s.reject(jid, reason="duplicate")
    assert m["stage"] == "rejected" and m["status"] == "terminal"
    assert (s.root / "rejected" / jid).is_dir()
    with pytest.raises(JobError):
        s.advance(jid)  # terminal


def test_review_kickback_to_in_progress(tmp_path: Path):
    s = _store(tmp_path)
    jid = s.create(service_id="x")["jobId"]
    for _ in range(4):
        s.advance(jid)  # -> review
    assert s.get(jid)["stage"] == "review"
    m = s.advance(jid, "in_progress", note="rework")
    assert m["stage"] == "in_progress"
    assert can_transition("review", "in_progress")


def test_add_artifact_records_in_manifest(tmp_path: Path):
    s = _store(tmp_path)
    jid = s.create(service_id="x")["jobId"]
    s.advance(jid); s.advance(jid); s.advance(jid)  # in_progress
    s.add_artifact(jid, "render_manifest.json", '{"frames": 10}')
    m = s.get(jid)
    assert "artifacts/render_manifest.json" in m["artifacts"]
    assert (s.job_dir(jid) / "artifacts" / "render_manifest.json").is_file()


def test_index_tracks_current_stage(tmp_path: Path):
    s = _store(tmp_path)
    jid = s.create(service_id="x")["jobId"]
    s.advance(jid)
    idx = json.loads(s.index_path.read_text(encoding="utf-8"))
    assert idx["jobs"][jid]["stage"] == "validated"
    assert idx["count"] == 1


def test_reconcile_detects_stage_drift(tmp_path: Path):
    s = _store(tmp_path)
    jid = s.create(service_id="x")["jobId"]
    # Corrupt: edit manifest.stage without moving the folder.
    mp = s.root / "intake" / jid / "manifest.json"
    data = json.loads(mp.read_text(encoding="utf-8"))
    data["stage"] = "delivered"
    mp.write_text(json.dumps(data), encoding="utf-8")
    result = s.reconcile()
    assert result["ok"] is False
    assert any("manifest.stage" in i for i in result["issues"])


def test_create_from_receipt_seeds_intake(tmp_path: Path):
    receipt = {
        "correlationId": "01J0000000000000000000000X",
        "serviceId": "video.explainer_ugc_ad",
        "unspsc": "82151502",
        "schemaValid": True,
        "submission": {"serviceId": "video.explainer_ugc_ad", "projectTitle": "Lumen"},
        "dispatchPlan": {"status": "READY", "lane": "STUDIO", "step_count": 6,
                         "gates": ["gate_0"], "workflow_template": "templates/video_explainer_ugc_ad.json"},
    }
    m = create_from_receipt(receipt, root=tmp_path / "Jobs")
    assert m["stage"] == "intake"
    assert m["serviceId"] == "video.explainer_ugc_ad"
    assert m["lane"] == "STUDIO"
    assert m["gates"] == ["gate_0"]
    assert m["dispatchStatus"] == "READY"
