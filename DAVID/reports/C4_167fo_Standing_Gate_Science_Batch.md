# C4 Standing QA Gate — inbound masters (T4_181 science astro + science)

**Owner:** C4 · **Date:** 2026-06-19 · **Gate def:** `DAVID/reports/C4_167_PrePublish_QA_Gate.md`
**Status:** **HOLD — all three FRAME-FAIL. No re-verdict until DAVID's real re-render + frame proof (#195).**

> **#195 correction applied.** QA now verdicts colour/continuity from the **actual delivered frames**
> (`DAVID/scripts/c4_frame_proof_qa.py`, 1 fps across the whole master), **not** from the
> self-reported `qa_report.json`. The JSON is corroborating-only and has been caught issuing live
> false passes. The renderer's own colour gate only samples one frame per segment midpoint, so
> tail / provenance-card casts slip through — that is the hole #195 names.

## Frame-proof results (this pass — diagnostic, NOT a verdict)

Ran the frame-proof verifier on the current (pre-re-render) masters. **2 of 3 are confirmed
FALSE PASSES** — `qa_report.json` says `pass:true` while the frames fail:

| Master | JSON self-report | Frame verdict | Coherence | Breach (real frames) |
|---|:---:|:---:|:---:|---|
| `science_black_hole_anatomy_v1` | `pass:true` ❌ | **FRAME-FAIL** | **INCOHERENT_FALSE_PASS** | magenta **0.79** @ t=42–47s; grey-drift 0.32 |
| `science_star_lifecycle_v1` | `pass:true` ❌ | **FRAME-FAIL** | **INCOHERENT_FALSE_PASS** | magenta **0.51–0.85** @ t=25–32s & 42–47s; grey-drift 0.29 |
| `science_galaxy_formation_v1` | `pass:false` | **FRAME-FAIL** | COHERENT | yellow-green **0.47–0.54** @ t=0–7s; master ~0.9 MB (truncated) |

Thresholds: magenta ≤ 0.42 · yellow-green ≤ 0.12 · grey-drift ≤ 0.12.
Evidence of record: `<prod>/frame_proof/` stills + `<prod>/frame_proof_qa.json` per master.

The t=42–47s magenta on black_hole + star is the **provenance-card / tail** region — exactly the
frames the midpoint-per-segment probe never measured. Visible cast, JSON-green. Caught now.

## Gate posture
- **Re-verdict only after DAVID delivers a real re-render** whose frame proof reads `FRAME-PASS`
  with `coherence` COHERENT/JSON_STRICTER. No SHIP/FIX verdict file is issued before that.
- Gate 0 (YELLOW, signed) + science honesty rail (PASS) remain green-lit for all three — the open
  blocker is purely render colour/continuity, now measured at frame level.
- On re-render, C4 re-runs `c4_frame_proof_qa.py`, confirms FRAME-PASS, then walks Dim-1 R1–R5 +
  Dim-4 brand and emits `DAVID/reports/C4_167_VERDICT_<slug>.md` citing breach-free frame proof.

## Re-render targets handed to DAVID
- **black_hole:** kill the magenta cast in the tail/provenance-card region (t≈42–47s); re-grade for grey-drift ≤ 0.12.
- **star_lifecycle:** kill magenta across t≈25–32s and the tail t≈42–47s; grey-drift ≤ 0.12.
- **galaxy:** neutralise the yellow-green cast in the opening (t≈0–7s) **and** re-render to full length (current master ~0.9 MB is truncated).

## Scope note
Same frame-proof posture applies to every DAVID longform/host/science master and sibling science
slates (`chem_physics_mini_slate`, `molecular_mini_slate`). Ping C4 on render-clean; I gate on the frames.
