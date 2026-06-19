# State-layer consolidation note

_Task T5-280 · 2026-06-19_

## Summary

- **Sources scanned:** 400 files across 10 roots
- **States merged:** 300 (multi-source: 100)
- **Conflicts:** 706 ({"text_disagreement": 706})
- **Gaps (NOT FOUND):** 0 state slots — not fabricated
- **Canonical corpus:** `Compliance_Research/groundtruth/Compliance/canonical_compliance_pack_v1.json`

## What merged

- **R1** (Food & Hospitality): 50/50 states, 344 facts, 0 multi-source merges
- **R2** (Construction & Trades): 50/50 states, 544 facts, 50 multi-source merges
- **R3** (Health & Personal Care): 50/50 states, 919 facts, 0 multi-source merges
- **R4** (Financial & Professional): 50/50 states, 1343 facts, 0 multi-source merges
- **R5** (Transport / Logistics / Auto): 50/50 states, 195 facts, 0 multi-source merges
- **R6** (Tech / Retail / Specialized): 50/50 states, 792 facts, 50 multi-source merges

## Conflicts (reconciled)

| Lane | State | Block | Type | Assessment |
|------|-------|-------|------|------------|
| R1 | AL | food_establishment_licenses | text_disagreement | Retained all variants as separate graded facts (URL collision, text differs); no synthesis — confirm with primary .gov s |
| R1 | AL | health_permits | text_disagreement | Retained all variants as separate graded facts (URL collision, text differs); no synthesis — confirm with primary .gov s |
| R1 | AR | food_establishment_licenses | text_disagreement | Retained all variants as separate graded facts (URL collision, text differs); no synthesis — confirm with primary .gov s |
| R1 | AR | health_permits | text_disagreement | Retained all variants as separate graded facts (URL collision, text differs); no synthesis — confirm with primary .gov s |
| R1 | AR | liquor_abc | text_disagreement | Retained all variants as separate graded facts (URL collision, text differs); no synthesis — confirm with primary .gov s |
| R1 | CO | food_establishment_licenses | text_disagreement | Retained all variants as separate graded facts (URL collision, text differs); no synthesis — confirm with primary .gov s |
| R1 | CO | health_permits | text_disagreement | Retained all variants as separate graded facts (URL collision, text differs); no synthesis — confirm with primary .gov s |
| R1 | CT | food_establishment_licenses | text_disagreement | Retained all variants as separate graded facts (URL collision, text differs); no synthesis — confirm with primary .gov s |
| R1 | CT | health_permits | text_disagreement | Retained all variants as separate graded facts (URL collision, text differs); no synthesis — confirm with primary .gov s |
| R1 | DE | food_establishment_licenses | text_disagreement | Retained all variants as separate graded facts (URL collision, text differs); no synthesis — confirm with primary .gov s |
| R1 | FL | food_establishment_licenses | text_disagreement | Retained all variants as separate graded facts (URL collision, text differs); no synthesis — confirm with primary .gov s |
| R1 | FL | liquor_abc | text_disagreement | Retained all variants as separate graded facts (URL collision, text differs); no synthesis — confirm with primary .gov s |
| R1 | FL | mobile_unit_commissary | text_disagreement | Retained all variants as separate graded facts (URL collision, text differs); no synthesis — confirm with primary .gov s |
| R1 | GA | food_establishment_licenses | text_disagreement | Retained all variants as separate graded facts (URL collision, text differs); no synthesis — confirm with primary .gov s |
| R1 | GA | liquor_abc | text_disagreement | Retained all variants as separate graded facts (URL collision, text differs); no synthesis — confirm with primary .gov s |
| R1 | GA | mobile_unit_commissary | text_disagreement | Retained all variants as separate graded facts (URL collision, text differs); no synthesis — confirm with primary .gov s |
| R1 | HI | food_establishment_licenses | text_disagreement | Retained all variants as separate graded facts (URL collision, text differs); no synthesis — confirm with primary .gov s |
| R1 | HI | health_permits | text_disagreement | Retained all variants as separate graded facts (URL collision, text differs); no synthesis — confirm with primary .gov s |
| R1 | IA | food_establishment_licenses | text_disagreement | Retained all variants as separate graded facts (URL collision, text differs); no synthesis — confirm with primary .gov s |
| R1 | IA | health_permits | text_disagreement | Retained all variants as separate graded facts (URL collision, text differs); no synthesis — confirm with primary .gov s |
| R1 | IA | liquor_abc | text_disagreement | Retained all variants as separate graded facts (URL collision, text differs); no synthesis — confirm with primary .gov s |
| R1 | ID | food_establishment_licenses | text_disagreement | Retained all variants as separate graded facts (URL collision, text differs); no synthesis — confirm with primary .gov s |
| R1 | ID | health_permits | text_disagreement | Retained all variants as separate graded facts (URL collision, text differs); no synthesis — confirm with primary .gov s |
| R1 | ID | liquor_abc | text_disagreement | Retained all variants as separate graded facts (URL collision, text differs); no synthesis — confirm with primary .gov s |
| R1 | ID | mobile_unit_commissary | text_disagreement | Retained all variants as separate graded facts (URL collision, text differs); no synthesis — confirm with primary .gov s |
| R1 | IL | food_establishment_licenses | text_disagreement | Retained all variants as separate graded facts (URL collision, text differs); no synthesis — confirm with primary .gov s |
| R1 | IL | mobile_unit_commissary | text_disagreement | Retained all variants as separate graded facts (URL collision, text differs); no synthesis — confirm with primary .gov s |
| R1 | IN | food_establishment_licenses | text_disagreement | Retained all variants as separate graded facts (URL collision, text differs); no synthesis — confirm with primary .gov s |
| R1 | IN | health_permits | text_disagreement | Retained all variants as separate graded facts (URL collision, text differs); no synthesis — confirm with primary .gov s |
| R1 | IN | liquor_abc | text_disagreement | Retained all variants as separate graded facts (URL collision, text differs); no synthesis — confirm with primary .gov s |
| R1 | KS | liquor_abc | text_disagreement | Retained all variants as separate graded facts (URL collision, text differs); no synthesis — confirm with primary .gov s |
| R1 | KY | food_establishment_licenses | text_disagreement | Retained all variants as separate graded facts (URL collision, text differs); no synthesis — confirm with primary .gov s |
| R1 | KY | health_permits | text_disagreement | Retained all variants as separate graded facts (URL collision, text differs); no synthesis — confirm with primary .gov s |
| R1 | KY | liquor_abc | text_disagreement | Retained all variants as separate graded facts (URL collision, text differs); no synthesis — confirm with primary .gov s |
| R1 | KY | mobile_unit_commissary | text_disagreement | Retained all variants as separate graded facts (URL collision, text differs); no synthesis — confirm with primary .gov s |
| R1 | LA | food_establishment_licenses | text_disagreement | Retained all variants as separate graded facts (URL collision, text differs); no synthesis — confirm with primary .gov s |
| R1 | LA | health_permits | text_disagreement | Retained all variants as separate graded facts (URL collision, text differs); no synthesis — confirm with primary .gov s |
| R1 | LA | mobile_unit_commissary | text_disagreement | Retained all variants as separate graded facts (URL collision, text differs); no synthesis — confirm with primary .gov s |
| R1 | MA | health_permits | text_disagreement | Retained all variants as separate graded facts (URL collision, text differs); no synthesis — confirm with primary .gov s |
| R1 | MD | food_establishment_licenses | text_disagreement | Retained all variants as separate graded facts (URL collision, text differs); no synthesis — confirm with primary .gov s |

_…and 666 more in `state_consolidation_note_v1.json`_

