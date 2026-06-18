# DAVID Post 1 — PIE Hybrid Host Brief (v1)

**Issue #70 · Format proof #2**  
**2026-06-18 · Owner: T2 (DAVID lane)**  
**Depends on:** Issue #69 host identity lock (`productions/host_identity_v1/david_identity_lock.json`)

**Pipeline:** locked DAVID avatar → hybrid host script → Grok Imagine 1.5 lip-sync shots → code-rendered provenance card → ffmpeg concat.

> **Production gate:** PIE has **zero attested texts**. Every on-screen and spoken claim must carry **RECONSTRUCTED — NOT ATTESTED**. Asterisk on every PIE form (scholarly convention).

---

## Why PIE for format proof #2

Latin/Gothic proofs (#41) validated the **language-native avatar** micro-lesson. Post 1 validates the **hybrid host** arc from `DAVID_Character_and_Host_Video_v1.md`:

1. DAVID hosts in the Archive → sets up the language
2. DAVID delivers the reconstructed line (no separate PIE-world avatar — there is no attested world)
3. DAVID explains the comparative method
4. Provenance card with heavy reconstruction labels

PIE is the boldest honesty test: if the brand survives this clip, every attested language is easier.

---

## Post metadata

| Field | Value |
|-------|-------|
| **Post #** | 1 |
| **Slug** | `proto-indo-european` |
| **Channel title** | *The Mother Tongue of English — Reconstructed* |
| **TikTok hook** | "No human ever spoke this natively. Hear it anyway." |
| **Text label** | **RECONSTRUCTED — NOT ATTESTED** |
| **Pronunciation label** | **RECONSTRUCTED pronunciation** |
| **Duration** | ~49s (42s host + 7s provenance card) |
| **Aspect** | 16:9 (Shorts/TikTok: center-crop to 9:16 in publish step) |

---

## Reconstructed excerpt

| Field | Value |
|-------|-------|
| **Form** | *h₂éwis, h₁éḱwōs h₁éḱontes |
| **Source** | Schleicher's Fable (*The Sheep and the Horses*), opening |
| **Translation** | "The sheep and the horses (were) going…" |
| **Draft IPA** | `[ˈh₂é.wis ˈh₁é.kʷoːs ˈh₁é.kʷon.tes]` |
| **Citation** | August Schleicher, *Compendium der vergleichenden Grammatik der indogermanischen Sprachen* (1861/1862); modern recension per [Wikipedia: Schleicher's fable](https://en.wikipedia.org/wiki/Schleicher%27s_fable) (CC BY-SA 3.0) |
| **Brain scrape** | `languages/reconstructed/proto-indo-european/research/brain/latest_scrape.json` — Wiktionary holds **language name IPA only**, not excerpt IPA |

---

## Shot plan (~49s)

### 1 · 0–6s — DAVID cold open (Archive)

**Speech:**
> Before Latin. Before Greek. Before anything was written down — there was one language. No one ever recorded it. And yet we can rebuild it… from its children.

**On-screen:** `DAVID · The Archive · 🔶 RECONSTRUCTED`

---

### 2 · 6–11s — Signature beat

**Speech:**
> What did they actually say? … And how do we prove it?

**On-screen:** `What did they actually say?`

---

### 3 · 11–26s — Reconstructed PIE line (heavy labels)

DAVID speaks the PIE opener slowly — **not** claiming it is a recording.

**Speech (PIE):** `h₂éwis, h₁éḱwōs h₁éḱontes`

**On-screen:**
```
*h₂éwis, h₁éḱwōs h₁éḱontes
[ˈh₂é.wis ˈh₁é.kʷoːs ˈh₁é.kʷon.tes]
RECONSTRUCTED — NOT ATTESTED
```

**Labels (mandatory):** RECONSTRUCTED text · RECONSTRUCTED pronunciation · NOT ATTESTED

---

### 4 · 26–36s — Comparative method explainer

**Speech:**
> We compare its daughters — Latin, Sanskrit, Old English — and work backward to the sound that *must* have stood behind them all. That's the comparative method. It's reconstruction, not a recording — and we'll always tell you which is which.

**On-screen:** `Comparative method · Latin ovis ← *h₂éwis · Sanskrit ávi- · English ewe`

**Label:** RECONSTRUCTED inference

---

### 5 · 36–42s — Tagline

**Speech:**
> Bring the dead tongues back — one attestation at a time. DAVID.

---

### 6 · 42–49s — Provenance card (code-rendered)

Orange **RECONSTRUCTED — NOT ATTESTED** banner. Full citation block, IPA, brain scrape path, CC BY-SA sources.

---

## Render

```bash
# Prerequisite: locked host identity (T1 / Issue #69)
python DAVID/scripts/render_host_identity.py

# Post 1 hybrid render (Issue #70)
python DAVID/scripts/render_post01_pie.py

# Script JSON only (no API calls)
python DAVID/scripts/render_post01_pie.py --script-only
```

**Outputs:**
- `productions/post_01_pie_hybrid_v1/post01_pie_script_final.json`
- `productions/post_01_pie_hybrid_v1/post01_pie_imagine_pack.json`
- `productions/post_01_pie_hybrid_v1/output/david_post01_pie_hybrid_v1.mp4`
- `productions/post_01_pie_hybrid_v1/qa_report.json`

---

## Publish copy (pin-ready)

```
DAVID · Dead languages, actually pronounced.
TEXT: RECONSTRUCTED — Schleicher, Compendium (1861/62); Schleicher's Fable
https://en.wikipedia.org/wiki/Schleicher%27s_fable
PRONUNCIATION: RECONSTRUCTED late PIE (laryngeal theory); moderate confidence
Corpus: languages/reconstructed/proto-indo-european/research/brain/latest_scrape.json
Phonology refs: Wikipedia / Wiktionary (CC BY-SA 3.0), Wikidata (CC0)
#deadlanguage #linguistics #ProtoIndoEuropean #PIE #history #DAVID
```

---

## Guardrails

- Reuse **locked** `david_avatar_reference.jpg` — do not regenerate host face per episode.
- Synthetic only; no real-person likeness.
- Never drop RECONSTRUCTED labels on the PIE shot — this is the brand honesty moat.
- QA lip-sync against IPA before publish; re-render if Grok Imagine drifts.