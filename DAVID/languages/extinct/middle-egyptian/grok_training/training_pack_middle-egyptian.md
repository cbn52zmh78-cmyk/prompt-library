# Grok Training Pack — Middle Egyptian
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

## Language profile: Middle Egyptian

- **Status:** extinct
- **Revival tier:** high
- **Family:** Afro-Asiatic > Egyptian
- **Period:** c. 2000–1300 BCE (classical phase)
- **Script:** Hieroglyphs, hieratic, demotic
- **Decipherment:** fully_read
- **Training readiness:** scaffold

## History cross-links

_No History figure links yet._

## Attested corpus (training blocks)

### Block 1: Royal blessing — ꜥnḫ wḏꜣ snb (Post 6) `[attested]`

**Source:** Formula ubiquitous in New Kingdom stelae; transliteration per Gardiner/James P. Allen, Middle Egyptian (2010); https://en.wikipedia.org/wiki/Egyptian_language (CC BY-SA 3.0)

**Transliteration / original:**
```
ꜥnḫ wḏꜣ snb
```

**Translation / gloss:**
Life, prosperity, health

**Notes:** DAVID Post 6 hook line. Hieroglyphic attestation secure; Egyptological vowel insertions are reconstructed.

## Pronunciation Guide `[reconstructed]`

**Model:** Loprieno/Allen/Peust — Coptic-reflex vocalization over consonantal skeleton.
**Confidence:** medium-low (high–medium consonants; low vowel timbre)
**Profile:** `languages/extinct/middle-egyptian/pronunciation/pronunciation_profile.json`

### Canonical sample (Ra formula)

**Text:** m rn.f n ra
**IPA:** `[mə ˈran.nəf ʔan ˈraʕ]`

### Key phonemes

- **Hieroglyphs = consonants only** — all vowels are scholarly insertions `[reconstructed]`
- **Ejectives** pʼ/tʼ/kʼ with glottal pop (Afroasiatic, not European)
- **ꜥ (ayin)** = pharyngeal [ʕ] (Arabic ع) — not silent
- **ꜣ (aleph)** = glottal stop [ʔ]
- **Epenthetic schwa** [ə] in unstressed positions (Egyptological convention)

### Grok Imagine audio guidance

Ejectives with glottal pop; pharyngeal ꜥ as deep throat constriction; emphatics heavier than plain stops. Insert epenthetic schwas; pure a/i/u without English diphthongs. Tag all vowels as reconstructed on screen. Reference Arabic/Ge'ez for ꜥ and ejectives.

### Tutoring hooks

- Hieroglyphs spell consonants only — vowels guessed from Coptic
- ꜥ is a deep throat sound, not a vowel
- Coptic = latest Egyptian with written vowels
- Ejectives rare in European languages, core to Egyptian
- ꜥnḫ wḏꜣ snb formula ubiquitous in tomb art

### Sources

- Antonio Loprieno, *Ancient Egyptian: A Linguistic Introduction*
- James P. Allen, *Middle Egyptian* (3rd ed.)
- Carsten Peust, *Egyptian Phonology*

## Reconstruction Notes

**Method:** Coptic phonological survival + Afroasiatic comparative + Greek/Assyrian name transcriptions + hieroglyphic consonantal skeleton.

**High confidence:** Ejectives, pharyngeals (ꜥ/ḥ), emphatics, glottal (ꜣ), consonant inventory.

**Low confidence:** All vowel qualities, stress placement, dialect variation, r articulation, j/w vocalic status.

**Vowel note:** Egyptologists insert epenthetic e/a by convention — these never appear in original script. Every vocalized form must carry `[reconstructed]` tag in revival drafts.

**Disputed phonemes file:** `languages/extinct/middle-egyptian/pronunciation/disputed_phonemes.json`

## Instructions for Grok

1. Treat each block as primary evidence — do not invent unattested forms.
2. When asked to 'speak' this language, produce glossed excerpts or revival drafts tagged `[reconstructed]`.
3. For editorial foreign-language copy in living languages, use native idiom.
4. Queue next research via `research_query_generator.py --language middle-egyptian`.

## Next research tasks

- Expand corpus for Middle Egyptian
- Add grammar sketch with sourced morphology tables
- Link additional History figures if applicable
