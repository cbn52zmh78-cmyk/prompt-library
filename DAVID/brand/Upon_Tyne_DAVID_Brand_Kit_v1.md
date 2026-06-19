# Upon Tyne + DAVID Brand Kit v1

**Task:** #141  
**Status:** LOCKED operator spec (design export pending)  
**Parent:** Upon Tyne Productions  
**Channel:** DAVID · The Archive  
**Date:** 2026-06-19

---

## 1. Identity hierarchy

```
Upon Tyne Productions          ← legal entity, credits, contracts, parent watermark
    └── DAVID · The Archive    ← YouTube / social channel (documentary-host format)
            └── Dead Languages slate, micro-lessons, pronunciation proofs
```

| Layer | Public name | Role | Appears on |
|-------|-------------|------|------------|
| **Parent** | Upon Tyne Productions | IP owner, production company | End-card footer, About, credits, legal |
| **Channel** | DAVID · The Archive | Host-led dead-language documentary | Banner, avatar, lower-thirds, intros |
| **Host** | DAVID (`@David-001`) | Synthetic keeper of the Archive | On-camera; not a separate consumer brand |

**Rule:** Audience-facing video branding leads with **DAVID · The Archive**. Parent credit is always present but subordinate (footer line, About, description tail).

**Locked anchors:** `DAVID/productions/host_identity_v1/david_identity_lock.json` · `@Set-Archive-001` · `@Style-Documentary-Prestige-001`

---

## 2. Locked color system

Reconciles Upon Tyne parent gold with Archive amber palette (intentional kinship — same warm gravitas family).

### Parent — Upon Tyne Productions

| Token | Hex | RGB | Use |
|-------|-----|-----|-----|
| `ut-black` | `#0D0D0D` | 13, 13, 13 | Letterpress wordmark, legal footer |
| `ut-warm-white` | `#F5F0E8` | 245, 240, 232 | Parent wordmark on dark |
| `ut-gold` | `#C9A84C` | 201, 168, 76 | Parent accent, credit line |

### Channel — DAVID · The Archive (primary UI)

| Token | Hex | RGB | Use |
|-------|-----|-----|-----|
| `archive-bg` | `#0C0E14` | 12, 14, 20 | Cards, overlays, end screens |
| `archive-title` | `#DCBE78` | 220, 190, 120 | Wordmark, titles, channel caption |
| `archive-border` | `#B4965A` | 180, 150, 90 | Closing card frame |
| `archive-body` | `#C8CDD7` | 200, 205, 215 | Subtitles, body on cards |
| `archive-cta` | `#FFB45A` | 255, 180, 90 | CTA, footer links |
| `archive-wood-dark` | `#3D2B1F` | 61, 43, 31 | Set reference, banner mood |
| `archive-wood-mid` | `#5C4033` | 92, 64, 51 | Set accent |
| `archive-parchment` | `#F5F0E6` | 245, 240, 230 | Manuscript tone, light text on bars |
| `archive-shadow` | `#2A2520` | 42, 37, 32 | Shadow neutral |

### Honesty labels (mandatory on pronunciation content)

| Label | RGBA | Hex approx | When |
|-------|------|------------|------|
| ATTESTED TEXT | 34, 110, 72, 230 | `#226E48` | Manuscript/inscription survives |
| RECONSTRUCTED PRONUNCIATION | 140, 88, 28, 230 | `#8C581C` | Inferred phonology |
| NOT ATTESTED | 160, 55, 30, 230 | `#A0371E` | Speculative line |

**Lighting canon:** Brass desk lamp **3200K** key — no magenta ambient, no teal shadows (`Set_Library_v1.json`).

---

## 3. Typography

| Role | Typeface | Fallback | Weight | Tracking |
|------|----------|----------|--------|----------|
| Parent wordmark | EB Garamond | Cormorant Garamond, Georgia | 500 | +2% |
| Channel wordmark | EB Garamond | same | 600 | DAVID +3%, · The Archive 0% |
| On-screen titles | EB Garamond | same | 600 | 0% |
| Lower-third body | Inter | DM Sans, Arial | 400 | 0% |
| IPA / transliteration | Charis SIL | Gentium Plus, Arial | 400 | 0% |
| Label chips | Inter | Arial | 600 | +4% all-caps |
| Legal footer | Inter | Arial | 400 | 0% |

**Pipeline note:** `render_longform.py` and `render_dead_language_proof.py` currently use Arial — brand export should swap to EB Garamond (titles) + Inter (body) when font files are bundled under `DAVID/brand/fonts/`.

---

## 4. Logo concepts

### 4.1 Upon Tyne Productions (parent wordmark)

**Concept:** Letterpress production slate — no icon v1.

```
UPON TYNE
PRODUCTIONS
```

| Spec | Value |
|------|-------|
| Layout | Two lines, centered or left-aligned |
| Color on dark | `ut-warm-white` + `ut-gold` rule (1px, 60% width) between lines |
| Color on light | `ut-black` |
| Min width | 120px digital |
| Clear space | 1× cap-height on all sides |
| Do not | Add AI/tech icons, gradients, or script fonts |

**Export deliverables:** `upon_tyne_wordmark_dark.svg`, `upon_tyne_wordmark_light.svg`, `upon_tyne_wordmark_dark_2x.png`

### 4.2 DAVID · The Archive (channel wordmark)

**Concept:** Scholarly broadcast lockup — DAVID dominant, Archive subordinate.

```
DAVID · The Archive
```

| Spec | Value |
|------|-------|
| DAVID | EB Garamond 600, `archive-title`, small caps optional |
| Separator | Middle dot ·, 50% title size, `archive-border` |
| The Archive | EB Garamond 400 italic or 500 regular, 72% DAVID size |
| Single-line only | Never stack for YouTube bug; stack allowed on end cards |
| Min width | 160px |
| Avatar variant | **D** monogram in brass circle on `archive-bg` (optional profile fallback) |

**Export deliverables:** `david_archive_wordmark.svg`, `david_archive_wordmark_1x.png` (1280w transparent), `david_monogram_avatar_800.png`

**Source reference for mood:** `DAVID/productions/host_identity_v1/references/archive_set_reference.jpg`

---

## 5. Per-asset specifications

### 5.1 YouTube channel banner

| Field | Spec |
|-------|------|
| **Canvas** | 2560 × 1440 px |
| **Safe zone (TV)** | Center 1546 × 423 px — all critical type/logos inside |
| **Safe zone (mobile)** | Center 640 × 360 px — wordmark + host face |
| **Composition** | Left third: soft-focus Archive shelves (`archive_set_reference.jpg` crop). Center-right: DAVID host chest-up from `david_avatar_reference.jpg`. Lower band: `DAVID · The Archive` wordmark. |
| **Tagline** | *Dead languages, actually pronounced.* — Inter 400, `archive-body`, below wordmark |
| **Parent credit** | *Upon Tyne Productions* — Inter 400, 11px, `ut-gold`, bottom-right inside safe zone |
| **Grade** | Documentary prestige — warm amber key, no magenta |
| **Export** | `DAVID/brand/export/youtube_banner_2560x1440.jpg` (sRGB, ≤6 MB) |

### 5.2 Channel avatar / profile picture

| Field | Spec |
|-------|------|
| **Canvas** | 800 × 800 px (displays at 98×98) |
| **Crop** | Chest-up host from `david_avatar_reference.jpg`, eyes upper-third |
| **Background** | Soft Archive bokeh or solid `archive-bg` |
| **Ring** | Optional 2px `archive-border` circle crop |
| **Export** | `DAVID/brand/export/channel_avatar_800.png` |

### 5.3 Intro sting (short bumper)

| Field | Spec |
|-------|------|
| **Duration** | **4.0 s** (acceptable range 3.5–5.0 s) |
| **Resolution** | 1920 × 1080 (master); 1280 × 720 (pipeline default) |
| **Audio** | Optional: single brass lamp room tone swell + 1 frame silence tail; no licensed music without clearance |
| **Picture** | 0.0–0.5 s: `archive-bg` fade in. 0.5–3.0 s: Archive wide OR host medium, lamp flares. 3.0–4.0 s: wordmark `DAVID · The Archive` center + tagline one line |
| **Source masters** | Cut from `david_intro_60s_v4_longform_v1/output/*_seamless_v1.mp4` **or** `host_identity_v1/output/david_host_test_signature_beat_v1.mp4` (signature question frames) |
| **On-screen** | `DAVID · The Archive` — matches `on_screen_caption` in identity lock |
| **Export** | `DAVID/brand/export/intro_sting_4s_1080p.mp4` (H.264, yuv420p) |
| **Full intro** | 69 s `david_intro_60s_v4` remains long-form channel trailer — sting is mandatory bumper before episodes |

### 5.4 Lower-third template (in-episode)

Matches `render_dead_language_proof.py` → `render_shot_overlay_png()`.

| Field | Spec |
|-------|------|
| **Canvas** | 1920 × 1080 (master); proof pipeline 854 × 480 |
| **Channel bug** | Top bar 16px margin: `DAVID · The Archive` — EB Garamond small, `archive-title` on `(18,20,28,210)` plate |
| **Label chips** | Below bug, y=52: rounded rect r=6, padding 10px — see honesty label colors §2 |
| **Lower-third bar** | Bottom, height 72px (110px if IPA): `(0,0,0,185)` gradient optional |
| **Primary line** | Attested/reconstructed line — `archive-parchment`, Inter 20px, max 2 lines wrap 48 chars |
| **IPA line** | `IPA {notation}` — Charis SIL 18px, `#B4D2FF`, 24px left margin |
| **Safe margin** | 24px from left/bottom |
| **Export** | `DAVID/brand/templates/lower_third_master_1920x1080.png` (RGBA transparent) |
| **Motion** | Optional 12-frame fade-in; static burn acceptable for v1 |

**Script field:** `shots[].on_screen`, `shots[].on_screen_labels`, `shots[].speech_ipa`

### 5.5 End card — closing (subscribe CTA)

Matches `render_provenance_card()` `card_type: closing`.

| Field | Spec |
|-------|------|
| **Canvas** | 1280 × 720 (pipeline); export 1920 × 1080 |
| **Background** | `archive-bg` `#0C0E14` |
| **Frame** | Rect inset 40px, 3px stroke `archive-border` |
| **Title** | Center, EB Garamond 56px → `DAVID · The Archive` or episode `brand.title` |
| **Subtitle** | Center +10px, Inter 24px, `archive-body` — e.g. *Dead languages, actually pronounced.* |
| **Footer CTA** | Center bottom −120px, Inter 20px, `archive-cta` — e.g. *Bring the dead tongues back — one attestation at a time.* |
| **Parent line** | Bottom 40px: *Upon Tyne Productions · Synthetic host · AI disclosure in description* — Inter 14px, `archive-body` at 70% opacity |
| **Duration** | 4–6 s as `provenance_card.duration_s` |
| **Export** | `DAVID/brand/templates/end_card_closing_1920x1080.png` + optional 5s MP4 |

### 5.6 End card — provenance (educational)

Matches `render_provenance_card()` `card_type: provenance` (non-closing).

| Field | Spec |
|-------|------|
| **Canvas** | 1280 × 720 |
| **Banner** | Top chip: `RECONSTRUCTED — NOT ATTESTED` or `ATTESTED TEXT · RECONSTRUCTED PRONUNCIATION` — fill `#502D14`, text `#FFC878` |
| **Title** | `DAVID · PROVENANCE` — EB Garamond 40px `archive-title` |
| **Body lines** | Citation, sources, brain scrape — Inter 20px, wrap 78 chars, `archive-body` |
| **Footer** | Source URL or CC-BY-SA note — `archive-cta` |
| **Duration** | 6–7 s default |
| **Export** | `DAVID/brand/templates/end_card_provenance_1920x1080.png` |

### 5.7 Parent end-slate (reusable)

For any Upon Tyne property — thin footer slate.

| Field | Spec |
|-------|------|
| **Canvas** | 1920 × 1080 or 1920 × 200 strip |
| **Content** | `Upon Tyne Productions` wordmark + *Directed. Not generated.* (parent tagline — lock on Director approval) |
| **Placement** | Last 2 s of any deliverable OR burned into closing card parent line |
| **Export** | `DAVID/brand/templates/parent_slate_upon_tyne.png` |

---

## 6. Channel About (YouTube)

Full paste-ready copy: `DAVID/brand/CHANNEL_ABOUT.md`

**Short description (1000 char limit):**

> DAVID · The Archive — dead languages, actually pronounced.
>
> I am DAVID, keeper of the Archive. Every episode asks one question: *What did they actually say — and how do we prove it?*
>
> We rebuild sound corpus-first — from inscriptions, manuscripts, meter, and grammarians who described the accent. Where evidence is firm, we say **attested**. Where we infer, we say **reconstructed** — on screen and in the delivery.
>
> Latin, Greek, Old English, Norse, Gothic, Sumerian, and the tongues time tried to silence.
>
> Synthetic host · Educational content · CC-BY-SA where noted in description
>
> Produced by **Upon Tyne Productions**

---

## 7. Voice, taglines, and copy locks

| Use | Copy | Lock |
|-----|------|------|
| Channel title | DAVID · The Archive | LOCKED |
| Subtitle | Dead languages, actually pronounced. | LOCKED |
| CTA | Bring the dead tongues back — one attestation at a time. DAVID. | LOCKED |
| Signature beat | What did they actually say? … And how do we prove it? | LOCKED (`david_identity_lock.json`) |
| Cold open | I am DAVID. I bring dead languages back — not as words on a page, but as sound you can hear. | Intro canon |
| Parent tagline (draft) | Directed. Not generated. | Upon Tyne — pending Director lock |
| Playlist | DAVID · Dead Languages | LOCKED |
| AI disclosure | Synthetic host · Educational demonstration · See description for attribution | Legal |

---

## 8. File manifest (export checklist)

| Asset | Path (target) | Status |
|-------|---------------|--------|
| Brand kit (this doc) | `DAVID/brand/Upon_Tyne_DAVID_Brand_Kit_v1.md` | ✅ |
| Machine specs | `DAVID/brand/asset_specs.json` | ✅ |
| Channel About | `DAVID/brand/CHANNEL_ABOUT.md` | ✅ |
| Host reference | `DAVID/productions/host_identity_v1/references/david_avatar_reference.jpg` | ✅ exists |
| Set reference | `DAVID/productions/host_identity_v1/references/archive_set_reference.jpg` | ✅ exists |
| Intro master (69s) | `DAVID/productions/david_intro_60s_v4_longform_v1/output/` | ✅ exists |
| Signature sting source | `DAVID/productions/host_identity_v1/output/david_host_test_signature_beat_v1.mp4` | ✅ exists |
| Banner export | `DAVID/brand/export/youtube_banner_2560x1440.jpg` | ⬜ design export |
| Avatar export | `DAVID/brand/export/channel_avatar_800.png` | ⬜ crop export |
| Intro sting 4s | `DAVID/brand/export/intro_sting_4s_1080p.mp4` | ⬜ edit export |
| Lower-third PNG | `DAVID/brand/templates/lower_third_master_1920x1080.png` | ⬜ design export |
| End cards | `DAVID/brand/templates/end_card_*.png` | ⬜ design export |
| Wordmarks SVG | `DAVID/brand/export/*.svg` | ⬜ design export |
| Brand fonts | `DAVID/brand/fonts/` | ⬜ license bundle |

---

## 9. Pipeline integration

| System | Field / function | Brand tie-in |
|--------|------------------|--------------|
| `production_intake.py` | `brand.title`, `brand.subtitle`, `brand.cta` | Closing card copy |
| `render_longform.py` | `render_provenance_card()` | End card colors §5.5–5.6 |
| `render_longform.py` | `shots[].on_screen` | Lower-third primary line |
| `render_dead_language_proof.py` | `render_shot_overlay_png()` | Label chips + IPA bar |
| `david_identity_lock.json` | `on_screen_caption` | Channel bug text |
| Legal Gate | AI disclosure | Footer + About |

---

## 10. Version history

| Version | Date | Change |
|---------|------|--------|
| 1.0 | 2026-06-19 | #141 — Parent + DAVID kit, per-asset specs, About, palette reconciliation |

*Upon Tyne Productions / DAVID · The Archive — directed, corpus-first, legally gated.*