# Pre-Publish QA Gate — DAVID (#167, C4 spine) — v1

**ID:** C4-QAGATE-001 · **Owner:** C4 (pre-publish QA — render · Gate 0 · honesty · brand)
**Date:** 2026-06-19 · **Applies to:** every DAVID longform/host/proof master **before upload**
**Prerequisite:** Gate 0 Legal **GREEN** logged (`STUDIO/Legal/Gate_0_Checklist.md`)
**Sits beside:** `STUDIO/Producers_Office/Pre_Publish_Gate.md` (STUDIO canon) — this gate is the
DAVID-channel, machine-checkable instrument that *applies* that canon to a rendered master.

> **Gate rule:** a master does not pass C4 until **every box in all four dimensions is PASS or
> explicitly WAIVED with a reason**. "Couldn't verify" → mark the row `VERIFY`, never pass
> silently. The verdict is **SHIP** only when zero rows are FAIL and zero rows are VERIFY.

This gate exists because a render can be technically complete yet unshippable for a legal,
honesty, or brand reason — and a legal-clean script can still ship a broken render. The four
dimensions below are independent; **all four must clear**. Each row names the artifact that
proves it, so the verdict is reproducible, not a vibe.

---

## How to run the gate

1. Identify the master: `<prod>/output/*_seamless_v1.mp4` and its sidecars
   (`qa_report.json`, `manifest.json`, `shots/extend_state.json`, `upload_kit/`).
2. Find the **latest-timestamp** Gate report for the slug in
   `STUDIO/Producers_Office/Legal_Gate/GATE_*_<slug>_*.json` — *latest wins; ignore superseded ones.*
3. Walk dimensions 1–4 below; record PASS / FAIL / VERIFY / WAIVED(reason) per row.
4. Emit a verdict file `DAVID/reports/C4_167_VERDICT_<slug>.md` (template at end).

```
SHIP   = all rows PASS (or WAIVED-with-reason)
FIX    = ≥1 FAIL that is fixable in post/packaging (HOLD, return, re-gate the touched dimension)
KILL   = Gate 0 RED / BLOCKED cast / minor depicted / honesty overclaim that can't be labeled away
```

---

## Dimension 1 — RENDER INTEGRITY

*Proves the file is technically whole and within technical spec.* Source of truth: the production's
own `qa_report.json` (must show `pass: true`, empty `issues`) plus a structural check of the outputs.

- [ ] **R1 — Master exists & is non-trivial.** `output/*_seamless_v1.mp4` present, > ~1 MB, not
      zero-byte/truncated. `upload_kit/manifest.json` `source_video` resolves to it.
- [ ] **R2 — All shots assembled.** Every shot in `script.json.shots[]` has a processed chain in
      `shots/` and the xfade chain runs through the last shot; `extend_state.json.segments ==
      len(shots)`; provenance card rendered and joined (`provenance_matched_*`).
- [ ] **R3 — Duration on target.** Master duration ≈ `target_seconds` (± ~10%, incl. provenance
      card). Cross-check `manifest.json.video_duration_s` and `qa_report` duration note.
- [ ] **R4 — Picture spec.** Resolution / aspect / fps match `config` (e.g. 720p, 16:9). No
      letterbox/scaling surprise vs deliverable spec.
- [ ] **R5 — Audio QC.** Audio present; loudness at pipeline target **−16 LUFS** integrated, shot
      spread ≤ **1.5 LU**; no clipping/dropouts; A/V sync pinned per shot.
- [ ] **R6 — Color/continuity QC.** Magenta score ≤ **0.42** (lamp 3200K warm-gold lock), no
      uncorrected cast/grade drift; lamp warm-ratio Δ stable across segments.
- [ ] **R7 — `qa_report.json` is GREEN.** `pass: true` **and** `issues: []`. A render with any
      blocking issue is FAIL even if a file exists.

> Note: `ffprobe` is not installed in this environment — R3–R6 are verified from the pipeline's
> emitted `qa_report.json` (which derives them at render time). If you have `ffprobe`, re-confirm
> R3/R4 directly. Never infer "duration OK" from file size alone.

## Dimension 2 — GATE 0 (LEGAL) FRESHNESS

*Proves the legal clearance is current and unambiguously GREEN.* Source of truth: the **newest**
`GATE_*_<slug>_*.json` and the script's embedded `intake.gate_0`.

- [ ] **G1 — Latest verdict is GREEN.** Sort all `GATE_*_<slug>_*.json` by timestamp; the newest is
      `GREEN`. *A project frequently carries stale `COUNSEL`/`YELLOW` runs — they do not count.*
- [ ] **G2 — Latest gate is not older than the master.** Gate timestamp reflects the shipped brief
      (re-gate if the script changed after the last GREEN).
- [ ] **G3 — All six rows PASS.** `checklist_domains.row_1…row_6` all `PASS` (synthetic ownership,
      music/sync, no-real-likeness, target-channel, age doc, AI-disclosure).
- [ ] **G4 — No open hard stops / counsel flags.** `hard_stops: []`, `counsel_flags: []`.
- [ ] **G5 — Sub-gates clear.** `historical_figure_gate` and `science_gate` are `applies:false`/`N/A`
      or `status` non-blocking (no `post_1900_blocked`, no science `overclaims`).
- [ ] **G6 — Script intake agrees.** `script.json.intake.gate_0.verdict == GREEN`,
      `blocked == false`, `human_signoff == true`; `channels` match the actual publish target.

> Pitfall (seen on `david_latin_corpus_v1`): an early `COUNSEL` flagged "living person likeness"
> off a brief that omitted `synthetic:true`; a later run with the brief declaring
> `synthetic: true, real_person_likeness: false` cleared to GREEN. **Always cite the newest report.**

## Dimension 3 — HONESTY RAILS

*Proves no claim is presented with more certainty than the evidence supports.* Pick the rail(s) that
apply to the content type; **at least one must apply** to any explainer/pronunciation/figure piece.

**3a — Science productions** (format contains `science`, `@2` swap slot, or a visualization shot):
- [ ] **H1 — Honesty rail PASS.** `python Science/scripts/science_honesty_rail.py <script.json>`
      returns PASS: illustrative-not-simulation label **and** a cited source **and** no simulation
      overclaim ("accurate simulation", "real data", "actual measurement", …).
- [ ] **H2 — Citations REAL/LIVE/ACCURATE.** Defer to the C2 fact-check checklist
      (`Science/reports/C2_159_Science_Fact_Check_Checklist.md`) — authors, journal, ID, resolution,
      quantity, direction, units all verified against the primary source.

**3b — Dead-language / pronunciation productions** (DAVID corpus & host formats):
- [ ] **H3 — Attested vs reconstructed is explicit.** Any reconstructed sound/feature is labeled
      **on screen** (`shots[].on_screen` / `on_screen_labels`, e.g. `RECONSTRUCTED PRONUNCIATION`)
      **and/or** stated in narration. A demonstrated reconstruction with no label is FAIL,
      *regardless of* `qa_rules.require_reconstructed_labels`.
- [ ] **H4 — No silent upgrade of certainty.** No "exactly how they sounded"; framing is corpus-first
      ("largely reconstructed from meter", "I label each claim accordingly"). `ATTESTED TEXT` only
      where the manuscript/inscription survives; `NOT ATTESTED` on speculative lines.

**3c — Historical-figure productions** (`historical-figure-documentary`):
- [ ] **H5 — Recency floor.** `historical_figure_gate` clears the death-year recency floor (1926) /
      hard 1900 ceiling; no living/recent-person likeness.

## Dimension 4 — BRAND CONFORMANCE

*Proves the master and its packaging read as DAVID · The Archive / Upon Tyne.* Source of truth:
`DAVID/brand/Upon_Tyne_DAVID_Brand_Kit_v1.md` + `asset_specs.json`.

- [ ] **B1 — Channel bug.** `DAVID · The Archive` appears on the opening shot (`shots[0].on_screen`),
      matching the identity-lock `on_screen_caption`.
- [ ] **B2 — Closing/provenance card copy locks.** `provenance_card` title `DAVID · The Archive`,
      subtitle `Dead languages, actually pronounced.`, footer = locked CTA. Card colors per Brand §5.5
      (`archive-bg #0C0E14`, frame `archive-border`, `archive-title`/`archive-body`).
- [ ] **B3 — Parent credit + AI disclosure present on output.** `Upon Tyne Productions` **and** a
      synthetic-host / AI disclosure appear in **a required surface** — closing-card parent line
      (Brand §5.5: *"Upon Tyne Productions · Synthetic host · AI disclosure in description"*) **and/or**
      `upload_kit/seo/description.txt`. This is the Pre-Publish row-3 obligation; description satisfies
      it, burned-in card line is the stronger form (advisory if only in description).
- [ ] **B4 — Publish metadata locks.** Title format `<Episode> | DAVID · The Archive`; playlist
      `DAVID · The Archive`; CTA matches the locked line; tags lead with the channel.
- [ ] **B5 — Look locks in prompts.** Every `shots[].video_prompt` carries the identity/set/style
      locks (`@David-001`, `@Set-Archive-001`, `@Style-Documentary-Prestige-001`), amber-3200K key,
      and the "no magenta / no teal" grade lock.

---

## Per-master scorecard (fill one per deliverable)

| Dim | Row | Verdict | Evidence / note |
|-----|-----|:-------:|-----------------|
| 1 Render | R1–R7 | | `qa_report.json`, `manifest.json`, `shots/` |
| 2 Gate 0 | G1–G6 | | newest `GATE_*_<slug>_*.json`, `intake.gate_0` |
| 3 Honesty | H1–H5 (applicable) | | rail output / on-screen labels / fact-check |
| 4 Brand | B1–B5 | | brand kit, `provenance_card`, `upload_kit` |

**Verdict:** SHIP / FIX / KILL — with punch list.

---

## Appendix A — Existing proof review (2026-06-19)

Proofs are **pipeline/format-validation** artifacts (mostly 480p, ~27–51 s), not ship candidates.
They are gated at the appropriate altitude: render-completes + honesty-label presence + Gate 0 —
not full upload-kit/brand polish. Rows I did not machine-verify this pass are marked **VERIFY**.

| Proof | Render | Gate 0 | Honesty | Notes |
|-------|:------:|:------:|:-------:|-------|
| `DAVID/.../david_black_hole_science_proof_v1` | master 480p present | VERIFY | **VERIFY (science)** | science format → must pass `science_honesty_rail.py` + C2 #159 fact-check before any non-proof promotion |
| `DAVID/.../david_elizabeth_tudor_proof_v1` | master 480p present | VERIFY | VERIFY (figure) | run `historical_figure_gate`; Tudor era well past recency floor |
| `DAVID/.../david_latin_pronunciation_proof_v1` | master 480p present | VERIFY | VERIFY (dead-lang) | confirm reconstructed labels present |
| `STUDIO/.../david_julius_caesar_figure_proof_480p_v1` | master + 30 chains | **YELLOW** (human-signed) | VERIFY (figure) | YELLOW must re-gate GREEN before ship |
| `STUDIO/.../gfe_companion_sage_proof_v1` | master + script | **YELLOW** (human-signed) | n/a | YELLOW must re-gate GREEN before ship |
| `STUDIO/.../gfe_companion_violet_proof_480p_v1` | master + 36 chains | VERIFY | n/a | confirm latest gate |
| `DAVID/.../gfe_companion_sage_proof_v1` | renders, **no script.json** | — | — | **anomaly:** duplicate of STUDIO copy, missing script — de-dupe or restore script |
| `DAVID/.../gfe_companion_violet_proof_480p_v1` | **empty stub** | — | — | **anomaly:** no output/shots/script — delete the stub or render it |

**Cross-cutting findings**
1. Two `gfe_companion_*` proof folders are duplicated under `DAVID/productions/` with the canonical
   pair under `STUDIO/Productions/Companion/`; the DAVID copies are an empty stub and a script-less
   render. Recommend consolidating to the STUDIO copies (de-dupe).
2. Two STUDIO proofs sit at Gate 0 **YELLOW** (human-signed for proof use). YELLOW is fine for a
   proof; it is a **HOLD** for any real publish — they must re-gate GREEN first.
3. Science/figure proofs were not honesty-machine-checked this pass — promotion of any proof to a
   shipping cut requires the applicable Dimension-3 rail to be run and PASS.

---

## Appendix B — Latin master verdict (summary)

`david_latin_corpus_v1` master **landed** and was taken through the full gate →
**verdict: SHIP** (all four dimensions PASS). Full sign-off:
`DAVID/reports/C4_167_VERDICT_david_latin_corpus_v1.md`.

---

## Cross-references

| Canon | Path |
|-------|------|
| Gate 0 Legal (prerequisite) | `STUDIO/Legal/Gate_0_Checklist.md` |
| Pre-Publish Gate (STUDIO canon) | `STUDIO/Producers_Office/Pre_Publish_Gate.md` |
| Science honesty rail (machine) | `Science/scripts/science_honesty_rail.py` |
| Science fact-check (C2 #159) | `Science/reports/C2_159_Science_Fact_Check_Checklist.md` |
| Legal gate CLI + sub-gates | `artifacts/legal/legal_gate.py` · `science_gate.py` · `historical_figure_gate.py` |
| Brand kit + machine specs | `DAVID/brand/Upon_Tyne_DAVID_Brand_Kit_v1.md` · `DAVID/brand/asset_specs.json` |

*Upon Tyne Productions / DAVID · The Archive — render-clean, legally gated, honestly labeled, on brand.*
