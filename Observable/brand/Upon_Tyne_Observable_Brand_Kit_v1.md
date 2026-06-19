# Upon Tyne + Observable Brand Kit v1

**Task:** #180  
**Status:** LOCKED v1 — operator spec + v1 raster exports (intro sting pending)  
**Parent:** Upon Tyne Productions  
**Channel:** Observable (Upon Tyne Science)  
**Date:** 2026-06-19

---

## 1. Identity hierarchy

```
Upon Tyne Productions          ← legal entity, credits, contracts, parent watermark
    └── Observable             ← YouTube / social channel (science-explainer format)
            └── Astro, Chem/Physics, Molecular slates
```

| Layer | Public name | Role | Appears on |
|-------|-------------|------|------------|
| **Parent** | Upon Tyne Productions | IP owner, production company | End-card footer, About, credits, legal |
| **Channel** | Observable | Science documentary explainers | Banner, avatar, lower-thirds, intros |
| **Legal lane** | Upon Tyne Science | Contracts, Science repo handoff | About, B2B, educator packs |
| **Host** | Julian Cross (`@Julian-001`) | Synthetic science communicator | On-camera; roster talent, not DAVID |

**Rule:** Audience-facing video branding leads with **Observable**. Parent credit is always present but subordinate. **Never** use DAVID · The Archive marks on Observable deliverables.

**Locked anchors:** `Julian-001` lock card · `@Set-Seamless-Neutral-001` · `@Style-Cool-Clinical-001` · `science-explainer` format

---

## 2. Julian-001 host identity

| Field | Value |
|-------|-------|
| Actor ID | `Julian-001` |
| Stage name | Julian Cross |
| Age (locked) | **31** |
| Lock card | `STUDIO/Cast/Casting_Bible/lock_cards/Julian-001.md` |
| Casting plate | `STUDIO/Cast/actors_roster/male/north_america/Julian_Cross/01_casting_shots/casting_turnaround_v1.jpg` |
| Voice | Warm mid-Atlantic baritone; clear enthusiastic science communicator |
| Format anchor | `@Julian-001` in `Production_Templates_v1.json` → `science-explainer` |

### On-camera wardrobe (production — not casting plate gym kit)

| Element | Lock |
|---------|------|
| Top | Smart-casual: fitted navy henley or unstructured blazer over neutral tee |
| Bottom | Dark chinos or clean denim (frame rarely shows waist-down) |
| Color | Navy, charcoal, forest green accent — **no** loud logos |
| Set pairing | Seamless neutral `#9A9A98` — wardrobe must not clash cool-clinical grade |
| Forbidden | Gym casting wardrobe on episode renders; celebrity likeness; handheld jitter |

### Continuity lock (intake emits verbatim)

```
CONTINUITY LOCK @Julian-001: identical presenter face, smart-casual wardrobe, seamless neutral set, same eye-line to camera — seamless continuation of prior take, zero jump cut.
```

**Future pack:** `Observable/productions/host_identity_v1/` (avatar crop, host test, identity JSON) — v1 references casting plate until host pack ships.

---

## 3. Locked color system

Cool-clinical palette — deliberate contrast with DAVID warm Archive amber.

### Parent — Upon Tyne Productions

Reuse DAVID parent tokens (`ut-black`, `ut-warm-white`, `ut-gold`). Same letterpress wordmark exports.

### Channel — Observable (primary UI)

| Token | Hex | RGB | Use |
|-------|-----|-----|-----|
| `obs-bg` | `#121820` | 18, 24, 32 | Cards, overlays, end screens |
| `obs-surface` | `#1A2430` | 26, 36, 48 | Lower-third plates, chips |
| `obs-title` | `#E8EEF2` | 232, 238, 242 | Wordmark, titles |
| `obs-accent` | `#2A7B9E` | 42, 123, 158 | Accent rules, links |
| `obs-accent-bright` | `#4DA8C7` | 77, 168, 199 | Hover, viz callouts |
| `obs-body` | `#A8B8C8` | 168, 184, 200 | Subtitles, body on cards |
| `obs-cta` | `#5EC4E8` | 94, 196, 232 | CTA, footer links |
| `obs-seamless` | `#9A9A98` | 154, 154, 152 | Set reference, banner backdrop |

### Evidence labels (mandatory on science viz content)

| Label | Hex | When |
|-------|-----|------|
| OBSERVED | `#1E8A6E` | Direct measurement, photograph, mission data |
| SIMULATION | `#2A5F9E` | Physics/cosmology/chem sim frames |
| MODEL | `#8A6B2A` | Structural/schematic model (e.g. PDB geometry) |
| ILLUSTRATIVE | `#6A5080` | Concept diagram, not claiming data |
| NOT TO SCALE | `#5A6470` | Any compressed or exaggerated geometry |

**Lighting canon:** Seamless neutral **5500K** bilateral soft key — no magenta vignette, no warm cozy cast (`Set_Library_v1.json` + `Style-Cool-Clinical-001`).

---

## 4. Typography

| Role | Typeface | Fallback | Weight |
|------|----------|----------|--------|
| Channel wordmark | IBM Plex Sans | Inter, DM Sans | 600 |
| On-screen titles | IBM Plex Sans | Inter | 600 |
| Lower-third body | Inter | DM Sans, Arial | 400 |
| Measurements / IDs | IBM Plex Mono | JetBrains Mono | 400 |
| Label chips | Inter | Arial | 600 all-caps |
| Legal footer | Inter | Arial | 400 |
| Parent wordmark | EB Garamond | (shared with Upon Tyne) | 500 |

**Pipeline note:** Science overlays currently inherit `render_longform.py` Arial — bundle Plex/Inter under `Observable/brand/fonts/` on design export.

---

## 5. Logo concepts

### 5.1 Observable (channel wordmark)

**Concept:** Clean measurement mark — single word, clinical trust.

```
Observable
```

| Spec | Value |
|------|-------|
| Type | IBM Plex Sans 600, `obs-title` |
| Accent | Optional: hollow circle on the **O** (aperture / observation — 1.5px stroke `obs-accent`) |
| Subline | *Evidence before wonder.* — Inter 400, 40% size, `obs-body` |
| Min width | 140px digital |
| Clear space | 0.75× cap-height |
| Do not | Telescope clipart, rocket icons, gradient nebula fills, DAVID amber palette |

**Export deliverables:** `observable_wordmark.svg`, `observable_wordmark_1x.png`, `observable_monogram_O_800.png`

### 5.2 Channel avatar monogram (fallback)

**O** aperture circle on `obs-bg`, `obs-accent` stroke — use if host crop unavailable at launch.

---

## 6. Per-asset specifications

### 6.1 YouTube channel banner

| Field | Spec |
|-------|------|
| **Canvas** | 2560 × 1440 px |
| **Safe zone (TV)** | Center 1546 × 423 px |
| **Safe zone (mobile)** | Center 640 × 360 px |
| **Composition** | Left: seamless neutral gradient (`#9A9A98` → `#7A7A78`). Right: Julian Cross chest-up (smart-casual wardrobe edit from casting plate). Center-bottom: **Observable** wordmark. |
| **Tagline** | *Evidence before wonder.* — Inter 400, `obs-body` |
| **Parent credit** | *Upon Tyne Productions* — Inter 400, 11px, `ut-gold`, bottom-right |
| **Grade** | Cool-clinical — neutral WB, low saturation |
| **Export** | `Observable/brand/export/youtube_banner_2560x1440.jpg` |

### 6.2 Channel avatar / profile picture

| Field | Spec |
|-------|------|
| **Canvas** | 800 × 800 px |
| **Crop** | Julian Cross front panel from casting turnaround — chest-up, smart-casual wardrobe |
| **Background** | `obs-bg` or soft seamless neutral |
| **Ring** | Optional 2px `obs-accent` circle |
| **Export** | `Observable/brand/export/channel_avatar_800.png` |

### 6.3 Intro sting (short bumper)

| Field | Spec |
|-------|------|
| **Duration** | **4.0 s** |
| **Resolution** | 1920 × 1080 |
| **Picture** | 0.0–0.5 s: `obs-bg` fade. 0.5–3.0 s: seamless neutral wide + Julian medium. 3.0–4.0 s: wordmark + tagline |
| **On-screen** | `Observable` + *Evidence before wonder.* |
| **Audio** | Room tone swell optional; `BED-CLI-001` / `BED-PHY-001` / `BED-CHE-001` per topic — clearance manifest only |
| **Export** | `Observable/brand/export/intro_sting_4s_1080p.mp4` |

### 6.4 Lower-third template (in-episode)

| Field | Spec |
|-------|------|
| **Channel bug** | Top margin: `Observable` — Plex Sans 14px, `obs-title` on `obs-surface` plate |
| **Label chips** | Evidence labels §3 — rounded rect r=6 |
| **Primary line** | Episode topic — `obs-title`, Inter 20px |
| **Viz line** | `science_subject_ref` or measurement — Plex Mono 16px, `obs-accent-bright` |
| **Export** | `Observable/brand/templates/lower_third_master_1920x1080.png` |

**Script fields:** `shots[].on_screen`, `shots[].on_screen_labels`, `intake.science_subject`

### 6.5 End card — closing

| Field | Spec |
|-------|------|
| **Background** | `obs-bg` |
| **Title** | `Observable` or `brand.title` |
| **Subtitle** | *Evidence before wonder.* |
| **CTA** | *Follow Observable — one measurement at a time.* — `obs-cta` |
| **Parent line** | *Upon Tyne Productions · Synthetic presenter · AI disclosure in description* |
| **Export** | `Observable/brand/templates/end_card_closing_1920x1080.png` |

### 6.6 End card — sources (science provenance)

| Field | Spec |
|-------|------|
| **card_type** | `sources` (from `science-explainer` provenance template) |
| **Title** | `Sources — {phenomenon_name}` |
| **Body** | Up to 3 citations from `science_subject.sources[]` |
| **Footer** | Domain + subject_id |
| **Duration** | 6 s default |
| **Export** | `Observable/brand/templates/end_card_sources_1920x1080.png` |

### 6.7 Parent end-slate

Reuse `DAVID/brand/templates/parent_slate_upon_tyne.png` — Upon Tyne wordmark is shared across properties.

---

## 7. Voice, taglines, and copy locks

| Use | Copy | Lock |
|-----|------|------|
| Channel title | Observable | LOCKED |
| Legal lane | Upon Tyne Science | LOCKED |
| Subtitle | Evidence before wonder. | LOCKED |
| CTA | Follow Observable — one measurement at a time. | LOCKED |
| Signature beat | What do we observe — and how do we know it? | LOCKED |
| Cold open pattern | Hook question → phenomenon plain language | Format canon |
| Parent tagline | Directed. Not generated. | Upon Tyne — pending Director lock |
| AI disclosure | Synthetic presenter · Educational content · Sources in description | Legal |
| Viz honesty | SIMULATION / MODEL / OBSERVED / NOT TO SCALE on payoff beats | LOCKED |

---

## 8. File manifest (export checklist)

| Asset | Path (target) | Status |
|-------|---------------|--------|
| Brand kit (this doc) | `Observable/brand/Upon_Tyne_Observable_Brand_Kit_v1.md` | ✅ |
| Machine specs | `Observable/brand/asset_specs.json` | ✅ |
| Channel About | `Observable/brand/CHANNEL_ABOUT.md` | ✅ |
| Host lock card | `STUDIO/Cast/Casting_Bible/lock_cards/Julian-001.md` | ✅ exists |
| Casting plate | `.../Julian_Cross/01_casting_shots/casting_turnaround_v1.jpg` | ✅ exists |
| Set reference | `STUDIO/Pipeline/references/seamless_neutral_grey_reference.json` | ✅ exists |
| Banner export | `Observable/brand/export/youtube_banner_2560x1440.jpg` | ✅ v1 PIL composite |
| Avatar export | `Observable/brand/export/channel_avatar_800.png` | ✅ v1 casting crop |
| Intro sting 4s | `Observable/brand/export/intro_sting_4s_1080p.mp4` | ⬜ edit export |
| Lower-third PNG | `Observable/brand/templates/lower_third_master_1920x1080.png` | ✅ v1 template |
| End cards | `Observable/brand/templates/end_card_*.png` | ✅ v1 templates |
| Wordmarks SVG | `Observable/brand/export/*.svg` | ✅ |
| Host identity pack | `Observable/productions/host_identity_v1/` | ✅ v1 lock JSON |

---

## 9. Pipeline integration

| System | Field / function | Brand tie-in |
|--------|------------------|--------------|
| `production_intake.py` | `brand.title`, `brand.subtitle`, `brand.cta` | Closing + sources card |
| `production_intake.py` | `science_subject` block | Sources provenance |
| `render_longform.py` | `render_provenance_card()` | End card §6.5–6.6 |
| `science-explainer` format | `04_visualization_payoff` | Evidence label chips §3 |
| `Science/reference_plates/` | `visualization_ref`, `plate_id` | @2 plate continuity |
| Legal Gate | AI disclosure | Footer + About |

---

## 10. Version history

| Version | Date | Change |
|---------|------|--------|
| 1.0 | 2026-06-19 | #180 — Observable kit, Julian-001 identity, chem/physics slate brand lock |

*Upon Tyne Productions / Observable — sourced, labeled, legally gated.*