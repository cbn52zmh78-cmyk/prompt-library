# Creator #4 Channel Bible v1 — Compliance / Back-Office Explainers

**Task:** #206 · **Working title:** ClearDesk (see `NAME_OPTIONS.md`) · **Parent:** Upon Tyne Productions  
**Date:** 2026-06-19 · **Status:** LOCKED v1 — doc/brand only, no render

---

## 1. Identity hierarchy

```
Upon Tyne Productions
├── DAVID · The Archive           ← language / attestation (David-001)
├── Observable                    ← phenomenon / measurement (Julian-001)
├── Creator #3 [Blueprint]        ← systems / mechanisms (Elijah-001)
└── Creator #4 [ClearDesk]        ← compliance / back-office literacy (Serena-001)
```

| Layer | Public name (draft) | Role |
|-------|---------------------|------|
| Parent | Upon Tyne Productions | IP, credits, legal |
| Channel | **ClearDesk** (TBD lock) | Compliance & back-office explainers |
| Legal lane | Upon Tyne Operations | Ops education, records literacy — **not** client delivery |
| Host | Serena Blake (`Serena-001`) | Synthetic operations communicator |

**Rule:** Never use DAVID Archive marks, Observable evidence palette, or Blueprint schematic cyan on Creator #4 deliverables.

---

## 2. Audience & promise

| Dimension | Observable | Blueprint | Creator #4 |
|-----------|------------|-----------|------------|
| Core question | What do we observe? | How is it built? | **What does this requirement mean?** |
| Evidence | Measurements, papers | Specs, cutaways | **Public sources, regulatory text, process diagrams** |
| Payoff | Science viz | Technical diagram | **Process clarity — what good records look like** |
| Viewer | STEM curiosity | Engineering literacy | **Ops leads, SMB owners, back-office staff** |

**Audience promise:** *Understand the requirement, see the process, know what records to keep — without hiring a lawyer to decode the memo.*

**Hard boundary:** Educational literacy only. **Not legal advice. Not tax advice. Not a substitute for licensed counsel or CPAs.**

---

## 3. Host selection

### Selected: `Serena-001` — Serena Blake

| Field | Value |
|-------|-------|
| Actor ID | `Serena-001` |
| Age (locked) | **30** |
| Lock card | `STUDIO/Cast/Casting_Bible/lock_cards/Serena-001.md` |
| Casting plate | `STUDIO/Cast/actors_roster/female/north_america/Serena_Blake/01_casting_shots/casting_turnaround_v1.jpg` |
| Voice | Rich timbre; **can sharpen to boardroom steel** |
| Genre fit | `procedural` · Executive glam persona |

**Why Serena over runners-up:**

| Candidate | Fit | Verdict |
|-----------|-----|---------|
| **Serena-001** ★ | Boardroom steel register; procedural genre; first female Upon Tyne host — distinct lane | **SELECTED** |
| James-001 | Stoic dependable mentor; fourth male host — less differentiation | Runner-up |
| Julian-001 | Boardroom cut in voice notes; already locked Observable | Reject |

### On-camera wardrobe (production — not casting kit)

| Element | Lock |
|---------|------|
| Top | Tailored blazer over neutral blouse or fine-knit — navy, charcoal, cream |
| Bottom | Matching trousers or structured skirt (frame rarely shows waist-down) |
| Accessories | Minimal — watch or slim folder as motivated prop only |
| Set pairing | Studio interior white cyclorama — wardrobe crisp, no loud patterns |
| Forbidden | Gym/bikini casting wardrobe on episode renders; celebrity likeness |

### Continuity lock (intake emits verbatim)

```
CONTINUITY LOCK @Serena-001: identical presenter face, professional wardrobe, studio interior set, same eye-line to camera — seamless continuation of prior take, zero jump cut.
```

**Identity pack:** `Creator4/productions/host_identity_v1/serena_identity_lock.json`

---

## 4. Format — reuse `explainer-ad`

**Format ID:** `explainer-ad` (existing `Production_Templates_v1.json`)  
**Target:** 30–54s (extend beats to 7–9s each for compliance depth vs product ad default)

### Beat map (compliance adaptation)

| Shot ID | Explainer role | Compliance content |
|---------|----------------|-------------------|
| `01_hook` | Hook | Audit question or deadline that exposes record chaos |
| `02_pain` | Pain | What breaks — scattered files, version drift, unclear ownership |
| `03_solution` | Solution | Name the framework / process / record type in plain language |
| `04_benefit_a` | Benefit A | Clarity outcome — findable, dated, attributable |
| `05_benefit_b` | Benefit B | Risk reduction — **educational framing, not legal guarantee** |
| `06_cta` | CTA | *Follow ClearDesk — one process at a time.* + disclaimer line |

### Intake block — `compliance_subject` (concept-level)

```json
{
  "subject_id": "COMP-REC-001",
  "domain": "Records Management — Audit Readiness",
  "topic": "What auditors mean by 'complete records'",
  "key_source": "Public agency guidance or cited regulatory excerpt (labeled)",
  "jurisdiction_note": "Illustrative — not jurisdiction-specific unless sourced",
  "sources": [
    { "citation": "...", "url": "...", "type": "primary", "notes": "Public government work or licensed excerpt" }
  ],
  "disclaimer": "Educational only — not legal, tax, or professional advice."
}
```

### Provenance card (mandatory)

```json
{
  "card_type": "closing",
  "footer": "Educational content only — not legal, tax, or professional advice. Synthetic presenter."
}
```

Reuse `explainer-ad` `require_claim_verification_flag` — any compliance claim ships `[CLAIM REQUIRES VERIFICATION]` until Gate 0 sign-off.

---

## 5. Set & style — clean professional identity

| Lock | Value |
|------|-------|
| Set | `@Set-Studio-Interior-001` — white cyclorama, editorial trust |
| Style | `@Style-Professional-Clean-001` (spec in brand kit — v1 may alias cool-clinical discipline with warmer neutrals) |

### On-screen label chips (payoff / citation beats)

| Label | When |
|-------|------|
| PUBLIC SOURCE | Agency site, statute excerpt, open guidance |
| PROCESS DIAGRAM | Workflow illustration |
| ILLUSTRATIVE | Example record layout — not a client file |
| NOT JURISDICTION-SPECIFIC | General literacy unless episode cites one state |
| NOT LEGAL ADVICE | Mandatory on episodes touching regulatory text |

---

## 6. Runway topics (not authored in this task)

| Domain | Example episode |
|--------|-----------------|
| Records | Audit trail vs activity log — what's the difference? |
| Licensing | What "primary source" means in a renewal packet |
| Privacy | Retention schedule basics (cited public guidance) |
| Finance ops | Invoice approval chain — who signs what |
| HR back-office | I-9 document list — educational walkthrough |

**Stonebridge adjacency:** Consumer/SMB education lane — does **not** ship Stonebridge client deliverables or imply assessor/certifier role.

---

## 7. Legal & Gate 0 requirements

Every concept **must** include:

1. `gate_0.human_signoff: true`
2. `ai_disclosure` in provenance + YouTube metadata
3. Disclaimer in `brand.legal_line` and video description template
4. No "we certify," "guaranteed compliant," "approved by," or law-firm voice
5. Sources cited when referencing regulatory language — paraphrase preferred over quoting statute without citation

---

## 8. Version history

| Version | Date | Change |
|---------|------|--------|
| 1.0 | 2026-06-19 | Creator #4 bible — ClearDesk rec, Serena-001, explainer-ad reuse, compliance identity |
| 1.1 | 2026-06-19 | #206 — positioning doc, concept template, task stamp |

*Upon Tyne Productions / Creator #4 — processes explained, records clarified, advice boundaries respected.*