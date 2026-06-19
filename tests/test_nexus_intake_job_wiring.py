"""NEXUS #283 — auto-create job folders from intake receipts (router → file system)."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
NEXUS = ROOT / "Nexus"
sys.path.insert(0, str(NEXUS))

from nexus import intake_v2 as v2  # noqa: E402
from nexus.lifecycle import JobStore  # noqa: E402
from nexus.submissions import SubmissionStore  # noqa: E402
from nexus.identifiers import ULID_RE, is_correlation_id  # noqa: E402

EXAMPLES = NEXUS / "Intake_Forms/examples"
PI_STORY = EXAMPLES / "pi_story_editorial_filled_v1.json"


def _ingest(tmp_path, payload, **kw):
    return v2.ingest_and_create_job(
        payload,
        store=SubmissionStore(tmp_path / "sot.json"),
        jobs_root=tmp_path / "Jobs",
        **kw,
    )


def test_pi_story_validated_form_auto_creates_intake_job(tmp_path):
    legacy = json.loads(PI_STORY.read_text(encoding="utf-8"))
    r = _ingest(tmp_path, legacy)

    assert r["validated"] is True
    assert r["job"] is not None
    job = r["job"]
    assert ULID_RE.match(job["jobId"])
    assert job["stage"] == "intake"
    assert job["correlationId"] == r["correlationId"]

    # folder physically exists at status=intake with a manifest
    folder = tmp_path / "Jobs" / "intake" / job["jobId"]
    assert (folder / "manifest.json").is_file()
    manifest = json.loads((folder / "manifest.json").read_text(encoding="utf-8"))
    assert manifest["stage"] == "intake"
    assert manifest["serviceId"] == "editorial.screenplay_dev"
    assert manifest["correlationId"] == r["correlationId"]
    assert (folder / "submission.json").is_file()
    assert (folder / "dispatch_plan.json").is_file()


def test_jobs_store_index_records_intake(tmp_path):
    r = _ingest(tmp_path, json.loads(PI_STORY.read_text(encoding="utf-8")))
    idx = json.loads((tmp_path / "Jobs" / "_index.json").read_text(encoding="utf-8"))
    assert idx["count"] == 1
    assert idx["jobs"][r["job"]["jobId"]]["stage"] == "intake"


def test_submissions_row_backlinks_jobid(tmp_path):
    store = SubmissionStore(tmp_path / "sot.json")
    r = v2.ingest_and_create_job(
        json.loads(PI_STORY.read_text(encoding="utf-8")),
        store=store, jobs_root=tmp_path / "Jobs",
    )
    row = store.get(r["correlationId"])
    assert row["jobId"] == r["job"]["jobId"]  # bidirectional link


def test_duplicate_submission_does_not_spawn_second_job(tmp_path):
    store = SubmissionStore(tmp_path / "sot.json")
    payload = json.loads(PI_STORY.read_text(encoding="utf-8"))
    r1 = v2.ingest_and_create_job(payload, store=store, jobs_root=tmp_path / "Jobs")
    r2 = v2.ingest_and_create_job(r1["submission"], store=store, jobs_root=tmp_path / "Jobs")

    assert r1["job"]["jobId"]
    assert r2["submissionOutcome"] == "duplicate"
    # idempotent: surfaces the existing job, creates no new folder
    assert r2["job"]["jobId"] == r1["job"]["jobId"]
    jobs = JobStore(tmp_path / "Jobs").list_jobs()
    assert len(jobs) == 1


def test_incomplete_submission_creates_no_job(tmp_path):
    # Registered service, but an incomplete form -> router BLOCKED_INCOMPLETE -> not validated.
    incomplete = {
        "serviceId": "editorial.coverage",
        "autoRoute": {"serviceId": "editorial.coverage", "lane": "Editorial",
                      "gates": ["editorial"], "routingMapRow": 2},
    }
    r = _ingest(tmp_path, incomplete)
    assert r["dispatchPlan"]["status"] == "BLOCKED_INCOMPLETE"
    assert r["validated"] is False
    assert r["job"] is None
    assert JobStore(tmp_path / "Jobs").list_jobs() == []


def test_plain_ingest_unchanged_no_job_side_effects(tmp_path):
    # The non-wired path must not create job folders (back-compat guard).
    r = v2.ingest_submission(
        json.loads(PI_STORY.read_text(encoding="utf-8")),
        store=SubmissionStore(tmp_path / "sot.json"),
    )
    assert "job" not in r
    assert not (tmp_path / "Jobs").exists()
    assert is_correlation_id(r["correlationId"])
