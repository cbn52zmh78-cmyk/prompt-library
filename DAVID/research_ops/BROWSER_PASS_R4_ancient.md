# Browser Pass R4 — Biblical Hebrew, Sanskrit, Akkadian, Sumerian
**CLI assignment:** R4
**Research depth:** Heavy — four languages across two major ancient families plus one isolate. Go deep into specialist sources for each.

---

## Browser Prompt (paste this into Grok browser)

You are doing deep linguistic research for DAVID — a dead language revival and human communication agent. Your job is to produce a detailed, scholarly JSON dataset on the reconstructed pronunciation of four ancient languages: **Biblical Hebrew**, **Classical Sanskrit**, **Akkadian**, and **Sumerian**.

These four span enormous linguistic diversity: Hebrew is a Semitic language with a living descendant (Modern Hebrew) but whose ancient pronunciation is partially lost; Sanskrit has the most precisely documented ancient phonology of any language thanks to the Shiksha texts; Akkadian is the lingua franca of the ancient Near East with cuneiform spelling giving us strong consonant data; Sumerian is a language isolate whose pronunciation is largely inferred through its Akkadian transcriptions.

Go deep into specialist academic sources:
- Hebrew: Khan *The Tiberian Pronunciation Tradition*, Joüon-Muraoka *Grammar of Biblical Hebrew*, Ben-Hayyim Samaritan tradition scholarship
- Sanskrit: the Shiksha texts (ancient phonetics treatises), Whitney *Sanskrit Grammar*, MacDonell *A Sanskrit Grammar*, Cardona *Pāṇini: A Survey of Research*
- Akkadian: Huehnergard *A Grammar of Akkadian*, von Soden *Grundriss der akkadischen Grammatik*, CDLI database notes
- Sumerian: Thomsen *The Sumerian Language*, Jagersma *A Descriptive Grammar of Sumerian*, ETCSL (Electronic Text Corpus of Sumerian Literature) documentation

**For each language, research and output:**

1. **Phoneme inventory** with IPA, confidence levels per phoneme
2. **The tradition question:**
   - Hebrew: Tiberian vs Babylonian vs Palestinian vs Samaritan traditions — which is most historically accurate?
   - Sanskrit: the Shiksha texts are our most precise ancient phonetics record — what do they actually say?
   - Akkadian: Old Babylonian vs Neo-Assyrian vs Neo-Babylonian pronunciation shifts
   - Sumerian: how Akkadian scribes transcribed Sumerian sounds — the Emesal dialect
3. **Script-to-sound mapping specifics:**
   - Hebrew: cantillation marks, dagesh, sheva, matres lectionis
   - Sanskrit: Devanagari is phonetically precise — explain the system
   - Akkadian: cuneiform CV/VC/CVC sign values, the aleph problem
   - Sumerian: logograms vs phonetic spellings, the DINGIR problem
4. **Canonical IPA transcriptions:**
   - Hebrew: "בְּרֵאשִׁית בָּרָא אֱלֹהִים" (Genesis 1:1 — In the beginning God created)
   - Sanskrit: "धर्मक्षेत्रे कुरुक्षेत्रे" (Bhagavad Gita 1:1 opening)
   - Akkadian: "ina rēš šarri šamê u erṣetim" (In the beginning of heaven and earth — Enuma Elish) or best phrase
   - Sumerian: "en-lil2 lugal kalam-ma" (Enlil, king of the land) or best attested phrase
5. **Grok Imagine audio guidance** — each language has specific challenges for audio generation:
   - Hebrew: guttural consonants (ayin, het, resh), cantillation pacing
   - Sanskrit: retroflex consonants, the aspirate distinction (p/ph, b/bh, etc.), length distinctions
   - Akkadian: emphatic consonants, the mimation ending
   - Sumerian: ergative case pronunciation, compound verb timing
6. **Tutoring hooks** — 3–5 per language (e.g., Sanskrit's Shiksha texts are more detailed about phonetics than anything in the Western tradition until the 19th century; Sumerian has no known living relatives)
7. **Modern descendants/survivals** — Hebrew → Modern Hebrew; Sanskrit → Sanskrit recitation tradition still alive; Akkadian → Aramaic/Arabic phonological influence; Sumerian → liturgical survival in early Babylonian religion

Output as a single JSON object with four top-level keys: `"biblical-hebrew"`, `"classical-sanskrit"`, `"akkadian"`, `"sumerian"`.

```json
{
  "biblical-hebrew": {
    "language": "biblical-hebrew",
    "status": "dead",
    "research_type": "pronunciation",
    "reconstruction_method": "",
    "scholarly_consensus": "",
    "tradition_comparison": {
      "tiberian": "",
      "babylonian": "",
      "samaritan": "",
      "most_historical": ""
    },
    "phoneme_inventory": {
      "vowels": [],
      "consonants": [],
      "gutturals": [],
      "distinctive_features": ""
    },
    "ipa_reconstructed": {
      "sample_text": "בְּרֵאשִׁית בָּרָא אֱלֹהִים",
      "romanization": "bərēʾšît bārāʾ ʾĕlōhîm",
      "transcription": "",
      "confidence": "",
      "confidence_note": ""
    },
    "stress_rules": "",
    "cantillation_notes": "",
    "prosody": {
      "rhythm": "",
      "pacing": ""
    },
    "grok_imagine_guidance": "",
    "tutoring_hooks": [],
    "sources": []
  },
  "classical-sanskrit": {
    "language": "classical-sanskrit",
    "status": "dead",
    "research_type": "pronunciation",
    "reconstruction_method": "Shiksha texts — ancient native phonetics treatises",
    "scholarly_consensus": "",
    "shiksha_notes": "what the Shiksha texts specify about articulation",
    "phoneme_inventory": {
      "vowels": [],
      "consonants": [],
      "retroflex_series": [],
      "aspirate_pairs": [],
      "distinctive_features": ""
    },
    "ipa_reconstructed": {
      "sample_text": "धर्मक्षेत्रे कुरुक्षेत्रे",
      "romanization": "dharmakṣetre kurukṣetre",
      "transcription": "",
      "confidence": "",
      "confidence_note": ""
    },
    "stress_rules": "",
    "prosody": {
      "rhythm": "",
      "pacing": "",
      "vedic_accent_note": ""
    },
    "grok_imagine_guidance": "",
    "tutoring_hooks": [],
    "sources": []
  },
  "akkadian": {
    "language": "akkadian",
    "status": "dead",
    "research_type": "pronunciation",
    "reconstruction_method": "cuneiform sign values + Sumerian-Akkadian bilinguals + Semitic comparative",
    "scholarly_consensus": "",
    "dialect_notes": {
      "old_babylonian": "",
      "neo_assyrian": "",
      "standard_babylonian": ""
    },
    "phoneme_inventory": {
      "vowels": [],
      "consonants": [],
      "emphatic_series": [],
      "distinctive_features": ""
    },
    "ipa_reconstructed": {
      "sample_text": "",
      "romanization": "",
      "transcription": "",
      "confidence": "",
      "confidence_note": ""
    },
    "stress_rules": "",
    "prosody": {
      "rhythm": "",
      "pacing": ""
    },
    "grok_imagine_guidance": "",
    "tutoring_hooks": [],
    "sources": []
  },
  "sumerian": {
    "language": "sumerian",
    "status": "dead",
    "research_type": "pronunciation",
    "reconstruction_method": "Akkadian transcriptions + internal spelling patterns + Emesal dialect contrast",
    "scholarly_consensus": "",
    "emesal_notes": "the women's/priestly dialect and what it reveals about standard pronunciation",
    "phoneme_inventory": {
      "vowels": [],
      "consonants": [],
      "disputed_phonemes": [],
      "distinctive_features": ""
    },
    "ipa_reconstructed": {
      "sample_text": "",
      "romanization": "",
      "transcription": "",
      "confidence": "low",
      "confidence_note": "Sumerian pronunciation is the least certain of any language in the DAVID registry"
    },
    "stress_rules": "",
    "prosody": {
      "rhythm": "",
      "pacing": ""
    },
    "grok_imagine_guidance": "",
    "tutoring_hooks": [],
    "sources": []
  }
}
```

Sumerian's confidence will be low across the board — that is expected and correct. Do not inflate confidence. The honest reconstruction is the valuable one.

---

## CLI R4 handoff instructions

After receiving browser JSON output:

1. Save raw output to `research_ops/outputs/R4_ancient_raw.json`
2. Create pronunciation folders:
   - `languages/dead/biblical-hebrew/pronunciation/pronunciation_profile.json`
   - `languages/dead/classical-sanskrit/pronunciation/pronunciation_profile.json`
   - `languages/dead/akkadian/pronunciation/pronunciation_profile.json`
   - `languages/dead/sumerian/pronunciation/pronunciation_profile.json`
3. Update training packs for all four — add `## Pronunciation Guide`, `## Reconstruction Notes`, and `## Grok Imagine Audio Guidance` sections
4. Sanskrit's `shiksha_notes` and `aspirate_pairs` are high-value tutoring content — flag for series planning
5. Sumerian `confidence: "low"` entries all go to `disputed_phonemes.json` and research queue
6. Hebrew's `cantillation_notes` feeds directly into video pacing for any documentary narration using Hebrew text
7. Update `language_registry.json` for all four
