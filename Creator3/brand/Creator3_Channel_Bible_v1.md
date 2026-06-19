# Creator #3 Channel Bible v1

**Task:** #186 · **Working title:** Blueprint (see `NAME_OPTIONS_v186.md`) · **Parent:** Upon Tyne Productions  
**Date:** 2026-06-19 · **Status:** DRAFT LOCK — brand + host selected; set plate + format template follow-on

---

## 1. Identity hierarchy

```
Upon Tyne Productions
├── DAVID · The Archive        ← language / attestation (David-001)
├── Observable                 ← phenomenon / measurement (Julian-001)
└── Creator #3 [Blueprint]     ← systems / mechanisms / technical diagrams (Elijah-001)
```

| Layer | Public name (draft) | Role |
|-------|---------------------|------|
| Parent | Upon Tyne Productions | IP, credits, legal |
| Channel | **Blueprint** (TBD lock) | Technical systems explainers |
| Legal lane | Upon Tyne Technical | B2B, educator packs, spec exports |
| Host | Elijah Brooks (`Elijah-001`) | Synthetic systems communicator |

**Rule:** Never use DAVID Archive marks or Observable evidence-label palette on Creator #3 deliverables.

---

## 2. Audience & promise

| Dimension | DAVID | Observable | Creator #3 |
|-----------|-------|------------|------------|
| Core question | What did they say — and how do we prove it? | What do we observe — and how do we know it? | **How is it built — and what does each part do?** |
| Evidence | Texts, attestation | Measurements, simulations | **Specs, standards, cutaways, exploded views** |
| Payoff beat | Period-language line | @2 science visualization | **@2 diagram / cutaway / assembly plate** |
| Viewer intent | Language, history | STEM curiosity | **Engineering literacy, how-things-work** |

**Audience promise:** *See the system — part by part, spec by spec, labeled honestly.*

---

## 3. Host selection (#186)

### Selected: `Elijah-001` — Elijah Brooks

| Field | Value |
|-------|-------|
| Actor ID | `Elijah-001` |
| Age (locked) | **37** |
| Lock card | `STUDIO/Cast/Casting_Bible/lock_cards/Elijah-001.md` |
| Casting plate | `STUDIO/Cast/actors_roster/male/north_america/Elijah_Brooks/01_casting_shots/casting_turnaround_v1.jpg` |
| Voice | Deep measured baritone; stillness fills frame |
| Format anchor | `@Elijah-001` in `technical-explainer` (format ships follow-on) |

**Why Elijah over runners-up:**

| Candidate | Age | Fit | Pass |
|-----------|-----|-----|------|
| **Elijah-001** ★ | 37 | Quiet authority; systems walk-through energy; visually distinct from Julian/David | **SELECTED** |
| James-001 | — | European workshop gravitas; less roster differentiation | Runner-up |
| Wei-001 | 31 | Tech-founder speed; overlaps Julian demographic + Observable lane | Reject |
| Kenji-001 | 34 | Capable; less "measured systems" persona in lock card | Runner-up |

### On-camera wardrobe (production — not gym casting kit)

| Element | Lock |
|---------|------|
| Top | Dark henley, chore jacket, or rolled-sleeve work shirt — no logos |
| Bottom | Dark chinos or work trousers |
| Accents | Optional caliper, pen, or rolled blueprint tube as motivated prop |
| Set pairing | Blueprint bench / warehouse industrial — wardrobe earth-neutral |
| Forbidden | Gym casting kit on episode renders; celebrity likeness |

### Continuity lock (intake emits verbatim)

```
CONTINUITY LOCK @Elijah-001: identical presenter face, workwear wardrobe, blueprint bench set, same eye-line to camera — seamless continuation of prior take, zero jump cut.
```

**Identity pack:** `Creator3/productions/host_identity_v1/elijah_identity_lock.json`

---

## 4. Set & style (technical / blueprint identity)

### Set — v1 interim: `@Set-Warehouse-Industrial-001`

Use locked industrial loft plate until `@Set-Blueprint-Bench-001` ships.

**Future set `@Set-Blueprint-Bench-001` (spec):**
- Engineering light table, rolled ISO drawings, calipers, part trays
- Dark navy wall `#0A1628`, cyan grid projection optional
- 4800K window key — matches warehouse discipline

### Style — `@Style-Blueprint-Technical-001` (new — spec in brand kit)

- Dark navy base, cyan schematic line accent, restrained gold dimension ticks
- Low saturation host grade; diagram overlays high-contrast
- **Not** cool-clinical (Observable) or warm Archive (DAVID)

### Diagram honesty labels (mandatory on payoff beats)

| Label | When |
|-------|------|
| AS-BUILT | Photograph or documented physical assembly |
| SPEC | Drawing per published standard / manufacturer doc |
| EXPLODED VIEW | Illustrative separation for teaching |
| ILLUSTRATIVE | Concept diagram, not claiming survey data |
| NOT TO SCALE | Compressed geometry or exaggerated clearances |

---

## 5. Format: `technical-explainer` (draft)

| Beat | Role | Duration | Content |
|------|------|----------|---------|
| `01_hook` | host | 7–9s | Surprising failure mode or "you use it daily, never saw inside" |
| `02_mechanism` | host | 7–9s | Name subsystems; what each does in plain language |
| `03_how_we_know` | host | 7–9s | Standard, manual, teardown, or spec sheet — citable |
| `04_diagram_payoff` | host + @2 | **9s** | Cutaway / exploded / schematic plate — label chips |
| `05_significance` | host | 7–9s | Stakes: safety, cost, design tradeoff, maintenance |

**Target:** ~54s · `actor_id`: `Elijah-001` · `format_id`: `technical-explainer` (template registration = follow-on #187)

**Script block:** `technical_subject` (parallel to Observable `science_subject`):

```json
{
  "subject_id": "SYS-XXX-001",
  "domain": "Mechanical Systems — HVAC",
  "system": "Heat pump reversing valve",
  "key_spec": "ANSI/ASHRAE reference cycle diagram",
  "visualization_ref": "Creator3/reference_plates/...",
  "plate_id": "@Tech-HeatPump-001",
  "sources": [{ "citation": "...", "type": "primary" }]
}
```

---

## 6. Runway topics (pilot slate — not authored in #186)

| Domain | Example episode |
|--------|-----------------|
| Mechanical | Heat pump / valve train cutaway |
| Electrical | Breaker panel branch circuit map |
| Civil | Bridge bearing exploded view |
| Software-adjacent | CDN edge cache flow (schematic) |

---

## 7. Pipeline integration (planned)

| System | Field | Tie-in |
|--------|-------|--------|
| `production_intake.py` | `brand.title`, `technical_subject` | Provenance + diagram labels |
| `render_longform.py` | diagram label chips | Payoff beat overlays |
| Legal Gate | AI disclosure | Footer + About |
| OBSERVATORY | 480p draft renders | Separate lane from Observable science queue |

---

## 8. Version history

| Version | Date | Change |
|---------|------|--------|
| 1.0 | 2026-06-19 | #186 — Bible, Elijah-001 host, Blueprint name recommendation, technical identity spec |

*Upon Tyne Productions / Creator #3 — systems named, specs cited, diagrams labeled.*