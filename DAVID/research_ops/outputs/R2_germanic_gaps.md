# R2 Germanic Browser Pass — Ingestion Report
**Date:** 2026-06-23
**Raw source:** `research_ops/outputs/R2_germanic_raw.json`

## Completed

| Language | Profile | Training pack | Registry |
|----------|---------|---------------|----------|
| Gothic | `languages/extinct/gothic/pronunciation/pronunciation_profile.json` | Updated | ipa_coverage: full |
| Old Norse | `languages/extinct/old-norse/pronunciation/pronunciation_profile.json` | Updated | ipa_coverage: full |
| Old English | `languages/extinct/old-english/pronunciation/pronunciation_profile.json` | Stub created | ipa_coverage: full |

## Disputed fields (queued)

- **Gothic:** diphthong monophthongization timing; nasalization extent → `rq-pron-r2-001`
- **Old Norse:** nasal vowel persistence timing; ʀ quality → `rq-pron-r2-002`
- **Old English:** short diphthong realization; palatalization timing → `rq-pron-r2-003`

## STUDIO handoff

Gothic `script_notes` — Wulfila 1:1 grapheme-to-phoneme mapping flagged for captioning system → `rq-studio-r2-001`

## Schema notes

- Sources ingested as plain strings (browser pass format); R1 Latin/Greek used structured source objects — normalize on next pass if needed.
- Old English `dialect_notes` lacks `mercian` field from browser template (only west_saxon + northumbrian provided).