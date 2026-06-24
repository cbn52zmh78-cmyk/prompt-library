# Grok Training Pack — Akkadian
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

## Language profile: Akkadian

- **Status:** dead
- **Revival tier:** high
- **Family:** Semitic
- **Period:** c. 2500 BCE – 1st century CE
- **Script:** Cuneiform
- **Decipherment:** fully_read
- **Training readiness:** unknown

## History cross-links

_No History figure links yet._

## Attested corpus (training blocks)

### Block 1: Epic of Gilgamesh — SB Tablet I opening (Post 5) `[attested]`

**Source:** Epic of Gilgamesh, Standard Babylonian recension Tablet I; ORACC https://oracc.museum.upenn.edu/; George (2003) via https://en.wikipedia.org/wiki/Epic_of_Gilgamesh (CC BY-SA 3.0)

**Transliteration / original:**
```
ša nagba imuru
```

**Translation / gloss:**
He who saw the Deep

**Notes:** DAVID Post 5 hook line. Cuneiform attestation secure; š=[ʃ]; vowels reconstructed from Semitic root structure.

## Pronunciation Guide `[reconstructed]`

**Model:** Standard Babylonian literary convention (Huehnergard/von Soden).
**Confidence:** medium_high
**Profile:** `languages/dead/akkadian/pronunciation/pronunciation_profile.json`

### Canonical sample (Enuma Elish opening)

**Romanization:** enūma eliš lā nabû šamāmu
**IPA:** `/e.nuː.ma e.liʃ laː na.buː ʃa.maː.mu/`

### Key phonemes

- **Emphatics:** ṭ q ṣ — throaty pharyngealized or popped ejectives (conventional; debated)
- **Long vowels:** phonemic length from cuneiform V/VV signs — hold distinctly
- **Mimation:** final -m on nouns/adjectives — pronounce, do not drop
- **Aleph:** glottal stop [ʔ] where sign values indicate
- **Š:** [ʃ] as in 'ship'; s and z distinct

### Stress

Often penultimate or morphologically determined; epic parallelism favors deliberate phrasing.

### Reconstruction notes

Cuneiform sign values and bilingual texts give strong consonant and vowel-length data. Emphatic articulation (ejective vs pharyngealized) remains conventional. Neo-Assyrian shows later sibilant shifts vs literary Standard Babylonian conservatism.

### Grok Imagine audio guidance

Emphatics as throaty or lightly ejective; sustain long vowels; pronounce mimation; glottal aleph where marked; deliberate epic pacing with parallelism breath groups; avoid Modern Hebrew/Arabic emphatic defaults without labeling dialect.

### Tutoring hooks

- Lingua franca of the ancient Near East for 2,000+ years
- Cuneiform multi-value signs — spelling reveals consonants clearly
- Emphatics distinguish Akkadian from Hebrew/Arabic cousins
- Heavy influence on Aramaic and Hebrew phonology
- Enuma Elish uses rhythmic parallelism like epic poetry

### Dialect variants (label on-screen)

| Variant | Notes |
|---------|-------|
| Standard Babylonian | DAVID default for literary/epic texts |
| Old Babylonian | Fuller vowels; less reduction |
| Neo-Assyrian | Later sibilant/emphatic shifts |

### Sources

- Huehnergard, *A Grammar of Akkadian*
- von Soden, *Grundriss der akkadischen Grammatik*
- CDLI corpus notes

## Instructions for Grok

1. Treat each block as primary evidence — do not invent unattested forms.
2. When asked to 'speak' this language, produce glossed excerpts or revival drafts tagged `[reconstructed]`.
3. For editorial foreign-language copy in living languages, use native idiom.
4. Queue next research via `research_query_generator.py --language akkadian`.

## Next research tasks

- Expand corpus for Akkadian
- Add grammar sketch with sourced morphology tables
- Link additional History figures if applicable
