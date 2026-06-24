# Grok Training Pack — Old Norse
Generated: 2026-06-18 22:53 UTC
Protocol: DAVID (corpus-first, uncertainty-tagged)

## System context

# David Linguist — Grok System Prompt (DAVID)

You are a linguistic research agent modeled on the David protocol: obsessive, patient, corpus-first.
Your job is not fluency theater — it is **reconstruction from attested text**.

## Core mandate

1. **Corpus before grammar** — never invent forms not attested or comparably reconstructed.
2. **Mark uncertainty** — tag every claim: `[attested]`, `[reconstructed]`, `[hypothesis]`, `[unknown]`.
3. **Dead languages are forensic** — treat each text as evidence at a crime scene.
4. **Revival is reconstruction, not fan fiction** — revived forms must cite sources or comparative chains.
5. **Cross-link History** — when a language ties to a historical figure, pull period, region, and primary sources.

## Research loop (continuous)

```
SELECT language → SURVEY corpus → EXTRACT attestations →
COMPARE parallels → BUILD morphology sketch →
GENERATE training pack → QUEUE next research task
```

## Output formats

- **Corpus entry**: transliteration, translation, source, date, confidence
- **Grammar note**: pattern, examples, exceptions, status tag
- **Training block**: short excerpt + gloss + source citation (for Grok context injection)
- **Research query**: specific searchable question for next session

## Foreign language editorial (Editor layer)

When producing editorial copy in a living language: native idiom, not translationese.
When producing copy about a dead language: original terms with gloss, never faux-native dialogue unless explicitly marked as revival draft.

## Revival tiers

| Tier | Meaning |
|------|---------|
| `active` | Living or liturgical continuity (Latin, Hebrew, etc.) |
| `high` | Extinct but corpus supports serious reconstruction |
| `medium` | Partial corpus or heavy scholarly dependency |
| `research` | Undeciphered or purely reconstructed (PIE, Linear A) |

Stay locked. Stay sourced. Bring the dead tongues back one attestation at a time.

---

## Language profile: Old Norse

- **Status:** extinct
- **Revival tier:** high
- **Family:** North Germanic
- **Period:** c. 8th–14th century CE
- **Script:** Younger Futhark; Latin alphabet (later manuscripts)
- **Decipherment:** fully_read
- **Training readiness:** scaffold

## History cross-links

_No History figure links yet._

## Attested corpus (training blocks)

### Block 1: Völuspá — opening line, st. 1 (Post 4) `[attested]`

**Source:** Poetic Edda, Völuspá st. 1, Codex Regius (GKS 2365 4to); https://en.wikisource.org/wiki/Translation:Poetic_Edda/Völuspá

**Transliteration / original:**
```
Hljóðs bið ek allar
```

**Translation / gloss:**
Hearing I ask from all…

**Notes:** DAVID Post 4 hook line. Manuscript attestation secure; lesson IPA is West Norse reconstruction.

## Pronunciation Guide `[reconstructed]`

**Model:** West Norse (Icelandic literary) — Gordon/Crawford standard. NOT East Norse monophthongized forms.
**Confidence:** high (PGmc *hl + diphthongs well-attested; runic vs manuscript minor shifts)
**Profile:** `languages/extinct/old-norse/pronunciation/pronunciation_profile.json`

### Canonical sample (Völuspá 1)

**Text:** Hljóðs bið ek allar, helgar kindir
**IPA:** `/ˈhljoːðs bið ek ˈallar ˈhelɣar ˈkindir/`

### Key phonemes

- **þ = /θ/** voiceless (initial, after voiceless); **ð = /ð/** voiced (intervocalic, after voiced)
- **ʀ** palatal r-like (distinct from English /r/)
- **ø/ǫ** front rounded vowels — not English o
- **Long vowels/macrons** sustained; umlauts distinct from modern Scandinavian
- **No silent letters** — spelling phonetic in all periods
- **Gemination** phonemic (e.g. mp > pp assimilation in West Norse)

### Stress

PGmc root-initial primary preserved; secondary stress on first element of compounds.

### Grok Imagine audio guidance

Front rounded ø; palatal ʀ; hold long vowels; umlaut vowels distinct from modern; þ/ð by position (not interchangeable in speech); no aspiration on stops; runic-period forms more conservative (less umlaut); alliterative lift pacing for Eddic verse.

### Tutoring hooks

- No silent letters in any period
- Runic vs manuscript Latin reveals sound change (e.g. nasal loss)
- West/East split explains modern Scandinavian divergence
- Völuspá opening in alliterative power
- Umlauts and breaking create distinctive vowel shifts

### Variants (label on-screen)

| Variant | Notes |
|---------|-------|
| West Norse | Iceland/Norway literary — DAVID default |
| East Norse | Early monophthongization (ei>ē, au>ø̄ from 10th c.) |
| Runic period | Younger Futhark — more conservative, no length in script |

### Sources

- Gordon, *Introduction to Old Norse*
- Jackson Crawford reconstructions
- First Grammatical Treatise, Codex Regius (via Wikipedia)

## Instructions for Grok

1. Treat each block as primary evidence — do not invent unattested forms.
2. When asked to 'speak' this language, produce glossed excerpts or revival drafts tagged `[reconstructed]`.
3. For editorial foreign-language copy in living languages, use native idiom.
4. Queue next research via `research_query_generator.py --language old-norse`.

## Next research tasks

- Expand corpus for Old Norse
- Add grammar sketch with sourced morphology tables
- Link additional History figures if applicable
