# Compliance conflict triage

_Task T5-280-B · 2026-06-19_

## Counts

- **Input conflicts:** 718
- **TRIVIAL (auto-collapse):** 146
- **SUBSTANTIVE:** 572
- **Facts collapsed:** 542

### By reason

| Class | Reason | Count |
|-------|--------|------:|
| TRIVIAL | wording_substring | 74 |
| TRIVIAL | wording_high_similarity | 68 |
| TRIVIAL | wording_portal_pointer | 4 |
| SUBSTANTIVE | url_multifact_distinct | 393 |
| SUBSTANTIVE | number_delta | 86 |
| SUBSTANTIVE | low_similarity_borderline | 76 |
| SUBSTANTIVE | requirement_polarity | 12 |
| SUBSTANTIVE | number_or_requirement_delta | 5 |

### By lane

| Lane | Trivial | Substantive |
|------|--------:|------------:|
| R1 | 18 | 93 |
| R2 | 53 | 57 |
| R3 | 23 | 103 |
| R4 | 34 | 198 |
| R5 | 0 | 28 |
| R6 | 18 | 93 |

## Substantive sample (assessment required)

| Lane | State | Block | Reason | Assessment |
|------|-------|-------|--------|------------|
| R1 | AL | food_establishment_licenses | url_multifact_distinct | Distinct facts share the same portal URL — not a POC-vs-lane wording conflict. Retain all variants;  |
| R1 | AL | health_permits | url_multifact_distinct | Distinct facts share the same portal URL — not a POC-vs-lane wording conflict. Retain all variants;  |
| R1 | AR | food_establishment_licenses | url_multifact_distinct | Distinct facts share the same portal URL — not a POC-vs-lane wording conflict. Retain all variants;  |
| R1 | AR | health_permits | url_multifact_distinct | Distinct facts share the same portal URL — not a POC-vs-lane wording conflict. Retain all variants;  |
| R1 | AR | liquor_abc | url_multifact_distinct | Distinct facts share the same portal URL — not a POC-vs-lane wording conflict. Retain all variants;  |
| R1 | CO | health_permits | url_multifact_distinct | Distinct facts share the same portal URL — not a POC-vs-lane wording conflict. Retain all variants;  |
| R1 | CT | food_establishment_licenses | url_multifact_distinct | Distinct facts share the same portal URL — not a POC-vs-lane wording conflict. Retain all variants;  |
| R1 | CT | health_permits | url_multifact_distinct | Distinct facts share the same portal URL — not a POC-vs-lane wording conflict. Retain all variants;  |
| R1 | DE | food_establishment_licenses | url_multifact_distinct | Distinct facts share the same portal URL — not a POC-vs-lane wording conflict. Retain all variants;  |
| R1 | FL | food_establishment_licenses | url_multifact_distinct | Distinct facts share the same portal URL — not a POC-vs-lane wording conflict. Retain all variants;  |
| R1 | FL | liquor_abc | url_multifact_distinct | Distinct facts share the same portal URL — not a POC-vs-lane wording conflict. Retain all variants;  |
| R1 | FL | mobile_unit_commissary | url_multifact_distinct | Distinct facts share the same portal URL — not a POC-vs-lane wording conflict. Retain all variants;  |
| R1 | GA | food_establishment_licenses | number_delta | Materially different content under shared URL (number_delta). Recommended canonical variant is the l |
| R1 | GA | liquor_abc | url_multifact_distinct | Distinct facts share the same portal URL — not a POC-vs-lane wording conflict. Retain all variants;  |
| R1 | GA | mobile_unit_commissary | url_multifact_distinct | Distinct facts share the same portal URL — not a POC-vs-lane wording conflict. Retain all variants;  |
| R1 | HI | food_establishment_licenses | number_delta | Materially different content under shared URL (number_delta). Recommended canonical variant is the l |
| R1 | HI | health_permits | url_multifact_distinct | Distinct facts share the same portal URL — not a POC-vs-lane wording conflict. Retain all variants;  |
| R1 | IA | food_establishment_licenses | url_multifact_distinct | Distinct facts share the same portal URL — not a POC-vs-lane wording conflict. Retain all variants;  |
| R1 | IA | liquor_abc | number_delta | Materially different content under shared URL (number_delta). Recommended canonical variant is the l |
| R1 | ID | food_establishment_licenses | url_multifact_distinct | Distinct facts share the same portal URL — not a POC-vs-lane wording conflict. Retain all variants;  |
| R1 | ID | health_permits | url_multifact_distinct | Distinct facts share the same portal URL — not a POC-vs-lane wording conflict. Retain all variants;  |
| R1 | ID | liquor_abc | url_multifact_distinct | Distinct facts share the same portal URL — not a POC-vs-lane wording conflict. Retain all variants;  |
| R1 | ID | mobile_unit_commissary | url_multifact_distinct | Distinct facts share the same portal URL — not a POC-vs-lane wording conflict. Retain all variants;  |
| R1 | IL | food_establishment_licenses | url_multifact_distinct | Distinct facts share the same portal URL — not a POC-vs-lane wording conflict. Retain all variants;  |
| R1 | IL | mobile_unit_commissary | url_multifact_distinct | Distinct facts share the same portal URL — not a POC-vs-lane wording conflict. Retain all variants;  |

