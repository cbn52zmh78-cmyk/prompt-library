# DAVID · Dead Language Corpus — Script-Only QA Validation Report
**ID:** DAVID #137  
**Date:** 2026-06-20  
**Validator:** Hub (Claude / NEXUS)  
**Scope:** All 12 dead-language corpus episodes — script-only pass (NO API render spend)  
**Gate framework:** C4-QAGATE-001 · Dimension 1 (Render) = PENDING; Dimensions 2–4 pre-confirmed  
**QA type:** Script-Only — validates structure, timing, gate, honesty rails, identity locks prior to any render

> **Reminder:** This is a script-only QA pass. Dimension 1 (Render Integrity, R1–R8) cannot be assessed until a render exists. All Dimension 1 rows are PENDING. This report clears Dimensions 2–4 for all 12 episodes and documents pre-render action items before the batch fires.

---

## Latin QA — Ep 1 (Reference / SHIP-cleared)

**Slug:** `david_latin_corpus_v1`  
**Status:** SHIP-cleared (C4 #167 verdict); master rendered at 720p. This episode is the script-only QA REFERENCE — used to confirm all other eps match its structure.

| Check | Result |
|-------|--------|
| Shot count: 8 | ✅ PASS |
| Duration pattern: 8+8+8+7+8+8+9+8 = 64s + 6s prov card = 70s (target 69s) | ✅ PASS (within ±10%) |
| Gate 0: GREEN, human_signoff=true, all 6 rows PASS | ✅ PASS |
| Music bed: BED-DOC-001 (owned, manifest-cleared) | ✅ PASS |
| Beat 01 on_screen: "DAVID · The Archive" | ✅ PASS |
| Beat 07 on_screen: "RECONSTRUCTED PRONUNCIATION · Classical Latin" | ✅ PASS |
| Beat 06 honesty: attested vs reconstructed explicitly named, no certainty upgrade | ✅ PASS |
| @David-001 continuity lock: all 8 shots | ✅ PASS |
| @Set-Archive-001 continuity lock: all 8 shots | ✅ PASS |
| @Style-Documentary-Prestige-001: all 8 shots | ✅ PASS |
| Provenance card: enabled=true | ✅ PASS |
| Music bed intake update needed before render | ✅ None — BED-DOC-001 is the T5 assignment |

**Latin script-only verdict: SCRIPT-QA PASS** (render already complete; D1 confirmed via C4 #167)

---

## Backlog Six QA — Eps 7–12 (Script-Only, PENDING render)

All 6 scripts tested via automated check. Results below.

### Ep 7 — Sanskrit: The Language Memory Kept Alive
**Slug:** `david_sanskrit_corpus_v1`

| Check | Result |
|-------|--------|
| Shot count: 8 | ✅ PASS |
| Durations: 8+8+8+7+8+8+9+8 = 70s with card (target 69s) | ✅ PASS |
| Gate 0: GREEN, human_signoff=true, all rows PASS | ✅ PASS |
| Beat 01 on_screen: "DAVID · The Archive" | ✅ PASS |
| Beat 07 on_screen: "ATTESTED TEXT · Classical Sanskrit · Rigveda 1.1.1" | ✅ PASS |
| Beat 06 honesty: "consonants and recitation remarkably stable — regional accents differ" | ✅ PASS |
| @David-001 lock: all 8 | ✅ PASS |
| @Set-Archive-001 lock: all 8 | ✅ PASS |
| Provenance card: enabled | ✅ PASS |
| ⚠ Music bed: script has BED-DOC-001; T5 assignment = BED-ANT-001 (fallback for BED-VED-001 SPEC) | ⚠ UPDATE before render |

**Ep 7 script-only verdict: SCRIPT-QA PASS** · Pre-render action: update `intake.gate_0.music_bed_id` → BED-ANT-001; re-run gate row-2

---

### Ep 8 — Biblical Hebrew: The Language That Came Back
**Slug:** `david_biblical_hebrew_corpus_v1`

| Check | Result |
|-------|--------|
| Shot count: 8 | ✅ PASS |
| Durations: 70s with card (target 69s) | ✅ PASS |
| Gate 0: GREEN, human_signoff=true, all rows PASS | ✅ PASS |
| Beat 01 on_screen: "DAVID · The Archive" | ✅ PASS |
| Beat 07 on_screen: "ATTESTED TEXT · Biblical Hebrew · Masoretic vocalization" | ✅ PASS |
| Beat 06 honesty: "consonants richly attested; Masoretic vowels record one revered reading tradition" | ✅ PASS |
| @David-001 lock: all 8 | ✅ PASS |
| @Set-Archive-001 lock: all 8 | ✅ PASS |
| Provenance card: enabled | ✅ PASS |
| ⚠ Music bed: script has BED-DOC-001; T5 assignment = BED-ANT-001 | ⚠ UPDATE before render |

**Ep 8 script-only verdict: SCRIPT-QA PASS** · Pre-render action: update `intake.gate_0.music_bed_id` → BED-ANT-001; re-run gate row-2

---

### Ep 9 — Akkadian: The Voice Inside the Clay
**Slug:** `david_akkadian_corpus_v1`

| Check | Result |
|-------|--------|
| Shot count: 8 | ✅ PASS |
| Durations: 70s with card (target 69s) | ✅ PASS |
| Gate 0: GREEN, human_signoff=true, all rows PASS | ✅ PASS |
| Beat 01 on_screen: "DAVID · The Archive" | ✅ PASS |
| Beat 07 on_screen: "ATTESTED TEXT · Akkadian · Gilgamesh I.1" | ✅ PASS |
| Beat 06 honesty: "syllabic spelling fixes much of pronunciation — but vowel length..." | ✅ PASS |
| @David-001 lock: all 8 | ✅ PASS |
| @Set-Archive-001 lock: all 8 | ✅ PASS |
| Provenance card: enabled | ✅ PASS |
| ⚠ Music bed: script has BED-DOC-001; T5 assignment = BED-ANT-002 (fallback for BED-NEAR-001 SPEC) | ⚠ UPDATE before render |

**Ep 9 script-only verdict: SCRIPT-QA PASS** · Pre-render action: update `intake.gate_0.music_bed_id` → BED-ANT-002; re-run gate row-2

---

### Ep 10 — Middle Egyptian: The Sound Behind the Hieroglyphs
**Slug:** `david_middle_egyptian_corpus_v1`

| Check | Result |
|-------|--------|
| Shot count: 8 | ✅ PASS |
| Durations: 70s with card (target 69s) | ✅ PASS |
| Gate 0: GREEN, human_signoff=true, all rows PASS | ✅ PASS |
| Beat 01 on_screen: "DAVID · The Archive" | ✅ PASS |
| Beat 07 on_screen: "RECONSTRUCTED PRONUNCIATION · Middle Egyptian · offering formula" | ✅ PASS |
| Beat 06 honesty: "the honest hard case: consonants well attested, but Middle Egyptian didn't write vowels" | ✅ PASS — this is one of the strongest honesty statements in the corpus |
| @David-001 lock: all 8 | ✅ PASS |
| @Set-Archive-001 lock: all 8 | ✅ PASS |
| Provenance card: enabled | ✅ PASS |
| ⚠ Music bed: script has BED-DOC-001; T5 assignment = BED-ANT-002 | ⚠ UPDATE before render |

**Ep 10 script-only verdict: SCRIPT-QA PASS** · Pre-render action: update `intake.gate_0.music_bed_id` → BED-ANT-002; re-run gate row-2

---

### Ep 11 — Classical Nahuatl: The Tongue the Conquest Wrote Down
**Slug:** `david_classical_nahuatl_corpus_v1`

| Check | Result |
|-------|--------|
| Shot count: 8 | ✅ PASS |
| Durations: 70s with card (target 69s) | ✅ PASS |
| Gate 0: GREEN, human_signoff=true, all rows PASS | ✅ PASS |
| Beat 01 on_screen: "DAVID · The Archive" | ✅ PASS |
| Beat 07 on_screen: "ATTESTED TEXT · Classical Nahuatl · in xochitl in cuicatl" | ✅ PASS |
| Beat 06 honesty: "written alphabetically by people who spoke it — much of pronunciation recoverable" | ✅ PASS |
| @David-001 lock: all 8 | ✅ PASS |
| @Set-Archive-001 lock: all 8 | ✅ PASS |
| Provenance card: enabled | ✅ PASS |
| Music bed: BED-DOC-001 — matches T5 assignment (no update needed) | ✅ PASS |

**Ep 11 script-only verdict: SCRIPT-QA PASS** · No pre-render music update needed

---

### Ep 12 — Old Church Slavonic: The Bible That Built an Alphabet
**Slug:** `david_old_church_slavonic_corpus_v1`

| Check | Result |
|-------|--------|
| Shot count: 8 | ✅ PASS |
| Durations: 70s with card (target 69s) | ✅ PASS |
| Gate 0: GREEN, human_signoff=true, all rows PASS | ✅ PASS |
| Beat 01 on_screen: "DAVID · The Archive" | ✅ PASS |
| Beat 07 on_screen: "ATTESTED TEXT · Old Church Slavonic · Otĭče našĭ" | ✅ PASS |
| Beat 06 honesty: "alphabet tailored to sounds, much is attested — but nasal vowels..." | ✅ PASS |
| @David-001 lock: all 8 | ✅ PASS |
| @Set-Archive-001 lock: all 8 | ✅ PASS |
| Provenance card: enabled | ✅ PASS |
| ⚠ Music bed: script has BED-DOC-001; T5 assignment = BED-MED-001 | ⚠ UPDATE before render |

**Ep 12 script-only verdict: SCRIPT-QA PASS** · Pre-render action: update `intake.gate_0.music_bed_id` → BED-MED-001; re-run gate row-2

---

## Summary — Script-Only QA

| Ep | Slug | Script-QA | Gate 0 | Honesty | Identity Locks | Music Update Needed |
|----|------|:---------:|:------:|:-------:|:--------------:|:-------------------:|
| 1 | david_latin_corpus_v1 | ✅ PASS | GREEN | PASS | PASS | None |
| 2 | david_ancient_greek_corpus_v1 | (in B183, not this report) | GREEN | — | — | — |
| 3 | david_old_english_corpus_v1 | (in B183) | GREEN | — | — | — |
| 4 | david_old_norse_corpus_v1 | (in B183) | GREEN | — | — | — |
| 5 | david_gothic_corpus_v1 | (in B183) | GREEN | — | — | — |
| 6 | david_sumerian_corpus_v1 | (in B183) | GREEN | — | — | — |
| 7 | david_sanskrit_corpus_v1 | ✅ PASS | GREEN | PASS | PASS | → BED-ANT-001 |
| 8 | david_biblical_hebrew_corpus_v1 | ✅ PASS | GREEN | PASS | PASS | → BED-ANT-001 |
| 9 | david_akkadian_corpus_v1 | ✅ PASS | GREEN | PASS | PASS | → BED-ANT-002 |
| 10 | david_middle_egyptian_corpus_v1 | ✅ PASS | GREEN | PASS | PASS | → BED-ANT-002 |
| 11 | david_classical_nahuatl_corpus_v1 | ✅ PASS | GREEN | PASS | PASS | None |
| 12 | david_old_church_slavonic_corpus_v1 | ✅ PASS | GREEN | PASS | PASS | → BED-MED-001 |

**All 7 eps validated (Ep 1 + Eps 7–12): SCRIPT-QA PASS across all checks.**

---

## Pre-Render Action Items (before B137 fires)

These are NOT blockers for script-only QA — they are actions required before any render call:

1. **Music bed intake updates** (5 eps): update `intake.gate_0.music_bed_id` in each script.json to reflect T5 #143 assignments; re-run `legal_gate.py` to confirm row-2 re-passes. Commands (per ep):
   ```python
   # Update script.json gate_0.music_bed_id and re-run legal_gate
   # Ep 7 Sanskrit: BED-ANT-001
   # Ep 8 Hebrew: BED-ANT-001
   # Ep 9 Akkadian: BED-ANT-002
   # Ep 10 Egyptian: BED-ANT-002
   # Ep 12 OCS: BED-MED-001
   ```
   Ep 11 Nahuatl: BED-DOC-001 already correct — no update needed.

2. **Benjamin's render greenlight** required before `fire_batch_manifest.py --go` on B137. No spend without explicit approval.

3. **Video pipeline fix status**: Per canon (2026-06-19), video creation is parked pending color/seam fix (#218). B137 ARMED status reflects script-readiness only. Render cannot proceed until video pipeline fix is verified + Benjamin's go.

---

## Render Queue — Next Steps

- B183 manifest: `DAVID/batches/B183_benjamin_go/manifest.json` — ARMED, awaiting pipeline fix + Benjamin's go (eps 2–6 + Royal Tongues)
- B137 manifest: `DAVID/batches/B137_backlog_six/manifest.json` — ARMED, awaiting pipeline fix + Benjamin's go (eps 7–12)
- Render sequence: B183 fires first (publish-priority order); B137 fires after B183 completes or as a parallel batch once the pipeline is verified

---

*Upon Tyne Productions / DAVID · The Archive · DAVID #137 · Script-Only QA · Hub 2026-06-20*
