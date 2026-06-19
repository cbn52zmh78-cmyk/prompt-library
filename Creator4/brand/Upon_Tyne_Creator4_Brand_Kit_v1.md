# Upon Tyne + Creator #4 Brand Kit v1

**Task:** #206 · **Working name:** ClearDesk · **Status:** LOCKED v1 (doc only — no render)  
**Parent:** Upon Tyne Productions · **Legal lane:** Upon Tyne Operations · **Date:** 2026-06-19

---

## 1. Locked copy (draft — pending name lock)

| Use | Copy |
|-----|------|
| Channel title | **ClearDesk** (TBD — see `NAME_OPTIONS.md`) |
| Legal lane | Upon Tyne Operations |
| Subtitle | Compliance, explained clearly. |
| CTA | Follow ClearDesk — one process at a time. |
| Signature beat | What does this requirement mean — and what would good records look like? |
| Legal line (mandatory) | **Educational content only — not legal, tax, or professional advice.** |
| AI disclosure | Synthetic presenter · Educational content · Sources in description |
| Parent credit | Upon Tyne Productions |

---

## 2. Color system — clean professional

Warm-neutral office trust — deliberate contrast with Observable clinical cool and Blueprint navy schematic.

### Parent — Upon Tyne (reuse)

`ut-black` `#0D0D0D` · `ut-warm-white` `#F5F0E8` · `ut-gold` `#C9A84C`

### Channel — ClearDesk (primary UI)

| Token | Hex | Use |
|-------|-----|-----|
| `cd-bg` | `#F7F5F2` | Cards, light end screens |
| `cd-surface` | `#FFFFFF` | Lower-thirds, document plates |
| `cd-title` | `#1E3A5F` | Wordmark, titles — navy trust |
| `cd-accent` | `#2A7B7B` | Links, rules — teal (not Observable cyan) |
| `cd-accent-soft` | `#5A9E9E` | Hover, secondary callouts |
| `cd-body` | `#4A5568` | Subtitles, body |
| `cd-cta` | `#1E6B6B` | CTA text |
| `cd-border` | `#D8DEE6` | Card rules, table lines |
| `cd-disclaimer` | `#6B7280` | Legal footer — always visible |

### Label chips

| Label | Hex | When |
|-------|-----|------|
| PUBLIC SOURCE | `#2E6B5A` | Cited agency / open guidance |
| PROCESS DIAGRAM | `#2A7B7B` | Workflow illustration |
| ILLUSTRATIVE | `#8A6B2A` | Example layouts |
| NOT JURISDICTION-SPECIFIC | `#5A6470` | General literacy episodes |
| NOT LEGAL ADVICE | `#8B3A3A` | **Mandatory** on regulatory-touch episodes |

---

## 3. Typography

| Role | Typeface | Weight |
|------|----------|--------|
| Wordmark | IBM Plex Sans | 600 |
| Titles | IBM Plex Sans | 600 |
| Body | Inter | 400 |
| Citations / record IDs | IBM Plex Mono | 400 |
| Disclaimer footer | Inter | 400 (11–12px) |

---

## 4. Logo concept

**Wordmark:** `ClearDesk` — Plex Sans 600, `cd-title`, optional soft rule underline in `cd-border` (desk surface metaphor).

**Subline:** *Compliance, explained clearly.* — Inter 400, `cd-body`

**Monogram fallback:** `CD` ligature on `cd-surface` with `cd-accent` rule — avatar if host crop unavailable.

**Do not:** Gavel clipart, courthouse columns, Observable O-aperture, DAVID amber, Blueprint cyan grid.

**Exports:** deferred (doc-only task) → `Creator4/brand/export/`

---

## 5. Style spec — `@Style-Professional-Clean-001`

| Field | Lock |
|-------|------|
| Grade | Warm-neutral white balance, accurate skin, low saturation, **no** film grain |
| Lighting | Soft 5200K wrap — even face, minimal shadow, studio cyclorama |
| Forbidden | Magenta cast, noir low-key, documentary Archive warmth, blueprint schematic overlays |
| Default set | `@Set-Studio-Interior-001` |
| End guard | Gesture peak on CTA — never dead frame |

*Register in `Style_Library_v1.json` on format activation — spec locked here for #4.*

---

## 6. Asset specifications (targets — not rendered)

### Banner (2560×1440)

Left: `cd-bg` with subtle document-line texture. Right: Serena chest-up, professional wardrobe. Center-bottom: wordmark + subtitle. Disclaimer micro-line in footer. Parent credit bottom-right `ut-gold`.

### Avatar (800×800)

Serena front-panel crop, `cd-surface` or soft cyclorama, optional `cd-accent` ring.

### Lower-third

Channel bug `ClearDesk` · topic line · `compliance_subject` citation mono · disclaimer chip on regulatory episodes.

---

## 7. Format binding

| Field | Value |
|-------|-------|
| `format_id` | `explainer-ad` |
| `default_set` | `@Set-Studio-Interior-001` |
| `default_style` | `@Style-Professional-Clean-001` |
| `identity_anchor` | `@Serena-001` |
| `target_seconds` | 30–54 |

---

## 8. File manifest

| Asset | Path | Status |
|-------|------|--------|
| Channel Bible | `Creator4/brand/Creator4_Channel_Bible_v1.md` | ✅ |
| Name options (3) | `Creator4/brand/NAME_OPTIONS.md` | ✅ |
| Brand kit (this doc) | `Creator4/brand/Upon_Tyne_Creator4_Brand_Kit_v1.md` | ✅ |
| Machine specs | `Creator4/brand/asset_specs.json` | ✅ |
| Channel About | `Creator4/brand/CHANNEL_ABOUT.md` | ✅ |
| Host identity | `Creator4/productions/host_identity_v1/` | ✅ |
| Raster exports | `Creator4/brand/export/` | ⬜ deferred |

---

*Upon Tyne Productions / Creator #4 — clear records, clear boundaries.*