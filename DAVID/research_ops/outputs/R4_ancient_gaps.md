# R4 Ancient Browser Pass — Ingestion Report
**Date:** 2026-06-23
**Raw source:** `research_ops/outputs/R4_ancient_raw.json`

## Completed

| Language | Profile | Disputed phonemes | Training pack | Registry |
|----------|---------|-------------------|---------------|----------|
| Biblical Hebrew | `languages/dead/biblical-hebrew/pronunciation/pronunciation_profile.json` | — | Updated | ipa_coverage: full, high confidence |
| Classical Sanskrit | `languages/dead/classical-sanskrit/pronunciation/pronunciation_profile.json` | — | Updated | ipa_coverage: full, high confidence |
| Akkadian | `languages/dead/akkadian/pronunciation/pronunciation_profile.json` | Created | Updated | ipa_coverage: partial, medium confidence |
| Sumerian | `languages/dead/sumerian/pronunciation/pronunciation_profile.json` | Created | Updated | ipa_coverage: partial, low confidence |

## Disputed fields (queued)

- **Sumerian:** ĝ realization, r quality → `rq-pron-r4-001`
- **Sumerian:** vowel length/harmony, stress → `rq-pron-r4-002`
- **Akkadian:** emphatic series articulation → `rq-pron-r4-003`
- **Biblical Hebrew:** Tiberian vs Samaritan gutturals → `rq-pron-r4-004`

## STUDIO / series handoff

- Hebrew `cantillation_notes` → documentary narration pacing → `rq-studio-r4-001`
- Sanskrit `shiksha_notes` + `aspirate_pairs` → tutoring series planning → `rq-series-r4-001`

## Schema notes

- Sources ingested as plain strings (browser pass format); consistent with R2.
- Sumerian confidence deliberately left low — not inflated per R4 protocol.
- New registry phonology status `reconstructed_low_confidence` introduced for Sumerian.