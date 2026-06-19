#!/usr/bin/env python3
"""Tests for #173 — science wired into the batch runner.

Observable (science) episodes run the SAME automated loop as DAVID, with two
added rails: the Science Gate (carried in the Gate-0 stamp) and the #158 honesty
rail (illustrative-not-simulation label + cited source), machine-enforced into
the manifest. DAVID episodes flow through untouched (science no-op).

Runnable standalone (python test_science_batch.py) or via pytest. Intake is
stubbed so the loop logic is tested fast and deterministically (no LegalGate /
render side effects); the real end-to-end dry-run is exercised by the CLI.
"""
from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import batch_runner as batch  # noqa: E402
import science_batch_runner as sbr  # noqa: E402

ROOT = batch.ROOT
GREEN_GATE = {"verdict": "GREEN", "blocked": False,
              "requires_human_signoff": False, "human_signoff": True, "warnings": []}
YELLOW_GATE = {"verdict": "YELLOW", "blocked": False,
               "requires_human_signoff": True, "human_signoff": False,
               "warnings": ["[SCIENCE] illustrative-not-simulation disclosure required"]}


def _science_script(slug: str, *, honest: bool) -> dict:
    shot = {"id": "02_at2_viz_payoff", "role": "visualization",
            "reference_slots": {"@2": "visualization"},
            "speech_text": "Here is the attached visualization.",
            "on_screen_labels": ["SCIENCE VISUALIZATION", "NOT TO SCALE"] if honest else []}
    sources = [{"citation": "NASA/ESA Hubble, composite", "url": "https://x"}] if honest else []
    return {"slug": slug, "format_id": "science-explainer",
            "config": {"visualization_reference": "Science/reference_plates/astro/x.jpg",
                       "resolution": "480p"},
            "shots": [{"id": "01_hook", "role": "presenter", "speech_text": "Hook."}, shot],
            "provenance_card": {"sources": sources}}


def _david_script(slug: str) -> dict:
    return {"slug": slug, "format_id": "documentary-host",
            "config": {"resolution": "480p"},
            "shots": [{"id": "01", "role": "host", "speech_text": "Hello."}],
            "provenance_card": {}}


# ---------------------------------------------------------------- science_review
def test_review_noop_for_david():
    sci = batch.science_review(_david_script("d1"), GREEN_GATE)
    assert sci["applies"] is False and sci["passed"] is True
    assert sci["honesty_rail"] is None


def test_review_passes_honest_science():
    sci = batch.science_review(_science_script("s1", honest=True), YELLOW_GATE)
    assert sci["applies"] is True and sci["passed"] is True
    assert sci["honesty_rail"]["status"] == "PASS"
    assert sci["science_gate"]["status"] == "CAUTION"  # brief-level [SCIENCE] warning surfaced


def test_review_fails_dishonest_science():
    sci = batch.science_review(_science_script("s2", honest=False), GREEN_GATE)
    assert sci["applies"] is True and sci["passed"] is False
    assert any("label" in f or "source" in f for f in sci["honesty_rail"]["failures"])


# ---------------------------------------------------------------- classify_item
def test_classify_honesty_fail_blocks_in_dry_run():
    sci = batch.science_review(_science_script("s2", honest=False), GREEN_GATE)
    status = batch.classify_item(gate=GREEN_GATE, render_result=None, qa=None,
                                 dry_run=True, science=sci)
    assert status == "honesty_fail"


def test_classify_honest_science_pending_in_dry_run():
    sci = batch.science_review(_science_script("s1", honest=True), GREEN_GATE)
    status = batch.classify_item(gate=GREEN_GATE, render_result=None, qa=None,
                                 dry_run=True, science=sci)
    assert status == "pending"


def test_classify_gate_precedence_over_honesty():
    # An unsigned YELLOW that is ALSO dishonest reports the gate block first.
    sci = batch.science_review(_science_script("s2", honest=False), YELLOW_GATE)
    status = batch.classify_item(gate=YELLOW_GATE, render_result=None, qa=None,
                                 dry_run=True, science=sci)
    assert status == "needs_signoff"


# ---------------------------------------------------------------- promote gating
def test_promote_requires_honesty_pass():
    sci_bad = {"applies": True, "passed": False}
    row = batch.build_item_row(
        concept_path=_write_concept("p1"), script_path=None, gate=GREEN_GATE,
        intake_exit=0, status="pass", resolution="480p", phase="draft_480p",
        qa={"pass": True}, science=sci_bad)
    assert row["promote_eligible"] is False and row["honesty_pass"] is False


# ---------------------------------------------------------------- summary
def test_summarize_science_rollup():
    items = [
        {"science_applies": True, "honesty_pass": True},
        {"science_applies": True, "honesty_pass": False},
        {"science_applies": False, "honesty_pass": None},
    ]
    assert batch.summarize_science(items) == {
        "science_episodes": 2, "honesty_pass": 1, "honesty_fail": 1}


# ---------------------------------------------------- end-to-end loop (both slates)
_TMP = ROOT / "DAVID" / "scripts" / "_t173_tmp"


def _write_concept(slug: str) -> Path:
    _TMP.mkdir(parents=True, exist_ok=True)
    p = _TMP / "concepts" / f"{slug}.concept.json"
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps({"slug": slug}), encoding="utf-8")
    return p


def test_end_to_end_both_slates_dry_run():
    """One runner, both slates: DAVID no-op + honest science pending + dishonest
    science honesty_fail — proving the same loop carries the science rails."""
    scripts = {
        "david_ep": _david_script("david_ep"),
        "sci_ok": _science_script("sci_ok", honest=True),
        "sci_bad": _science_script("sci_bad", honest=False),
    }
    gates = {"david_ep": GREEN_GATE, "sci_ok": GREEN_GATE, "sci_bad": GREEN_GATE}

    concepts_dir = _TMP / "concepts"
    if concepts_dir.exists():
        shutil.rmtree(concepts_dir)
    for slug in scripts:
        _write_concept(slug)

    orig = batch.run_intake
    batch.run_intake = lambda cp: (  # type: ignore[assignment]
        json.loads(json.dumps(scripts[json.loads(cp.read_text())["slug"]])),
        gates[json.loads(cp.read_text())["slug"]], 0)
    try:
        args = argparse.Namespace(
            concepts_dir=str(concepts_dir), batch_id="t173", batch_dir=str(_TMP / "batch"),
            dry_run=True, no_seamless=True, max_attempts=1, backoff_base=1.0, backoff_max=1.0)
        rc = batch.cmd_run(args)
    finally:
        batch.run_intake = orig  # type: ignore[assignment]

    assert rc == 0
    manifest = json.loads((_TMP / "batch" / "manifest.json").read_text(encoding="utf-8"))
    by_slug = {i["slug"]: i for i in manifest["items"]}
    assert by_slug["david_ep"]["science_applies"] is False
    assert by_slug["david_ep"]["status"] == "pending"
    assert by_slug["sci_ok"]["status"] == "pending" and by_slug["sci_ok"]["honesty_pass"] is True
    assert by_slug["sci_bad"]["status"] == "honesty_fail" and by_slug["sci_bad"]["honesty_pass"] is False
    assert manifest["science_summary"] == {
        "science_episodes": 2, "honesty_pass": 1, "honesty_fail": 1}


# ============================================================ science_batch_runner
# The #173 readiness gate that sits IN FRONT of the shared loop: harvest-status
# normalisation across the 3 manifest shapes + a plate-integrity check the honesty
# rail can't see (it reads the script, this reads the on-disk reference image).

def test_domain_for_subject_maps_prefixes():
    assert sbr.domain_for_subject("Astrophysics — Black Holes") == "astro"
    assert sbr.domain_for_subject("Molecular Biology — DNA") == "molecular"
    assert sbr.domain_for_subject("Chemistry — Bonding") == "chemistry"
    assert sbr.domain_for_subject("Physics — Electromagnetism") == "physics"
    assert sbr.domain_for_subject("History — Rome") is None
    assert sbr.domain_for_subject(None) is None


def test_harvest_map_normalises_three_shapes():
    """Both manifest shapes normalise the same way; HARVEST_FAILED → not ready.

    Hermetic: live harvest manifests are updated by other lanes, so this drives
    synthetic manifests of each shape rather than asserting on volatile status.
    """
    entries_shape = _TMP / "m_entries.json"     # astro shape
    subjects_shape = _TMP / "m_subjects.json"   # molecular/chem/physics shape
    entries_shape.parent.mkdir(parents=True, exist_ok=True)
    entries_shape.write_text(json.dumps({"entries": [
        {"slug": "ok-plate", "harvest_status": "OK"},
        {"slug": "bad-plate", "harvest_status": "HARVEST_FAILED"}]}), encoding="utf-8")
    subjects_shape.write_text(json.dumps({"subjects": [
        {"slug": "locked-plate", "status": "HARVESTED"},
        {"slug": "failed-plate", "status": "HARVEST_FAILED"}]}), encoding="utf-8")

    orig = dict(sbr.DOMAIN_MANIFESTS)
    try:
        sbr.DOMAIN_MANIFESTS["_t_entries"] = entries_shape
        sbr.DOMAIN_MANIFESTS["_t_subjects"] = subjects_shape
        sbr._HARVEST_CACHE.clear()
        ent = sbr._harvest_map("_t_entries")
        sub = sbr._harvest_map("_t_subjects")
    finally:
        sbr.DOMAIN_MANIFESTS.clear()
        sbr.DOMAIN_MANIFESTS.update(orig)
        sbr._HARVEST_CACHE.clear()

    assert ent == {"ok-plate": True, "bad-plate": False}
    assert sub == {"locked-plate": True, "failed-plate": False}


def _ep(slug, domain, plate_slug, ref):
    return {"slug": slug, "concept_path": f"x/{slug}.concept.json", "plate_slug": plate_slug,
            "plate_id": "@X", "subject_domain": domain, "domain": sbr.domain_for_subject(domain),
            "visualization_ref": ref}


def test_check_episode_flags_broken_plate():
    # Harvest says OK, but the reference image on disk is a broken stub.
    sbr._HARVEST_CACHE["chemistry"] = {"covalent-bonding": True}
    broken = _TMP / "broken.png"
    broken.parent.mkdir(parents=True, exist_ok=True)
    broken.write_bytes(b"x" * 400)  # < MIN_REF_BYTES
    ep = _ep("brk", "Chemistry — Bonding", "covalent-bonding", batch_runner_rel(broken))
    out = sbr.check_episode(ep)
    assert out["harvest_ok"] is True
    assert out["ref_ok"] is False and out["ready"] is False
    assert any("broken plate" in r for r in out["reasons"])


def test_check_episode_flags_unharvested():
    sbr._HARVEST_CACHE["physics"] = {"double-slit-interference": False}
    good = _TMP / "good.jpg"
    good.parent.mkdir(parents=True, exist_ok=True)
    good.write_bytes(b"x" * (sbr.MIN_REF_BYTES + 1))
    ep = _ep("ds", "Physics — Interference", "double-slit-interference", batch_runner_rel(good))
    out = sbr.check_episode(ep)
    assert out["ref_ok"] is True and out["harvest_ok"] is False
    assert out["ready"] is False
    assert any("not harvested" in r for r in out["reasons"])


def test_check_episode_ready_when_harvest_and_plate_ok():
    sbr._HARVEST_CACHE["astro"] = {"black-hole": True}
    good = _TMP / "bh.jpg"
    good.parent.mkdir(parents=True, exist_ok=True)
    good.write_bytes(b"x" * (sbr.MIN_REF_BYTES + 10))
    ep = _ep("bh", "Astrophysics — Black Holes", "black-hole", batch_runner_rel(good))
    out = sbr.check_episode(ep)
    assert out["ready"] is True and not out["reasons"]


def test_find_locked_reference_recovers_covalent_plate():
    # Real repo data: the locked covalent_bonding_reference.jpg is the repair target.
    locked = sbr.find_locked_reference("chemistry", "covalent-bonding")
    assert locked and locked.endswith("covalent_bonding_reference.jpg")
    assert sbr._ref_bytes(locked) >= sbr.MIN_REF_BYTES


def test_domain_rollup_counts_honesty_per_slate():
    items = [
        {"slate": "astro", "honesty_pass": True},
        {"slate": "astro", "honesty_pass": True},
        {"slate": "chem_physics", "honesty_pass": False},
        {"slate": "chem_physics", "honesty_pass": True},
    ]
    roll = sbr._domain_rollup(items)
    assert roll["astro"] == {"episodes": 2, "honesty_pass": 2, "honesty_fail": 0}
    assert roll["chem_physics"] == {"episodes": 2, "honesty_pass": 1, "honesty_fail": 1}


def batch_runner_rel(path: Path) -> str:
    """Path relative to ROOT, posix — how concepts store visualization_ref."""
    return str(path.relative_to(ROOT)).replace("\\", "/")


# ---------------------------------------------------------------- standalone runner
def _cleanup():
    sbr._HARVEST_CACHE.clear()
    if _TMP.exists():
        shutil.rmtree(_TMP, ignore_errors=True)


def _run() -> int:
    tests = [v for k, v in sorted(globals().items())
             if k.startswith("test_") and callable(v)]
    failures = 0
    for fn in tests:
        try:
            fn()
            print(f"PASS  {fn.__name__}")
        except Exception as exc:  # noqa: BLE001
            failures += 1
            print(f"FAIL  {fn.__name__}: {exc}")
    _cleanup()
    print(f"\n{len(tests) - failures}/{len(tests)} passed")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(_run())
