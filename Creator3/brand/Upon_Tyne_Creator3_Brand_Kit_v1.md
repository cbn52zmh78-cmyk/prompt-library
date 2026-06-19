# Upon Tyne + Creator #3 Brand Kit v1

**Task:** #186 · **Working name:** Blueprint · **Status:** DRAFT LOCK (design export pending)  
**Parent:** Upon Tyne Productions · **Legal lane:** Upon Tyne Technical · **Date:** 2026-06-19

---

## 1. Locked copy (draft — pending name lock)

| Use | Copy |
|-----|------|
| Channel title | **Blueprint** (TBD — see `NAME_OPTIONS_v186.md`) |
| Legal lane | Upon Tyne Technical |
| Subtitle | Built logic, part by part. |
| CTA | Follow Blueprint — one system at a time. |
| Signature beat | How is it built — and what does each part do? |
| Parent tagline | Directed. Not generated. |
| AI disclosure | Synthetic presenter · Educational content · Sources in description |

---

## 2. Color system — blueprint technical

Deliberate contrast: DAVID warm amber · Observable cool clinical · **Creator #3 cyan-on-navy schematic**.

### Parent — Upon Tyne (reuse)

`ut-black` `#0D0D0D` · `ut-warm-white` `#F5F0E8` · `ut-gold` `#C9A84C`

### Channel — Blueprint (primary UI)

| Token | Hex | Use |
|-------|-----|-----|
| `bp-bg` | `#0A1628` | Cards, overlays, sting base |
| `bp-surface` | `#122038` | Lower-third plates, diagram backdrop |
| `bp-title` | `#E8F2FA` | Wordmark, titles |
| `bp-line` | `#3DB8E8` | Schematic lines, accent rules |
| `bp-line-dim` | `#2A7A9E` | Secondary diagram strokes |
| `bp-body` | `#9BB0C8` | Subtitles, body on cards |
| `bp-cta` | `#5EC4E8` | CTA, footer links |
| `bp-grid` | `#1A3050` | Optional background grid |
| `bp-dimension` | `#C9A84C` | Dimension ticks (parent gold, sparse) |

### Diagram labels

| Label | Hex | When |
|-------|-----|------|
| AS-BUILT | `#2E8A6E` | Documented physical assembly |
| SPEC | `#3DB8E8` | Standard / manufacturer drawing |
| EXPLODED VIEW | `#6A5080` | Teaching separation |
| ILLUSTRATIVE | `#8A6B2A` | Concept schematic |
| NOT TO SCALE | `#5A6470` | Exaggerated clearances |

---

## 3. Typography

| Role | Typeface | Weight |
|------|----------|--------|
| Wordmark | IBM Plex Sans | 600 |
| Titles | IBM Plex Sans | 600 |
| Body / lower-third | Inter | 400 |
| Specs / part IDs | IBM Plex Mono | 400 |
| Label chips | Inter | 600 all-caps |

---

## 4. Logo concept

**Wordmark:** `Blueprint` — Plex Sans 600, `bp-title`, optional cyan corner bracket on **B** (ISO drawing symbol).

**Subline:** *Built logic, part by part.* — Inter 400, 40% size, `bp-body`

**Monogram fallback:** B with corner brackets on `bp-bg`, `bp-line` stroke — avatar if host crop unavailable.

**Do not:** Observable aperture-O, DAVID letterpress, nebula gradients, wrench clipart.

**Export targets (pending):**
- `Creator3/brand/export/blueprint_wordmark.svg`
- `Creator3/brand/export/blueprint_wordmark_1x.png`
- `Creator3/brand/export/blueprint_monogram_B_800.png`
- `Creator3/brand/export/youtube_banner_2560x1440.jpg`
- `Creator3/brand/export/channel_avatar_800.png`

---

## 5. Per-asset specifications

### 5.1 YouTube banner

| Field | Spec |
|-------|------|
| Canvas | 2560 × 1440 px |
| TV safe | Center 1546 × 423 px |
| Composition | Left: navy + faint cyan grid. Right: Elijah Brooks chest-up (workwear edit). Center-bottom: wordmark + subtitle. |
| Parent credit | *Upon Tyne Productions* — Inter 400, 11px, `ut-gold`, bottom-right |

### 5.2 Channel avatar

| Field | Spec |
|-------|------|
| Canvas | 800 × 800 px |
| Crop | Elijah front panel, chest-up, workwear |
| Background | `bp-bg` |
| Ring | Optional 2px `bp-line` bracket corners |

### 5.3 Intro sting (4s) — spec owned by Observable handoff lane; Creator #3 sting deferred

Creator #3 intro sting follows same 4s structure when brand exports — **not in #186 scope**.

### 5.4 Lower-third

| Field | Spec |
|-------|------|
| Channel bug | `Blueprint` — Plex Sans 14px on `bp-surface` |
| Primary | System topic — `bp-title`, Inter 20px |
| Spec line | `technical_subject_ref` — Plex Mono 16px, `bp-line` |
| Chips | Diagram labels §2 |

---

## 6. Host — Elijah-001 summary

See `Creator3_Channel_Bible_v1.md` §3 · lock card `Elijah-001.md` · identity pack `Creator3/productions/host_identity_v1/`

---

## 7. File manifest

| Asset | Path | Status |
|-------|------|--------|
| Channel Bible | `Creator3/brand/Creator3_Channel_Bible_v1.md` | ✅ |
| Name options | `Creator3/brand/NAME_OPTIONS_v186.md` | ✅ |
| Brand kit (this doc) | `Creator3/brand/Upon_Tyne_Creator3_Brand_Kit_v1.md` | ✅ |
| Machine specs | `Creator3/brand/asset_specs.json` | ✅ |
| Channel About | `Creator3/brand/CHANNEL_ABOUT.md` | ✅ |
| Host identity | `Creator3/productions/host_identity_v1/` | ✅ v1 lock JSON |
| Raster exports | `Creator3/brand/export/` | ⬜ design export |
| Set plate | `@Set-Blueprint-Bench-001` | ⬜ future |
| Format template | `technical-explainer` in Production_Templates | ⬜ #187 |

---

*Upon Tyne Productions / Creator #3 — schematic honesty, spec-first.*