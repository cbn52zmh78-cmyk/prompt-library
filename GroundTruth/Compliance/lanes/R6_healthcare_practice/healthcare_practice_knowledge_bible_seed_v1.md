# Healthcare Practice Knowledge Bible — Seed v1 (R6)

**Lane:** R6 — Healthcare Practice  
**Variant:** 3-state seed (CA, TX, NY) + federal HIPAA control-map  
**As-of:** 2026-06-19  
**Status:** SEED (not sellable)  
**Citation standard:** STD-CITE-001

> Operational compliance research and cited public-records compilation — not legal advice.

---

## 1. TL;DR / Executive Summary

This seed gathers **federal HIPAA** Privacy, Security, Breach Notification, and **BAA** requirements from **eCFR** (primary), plus state medical-privacy add-ons for **California (CMIA)**, **Texas (HS Ch. 181)**, and **New York (PHL + SHIELD context)**.

| Metric | Value |
|--------|-------|
| Cited claims | 42 |
| Federal controls mapped | 32 (31 FOUND) |
| States | CA, TX, NY |
| Gaps flagged | 8 |
| Parked sources | 6 |

**Honesty rule:** Gaps render as `NOT FOUND — [source checked: …]`. HHS.gov returned **HTTP 403**; eCFR used as federal primary.

---

## 2. Scope, Methodology & As-Of Date

**Scope:** Outpatient medical practices (physician, dental, behavioral health, urgent care, multi-specialty groups).

**Domains:** HIPAA privacy/security, vendor BAA chain, breach notification, state medical-privacy overlays.

**Methodology:** Public `.gov` and official statute portals only; no bypass. AI-assisted synthesis with explicit gap taxonomy.

---

## 3. Body — Cited Compliance Record

### Federal HIPAA (eCFR primary)

- **Covered entities** = health plans, clearinghouses, or providers transmitting electronic covered transactions ([45 CFR §160.103](https://www.ecfr.gov/current/title-45/section-160.103)).
- **Privacy:** No use/disclosure except as permitted/required; **minimum necessary** applies ([§164.502](https://www.ecfr.gov/current/title-45/section-164.502)).
- **BAA:** Written contract with §164.504(e) elements — permitted uses, ePHI safeguards, breach reporting, subcontractor flow-down, termination rights ([§164.504](https://www.ecfr.gov/current/title-45/section-164.504), [§164.314](https://www.ecfr.gov/current/title-45/section-164.314)).
- **Security (admin):** Risk analysis, security official, incident response, contingency plan ([§164.308](https://www.ecfr.gov/current/title-45/section-164.308)).
- **Security (technical):** Access control, audit, integrity, authentication, transmission security ([§164.312](https://www.ecfr.gov/current/title-45/section-164.312)).
- **Breach:** Individual notice within **60 days**; BA notifies CE within 60 days ([§164.404](https://www.ecfr.gov/current/title-45/section-164.404)).

Full control map: `hipaa_control_map_seed_v1.json`.

### California — CMIA

- No disclosure without **authorization** except §56.10(b)/(c) cases ([Civ. §56.10](https://leginfo.legislature.ca.gov/faces/codes_displaySection.xhtml?sectionNum=56.10.&lawCode=CIV)).
- Prohibits sale/marketing/non-treatment use of medical information (§56.10(d)).
- Authorization: **14-point type**, specific uses, **1-year max** expiration ([§56.11](https://leginfo.legislature.ca.gov/faces/codes_displaySection.xhtml?sectionNum=56.11.&lawCode=CIV)).
- HIPAA Part 164 cross-reference for ERISA plan disclosures (§56.10(c)(21)).

### Texas — Medical Records Privacy

- **FOUND:** Ch. 181 index anchor at [statutes.capitol.texas.gov](https://statutes.capitol.texas.gov/Docs/HS/htm/HS.181.htm).
- **ACCESS_RESTRICTED:** Section text not harvestable (SPA shell). TMB privacy page **404**.

### New York — PHL + SHIELD

- **FOUND:** [NY DOH HIPAA hub](https://www.health.ny.gov/regulations/hipaa/) and [preemption charts](https://www.health.ny.gov/regulations/hipaa/preemption_charts.htm) — state laws more stringent than HIPAA are not superseded; PHL §17/§18 prevail in documented scenarios.
- **REQUIRES_CONFIRMATION:** GBL §899-aa (SHIELD) — nysenate.gov **PARKED** (Cloudflare).
- **NOT FOUND:** NY AG breach reporting URL **404**.

---

## 4. Source Register (Graded)

See `source_register.json` — 12 harvested, 6 parked/restricted.

---

## 5. Conflict Reconciliation

| Topic | Assessment |
|-------|------------|
| HHS vs eCFR | eCFR operative; HHS guidance parked |
| HIPAA vs CMIA | Apply stricter; CMIA references Part 164 |
| HIPAA vs NY PHL | Dual-track; NY DOH charts document prevailing law |

---

## 6. Gaps / NOT FOUND

1. **PARKED** — HHS HIPAA pages (403)
2. **ACCESS_RESTRICTED** — Texas Ch. 181 section text (SPA)
3. **PARKED** — NY SHIELD statute (Cloudflare)
4. **NOT FOUND** — NY AG breach portal (404)
5. **NOT FOUND** — TMB privacy page (404)

---

## 7. Confidence

| Section | Confidence |
|---------|------------|
| Federal HIPAA | HIGH |
| California | HIGH |
| Texas | LOW |
| New York | MEDIUM |

---

## 8. Citation Appendix

Numbered references match `healthcare_practice_knowledge_bible_seed_v1.json` §8 and `hipaa_control_map_seed_v1.json` citations array.