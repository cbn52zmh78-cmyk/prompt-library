# C4 Standing QA Gate — inbound masters (T4_181 science astro + science)

**Owner:** C4 · **Date:** 2026-06-19 · **Gate def:** `DAVID/reports/C4_167_PrePublish_QA_Gate.md`
**Status:** **STANDING — queue triaged, ready to gate on first clean render.**

> Discipline note: gate reads the **on-disk** `<prod>/qa_report.json` (latest-wins), **not** the batch
> `manifest.json` snapshot. The 06:19 manifest snapshot is already stale — it lists black_hole + star
> as `qa_pass=True`, but the current on-disk QA for **all three** is `pass:false`. Cite the render's own
> live qa_report, same as Gate 0's "newest report wins".

## Inbound queue — T4_181_science_astro (phase: draft_480p)

All three: **Gate 0 = YELLOW (human-signed)** ✓ · **Science honesty rail = PASS** ✓ (illustrative-label
+ cited source + no simulation overclaim). Each carries one **open Dimension-1 (Render Integrity)** blocker:

| Master | Gate 0 | Honesty | Render-integrity blocker (live qa) | C4 call |
|---|:---:|:---:|---|:---:|
| `science_black_hole_anatomy_v1` (5.71 MB) | YELLOW✓ | PASS✓ | **R6** yellow-green cast > 0.42 on 4 chains (0.46/0.53/0.49/0.42) | **FIX** |
| `science_galaxy_formation_v1` (0.91 MB) | YELLOW✓ | PASS✓ | **R5** loudness spread 7.19 LU > 1.5; master ~0.9 MB (likely truncated) | **FIX** |
| `science_star_lifecycle_v1` (6.81 MB) | YELLOW✓ | PASS✓ | **R6** hue drift across segments (grey_balance 0.11→0.32) | **FIX** |

**Verdict at this instant: none SHIP-ready.** Each is a single render-pass FIX (color lock / audio
loudnorm / segment grade) away from a full C4 walk. Gate 0 + honesty are already green-lit, so once
`qa_report.json.pass:true && issues:[]` lands, the C4 run is fast: re-walk Dim-1 only, then Dim-4 brand
(these are 480p drafts → brand polish gated at proof altitude per #167 Appendix A).

## What "clean" requires before I issue SHIP/FIX verdict files
For each: live `qa_report.json` → `pass:true`, `issues:[]` (clears R5/R6/R7); master present & non-trivial
(galaxy's ~0.9 MB must be re-rendered to full length); then I emit
`DAVID/reports/C4_167_VERDICT_<slug>.md`. Science masters also defer citation accuracy to C2 #159
fact-check (H2) before any promotion above proof.

## Scope note
Same posture extends to sibling science slates when they render (`chem_physics_mini_slate`,
`molecular_mini_slate`) and to any DAVID longform/host master — all routed through the #167 C4 gate.
Ping C4 on render-clean; I gate on arrival.
