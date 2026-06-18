# DAVID — Sample Video Briefs: Latin & Gothic (v1)

**2026-06-18 · Owner: NEXUS (DAVID lane) · Pipeline:** corpus → attested text → IPA → Grok Imagine 1.5 (lip-synced avatar) → QA against attestation → publish.

**Two first-proofs, by design:**
- **Latin = reach play** (huge built-in curiosity, classics/seminary audience, high-confidence pronunciation).
- **Gothic = virality play** ("hear a dead Germanic language" — uncontested, inherently shareable).

> **Production gate (STD honesty):** the IPA below is a **draft** for scripting. Before render, reconcile each line against the language's `research/brain/latest_scrape.json` IPA fields and label every clip **attested text / [reconstructed | attested] pronunciation** on-screen. Never overclaim certainty on dead-language phonetics.

---

## BRIEF 1 — LATIN (reach)

**Slug:** `classical-latin` · **Status:** dead (attested) · **Revival tier:** active
**Text source (public domain):** Virgil, *Aeneid* 1.1–1.7 (opening). Attested manuscript tradition; text itself is not in doubt.
**Pronunciation model:** scholarly **reconstructed Classical** pronunciation (high confidence — restituta), labeled as reconstructed-scholarship, NOT Ecclesiastical.

### Chosen line (clip 1 — the hook)
> **Arma virumque canō, Trōiae quī prīmus ab ōrīs**
> *"I sing of arms and the man, who first from the shores of Troy…"*

**Draft IPA (Classical, verify vs brain scrape):**
`[ˈar.ma wɪˈrũːk.we ˈka.noː ˈtroː.jae kʷiː ˈpriː.mʊs ab ˈoː.riːs]`

Key teaching beats (on-screen captions): `v = [w]` · `c = [k]` always · vowel **length** is phonemic (macrons) · `ae = [ae̯]` diphthong.

### 35–45s shot plan (Grok Imagine 1.5)
1. **0–4s** — Cold open: avatar (neutral classical bust / scholar, synthetic likeness only) speaks the line slowly, lip-synced. Caption: *Latin · Virgil, Aeneid (19 BCE)*.
2. **4–10s** — Replay at natural pace; IPA appears under the words, syllable-highlighted.
3. **10–28s** — Micro-lesson: 3 caption cards (v→w, c→k, vowel length) each with the avatar voicing a minimal contrast.
4. **28–38s** — Avatar delivers the full line once more, confident pace.
5. **38–45s** — Provenance card (below) + soft CTA: *"More dead languages, actually pronounced — DAVID."*

### Provenance card (the moat — always shown)
- **Text:** Virgil, *Aeneid* 1.1, public domain. Attested.
- **Pronunciation:** reconstructed Classical (restituta), scholarly consensus; high confidence.
- **Sources:** Wikipedia / Wiktionary (CC BY-SA), Wikidata (CC0), retrieved 2026-06-18.

---

## BRIEF 2 — GOTHIC (virality)

**Slug:** `gothic` · **Status:** extinct (attested) · **Revival tier:** high
**Text source (public domain):** Wulfila's Gothic Bible, *Matthew 6:9* (the Lord's Prayer opening), Codex Argenteus. Attested in the manuscript.
**Pronunciation model:** **reconstructed** from Wulfila's purpose-built alphabet — good evidence but real uncertainty. Label clearly as reconstructed.

### Chosen line (clip 1 — the hook)
> **Atta unsar þu in himinam, weihnai namo þein**
> *"Our Father who is in heaven, hallowed be thy name."*

**Draft IPA (reconstructed, verify vs brain scrape):**
`[ˈat.ta ˈun.sar θuː in ˈhi.mi.nam ˈwiːh.nɛː ˈna.moː θiːn]`

Key teaching beats (captions): `þ = [θ]` (English "th") · `ai` here ≈ `[ɛː]` (Wulfila convention) · `ei = [iː]` · Gothic is the **oldest substantial Germanic text** (4th c. CE).

### 35–45s shot plan (Grok Imagine 1.5)
1. **0–4s** — Cold open: avatar speaks the line slowly, lip-synced. Caption: *Gothic · Wulfila's Bible, 4th c. CE — a Germanic language dead ~1,000 years*.
2. **4–10s** — Replay natural pace; IPA syllable-highlighted underneath.
3. **10–28s** — Micro-lesson: 3 caption cards (þ→th, ai→ɛː, "oldest Germanic text") with the avatar voicing each.
4. **28–38s** — Full line again, confident pace; show the Gothic-script glyphs alongside transliteration.
5. **38–45s** — Provenance card + CTA.

### Provenance card (the moat — always shown)
- **Text:** Wulfila, Gothic Bible, Matthew 6:9 (Codex Argenteus), public domain. Attested.
- **Pronunciation:** **reconstructed** from Wulfila's alphabet + comparative Germanic; moderate confidence, debated points flagged.
- **Sources:** Wikipedia / Wiktionary (CC BY-SA), Wikidata (CC0), retrieved 2026-06-18.

---

## Shared guardrails (both)
- Synthetic/owned avatars only — no real-person likeness.
- On-screen label every clip: **attested text** vs **reconstructed pronunciation**.
- Honor CC-BY-SA attribution on Wikimedia-sourced phonology in the video description.
- QA each rendered clip against the corpus attestation before publish; if Grok Imagine drifts from the IPA, re-render — accuracy is the brand.

## Next step
T1 pulls exact IPA from each `latest_scrape.json`, finalizes the two scripts, and produces the Grok Imagine 1.5 generation prompts (avatar spec + per-line timing). Render → QA → publish as the channel's first two posts.
