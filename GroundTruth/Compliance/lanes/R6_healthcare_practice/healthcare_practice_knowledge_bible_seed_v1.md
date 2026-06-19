# Healthcare Practice Knowledge Bible — Seed v1.1 (R6-C)

**Lane:** R6 — Healthcare Practice  
**Variant:** 11-state seed (CA, TX, NY, WA, FL, MA, OH, PA, IL, NJ, GA) + federal HIPAA control-map  
**As-of:** 2026-06-19  
**Status:** SEED (approaching sellable depth — not sellable yet)  
**Citation standard:** STD-CITE-001

> Operational compliance research and cited public-records compilation — not legal advice.

---

## 1. TL;DR / Executive Summary

R6-C adds a **high-volume state tranche** (IL · PA · NJ · GA · OH) to the existing 6-state seed. Federal HIPAA remains eCFR-primary with CMS/ASPE fallbacks.

| Metric | Value |
|--------|-------|
| Cited claims | 90 |
| Federal controls | 35 (34 FOUND) |
| States | 11 |
| State facts | 55 |
| Gaps flagged | 12 |
| Parked sources | 10 |

**Honesty rule:** Portal blocks render as `NOT FOUND — [source checked: …]`. No bypass.

---

## 2. Scope, Methodology & As-Of Date

**Scope:** Outpatient medical practices — HIPAA + state medical-privacy and breach-notification overlays.

**R6-C tranche:** IL, PA, NJ, GA, OH — privacy/breach add-ons only.

---

## 3. Body — Cited Compliance Record

### Ohio — FOUND (primary)

- [§3701.74](https://codes.ohio.gov/ohio-revised-code/section-3701.74) — written request for medical-record access; record definition.
- [§4731.22](https://codes.ohio.gov/ohio-revised-code/section-4731.22) — betraying professional confidence = discipline.
- [§1349.19](https://codes.ohio.gov/ohio-revised-code/section-1349.19) — breach definition; 45-day notice; **HIPAA CE exempt**.

### Pennsylvania — PARTIAL

- **FOUND:** [42 Pa.C.S. §6155–6156](https://www.palegis.us/statutes/consolidated/view-statute?txtType=PDF&ttl=42&div=00.&chpt=61&sctn=55&subsctn=0) (PDF primary) — patient access, protective orders, sealed-record consent.
- **FOUND (secondary):** [PA OAG BPINA](https://www.attorneygeneral.gov/protect-yourself/bpina/) — breach definition, resident notice, AG notice (500+).
- **NOT FOUND:** 73 P.S. §2301 primary at palegis (2026 Title 73 chpt collision).

### Illinois — ACCESS_RESTRICTED

- **ACCESS_RESTRICTED:** 740 ILCS 110/ and 815 ILCS 530/ — ilga.gov ILCS/JCAR 404/500.

### New Jersey — PARKED

- **PARKED:** N.J.S.A. 26:5C and 56:8-163 — lis.njleg SPA shell; cyber.nj.gov Incapsula.

### Georgia — ACCESS_RESTRICTED

- **ACCESS_RESTRICTED:** O.C.G.A. §31-33 and §10-1-910 — legis.ga.gov API 404/401; sos.ga.gov PDF 403.

*(Prior states CA, TX, NY, WA, FL, MA unchanged from R6-B — see state packs.)*

---

## 4. Source Register (Graded)

See `source_register.json` v1.2 — **28 harvested, 10 parked**.

---

## 5. Conflict Reconciliation

| Topic | Assessment |
|-------|------------|
| PA BPINA primary vs OAG | palegis chpt collision; OAG secondary operative until primary re-located |
| OH §1349.19 vs HIPAA | CE exempt; non-CE PI holders still notify |

---

## 6. Gaps / NOT FOUND

1. **PARKED** — HHS HIPAA (403)
2. **NOT FOUND** — 73 P.S. §2301 BPINA primary (palegis)
3. **ACCESS_RESTRICTED** — Illinois ILCS 815/740
4. **PARKED** — New Jersey lis.njleg + cyber.nj.gov
5. **ACCESS_RESTRICTED** — Georgia legis.ga.gov / sos.ga.gov
6. *(Prior R6 gaps: TX SPA, NY nysenate, MA 201 CMR 17, etc.)*

---

## 7. Confidence

| Section | Confidence |
|---------|------------|
| Federal HIPAA | HIGH |
| Ohio | HIGH |
| Pennsylvania | MEDIUM |
| Illinois / NJ / GA | LOW |

---

## 8. Citation Appendix

Numbered references in `healthcare_practice_knowledge_bible_seed_v1.json` §8 and per-state packs under `states/`.