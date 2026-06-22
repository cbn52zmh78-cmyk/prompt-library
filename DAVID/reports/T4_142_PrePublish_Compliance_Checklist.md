# DAVID · Dead Language Slate — Pre-Publish Compliance Checklist
**ID:** T4-#142-CHECKLIST-001  
**Date:** 2026-06-19  
**Gate framework:** C4-QAGATE-001 (`DAVID/reports/C4_167_PrePublish_QA_Gate.md`)  
**Slate:** Dead Language Corpus — 12 episodes (launch six + backlog six)  
**Render status:** Latin master rendered; eps 2–12 script-only (render-queue held — no API spend pending Benjamin's launch decision)  
**Gate 0 basis:** `STUDIO/Pipeline/Concepts/gate_0_regate_T4_142.json` (launch six) + `STUDIO/Pipeline/Concepts/gate_0_regate_T4_181.json` (all twelve)

> **Use this checklist at render-time.** Dimension 1 (Render Integrity) rows are PENDING for all un-rendered episodes. Complete this checklist per episode before each YouTube upload. Gate 0 (Dimension 2) and Honesty (Dimension 3) rows are pre-confirmed here; re-verify if the script changes post-render.

---

## Floor-Age & PII Verification — Launch Six (Eps 1–6)

All launch episodes use David-001 (DAVID · The Archive host) as the sole on-screen talent. This table confirms the floor-age and no-PII status for the public-channel context.

| Ep | Slug | Actor | Type | Age Lock | PII Present | Real Likeness | Verdict |
|----|------|-------|------|----------|-------------|---------------|---------|
| 1 | `david_latin_corpus_v1` | David-001 | Synthetic | 45–55 read-age (invented face) | None | No | ✅ CLEAR |
| 2 | `david_ancient_greek_corpus_v1` | David-001 | Synthetic | 45–55 read-age (invented face) | None | No | ✅ CLEAR |
| 3 | `david_old_english_corpus_v1` | David-001 | Synthetic | 45–55 read-age (invented face) | None | No | ✅ CLEAR |
| 4 | `david_old_norse_corpus_v1` | David-001 | Synthetic | 45–55 read-age (invented face) | None | No | ✅ CLEAR |
| 5 | `david_gothic_corpus_v1` | David-001 | Synthetic | 45–55 read-age (invented face) | None | No | ✅ CLEAR |
| 6 | `david_sumerian_corpus_v1` | David-001 | Synthetic | 45–55 read-age (invented face) | None | No | ✅ CLEAR |

**David-001 identity anchor:** `DAVID/productions/host_identity_v1/david_identity_lock.json` — status LOCKED (issue #69, 2026-06-19). Face is fully invented per lock: "no real person likeness, no celebrity resemblance, invented face only." Age-read 45–55. No name, biometric, or personal data in any episode. No third-party casting consent required.

**PII sweep — full slate:** No real person's name, face, voice, or identifying information is incorporated in any episode's script, concept, brief, or prompt. All named figures in episode content are historical (deceased ≥1926) and are referenced by reputation/corpus only — not depicted as speaking characters. David-001 is a synthetic host only.

---

## Per-Episode Compliance Matrix

**Legend:**  
✅ PASS · ⏳ PENDING (requires render) · ⚠️ VERIFY (flag before ship) · ❌ FAIL

### Dimension 2 — Gate 0 (Legal) · All 12 episodes

Pre-confirmed from T4 re-gate batch (2026-06-19). No re-gate required unless script changes.

| # | Slug | G1 Latest GREEN | G2 Gate ≥ Script | G3 6-row checklist | G4 No hard stops | G5 Sub-gates clear | G6 Intake agrees | Verdict |
|---|------|:-:|:-:|:-:|:-:|:-:|:-:|:-:|
| 1 | `david_latin_corpus_v1` | ✅ | ✅ | ✅ 6/6 | ✅ | ✅ N/A | ✅ | **GREEN** |
| 2 | `david_ancient_greek_corpus_v1` | ✅ | ✅ | ✅ 6/6 | ✅ | ✅ N/A | ✅ | **GREEN** |
| 3 | `david_old_english_corpus_v1` | ✅ | ✅ | ✅ 6/6 | ✅ | ✅ N/A | ✅ | **GREEN** |
| 4 | `david_old_norse_corpus_v1` | ✅ | ✅ | ✅ 6/6 | ✅ | ✅ N/A | ✅ | **GREEN** |
| 5 | `david_gothic_corpus_v1` | ✅ | ✅ | ✅ 6/6 | ✅ | ✅ N/A | ✅ | **GREEN** |
| 6 | `david_sumerian_corpus_v1` | ✅ | ✅ | ✅ 6/6 | ✅ | ✅ N/A | ✅ | **GREEN** |
| 7 | `david_sanskrit_corpus_v1` | ✅ | ✅ | ✅ 6/6 | ✅ | ✅ N/A | ✅ | **GREEN** |
| 8 | `david_biblical_hebrew_corpus_v1` | ✅ | ✅ | ✅ 6/6 | ✅ | ✅ N/A | ✅ | **GREEN** |
| 9 | `david_akkadian_corpus_v1` | ✅ | ✅ | ✅ 6/6 | ✅ | ✅ N/A | ✅ | **GREEN** |
| 10 | `david_middle_egyptian_corpus_v1` | ✅ | ✅ | ✅ 6/6 | ✅ | ✅ N/A | ✅ | **GREEN** |
| 11 | `david_classical_nahuatl_corpus_v1` | ✅ | ✅ | ✅ 6/6 | ✅ | ✅ N/A | ✅ | **GREEN** |
| 12 | `david_old_church_slavonic_corpus_v1` | ✅ | ✅ | ✅ 6/6 | ✅ | ✅ N/A | ✅ | **GREEN** |

**Shared gate parameters (all 12):**  
- `human_signoff: true` · `rating: "PG"` · `channels: ["social","streaming"]` · `publish_platform: "youtube"` · `ai_disclosure: "provenance card + YouTube upload metadata"` · `music_bed_id: "BED-DOC-001"`

---

### Dimension 3 — Honesty Rails · All 12 episodes (3b: Dead-language / pronunciation)

Beat 07 on-screen labels confirmed from concept.json. Beat 06 honesty statements confirmed from concept.json.

| # | Slug | H3 — Attested/Reconstructed label (beat 07 on_screen) | H4 — No certainty upgrade (beat 06) | Verdict |
|---|------|------|------|:-:|
| 1 | `david_latin_corpus_v1` | ✅ `RECONSTRUCTED PRONUNCIATION · Classical Latin` | ✅ Explicitly notes "sound of the educated Roman" reconstructed via Cicero/Quintilian | **PASS** |
| 2 | `david_ancient_greek_corpus_v1` | ✅ `RECONSTRUCTED PRONUNCIATION · pitch accent · ἄνδρα` | ✅ "I label each claim accordingly" corpus-first framing | **PASS** |
| 3 | `david_old_english_corpus_v1` | ✅ `RECONSTRUCTED PRONUNCIATION · West Saxon · Hwæt` | ✅ Corpus-first; attested manuscript vs reconstructed prosody | **PASS** |
| 4 | `david_old_norse_corpus_v1` | ✅ `ATTESTED · Jelling runes · RECONSTRUCTED · skaldic meter` | ✅ Dual label distinguishes runic attestation from metric reconstruction | **PASS** |
| 5 | `david_gothic_corpus_v1` | ✅ `RECONSTRUCTED PRONUNCIATION · Wulfila's Gothic` | ✅ Codex Argenteus attested; pronunciation via comparative method | **PASS** |
| 6 | `david_sumerian_corpus_v1` | ✅ `RECONSTRUCTED PRONUNCIATION · syllabic corpus` | ✅ Cuneiform syllabary attested; pronunciation reconstructed | **PASS** |
| 7 | `david_sanskrit_corpus_v1` | ✅ `ATTESTED TEXT · Classical Sanskrit · Rigveda 1.1.1` | ✅ beat 06: `ATTESTED text · RECONSTRUCTED accent` | **PASS** |
| 8 | `david_biblical_hebrew_corpus_v1` | ✅ `ATTESTED TEXT · Biblical Hebrew · Masoretic vocalization` | ✅ beat 06: `ATTESTED text · RECONSTRUCTED vowels` | **PASS** |
| 9 | `david_akkadian_corpus_v1` | ✅ `ATTESTED TEXT · Akkadian · Gilgamesh I.1` | ✅ beat 06: `ATTESTED text · RECONSTRUCTED prosody` | **PASS** |
| 10 | `david_middle_egyptian_corpus_v1` | ✅ `RECONSTRUCTED PRONUNCIATION · Middle Egyptian · offering formula` | ✅ beat 06: `ATTESTED consonants · RECONSTRUCTED vowels` | **PASS** |
| 11 | `david_classical_nahuatl_corpus_v1` | ✅ `ATTESTED TEXT · Classical Nahuatl · in xochitl in cuicatl` | ✅ beat 06: `ATTESTED orthography · RECONSTRUCTED detail` | **PASS** |
| 12 | `david_old_church_slavonic_corpus_v1` | ✅ `ATTESTED TEXT · Old Church Slavonic · Otĭče našĭ` | ✅ beat 06: `ATTESTED text · RECONSTRUCTED jers` | **PASS** |

> **Note:** Eps 13–18 (Hittite, Classical Japanese, Etruscan, PIE, Linear A, Coptic) are concept-only — not yet intake-run. Their honesty labels are established in concept.json but must be re-verified through intake before a checklist entry is issued.

---

### Dimension 4 — Brand Conformance · All 12 episodes

B1 (channel bug) and B2 (provenance card copy) confirmed from concept.json beat_01 on_screen. B3–B5 require render-time verification.

| # | Slug | B1 — `DAVID · The Archive` in beat 01 | B2 — Closing card copy locked | B3–B5 — Upload kit / metadata | Verdict |
|---|------|:-:|:-:|:-:|:-:|
| 1 | `david_latin_corpus_v1` | ✅ | ✅ (C4 verdict confirmed) | ⏳ Pre-confirmed for Latin only; ⏳ PENDING render for 2–12 | **B1–B2 PASS; B3–B5 PENDING** |
| 2–12 | (all remaining) | ✅ (all beat 01 on_screen = `DAVID · The Archive`) | ⏳ Verify at render | ⏳ PENDING render | **B1 PASS; B2–B5 PENDING** |

**Shared brand parameters (all 12):**
- `brand.title: "DAVID · The Archive"` · `brand.subtitle: "Dead languages, actually pronounced."` · `brand.cta: "Bring the dead tongues back — one attestation at a time. DAVID."`
- `actor_id: David-001` · `@Set-Archive-001` · `@Style-Documentary-Prestige-001` · `david_identity_lock.json` status LOCKED

---

### Dimension 1 — Render Integrity

| # | Slug | R1 Master | R2 Shots assembled | R3 Duration | R4 Spec | R5 Audio | R6 Color/continuity | R7 qa_report | R8 Frame proof | Pre-Render Status |
|---|------|:-:|:-:|:-:|:-:|:-:|:-:|:-:|:-:|:-:|
| 1 | `david_latin_corpus_v1` | ✅ mp4 present | ⚠️ VERIFY | ⚠️ VERIFY | ⚠️ VERIFY | ⚠️ VERIFY | ⚠️ VERIFY | ⚠️ VERIFY | ⚠️ Run c4_frame_proof_qa.py | **PARTIAL — VERIFY at ship** |
| 2–12 | (all remaining) | ⏳ Not rendered | ⏳ | ⏳ | ⏳ | ⏳ | ⏳ | ⏳ | ⏳ | **PENDING — held, no API spend** |

> Latin master path: `DAVID/productions/david_latin_corpus_v1_longform_v1/output/david_david_latin_corpus_v1_seamless_v1.mp4`  
> Latin pre-publish verdict: `DAVID/reports/C4_167_VERDICT_david_latin_corpus_v1.md` — SHIP (confirmed by C4 #167)

---

## Per-Episode Ship Checklist (Run at Render Time)

Copy one block per episode. Fill in after render completes.

```
EPISODE SHIP CHECKLIST
Slug: ___________________________
Render date: ___________________
Checker: Hub (Claude) · final sign-off: Benjamin Cartwright

[ ] D1-R1  Master exists, non-zero, upload_kit/manifest.json resolves to it
[ ] D1-R2  All shots assembled; extend_state.json.segments == len(shots)
[ ] D1-R3  Duration ≈ target_seconds ± 10%
[ ] D1-R4  Resolution/aspect/fps match config
[ ] D1-R5  Audio: −16 LUFS integrated; spread ≤1.5 LU; no clipping; A/V sync pinned
[ ] D1-R6  Color: magenta score ≤0.42; no uncorrected cast drift
[ ] D1-R7  qa_report.json: pass=true AND issues=[]
[ ] D1-R8  c4_frame_proof_qa.py → frame_verdict=FRAME-PASS AND coherence ∈ {COHERENT, JSON_STRICTER}

[ ] D2-G1  Latest GATE_*_{slug}_*.json verdict = GREEN (sort by timestamp; newest wins)
[ ] D2-G2  Gate timestamp ≥ script mtime (no script change after last GREEN)
[ ] D2-G3  All 6 checklist rows PASS in gate JSON
[ ] D2-G4  hard_stops=[] AND counsel_flags=[]
[ ] D2-G5  historical_figure_gate and science_gate N/A or non-blocking
[ ] D2-G6  script.json.intake.gate_0.verdict=GREEN AND human_signoff=true

[ ] D3-H3  Beat 07 on_screen label: ATTESTED or RECONSTRUCTED explicitly stated
[ ] D3-H4  No "exactly how they sounded"; all claims corpus-first

[ ] D4-B1  Beat 01 on_screen = "DAVID · The Archive"
[ ] D4-B2  Provenance card: title=DAVID · The Archive, subtitle=Dead languages, actually pronounced.
[ ] D4-B3  Upload description includes AI disclosure + Upon Tyne Productions credit
[ ] D4-B4  Title format: <Episode title> | DAVID · The Archive; playlist=DAVID · The Archive
[ ] D4-B5  Every shot prompt carries @David-001, @Set-Archive-001, @Style-Documentary-Prestige-001

VERDICT:  SHIP / FIX / KILL
Punch list: ____________________
```

---

## T4 #142 Issue Summary

| Deliverable | Status |
|-------------|--------|
| Gate 0 verified GREEN for DAVID YouTube channel (launch 6) | ✅ DONE — T4_142 gate report, 6/6 GREEN |
| Gate 0 verified GREEN for dead-language corpus slate (all 12) | ✅ DONE — T4_181 gate report, 12/12 GREEN |
| 3 lane samples re-gated on real channels | ✅ DONE — `gate_0_regate_T4_142_lane_samples.json`; movies=GREEN, flowdesk=GREEN, companion=YELLOW-HOLD |
| Per-episode pre-publish compliance checklist | ✅ DONE — this document |
| Floor-age verification (launch six) | ✅ DONE — David-001 synthetic, 21+, no PII, no real likeness |
| PII/real-likeness sweep (full 12-ep slate) | ✅ DONE — David-001 only; no PII; no real-person likeness in any episode |
| Companion lane YELLOW → pre-publish resolution path documented | ✅ DONE — 3 blockers listed in lane_samples re-gate JSON |
| Non-GREEN items from T4_181 requiring attention | ⚠️ ON-FILE — 1 COUNSEL (Richard Lionheart, requires Benjamin), 5 YELLOW (3 astro + 2 molecular, "illustrative-not-simulation" disclosure needed) |
| Eps 13–18 gate (concept-only, T3 #141) | ⏳ PENDING — requires `production_intake.py` + human signoff before gate report can be issued |

---

*Upon Tyne Productions / DAVID · The Archive · T4 #142 · Hub compilation 2026-06-19*
