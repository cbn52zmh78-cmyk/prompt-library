# Grok Training Pack — Etruscan
Generated: 2026-06-16 23:02 UTC
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

## Language profile: Etruscan

- **Status:** extinct
- **Revival tier:** high
- **Family:** Tyrsenian (isolate)
- **Period:** c. 700 BCE – 50 CE
- **Script:** Etruscan alphabet (adapted from Greek)
- **Decipherment:** readable_script_unknown_language
- **Training readiness:** partial

## History cross-links

_No History figure links yet._

## Attested corpus (training blocks)

### Block 1: Pyrgi Tablet — Etruscan portion `[attested]`

**Source:** Museo Nazionale di Villa Giulia, Rome

**Transliteration / original:**
```
Itanim heramave avil eniaci pulumχva
```

**Translation / gloss:**
This temple and this sanctuary ... (partial; bilingual context from Phoenician side)

**Notes:** Bilingual with Phoenician — key for proper-name and formulaic pattern extraction.

### Block 2: Liber Linteus — ritual calendar excerpt `[attested]`

**Source:** Zagreb Archaeological Museum (linen book)

**Transliteration / original:**
```
[excerpt pending cataloguing]
```

**Translation / gloss:**
[partial — ritual calendar of Haruspicina]

**Notes:** Longest continuous Etruscan text; priority for full line-by-line training pack.

## Pronunciation Guide `[reconstructed]`

**Model:** Bonfante/Rix/Wallace standard — Greek-adapted alphabet, no voiced stops.
**Confidence:** medium (high consonants/alphabet; medium-low vowels/prosody)
**Profile:** `languages/extinct/etruscan/pronunciation/pronunciation_profile.json`

### Canonical sample (dedicatory formula)

**Text:** mi mulu larisal
**IPA:** `[mi ˈmu.lu laˈris.al]`

### Key phonemes

- **No voiced stops** — b/d/g absent; use p/t/k only
- **ph/th/kh** = aspirated stops with audible puff (not fricatives)
- **Four vowels** /a e i u/ — no forced Italian o-vowel
- **ś** approximated as [s] or [ʃ] (disputed)
- **Initial stress** → syncope and consonant clusters in later forms

### Grok Imagine audio guidance

Aspirated puffs on ph/th/kh; pure vowels; no voiced stops; initial stress. Approximate clusters and syllabic liquids; avoid Italianate voicing. Crisp/neutral timbre where vowel quality uncertain.

### Tutoring hooks

- Etruscan had NO voiced stops — unique among neighbors
- Greek alphabet adapted with unique F-symbol
- Initial stress caused vowel syncope → wild clusters
- Phonetics better attested than meanings (isolate)
- Possible Tuscan aspiration influence

### Sources

- Bonfante & Bonfante, *The Etruscan Language* (2nd ed., 2002)
- Helmut Rix, *Etruskische Texte*
- Rex E. Wallace, *Zikh Rasna*

## Reconstruction Notes

**Method:** Greek-derived alphabet + Latin/Greek bilingual transcriptions + internal spelling/syncope patterns.

**High confidence:** Consonant inventory, aspirate/tenuis contrast, absence of voiced stops, alphabet-to-sound mapping.

**Low confidence:** Vowel length/quality, exact ś value, syllabic sonorant extent, prosodic rhythm.

**Disputed phonemes file:** `languages/extinct/etruscan/pronunciation/disputed_phonemes.json`

**Series flag:** `notable_absences` (no b/d/g) — high-value tutoring hook for content planning.

## Instructions for Grok

1. Treat each block as primary evidence — do not invent unattested forms.
2. When asked to 'speak' this language, produce glossed excerpts or revival drafts tagged `[reconstructed]`.
3. For editorial foreign-language copy in living languages, use native idiom.
4. Queue next research via `research_query_generator.py --language etruscan`.

## Next research tasks

- Expand corpus for Etruscan
- Add grammar sketch with sourced morphology tables
- Link additional History figures if applicable
