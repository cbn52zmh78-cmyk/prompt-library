# Observable — Channel Setup Kit  (DRAFT · NO UPLOAD)

> **DRAFT — operator runbook only. Nothing in this kit has been uploaded or published.**
> One-pass checklist to stand up the YouTube channel before the first video goes live.
> Source of truth: `asset_specs.json` · `CHANNEL_ABOUT.md` · `Upon_Tyne_Observable_Brand_Kit_v1.md`

---

## 0. Status at a glance

| Item | State |
|------|-------|
| Channel identity (name/colors/voice) | ✅ Locked (`asset_specs.json` #180) |
| About / descriptions | ✅ Drafted (`CHANNEL_ABOUT.md`) |
| Avatar (800×800) | ✅ Rendered — `brand/export/channel_avatar_800.png` |
| Banner (2560×1440) | ✅ Rendered — `brand/export/youtube_banner_2560x1440.jpg` |
| Wordmark + monogram | ✅ Rendered — `brand/export/observable_wordmark*.{svg,png}`, `observable_monogram_O_800.png` |
| Lower-third / end-card templates | ✅ Rendered — `brand/templates/` |
| Intro sting (4s) | ⏳ **QUEUED OBSERVATORY** — `STUDIO/Producers_Office/OBSERVATORY/handoffs/OBSERVABLE_intro_sting_4s_handoff_v186.json` |
| First episode package | ⏳ In production (astro/chem slate; e.g. star lifecycle #184) — no upload_kit SHIP-cleared yet |
| Live links / business email | ⛔ TBD (placeholders in About) |

**Channel art is ready to set.** Remaining blockers are optional (intro sting) or per-episode.

---

## 1. Channel identity

| Field | Value |
|-------|-------|
| Channel name | **Observable** |
| Legal / parent | Upon Tyne Science (Upon Tyne Productions) |
| Proposed handle | `@ObservableScience` *(verify availability at setup)* |
| Slug | `observable-science` |
| Tagline / subtitle | Evidence before wonder. |
| Host | Julian Cross (`Julian-001`, synthetic presenter) |
| Category | Education / Science & Technology |
| Default language | English (en) |
| Country | *(set at creation)* |

---

## 2. Channel art (upload in YouTube Studio → Customisation → Branding)

| Slot | Spec | File | Status |
|------|------|------|--------|
| Avatar | 800×800 PNG | `brand/export/channel_avatar_800.png` | ✅ ready |
| Banner | 2560×1440 JPG, TV-safe 1546×423 | `brand/export/youtube_banner_2560x1440.jpg` | ✅ ready |
| Video watermark | monogram | `brand/export/observable_monogram_O_800.png` | ✅ ready |
| Wordmark (overlays) | SVG + 1× PNG | `brand/export/observable_wordmark.svg` | ✅ ready |

Brand palette: bg `#121820` · surface `#1A2430` · title `#E8EEF2` · accent `#2A7B9E` / bright `#4DA8C7` · CTA `#5EC4E8`.
Type: IBM Plex Sans 600 (wordmark) · Inter 400 (body) · IBM Plex Mono 400 (data).
Label chips: OBSERVED `#1E8A6E` · SIMULATION `#2A5F9E` · MODEL `#8A6B2A` · NOT TO SCALE `#5A6470`.

---

## 3. About tab

Paste from `CHANNEL_ABOUT.md`:
- **Channel description (long)** → About → Description
- **Short description (≤1000 chars)** → short bio fields
- Business email: ⛔ insert when live
- Links: Website / Upon Tyne Productions — ⛔ TBD

Required disclosure (About + every video): *Julian Cross (Julian-001) is a synthetic science presenter (AI-generated performer). No real-person likeness. Educational content only — not medical or legal advice.*

---

## 4. Playlists to create

| Playlist | Contents |
|----------|----------|
| Observable · Astrophysics | Black holes, stars, galaxies |
| Observable · Chemistry & Materials | Bonds, crystals, reactions |
| Observable · Physics | Fields, waves, particles |
| Observable · Molecules of Life | DNA, proteins, immunology |
| Observable · How We Know | Method, viz literacy, sources |

---

## 5. Channel-level upload defaults (Settings → Upload defaults)

- Category: **Education** (Science & Technology where applicable)
- Title/description language: **English**
- License: **Standard YouTube License** (sources cited per video; adjust per asset)
- "Altered or synthetic content" disclosure: **Yes** (AI-generated performer)
- Audience: **Not made for kids** (channel-wide)
- Comments: hold potentially inappropriate for review (recommended)
- Default description footer: paste the disclosure block from `CHANNEL_ABOUT.md` template

---

## 6. Channel keywords (Settings → Channel → Basic info)

`science, physics, chemistry, biology, astrophysics, cosmology, black holes, molecules, DNA, sourced science, data visualization, simulation vs observation, science explainer, Observable, Julian Cross, Upon Tyne Science`

---

## 7. First upload (separate, gated)

No episode is SHIP-cleared yet — slate in production under `Observable/productions/` and the astro/science batches.
When an episode's `upload_kit/` is gated GREEN + QA-pass, follow its own `CHECKLIST.md`. Do **not** upload from this kit.

---

## 8. Open TODOs before "go live"

- [ ] OBSERVATORY: render intro sting per `STUDIO/Producers_Office/OBSERVATORY/handoffs/OBSERVABLE_intro_sting_4s_handoff_v186.json` → `brand/export/intro_sting_4s_1080p.mp4`
- [ ] Confirm handle `@ObservableScience` available; claim it
- [ ] Insert business email + live links in About
- [ ] Create the 5 playlists
- [ ] Set channel-level upload defaults + synthetic-content disclosure
- [ ] Verify channel (phone) to unlock custom thumbnail + >15min uploads
- [ ] Gate + package first episode → its own upload_kit
