"""C3 #259 — output-path enforcement: registry + validator + path-stamping."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / "tools"
sys.path.insert(0, str(TOOLS))

import output_registry as reg  # noqa: E402
import output_validator as val  # noqa: E402


# --- registry: resolve -----------------------------------------------------
def test_resolve_substitutes_root_and_template():
    p = reg.resolve("batch_manifest", mkdirs=False, batch_id="B_259")
    assert reg.rel_canonical(p) == "DAVID/batches/B_259/manifest.json"
    p2 = reg.resolve("production_output", mkdirs=False, lane="Narrative", slug="s1", filename="f.mp4")
    assert reg.rel_canonical(p2) == "Studio/Productions/Narrative/s1/output/f.mp4"


def test_resolve_unknown_kind_raises():
    with pytest.raises(KeyError):
        reg.resolve("not_a_kind", mkdirs=False)


def test_resolve_missing_param_raises():
    with pytest.raises(ValueError):
        reg.resolve("batch_manifest", mkdirs=False)  # batch_id missing


# --- registry: classify ----------------------------------------------------
@pytest.mark.parametrize("path,kind", [
    ("Studio/Legal/Gate_Reports/GATE_GREEN_x_1_editorial.md", "gate_report"),
    ("DAVID/batches/T4_181_science_molecular/manifest.json", "batch_manifest"),
    ("Studio/Productions/Editorial/foo/output/v.mp4", "production_output"),
    ("Content_Production/SCRIBE/editorials/pi_story/intake.json", "editorial_project"),
    ("Science/reference_plates/molecular/x_reference.json", "reference_plate"),
])
def test_classify_known(path, kind):
    assert reg.classify(path) == kind


def test_classify_case_insensitive_root():
    # STUDIO/ classifies the same as Studio/ (drift is tolerated for classification,
    # but flagged by is_canonical / the validator).
    assert reg.classify("STUDIO/Legal/Gate_Reports/x.md") == "gate_report"


def test_classify_unknown_area_is_none():
    assert reg.classify("some/random/place/file.txt") is None


# --- registry: casing ------------------------------------------------------
def test_canonicalize_fixes_case_drift():
    out = reg.rel_canonical("STUDIO/Productions/Narrative/x")
    assert out == "Studio/Productions/Narrative/x"


def test_has_case_drift():
    assert reg.has_case_drift("STUDIO/Legal/x.md") is True
    assert reg.has_case_drift("Studio/Legal/x.md") is False
    assert reg.has_case_drift("DAVID/batches/x") is False  # DAVID is canonical


def test_is_canonical():
    ok, reasons = reg.is_canonical("Studio/Legal/Gate_Reports/x.md")
    assert ok and not reasons
    ok2, reasons2 = reg.is_canonical("STUDIO/Legal/Gate_Reports/x.md")
    assert not ok2 and any("case drift" in r for r in reasons2)
    ok3, reasons3 = reg.is_canonical("scattered_at_root.json")
    assert not ok3 and any("workspace root" in r for r in reasons3)


# --- stamping --------------------------------------------------------------
def test_make_stamp_and_payload():
    stamp = reg.make_stamp("compliance_report", "Studio/Producers_Office/Compliance_Reports/x.json",
                           terminal="C3", params={"filename": "x.json"})
    assert stamp["key"] == "compliance_report"
    assert stamp["canonical_path"].endswith("Compliance_Reports/x.json")
    assert stamp["terminal"] == "C3"
    payload = reg.stamp_payload({"a": 1}, "compliance_report",
                                "Studio/Producers_Office/Compliance_Reports/x.json")
    assert reg.STAMP_KEY in payload and payload["a"] == 1


def test_write_stamped_dict_embeds_and_ledgers(tmp_path, monkeypatch):
    monkeypatch.setattr(reg, "LEDGER_PATH", tmp_path / "ledger.jsonl")
    out = reg.resolve("compliance_report", mkdirs=False, filename="_test259_unit.json")
    try:
        p = reg.write_stamped("compliance_report", {"verdict": "GREEN"},
                              params={"filename": "_test259_unit.json"}, terminal="C3")
        data = json.loads(p.read_text(encoding="utf-8"))
        assert data["verdict"] == "GREEN"
        assert data[reg.STAMP_KEY]["key"] == "compliance_report"
        lines = (tmp_path / "ledger.jsonl").read_text(encoding="utf-8").splitlines()
        assert len(lines) == 1 and json.loads(lines[0])["terminal"] == "C3"
    finally:
        if out.exists():
            out.unlink()


def test_write_stamped_str_writes_sidecar(tmp_path, monkeypatch):
    monkeypatch.setattr(reg, "LEDGER_PATH", tmp_path / "ledger.jsonl")
    out = reg.resolve("gate_report", mkdirs=False, filename="_test259_unit.md")
    sidecar = out.with_name(out.name + ".stamp.json")
    try:
        reg.write_stamped("gate_report", "# Report\n", params={"filename": "_test259_unit.md"})
        assert out.read_text(encoding="utf-8").startswith("# Report")
        assert sidecar.is_file()
        assert json.loads(sidecar.read_text(encoding="utf-8"))["key"] == "gate_report"
    finally:
        for f in (out, sidecar):
            if f.exists():
                f.unlink()


# --- validator -------------------------------------------------------------
def test_validator_flags_planted_root_scatter():
    planted = ROOT / "_scatter_test_259.tmp"
    planted.write_text("x", encoding="utf-8")
    try:
        violations = val.scan_root_scatter()
        names = {v.path for v in violations}
        assert "_scatter_test_259.tmp" in names
    finally:
        planted.unlink()


def test_validator_fix_removes_empty_root_file():
    planted = ROOT / "_scatter_empty_259"
    planted.touch()
    try:
        violations, fixed = val.scan(fix=True)
        assert "_scatter_empty_259" in fixed
        assert not planted.exists()
    finally:
        if planted.exists():
            planted.unlink()


def test_validator_allows_dotfiles_and_known_root_files():
    assert val._is_allowed_root_file(ROOT / ".gitignore")
    assert val._is_allowed_root_file(ROOT / "README.md")
    assert val._is_allowed_root_file(ROOT / ".wave_commit.ps1")
    assert not val._is_allowed_root_file(ROOT / "=")


def test_validator_check_mode_flags_drift_and_wrong_kind():
    v1 = val.check_paths(["STUDIO/Legal/Gate_Reports/x.md"])
    assert any(c.code == "NONCANON" for c in v1)
    v2 = val.check_paths(["Studio/Legal/Gate_Reports/x.md"], expected_kind="batch_manifest")
    assert any(c.code == "WRONG_KIND" for c in v2)
    v3 = val.check_paths(["Studio/Legal/Gate_Reports/x.md"], expected_kind="gate_report")
    assert v3 == []


def test_live_workspace_has_no_root_scatter():
    # the permanent invariant: nothing scattered at the workspace root
    violations, _ = val.scan(fix=False)
    root_scatter = [v for v in violations if v.code == "ROOT_SCATTER"]
    assert root_scatter == [], f"scatter present: {[v.path for v in root_scatter]}"
