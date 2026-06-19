"""C3 #213 — Editorial Gate wired into the pipeline.

Covers:
  * editorial gate reports route to the shared Studio/Legal/Gate_Reports sink
  * production_intake's EDITORIAL_FORMAT branch detects + routes editorial forms
  * end-to-end validation on the PI_Story editorial form
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
PIPELINE = ROOT / "STUDIO" / "Pipeline"
LEGAL = ROOT / "artifacts" / "legal"
SCRIBE = ROOT / "Content_Production" / "SCRIBE"
SHARED_SINK = ROOT / "STUDIO" / "Legal" / "Gate_Reports"
PI_STORY_FORM = ROOT / "Nexus" / "Intake_Forms" / "examples" / "pi_story_editorial_filled_v1.json"

for _p in (PIPELINE, LEGAL, SCRIBE):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

import production_intake as pi  # noqa: E402
from editorial_gate import evaluate_editorial_gate, save_editorial_report  # noqa: E402


# --- detection -------------------------------------------------------------
@pytest.mark.parametrize("concept", [
    {"format_id": "editorial"},
    {"auto_route": {"lane": "Editorial"}},
    {"auto_route": {"service_id": "editorial.screenplay_dev"}},
    {"auto_route": {"gates": ["editorial"]}},
    {"gates": ["editorial"]},
    {"editorial_brief": "manuscript dev"},
])
def test_is_editorial_intake_positive(concept):
    assert pi.is_editorial_intake(concept) is True


@pytest.mark.parametrize("concept", [
    {"format_id": "science-explainer"},
    {"auto_route": {"lane": "Science"}},
    {"slug": "david_latin", "tags": ["history"]},
    {},
])
def test_is_editorial_intake_negative(concept):
    assert pi.is_editorial_intake(concept) is False


# --- source resolution / meta ---------------------------------------------
def test_source_rank_prefers_screenplay():
    atts = ["bible.md", "script.fountain", "notes.txt", "art.png"]
    assert sorted(atts, key=pi._editorial_source_rank)[0] == "script.fountain"


def test_meta_from_form_maps_fields():
    form = json.loads(PI_STORY_FORM.read_text(encoding="utf-8"))
    meta = pi._editorial_meta_from_form(form)
    assert meta["client_deliverable"] is True
    assert meta["title"] == "PI Story"
    assert meta["names_real_people"] is False
    assert "noir" in meta["genre"].lower()
    assert meta["project_id"] == "pi_story"


# --- shared sink ----------------------------------------------------------
def test_save_editorial_report_lands_in_shared_sink():
    res = evaluate_editorial_gate(
        "# Memoir\n\nGenre: memoir. Work-for-hire; client owns all rights.\n"
        "Original work, written from scratch.\n\n## Chapter 1\nA life.\n",
        {"client_deliverable": True},
    )
    out = save_editorial_report(res, project="unit_test_sink", stage="intake")
    assert out is not None, "path helpers unavailable"
    md = out["md"]
    assert md.is_file()
    assert md.parent == SHARED_SINK, f"report not in shared sink: {md.parent}"
    assert md.name.startswith("GATE_") and md.name.endswith("_editorial.md")
    body = md.read_text(encoding="utf-8")
    assert "# Editorial Gate" in body and "Editorial Rails" in body
    md.unlink()  # keep the sink clean
    if out["json"].is_file():
        out["json"].unlink()


# --- end-to-end validation on PI_Story ------------------------------------
def test_pi_story_form_routes_to_editorial_engine():
    assert PI_STORY_FORM.is_file()
    form = json.loads(PI_STORY_FORM.read_text(encoding="utf-8"))
    assert pi.is_editorial_intake(form)

    before = len(list(SHARED_SINK.glob("*_editorial.md")))
    routing = pi.route_editorial_intake(form, concept_file=PI_STORY_FORM)

    assert routing["lane"] == "Editorial"
    assert routing["service_id"] == "editorial.screenplay_dev"
    assert routing["project_id"] == "pi_story"
    assert routing["doc_kind"] == "screenplay"
    assert routing["source"].endswith("PI_Story_Act_I_Screenplay_v1.fountain")
    assert routing["gate"] == "editorial"
    assert routing["gate_verdict"] in {"GREEN", "YELLOW", "RED"}

    # report routed to the shared sink
    assert routing["gate_report"], "no gate report path returned"
    report = ROOT / routing["gate_report"]
    assert report.is_file()
    assert report.resolve().parent == SHARED_SINK.resolve()
    after = len(list(SHARED_SINK.glob("*_editorial.md")))
    assert after == before + 1

    # intake record written by the engine
    intake = ROOT / routing["intake_record"]
    assert intake.is_file()
    rec = json.loads(intake.read_text(encoding="utf-8"))
    assert rec["doc_kind"] == "screenplay"
    assert rec["gate"]["verdict"] == routing["gate_verdict"]
    assert rec["gate"]["report_path"] == routing["gate_report"]


def test_pi_story_main_cli_routes_and_exits_signoff(capsys):
    rc = pi.main([str(PI_STORY_FORM)])
    out = capsys.readouterr().out
    assert "Editorial lane" in out
    assert "editorial_gate" in out
    # YELLOW (unsigned client deliverable) → signoff-required exit code
    assert rc in {0, pi.GATE_EXIT_SIGNOFF_REQUIRED}
