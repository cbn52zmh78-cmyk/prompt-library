"""Visual-Source Interpretation gate + FeederPacket emitter (v1).

Enforces the 7 rails (Nexus/gates/visual_source_interpretation_gate.json /
.../visual-source/INTERPRETATION_GATE.md) over a visual-source manifest, then
emits a FeederPacket and validates the handoff into AI -> STUDIO/SCRIBE per
AI/docs/Feeder_AI_STUDIO_Handoff_Contract_v1.md.

Mirrors the DAVID gate pattern (t243_pre_render_gate.py): evaluate_* -> verdict,
format_one_line, assert_*. Pure stdlib.
"""
from __future__ import annotations

import json
import sys
import uuid
from pathlib import Path
from typing import Any

WORKSPACE = Path(__file__).resolve().parents[2]
GATE_SPEC = WORKSPACE / "Nexus" / "gates" / "visual_source_interpretation_gate.json"
MANIFEST = (WORKSPACE / "DAVID" / "communication-modalities" / "visual-source"
            / "visual_source_manifest.json")

STATUS_ENUM = {"DECIPHERED", "PARTIALLY_DECIPHERED", "UNDECIPHERED"}
GRADES = {"primary", "secondary", "tertiary"}
PASS_LINE = "VISUAL_SOURCE_GATE PASS"
FAIL_PREFIX = "VISUAL_SOURCE_GATE FAIL:"


def load_gate_spec() -> dict[str, Any]:
    return json.loads(GATE_SPEC.read_text(encoding="utf-8"))


def evaluate_entry(entry: dict[str, Any]) -> dict[str, Any]:
    """Return {slug, verdict, failed} after checking all 7 rails on one entry."""
    failed: list[str] = []
    status = entry.get("decipherment_status")
    interp = entry.get("interpretation", "__missing__")
    claims = entry.get("claims") or []

    # R2 — status mandatory + in enum
    if status not in STATUS_ENUM:
        failed.append("R2")

    # R5 — transcription / transliteration / interpretation are separate fields (keys present)
    if not all(k in entry for k in ("transcription", "transliteration", "interpretation")):
        failed.append("R5")

    # R6 — confidence present + dissent is a list
    if not entry.get("confidence") or not isinstance(entry.get("dissent"), list):
        failed.append("R6")

    # R4 — provenance + license, OR parked
    parked = entry.get("harvest_status") == "PARKED"
    if not parked and not (entry.get("source_url") and entry.get("license")):
        failed.append("R4")

    # R3 — each claim cites a graded source
    for c in claims:
        if not c.get("citation") or c.get("grade") not in GRADES:
            failed.append("R3")
            break

    # R1 — DECIPHERED requires interpretation + >=1 citation
    if status == "DECIPHERED":
        if not entry.get("interpretation") or not claims:
            failed.append("R1")

    # R7 — UNDECIPHERED must NOT assert meaning (interpretation is null)
    if status == "UNDECIPHERED" and entry.get("interpretation") is not None:
        failed.append("R7")

    failed = sorted(set(failed))
    return {"slug": entry.get("slug"), "status": status,
            "verdict": "PASS" if not failed else "FAIL", "failed": failed}


def evaluate_manifest(manifest: dict[str, Any]) -> dict[str, Any]:
    results = [evaluate_entry(e) for e in manifest.get("entries", [])]
    failed = [r for r in results if r["verdict"] != "PASS"]
    return {
        "gate": "VISUAL_SOURCE_INTERPRETATION",
        "verdict": "PASS" if not failed else "FAIL",
        "entry_count": len(results),
        "pass_count": len(results) - len(failed),
        "fail_count": len(failed),
        "entries": results,
    }


def format_one_line(result: dict[str, Any]) -> str:
    if result["verdict"] == "PASS":
        return f"{PASS_LINE} ({result['pass_count']}/{result['entry_count']} entries)"
    bad = "; ".join(f"{r['slug']}:{','.join(r['failed'])}" for r in result["entries"] if r["failed"])
    return f"{FAIL_PREFIX} {bad}"


def assert_gate(manifest_path: Path | None = None) -> dict[str, Any]:
    manifest = json.loads((manifest_path or MANIFEST).read_text(encoding="utf-8"))
    result = evaluate_manifest(manifest)
    if result["verdict"] != "PASS":
        raise AssertionError(format_one_line(result))
    return result


# ---------------------------------------------------------------- FeederPacket
def emit_feeder_packet(manifest: dict[str, Any], *, gate_result: dict[str, Any]) -> dict[str, Any]:
    """Build a FeederPacket (AI handoff contract v1) from a gated manifest."""
    facts = []
    for e in manifest.get("entries", []):
        for c in e.get("claims", []):
            facts.append({"claim": c["claim"], "citation": c["citation"], "grade": c["grade"]})
    plates = [{"id": e.get("plate_id"), "path": e.get("file"),
               "license": e.get("license"), "source_url": e.get("source_url"),
               "decipherment_status": e.get("decipherment_status")}
              for e in manifest.get("entries", [])]
    return {
        "packet_id": str(uuid.uuid4()),
        "source_repo": "DAVID",
        "domain": "visual_source",
        "subject": "Visual-Source Interpretation v1 (POC)",
        "as_of": manifest.get("generated_at"),
        "research_payload": {"facts": facts, "sim_parameters": {}},
        "render_assets": {
            "reference_manifest": "DAVID/communication-modalities/visual-source/visual_source_manifest.json",
            "plates": plates,
            "parked_sources": manifest.get("parked_sources"),
        },
        "gate_status": {"visual_source_interpretation_gate": gate_result["verdict"]},
    }


_REQUIRED_PACKET_KEYS = ("packet_id", "source_repo", "domain", "subject", "as_of",
                         "research_payload", "render_assets", "gate_status")


def validate_feeder_packet(packet: dict[str, Any]) -> tuple[bool, list[str]]:
    """Check a FeederPacket against the handoff contract's required shape."""
    errs: list[str] = []
    for k in _REQUIRED_PACKET_KEYS:
        if k not in packet:
            errs.append(f"missing key: {k}")
    rp = packet.get("research_payload") or {}
    if "facts" not in rp:
        errs.append("research_payload.facts missing")
    for f in rp.get("facts", []):
        if not f.get("citation") or f.get("grade") not in GRADES:
            errs.append("a fact lacks citation/grade (STD-CITE-001)")
            break
    ra = packet.get("render_assets") or {}
    if "reference_manifest" not in ra:
        errs.append("render_assets.reference_manifest missing")
    if packet.get("gate_status", {}).get("visual_source_interpretation_gate") != "PASS":
        errs.append("feeder gate not PASS — handoff blocked")
    return (not errs, errs)


def route_ai_to_studio_scribe(packet: dict[str, Any]) -> dict[str, Any]:
    """AI federation passthrough for a research-only packet -> StudioPackage for SCRIBE.

    visual_source is text/interpretation (no viz domain), so the federation passes it
    straight through (handoff contract S.2) and targets the editorial engine (Scribe/SCRIBE).
    """
    return {
        "message_type": "StudioPackage",
        "packet_id": packet["packet_id"],          # correlation key carried through
        "source": packet["source_repo"],
        "domain": packet["domain"],
        "task": "editorial_interpretation",
        "ai_processing": "passthrough (research-only; no viz transform)",
        "jantzen_compliance": "N/A (non-viz)",
        "target": "STUDIO -> Scribe/SCRIBE (editorial engine)",
        "facts": packet["research_payload"]["facts"],
        "parked_sources": packet["render_assets"].get("parked_sources"),
    }


def main(argv: list[str] | None = None) -> int:
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    result = evaluate_manifest(manifest)

    def emit(line: str) -> None:
        buf = getattr(sys.stdout, "buffer", None)
        (buf.write((line + "\n").encode("utf-8")), buf.flush()) if buf else print(line)

    emit("=== Visual-Source Interpretation Gate ===")
    emit(format_one_line(result))
    for r in result["entries"]:
        emit(f"  [{r['verdict']}] {r['slug']} ({r['status']})"
             + (f" failed={r['failed']}" if r["failed"] else ""))

    # POC negative control — prove the gate bites: undeciphered + asserted meaning => R7 FAIL
    neg = evaluate_entry({
        "slug": "NEGATIVE_CONTROL_undeciphered_with_fake_meaning",
        "decipherment_status": "UNDECIPHERED",
        "transcription": "x", "transliteration": "y",
        "interpretation": "invented meaning (should be RED)",
        "confidence": "high", "dissent": [], "source_url": "x", "license": "x",
        "claims": [{"claim": "fake", "citation": "none", "grade": "primary"}],
    })
    emit(f"  [negative-control] expect FAIL R7 -> got {neg['verdict']} {neg['failed']}")

    # FeederPacket + handoff validation
    packet = emit_feeder_packet(manifest, gate_result=result)
    ok, errs = validate_feeder_packet(packet)
    emit("\n=== FeederPacket -> AI -> STUDIO/SCRIBE ===")
    emit(f"packet_id={packet['packet_id']}  facts={len(packet['research_payload']['facts'])}  "
         f"plates={len(packet['render_assets']['plates'])}")
    emit(f"handoff valid: {ok}" + (f"  errors={errs}" if errs else ""))
    if ok:
        sp = route_ai_to_studio_scribe(packet)
        emit(f"StudioPackage target: {sp['target']}  (packet_id carried: {sp['packet_id']==packet['packet_id']})")

    gate_ok = result["verdict"] == "PASS" and neg["verdict"] == "FAIL" and ok
    emit(f"\nPOC RESULT: {'GREEN' if gate_ok else 'RED'}")
    return 0 if gate_ok else 2


if __name__ == "__main__":
    raise SystemExit(main())
