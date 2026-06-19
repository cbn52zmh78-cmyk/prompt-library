#!/usr/bin/env python3
"""Editorial engine #212 — pipeline + gate-boundary tests (standalone or pytest)."""

from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import editorial_engine as ee  # noqa: E402

_TMP = Path(__file__).resolve().parent / "_t212_tmp"

_CLEAN_PROSE = (
    "# The Salt Road\n\n"
    "Genre: literary fiction. Work-for-hire — client owns all rights; chain of title on file.\n"
    "Originality confirmed — written from scratch.\n\n"
    "## Chapter 1\n" + ("The caravan crossed the dunes at dawn. " * 40) + "\n\n"
    "## Chapter 2\n" + ("By dusk the wells had run dry and Mara turned back. " * 40) + "\n\n"
    "Sources: author field notes 2025.\n"
)

_DELIVERABLE_META = {"client_deliverable": True, "genre": "literary fiction",
                     "ip_attestation": True, "originality_attestation": True,
                     "title": "The Salt Road"}


def _src(name: str, text: str) -> Path:
    _TMP.mkdir(parents=True, exist_ok=True)
    p = _TMP / name
    p.write_text(text, encoding="utf-8")
    return p


def _meta(name: str, data: dict) -> Path:
    p = _TMP / name
    p.write_text(json.dumps(data), encoding="utf-8")
    return p


def _run(source: Path, meta: Path | None, **over) -> int:
    import argparse
    args = argparse.Namespace(
        source=str(source), meta=str(meta) if meta else None, project_id=None,
        out=str(_TMP / "out" / source.stem), through="deliver", revision=1,
        change_note=None, dry_run=False)
    for k, v in over.items():
        setattr(args, k, v)
    return ee.cmd_run(args)


def _manifest(stem: str) -> dict:
    return json.loads((_TMP / "out" / stem / "manifest.json").read_text(encoding="utf-8"))


# --------------------------------------------------------------- prose full pipeline
def test_prose_deliverable_runs_all_seven_stages():
    src = _src("salt.md", _CLEAN_PROSE)
    meta = _meta("salt.meta.json", _DELIVERABLE_META)
    rc = _run(src, meta)
    assert rc == 0
    m = _manifest("salt")
    assert m["doc_kind"] == "prose"
    assert m["editorial_summary"]["delivered"] is True
    assert m["editorial_summary"]["stages_done"] == 7
    assert m["gate_intake"]["verdict"] == "GREEN"
    names = [s["name"] for s in m["stages"]]
    assert names == ee.STAGES
    # delivery package + coverage artifacts exist
    assert (_TMP / "out" / "salt" / "delivery_manifest.json").is_file()
    assert (_TMP / "out" / "salt" / "coverage.md").is_file()


def test_prose_coverage_detects_chapters():
    src = _src("salt2.md", _CLEAN_PROSE)
    meta = _meta("salt2.meta.json", _DELIVERABLE_META)
    _run(src, meta)
    cov = json.loads((_TMP / "out" / "salt2" / "coverage.json").read_text(encoding="utf-8"))
    assert cov["kind"] == "prose" and cov["unit_label"] == "chapter"
    assert cov["unit_count"] == 2
    assert cov["word_count"] > 100


# ------------------------------------------------------------- intake gate blocking
def test_intake_red_blocks_pipeline():
    bad = _CLEAN_PROSE + "\nNote: this chapter was copied verbatim from another author.\n"
    src = _src("plag.md", bad)
    meta = _meta("plag.meta.json", _DELIVERABLE_META)
    rc = _run(src, meta)
    assert rc == ee.GATE_EXIT_RED
    m = _manifest("plag")
    assert m["gate_intake"]["verdict"] == "RED"
    assert (m["stages"][0]["status"]) == "blocked"
    # pipeline halted: coverage never ran
    assert all(s["name"] != "coverage" for s in m["stages"])
    assert m["editorial_summary"]["delivered"] is False


# ----------------------------------------------------------- deliver signoff gating
def test_yellow_deliverable_unsigned_needs_signoff():
    # No IP / originality attestation on a client deliverable → YELLOW at deliver.
    src = _src("memoir.md", "# Untitled Memoir\n\nGenre: memoir.\n\n"
               "## Chapter 1\n" + ("I was born in spring. " * 30) + "\n\n"
               "## Chapter 2\n" + ("Then came the long war. " * 30) + "\n")
    meta = _meta("memoir.meta.json", {"client_deliverable": True, "genre": "memoir"})
    rc = _run(src, meta)
    assert rc == ee.GATE_EXIT_SIGNOFF_REQUIRED
    m = _manifest("memoir")
    assert m["gate_intake"]["verdict"] == "YELLOW"
    assert (m["stages"][-1]["status"]) == "needs_signoff"
    assert m["editorial_summary"]["delivered"] is False


def test_yellow_deliverable_signed_delivers():
    src = _src("memoir2.md", "# Untitled Memoir\n\nGenre: memoir.\n\n"
               "## Chapter 1\n" + ("I was born in spring. " * 30) + "\n\n"
               "## Chapter 2\n" + ("Then came the long war. " * 30) + "\n")
    meta = _meta("memoir2.meta.json", {"client_deliverable": True, "genre": "memoir",
                                       "human_signoff": True})
    rc = _run(src, meta)
    assert rc == 0
    m = _manifest("memoir2")
    assert m["editorial_summary"]["delivered"] is True


# ------------------------------------------------------------------ dry-run & stage
def test_dry_run_assesses_without_delivery():
    src = _src("salt3.md", _CLEAN_PROSE)
    meta = _meta("salt3.meta.json", _DELIVERABLE_META)
    rc = _run(src, meta, dry_run=True)
    assert rc == 0
    m = _manifest("salt3")
    assert (m["stages"][-1]["status"]) == "skipped"
    assert m["editorial_summary"]["delivered"] is False
    assert not (_TMP / "out" / "salt3" / "delivery_manifest.json").is_file()


def test_through_stops_early():
    src = _src("salt4.md", _CLEAN_PROSE)
    meta = _meta("salt4.meta.json", _DELIVERABLE_META)
    rc = _run(src, meta, through="coverage")
    assert rc == 0
    m = _manifest("salt4")
    names = [s["name"] for s in m["stages"]]
    assert names == ["intake", "coverage"]


def test_screenplay_kind_detected_and_covered():
    fountain = "Title: Test\n\nINT. HOUSE - DAY\n\nAna enters.\n\nANA\nHello.\n\n" \
               "EXT. PARK - NIGHT\n\nThey walk.\n\nINT. CAR - DAY\n\nSilence.\n"
    src = _src("mini.fountain", fountain)
    rc = _run(src, None, through="coverage")
    assert rc == 0
    m = _manifest("mini")
    assert m["doc_kind"] == "screenplay"
    cov = json.loads((_TMP / "out" / "mini" / "coverage.json").read_text(encoding="utf-8"))
    assert cov["kind"] == "screenplay" and cov["unit_count"] == 3


def _cleanup():
    if _TMP.exists():
        shutil.rmtree(_TMP, ignore_errors=True)


def _standalone() -> int:
    tests = [v for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)]
    failures = 0
    for fn in tests:
        try:
            fn()
            print(f"PASS  {fn.__name__}")
        except Exception as exc:  # noqa: BLE001
            failures += 1
            print(f"FAIL  {fn.__name__}: {exc!r}")
    _cleanup()
    print(f"\n{len(tests) - failures}/{len(tests)} passed")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(_standalone())
