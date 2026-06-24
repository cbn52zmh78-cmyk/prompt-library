# Grok Training Pack — Gothic
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

## Language profile: Gothic

- **Status:** extinct
- **Revival tier:** high
- **Family:** East Germanic
- **Period:** c. 4th century CE
- **Script:** Gothic alphabet (Wulfila)
- **Decipherment:** fully_read
- **Training readiness:** good

## History cross-links

_No History figure links yet._

## Attested corpus (training blocks)

### Block 1: Atta unsar (Lord's Prayer) `[attested]`

**Source:** Codex Argenteus, Uppsala University Library

**Transliteration / original:**
```
Atta unsar þu in himinam, weihnai namo þein
```

**Translation / gloss:**
Our Father, thou in heaven, hallowed be thy name

**Notes:** Standard entry text for Gothic phonology and morphology training.

## Pronunciation Guide `[reconstructed]`

**Model:** Braune/Wright/Streitberg PGmc reconstruction — Wulfila orthography baseline.
**Confidence:** high (core segments undisputed; minor nasal/quality variants)
**Profile:** `languages/extinct/gothic/pronunciation/pronunciation_profile.json`

### Canonical sample (Lord's Prayer opening)

**Text:** Atta unsar þu in himinam, weihnai namo þein
**IPA:** `/ˈatːa ˈunsar θuː in ˈhiminaːm ˈwiːhnai ˈnaːmoː θeiːn/`

### Key phonemes

- **þ = /θ/** dental fricative (not English th-as-stop)
- **ƕ = /hʷ/ or [ʍ]** — distinct from plain /h/
- **q = /kʷ/** labialized velar stop
- **Long vowels phonemic** — sustain macron vowels; geminates held (e.g. atta /ˈatːa/)
- **Intervocalic fricatives** β ð ɣ voiced (positional allophones)
- **No silent letters** — Wulfila script maps 1:1 to phonemes

### Script (captioning)

Wulfila's 27-letter alphabet: Greek-uncial base plus runic/Latin additions for PGmc-only sounds. Direct grapheme-to-phoneme mapping — ideal for on-screen caption alignment.

### Stress

PGmc root-initial primary stress preserved (fixed); secondary stress on first element of compounds.

### Grok Imagine audio guidance

Dental θ/ð (not stops); intervocalic β/ɣ/x as fricatives; sustain long vowels; ƕ as [ʍ] or aspirated hw; Greek-like vowel qualities; slow deliberate pacing with geminates held; laryngeals as [x/h]; no English schwa reduction.

### Tutoring hooks

- Sole complete East Germanic corpus — Wulfila Bible (~350 AD)
- Wulfila invented the Gothic alphabet for Bible translation
- 'Atta' cognate to English 'dad'; no silent letters ever
- Comparative goldmine: Gothic vs ON/OE for PGmc reconstruction
- Earliest substantial literary Germanic text

### Sources

- Braune's Gothic Grammar (with Balg)
- Joseph Wright, Gothic grammar
- Wulfila Project (wulfila.be)
- Streitberg, Lehmann (via Wikipedia phonology)

## Instructions for Grok

1. Treat each block as primary evidence — do not invent unattested forms.
2. When asked to 'speak' this language, produce glossed excerpts or revival drafts tagged `[reconstructed]`.
3. For editorial foreign-language copy in living languages, use native idiom.
4. Queue next research via `research_query_generator.py --language gothic`.

## Next research tasks

- Expand corpus for Gothic
- Add grammar sketch with sourced morphology tables
- Link additional History figures if applicable
