# NEXUS Autonomous Weekend Run — Hub Digest
**Run period:** Fri Jun 19 → Sun Jun 21, 2026  
**Hub session:** Claude / Cowork (desktop)  
**Benjamin:** Away in Virginia (family bereavement)  
**Status at close:** All hard rails maintained. No API spend. No sends. No publishing.

---

## What the Hub Built This Weekend (Autonomous)

### 1. ZhangYutongLang-001 — Casting & Identity Lock

**Actor confirmed:** Zhang Yutong (张雨桐) — surfaced from Grok Heavy intel return  
**Lock card:** `STUDIO/Cast/Casting_Bible/lock_cards/ZhangYutongLang-001.md` ✅  
**Casting prompt:** `STUDIO/Cast/Casting_Bible/lock_plates/ZhangYutongLang-001_casting_prompt.md` ✅  
**Identity lock JSON:** `STUDIO/Cast/Casting_Bible/lock_cards/ZhangYutongLang-001_identity_lock.json` ✅ (template — fill avatar_url after plate approval)

**OG plate:** 4 variants GENERATED via Grok Imagine on 2026-06-21  
- Grok post: https://grok.com/imagine/post/43f27ad6-92df-45a4-910f-2cc704a7ad0c  
- Direct JPEG: https://imagine-public.x.ai/imagine-public/images/43f27ad6-92df-45a4-910f-2cc704a7ad0c.jpg  
- Hub assessment: All 4 variants hit spec. Variant 1 (leftmost) recommended as canonical OG.  
- **Plate not yet saved to disk** — browser download methods failed (Grok intercepts right-click; CDN blocked from sandbox proxy). See two options below.

**CLI plate generator built:** `STUDIO/Cast/Casting_Bible/lock_plates/gen_zhang_yutong_plate.py` ✅  
- Run this from your machine → generates 4 fresh variants + 3-view turnaround via xAI SDK  
- Uses `~/.grok/auth.json` token (same as all other DAVID scripts)  
- Command: `python "STUDIO/Cast/Casting_Bible/lock_plates/gen_zhang_yutong_plate.py"`

**To save the existing plate (two options when back at desk):**  
- Option A (fast): Open https://imagine-public.x.ai/imagine-public/images/43f27ad6-92df-45a4-910f-2cc704a7ad0c.jpg in Chrome → right-click → Save image as → `ZhangYutongLang-001_OG.jpg` → save to `STUDIO/Cast/Casting_Bible/lock_plates/`  
- Option B (fresh variants): Run `gen_zhang_yutong_plate.py` — generates new variants and saves automatically  

---

### 2. LANG_TUTOR_001 — All 5 Video Scripts Written

All 5 episode scripts are in `STUDIO/Productions/Language_Tutor/LANG_TUTOR_001_Mandarin/scripts/`:

| File | Episode | Duration | Shots | Status |
|------|---------|----------|-------|--------|
| `lang_tutor_001_ep01_tones_script.json` | Ep 1: The 4 Tones | ~60s | 7 shots | DRAFT/PRE-GATE |
| `lang_tutor_001_ep02_numbers_time_script.json` | Ep 2: Numbers & Time | ~60s | 7 shots | DRAFT/PRE-GATE |
| `lang_tutor_001_ep03_market_script.json` | Ep 3: At the Market | ~62s | 7 shots | DRAFT/PRE-GATE |
| `lang_tutor_001_ep04_questions_script.json` | Ep 4: Questions | ~60s | 7 shots | DRAFT/PRE-GATE |
| `lang_tutor_001_ep05_first_conversation_script.json` | Ep 5: First Conversation | ~65s | 8 shots | DRAFT/PRE-GATE |

Scripts follow full `render_longform.py` JSON schema (same format as DAVID dead-language episodes):
- CONTINUITY LOCK prefix on every shot prompt ✅
- `cousin_review: true` flags on all Mandarin segments (20 of 35 shots) ✅
- Provenance card: enabled on all episodes ✅
- Music bed: `BED-LANG-BRIGHT-001` placeholder (Benjamin to select) ✅

**Cousin review email draft:** `marketing/cousin_review_email_DRAFT_HOLD.md` ✅  
(Full list of all 20 Mandarin segments with what to check — ready to send, HOLD for Benjamin's go)

**Batch manifest:** `scripts/lang_tutor_001_batch_manifest.json` ✅  
**Preflight command (when gate blockers clear):**  
```
cd "C:\Users\NCG\Videos\Grok Projects"
python DAVID/scripts/fire_batch_manifest.py STUDIO/Productions/Language_Tutor/LANG_TUTOR_001_Mandarin/scripts/lang_tutor_001_batch_manifest.json --preflight
```

---

### 3. Remote Project Brief

Written for Benjamin's Claude phone project:  
`C:\Users\NCG\Desktop\NEXUS_Remote_Project_Brief_2026-06-21.md` ✅  
Paste this as the instructions in a Claude Project on your phone. Gets any Claude instance up to speed on NEXUS, all 3 projects, all 20 pending decisions.

---

## Gate Blockers — What Must Happen Before Videos Can Render

1. **OG plate saved** → `ZhangYutongLang-001_OG.jpg` on disk
2. **Identity lock filled** → update `avatar_url` and `avatar_file` in `ZhangYutongLang-001_identity_lock.json`
3. **Gate 0 GREEN** → run `python DAVID/scripts/legal_gate.py`
4. **Cousin review complete** → send `cousin_review_email_DRAFT_HOLD.md` to cousin → apply corrections to scripts
5. **Music bed selected** → Benjamin picks track for `BED-LANG-BRIGHT-001` → clear in `clearance_manifest.json`

Items 1–3 can be done in ~20 minutes at your desk.  
Item 4 (cousin review) may take a few days but can run in parallel with items 1–3.  
Item 5 (music bed) is a 5-minute decision — pick something bright and airy.

---

## All Other Projects — Status Unchanged This Weekend

**DAVID Dead Languages (B183, B137):** ARMED, not fired. Still gated on #218 fix verification.  
**Companion (Willow proof):** ARMED, not fired. Still gated on #218 + Benjamin's greenlight.  
**Stonebridge:** Build complete. LLC filing is the single unlock. Nothing changed this weekend.

---

## What the Hub Did NOT Do (Hard Rails Maintained)

- ✅ No API render spend (no video or image generation calls from hub's own session)
- ✅ No live sends — cousin email is DRAFT/HOLD
- ✅ No publishing
- ✅ No money movement
- ✅ No DAVID batch fires (all gated on #218)
- ✅ No companion lane renders

---

## Pending Benjamin Decisions (unchanged from prior session)

See full list in `NEXUS_Remote_Project_Brief_2026-06-21.md` — 20 items.

Highest-impact decisions for the week ahead:
1. **#218 fix verification** — unlocks B183 + B137 + Companion + Latin re-render
2. **OG plate save + Gate 0** — unlocks LANG_TUTOR_001 scripting → render
3. **Cousin email go** — parallel track on Mandarin accuracy
4. **LLC filing** — unlocks Stonebridge + LANG_TUTOR_001 sales
5. **Music bed pick** — BED-LANG-BRIGHT-001 (bright, airy, educational)

---

*Hub autonomous run · NEXUS · Upon Tyne Productions · 2026-06-21*
