# Browser Pass — Living Languages (Translation Service)
**CLI assignment:** R1 or R2 (coordinate)
**Research depth:** Heavy — focus on register, idiom, and translation pitfalls. Not phonology — these languages are alive.

---

## Browser Prompt (paste this into Grok browser)

You are doing deep research for DAVID — a human communication agent that provides professional document translation services. Your job is to produce a detailed reference dataset for **eight living languages** covering what professional translators need to know: register differences, common translationese traps, idiomatic expression mapping, and document type conventions.

This is NOT a basic grammar overview. Go into professional translation studies sources: Venuti *The Translator's Invisibility*, Baker *In Other Words*, professional translation association guidelines (ATA, ITI), language-specific style guides, bilingual academic papers on translation quality, and native speaker editorial standards for each language.

**Languages in scope:**
Spanish (Latin American + Castilian split), French (European + Canadian), Italian, German, Japanese, Mandarin Chinese, Modern Arabic (MSA + regional awareness), Portuguese (Brazilian + European)

**For each language, research and output:**

1. **Register system** — how does this language divide formal/informal/written/spoken registers? Where do translators get it wrong?
2. **Common translationese traps** — constructions that sound like translated English even when grammatically correct
3. **Document type conventions** — how do legal, business, academic, and creative documents differ in this language vs English conventions?
4. **Idiom mapping philosophy** — literal vs functional equivalence; what idiomatic clusters need special handling?
5. **Return-to-original workflow notes** — if a document comes in this language, gets edited in English, then returns to this language: what are the highest-risk quality loss points?
6. **Pronunciation notes for tutoring** — key features of this language's sound system for a language tutoring series (IPA not required — accessible description is fine for living languages)
7. **Script/orthography notes** — Japanese (kanji/kana system), Arabic (right-to-left, no short vowels in MSA), Mandarin (simplified vs traditional, pinyin), German (ß, umlauts), etc.
8. **Top professional resources** — style guides, dictionaries, professional glossaries

Output as a single JSON object with one key per language slug.

```json
{
  "spanish": {
    "language": "spanish",
    "status": "living",
    "research_type": "translation_service",
    "variant_notes": {
      "latin_american": "",
      "castilian": "",
      "recommended_default": ""
    },
    "register_system": "",
    "translationese_traps": [],
    "document_conventions": {
      "legal": "",
      "business": "",
      "academic": "",
      "creative": ""
    },
    "return_to_original_risks": [],
    "idiom_mapping_notes": "",
    "tutoring_pronunciation_hooks": [],
    "orthography_notes": "",
    "professional_resources": []
  },
  "french": { "...same structure..." },
  "italian": { "...same structure..." },
  "german": { "...same structure..." },
  "japanese": {
    "language": "japanese",
    "status": "living",
    "research_type": "translation_service",
    "script_system": {
      "hiragana": "",
      "katakana": "",
      "kanji": "",
      "romaji_note": ""
    },
    "register_system": "",
    "keigo_notes": "Japanese honorific speech system — critical for document register",
    "translationese_traps": [],
    "document_conventions": {
      "legal": "",
      "business": "",
      "academic": "",
      "creative": ""
    },
    "return_to_original_risks": [],
    "idiom_mapping_notes": "",
    "tutoring_pronunciation_hooks": [],
    "professional_resources": []
  },
  "mandarin": {
    "language": "mandarin",
    "status": "living",
    "research_type": "translation_service",
    "script_notes": {
      "simplified": "",
      "traditional": "",
      "pinyin": ""
    },
    "register_system": "",
    "translationese_traps": [],
    "document_conventions": {
      "legal": "",
      "business": "",
      "academic": "",
      "creative": ""
    },
    "return_to_original_risks": [],
    "idiom_mapping_notes": "",
    "tutoring_pronunciation_hooks": [],
    "professional_resources": []
  },
  "arabic": {
    "language": "arabic",
    "status": "living",
    "research_type": "translation_service",
    "variant_notes": {
      "msa": "Modern Standard Arabic — for formal documents",
      "regional_awareness": ""
    },
    "script_notes": "right-to-left, no short vowel marking in MSA, abjad system",
    "register_system": "",
    "diglossia_note": "the gulf between written MSA and spoken dialects — critical for document work",
    "translationese_traps": [],
    "document_conventions": {
      "legal": "",
      "business": "",
      "academic": "",
      "creative": ""
    },
    "return_to_original_risks": [],
    "idiom_mapping_notes": "",
    "tutoring_pronunciation_hooks": [],
    "professional_resources": []
  },
  "portuguese": {
    "language": "portuguese",
    "status": "living",
    "research_type": "translation_service",
    "variant_notes": {
      "brazilian": "",
      "european": "",
      "recommended_default": ""
    },
    "register_system": "",
    "translationese_traps": [],
    "document_conventions": {
      "legal": "",
      "business": "",
      "academic": "",
      "creative": ""
    },
    "return_to_original_risks": [],
    "idiom_mapping_notes": "",
    "tutoring_pronunciation_hooks": [],
    "professional_resources": []
  }
}
```

---

## CLI handoff instructions

After receiving browser JSON output:

1. Save raw output to `research_ops/outputs/LIVING_translation_raw.json`
2. Create `languages/living/` directory in DAVID repo
3. Create one folder per language: `languages/living/{slug}/`
4. Save `translation_profile.json` in each
5. Create stub `tutoring/lesson_plan.md` in each living language folder using `tutoring_pronunciation_hooks`
6. Add all 8 languages to `language_registry.json` with `status: "living"` and `revival_tier: "active"`
7. Japanese `keigo_notes` and Arabic `diglossia_note` are high-value tutoring content — flag for series
