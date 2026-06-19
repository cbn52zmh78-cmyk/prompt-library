# DAVID · The Archive — Channel Setup Kit  (DRAFT · NO UPLOAD)

> **DRAFT — operator runbook only. Nothing in this kit has been uploaded or published.**
> One-pass checklist to stand up the YouTube channel before the first video goes live.
> Source of truth: `asset_specs.json` · `CHANNEL_ABOUT.md` · `Upon_Tyne_DAVID_Brand_Kit_v1.md`

---

## 0. Status at a glance

| Item | State |
|------|-------|
| Channel identity (name/colors/voice) | ✅ Locked (`asset_specs.json` #141) |
| About / descriptions | ✅ Drafted (`CHANNEL_ABOUT.md`) |
| Visual assets (banner, avatar, wordmark) | ⛔ **NOT RENDERED** — `brand/export/` empty (only `.gitkeep`) |
| Lower-third / end-card templates | ⛔ **NOT RENDERED** — `brand/templates/` empty |
| First episode package | ✅ SHIP-cleared — `productions/david_latin_corpus_v1_longform_v1/upload_kit/` |
| Live links / business email | ⛔ TBD (placeholders in About) |

**Blocking before channel art can be set:** render `youtube_banner_2560x1440.jpg` + `channel_avatar_800.png` per `asset_specs.json`.

---

## 1. Channel identity

| Field | Value |
|-------|-------|
| Channel name | **DAVID · The Archive** |
| Proposed handle | `@DAVIDTheArchive` *(verify availability at setup)* |
| Slug | `david-the-archive` |
| Tagline / subtitle | Dead languages, actually pronounced. |
| Owner / parent | Upon Tyne Productions |
| Category | Education |
| Default language | English (en) |
| Country | *(set at creation)* |

---

## 2. Channel art (upload in YouTube Studio → Customisation → Branding)

| Slot | Spec | File | Status |
|------|------|------|--------|
| Avatar | 800×800 PNG | `brand/export/channel_avatar_800.png` | ⛔ render |
| Banner | 2560×1440 JPG, TV-safe 1546×423 | `brand/export/youtube_banner_2560x1440.jpg` | ⛔ render |
| Video watermark | use avatar / monogram | `brand/export/` | ⛔ render |
| Wordmark (overlays) | SVG + 1× PNG | `brand/export/david_archive_wordmark.svg` | ⛔ render |

Brand palette (banner/overlays): bg `#0C0E14` · title `#DCBE78` · border `#B4965A` · body `#C8CDD7` · CTA `#FFB45A`.
Type: EB Garamond 600 (wordmark) · Inter 400 (body) · Charis SIL 400 (IPA).

---

## 3. About tab

Paste from `CHANNEL_ABOUT.md`:
- **Channel description (long)** → About → Description
- **Short description (≤1000 chars)** → use where a short bio is required
- Business email: ⛔ insert when live
- Links: Website / Upon Tyne Productions — ⛔ TBD

Required disclosure (must remain in About + every video): *DAVID is a synthetic documentary host (AI-generated performer). No real-person likeness. Educational content only.*

---

## 4. Playlists to create

| Playlist | Contents |
|----------|----------|
| DAVID · Dead Languages | Main episodic slate (Latin ep is first) |
| DAVID · Attested vs Reconstructed | Honesty-method explainers |
| DAVID · Intro & Archive | Channel intro, behind-the-method |

---

## 5. Channel-level upload defaults (Settings → Upload defaults)

- Category: **Education**
- Title/description language: **English**
- License: **Creative Commons – Attribution (CC-BY-SA where noted)**
- "Altered or synthetic content" disclosure: **Yes** (AI-generated performer)
- Audience: **Not made for kids** (channel-wide)
- Comments: hold potentially inappropriate for review (recommended)
- Default description footer: paste the disclosure block from `CHANNEL_ABOUT.md` template

---

## 6. Channel keywords (Settings → Channel → Basic info)

`dead languages, Latin, Ancient Greek, Old English, Old Norse, Gothic, Sumerian, historical linguistics, pronunciation, reconstructed pronunciation, attested, philology, manuscripts, documentary, DAVID The Archive, Upon Tyne Productions`

---

## 7. First upload (separate, gated)

First episode is packaged and SHIP-cleared but **not uploaded**:
`DAVID/productions/david_latin_corpus_v1_longform_v1/upload_kit/` — follow its `CHECKLIST.md`.
Title: *Why Latin Never Really Died | DAVID · The Archive*.

---

## 8. Open TODOs before "go live"

- [ ] Render banner + avatar + wordmark (`asset_specs.json` → `brand/export/`)
- [ ] Render lower-third + end-card templates (`brand/templates/`)
- [ ] Confirm handle `@DAVIDTheArchive` available; claim it
- [ ] Insert business email + live links in About
- [ ] Create the 3 playlists
- [ ] Set channel-level upload defaults + synthetic-content disclosure
- [ ] Verify channel (phone) to unlock custom thumbnail + >15min uploads
