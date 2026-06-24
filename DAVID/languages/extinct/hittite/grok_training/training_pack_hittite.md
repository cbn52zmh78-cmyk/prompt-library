# Grok Training Pack — Hittite
Generated: 2026-06-18 22:54 UTC
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

## Language profile: Hittite

- **Status:** extinct
- **Revival tier:** high
- **Family:** Anatolian > Indo-European
- **Period:** c. 1650–1200 BCE
- **Script:** Cuneiform (adapted Akkadian)
- **Decipherment:** fully_read
- **Training readiness:** scaffold

## History cross-links

_No History figure links yet._

## Attested corpus (training blocks)

### Block 1: Hittite Laws §1 — opening formula (Post 10) `[attested]`

**Source:** Corpus des textes hittites; Hoffner, Hittite Laws (1997); https://en.wikipedia.org/wiki/Hittite_language (CC BY-SA 3.0)

**Transliteration / original:**
```
nu-za-kán ḫa-a[n-…]
```

**Translation / gloss:**
If a man slays…

**Notes:** DAVID Post 10 hook line. Cuneiform attestation secure at Boğazköy; ḫ=[x]; excerpt truncated at lacuna; vocalization reconstructed.

## Pronunciation Guide `[reconstructed]`

**Model:** Melchert/Kimball Neo-Hittite standard — fortis/lenis stops, preserved laryngeals.
**Confidence:** medium (high consonants/ḫ; medium vowels/stress)
**Profile:** `languages/extinct/hittite/pronunciation/pronunciation_profile.json`

### Canonical sample (ritual formula)

**Text:** namma antuhsas andan esdu
**IPA:** `[ˈnam.ma ˈan.tuːχ.saːs ˈan.dan ˈeːʃ.du]`

### Key phonemes

- **ḫ** = guttural fricative [x~χ] (Scottish loch / German Bach) — PIE laryngeal reflex
- **Fortis geminates** pp/tt/kk held longer than single stops
- **Four vowels** /a e i u/ with phonemic length (VV plene writing)
- **š** ≈ [ʃ]; no English voiced b/d/g defaults
- **Stress** on first full syllable of content word (conservative default)

### Grok Imagine audio guidance

Guttural ḫ as back-of-throat scrape; hold geminate stops; pure vowels; š as [ʃ]. Avoid silent ḫ or English h. Flag ḫ and geminates as non-English articulations.

### Tutoring hooks

- Oldest attested Indo-European language (~1650 BCE)
- ḫ preserves PIE laryngeals — proof of laryngeal theory
- Cuneiform spells syllables (ḫa = ḫ+a), not just logograms
- Fortis/lenis matters more than voiced/voiceless
- Hittite Laws formula recognizable across millennia

### Sources

- H. Craig Melchert, *Hittite Historical Phonology*
- Sara E. Kimball, *Hittite Historical Phonology*
- Alwin Kloekhorst, *Etymological Dictionary of the Hittite Inherited Lexicon*
- Benjamin W. Fortson IV, *Indo-European Language and Culture*

## Reconstruction Notes

**Method:** Neo-Hittite cuneiform syllabic spelling + plene vowels + comparative Anatolian + PIE laryngeal theory via ḫ.

**High confidence:** Consonant inventory, ḫ as laryngeal reflex, vowel length from plene writing, syllabic cuneiform mapping.

**Low confidence:** Fortis articulation detail, exact ḫ place (uvular vs velar), š value, stress position, unstressed vowel qualities.

**Laryngeal note:** ḫ = empirical proof of PIE *h2/*h3 — colors adjacent vowels; unavailable evidence in Greek/Latin/Sanskrit.

**Disputed phonemes file:** `languages/extinct/hittite/pronunciation/disputed_phonemes.json`

## Instructions for Grok

1. Treat each block as primary evidence — do not invent unattested forms.
2. When asked to 'speak' this language, produce glossed excerpts or revival drafts tagged `[reconstructed]`.
3. For editorial foreign-language copy in living languages, use native idiom.
4. Queue next research via `research_query_generator.py --language hittite`.

## Next research tasks

- Expand corpus for Hittite
- Add grammar sketch with sourced morphology tables
- Link additional History figures if applicable
