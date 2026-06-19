"""NEXUS intake v2 (#247) — identifiers, SoT idempotency, schema upgrade, migration."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
NEXUS = ROOT / "Nexus"
sys.path.insert(0, str(NEXUS))

from nexus import intake_v2 as v2  # noqa: E402
from nexus.identifiers import (  # noqa: E402
    is_correlation_id,
    new_correlation_id,
    ulid,
    uuid7,
)
from nexus.submissions import SubmissionStore, content_hash  # noqa: E402
from nexus.intake_router import (  # noqa: E402
    parse_auto_route_block,
    validate_auto_route_schema,
)

EXAMPLES = NEXUS / "Intake_Forms/examples"
V2_EXAMPLES = EXAMPLES / "v2"
MD_FORMS = NEXUS / "Intake_Forms/md"
SUBMISSION_SCHEMA = NEXUS / "Intake_Forms/schema/submission.schema.json"
THREE = ["pi_story_editorial", "video_explainer", "stonebridge_compliance"]


# ---------------------------------------------------------------- identifiers
def test_uuid7_format_version_and_uniqueness():
    ids = {uuid7() for _ in range(500)}
    assert len(ids) == 500
    for i in list(ids)[:20]:
        assert is_correlation_id(i)
        assert i[14] == "7"          # version nibble
        assert i[19] in "89ab"       # variant nibble


def test_ulid_format_and_uniqueness():
    ids = {ulid() for _ in range(500)}
    assert len(ids) == 500
    for i in list(ids)[:20]:
        assert len(i) == 26 and is_correlation_id(i)


def test_uuid7_is_time_sortable():
    a = uuid7(ms=1_000_000_000_000)
    b = uuid7(ms=2_000_000_000_000)
    assert a < b  # earlier timestamp sorts first


def test_is_correlation_id_rejects_junk():
    assert not is_correlation_id("not-an-id")
    assert not is_correlation_id("")
    assert not is_correlation_id("12345678-1234-1234-1234-123456789012")  # v1, not v7
    assert new_correlation_id("ulid") and new_correlation_id("uuidv7")
    with pytest.raises(ValueError):
        new_correlation_id("bogus")


# ----------------------------------------------------------- submissions SoT
def test_content_hash_stable_and_sensitive():
    a = {"serviceId": "x", "projectTitle": "T", "submittedAt": "now"}
    b = {"serviceId": "x", "projectTitle": "T", "submittedAt": "LATER"}  # volatile only
    c = {"serviceId": "x", "projectTitle": "CHANGED"}
    assert content_hash(a) == content_hash(b)  # volatile fields ignored
    assert content_hash(a) != content_hash(c)


def test_store_idempotency_created_duplicate_conflict(tmp_path):
    store = SubmissionStore(tmp_path / "sot.json")
    sub = {"correlationId": uuid7(), "serviceId": "editorial.coverage", "projectTitle": "A"}

    r1 = store.record(sub, service_id="editorial.coverage")
    assert r1["outcome"] == "created" and store.count() == 1

    r2 = store.record(sub, service_id="editorial.coverage")
    assert r2["outcome"] == "duplicate" and store.count() == 1  # dedup, no new row

    changed = {**sub, "projectTitle": "B"}
    r3 = store.record(changed, service_id="editorial.coverage")
    assert r3["outcome"] == "conflict" and store.count() == 1   # no silent overwrite

    # persistence round-trip
    reopened = SubmissionStore(tmp_path / "sot.json")
    assert reopened.count() == 1 and reopened.get(sub["correlationId"])["status"] == "routed"


def test_store_mints_correlation_id_when_absent(tmp_path):
    store = SubmissionStore(tmp_path / "sot.json")
    r = store.record({"serviceId": "editorial.coverage", "projectTitle": "A"})
    assert is_correlation_id(r["correlationId"])


def test_store_update_status(tmp_path):
    store = SubmissionStore(tmp_path / "sot.json")
    cid = uuid7()
    store.record({"correlationId": cid, "serviceId": "editorial.coverage", "projectTitle": "A"})
    row = store.update_status(cid, "dispatched")
    assert row["status"] == "dispatched"
    assert [h["status"] for h in row["history"]] == ["routed", "dispatched"]


# ------------------------------------------------------------- normalize / migrate
def test_normalize_keys_snake_to_camel():
    out = v2.normalize_keys({"service_id": "x", "auto_route": {"owner_terminals": ["T1"]}})
    assert out["serviceId"] == "x"
    assert out["autoRoute"]["ownerTerminals"] == ["T1"]


def test_migrate_legacy_adds_correlation_unspsc_semver_camel():
    legacy = json.loads((EXAMPLES / "pi_story_editorial_filled_v1.json").read_text(encoding="utf-8"))
    m = v2.migrate_submission(legacy)
    assert m["serviceId"] == "editorial.screenplay_dev"           # hoisted + camelCase
    assert is_correlation_id(m["correlationId"])                  # ULID/UUIDv7
    assert m["unspsc"] == "82111803"                              # UNSPSC attached
    assert m["schemaVersion"] == v2.SUBMISSION_SCHEMA_VERSION     # SemVer
    assert "service_id" not in m and "auto_route" not in m        # no snake_case left
    assert m["autoRoute"]["serviceId"] == "editorial.screenplay_dev"


def test_migrate_is_idempotent_on_already_v2():
    legacy = json.loads((EXAMPLES / "video_explainer_filled_v1.json").read_text(encoding="utf-8"))
    m1 = v2.migrate_submission(legacy)
    m2 = v2.migrate_submission(m1)
    assert m1["correlationId"] == m2["correlationId"]  # keeps existing valid id


def test_unspsc_map_covers_all_11_services():
    codes = v2.load_service_codes()
    assert len(codes) == 11
    for sid, entry in codes.items():
        assert len(entry["unspsc"]) == 8 and entry["unspsc"].isdigit()
    assert v2.unspsc_for("science.moa_viz") == "82141502"


# --------------------------------------------------------------- schema (2020-12)
def _valid_v2():
    return {
        "correlationId": uuid7(),
        "schemaVersion": "2.0.0",
        "serviceId": "video.explainer_ugc_ad",
        "projectTitle": "Demo",
        "clientContact": "Jane Doe",
        "unspsc": "82151502",
        "autoRoute": {"serviceId": "video.explainer_ugc_ad", "lane": "STUDIO",
                      "gates": ["gate_0"], "routingMapRow": 6},
    }


def test_submission_schema_accepts_valid_v2():
    errs = v2.validate_against_schema(_valid_v2(), v2.load_submission_schema())
    assert errs == [], errs


def test_submission_schema_rejects_bad_correlation_unspsc_semver():
    bad = _valid_v2()
    bad["correlationId"] = "nope"
    bad["unspsc"] = "12"            # not 8 digits
    bad["schemaVersion"] = "v2"     # not SemVer
    errs = v2.validate_against_schema(bad, v2.load_submission_schema())
    joined = " ".join(errs)
    assert "correlationId" in joined and "unspsc" in joined and "schemaVersion" in joined


def test_submission_schema_rejects_unknown_autoroute_key():
    bad = _valid_v2()
    bad["autoRoute"]["mystery"] = "x"
    errs = v2.validate_against_schema(bad, v2.load_submission_schema())
    assert any("mystery" in e for e in errs)


# ------------------------------------------------------- ingest (backward compat)
def test_ingest_all_three_legacy_forms_backward_compatible(tmp_path):
    for i, name in enumerate(THREE):
        legacy = json.loads((EXAMPLES / f"{name}_filled_v1.json").read_text(encoding="utf-8"))
        store = SubmissionStore(tmp_path / f"sot_{i}.json")
        r = v2.ingest_submission(legacy, store=store)
        assert r["schemaValid"] is True, r["schemaErrors"]
        assert r["unspsc"] and len(r["unspsc"]) == 8
        assert r["schemaVersion"] == "2.0.0"
        assert r["submissionOutcome"] == "created"
        assert r["dispatchPlan"]["status"] in ("READY", "READY_WITH_WARNINGS")
        assert r["dispatchPlan"]["dispatch_authorization"]["auto_execute"] is False
        assert store.count() == 1


def test_ingest_dedups_on_correlation_id(tmp_path):
    legacy = json.loads((EXAMPLES / "pi_story_editorial_filled_v1.json").read_text(encoding="utf-8"))
    store = SubmissionStore(tmp_path / "sot.json")
    r1 = v2.ingest_submission(legacy, store=store)
    r2 = v2.ingest_submission(r1["submission"], store=store)  # same minted correlationId
    assert r2["submissionOutcome"] == "duplicate" and store.count() == 1


def test_ingest_ulid_scheme(tmp_path):
    legacy = json.loads((EXAMPLES / "video_explainer_filled_v1.json").read_text(encoding="utf-8"))
    store = SubmissionStore(tmp_path / "sot.json")
    r = v2.ingest_submission(legacy, store=store, correlation_scheme="ulid")
    assert len(r["correlationId"]) == 26  # ULID


# --------------------------------------------------------------- migrated artifacts
def test_migrated_v2_example_files_exist_and_validate():
    schema = v2.load_submission_schema()
    for name in THREE:
        path = V2_EXAMPLES / f"{name}_filled_v2.json"
        assert path.is_file(), f"missing migrated form: {path}"
        sub = json.loads(path.read_text(encoding="utf-8"))
        assert is_correlation_id(sub["correlationId"])
        assert sub["schemaVersion"] == "2.0.0" and len(sub["unspsc"]) == 8
        assert v2.validate_against_schema(sub, schema) == []


# --------------------------------------------------- full v2 rollout (all 11)
def test_full_library_has_eleven_v1_and_v2_examples():
    v1 = sorted(EXAMPLES.glob("*_filled_v1.json"))
    v2_files = sorted(V2_EXAMPLES.glob("*_filled_v2.json"))
    assert len(v1) == 11, [p.name for p in v1]
    assert len(v2_files) == 11, [p.name for p in v2_files]


def test_all_eleven_v1_forms_ingest_backward_compatible(tmp_path):
    seen_services = set()
    for i, p in enumerate(sorted(EXAMPLES.glob("*_filled_v1.json"))):
        legacy = json.loads(p.read_text(encoding="utf-8"))
        r = v2.ingest_submission(legacy, store=SubmissionStore(tmp_path / f"s{i}.json"))
        assert r["schemaValid"] is True, (p.name, r["schemaErrors"])
        assert len(r["unspsc"]) == 8 and r["schemaVersion"] == "2.0.0"
        assert r["dispatchPlan"]["status"] in ("READY", "READY_WITH_WARNINGS")
        seen_services.add(r["serviceId"])
    assert len(seen_services) == 11  # one filled example per service


def test_all_eleven_v2_examples_validate():
    schema = v2.load_submission_schema()
    files = sorted(V2_EXAMPLES.glob("*_filled_v2.json"))
    assert len(files) == 11
    for path in files:
        sub = json.loads(path.read_text(encoding="utf-8"))
        assert is_correlation_id(sub["correlationId"])
        assert sub["schemaVersion"] == "2.0.0" and len(sub["unspsc"]) == 8
        assert "service_id" not in sub and "auto_route" not in sub  # camelCase only
        assert v2.validate_against_schema(sub, schema) == [], path.name


def test_all_eleven_md_forms_carry_v2_standard():
    codes = v2.load_service_codes()
    forms = sorted(MD_FORMS.glob("*.md"))
    assert len(forms) == 11
    for md in forms:
        ar = parse_auto_route_block(md.read_text(encoding="utf-8"))
        assert ar["schemaVersion"] == "2.0.0", md.name
        assert ar["unspsc"] == codes[ar["service_id"]]["unspsc"], md.name
        assert "correlationId" in ar, md.name           # placeholder, minted at intake
        assert validate_auto_route_schema(ar)["valid"] is True, md.name
