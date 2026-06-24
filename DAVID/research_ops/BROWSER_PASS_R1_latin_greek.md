# Browser Pass R1 — Classical Latin & Ancient Greek
**CLI assignment:** R1
**Research depth:** Heavy — go deep into scholarly and academic sources, not surface Wikipedia

---

## Browser Prompt (paste this into Grok browser)

You are doing deep linguistic research for DAVID — a dead language revival and human communication agent. Your job is to produce a detailed, scholarly JSON dataset on the reconstructed pronunciation of two languages: **Classical Latin** and **Ancient Greek (Attic/Koine)**.

This is NOT a surface-level summary. Go deep into academic sources: Allen's *Vox Latina*, Allen's *Vox Graeca*, university linguistics departments, scholarly papers on historical phonology, reconstructed pronunciation guides used by classicists and theater practitioners. Cross-reference multiple sources.

**For each language, research and output:**

1. **Phoneme inventory** — every vowel and consonant with IPA symbol, articulation description, and any scholarly dispute about the sound
2. **Quantity distinctions** — Latin and Greek both have long/short vowel distinctions that are critical for meter and pacing
3. **Stress and accent** — Latin word stress rules (penult law); Greek pitch accent (acute, grave, circumflex) and its reconstruction debate
4. **Canonical IPA transcription** — provide IPA for:
   - Latin: "Arma virumque cano, Troiae qui primus ab oris" (Aeneid I.1)
   - Greek: "μῆνιν ἄειδε θεά, Πηληϊάδεω Ἀχιλῆος" (Iliad I.1)
5. **Confidence assessment** — what is attested vs reconstructed vs disputed
6. **Grok Imagine audio guidance** — specific notes for generating audio with lip sync: key phonemes that differ from English, timing for long vowels, how to handle aspirates, breath placement
7. **Tutoring hooks** — 3–5 counterintuitive or surprising pronunciation facts for a YouTube tutoring series (e.g., Latin V was /w/ not /v/)
8. **Classical vs later pronunciation** — for Latin: Classical vs Ecclesiastical split; for Greek: Ancient vs Byzantine vs Modern
9. **Top scholarly sources** with author, title, year, and URL/DOI where available

Output as a single JSON object with two top-level keys: `"classical-latin"` and `"ancient-greek"`, each following the schema below.

```json
{
  "classical-latin": {
    "language": "classical-latin",
    "status": "dead",
    "research_type": "pronunciation",
    "scholarly_consensus": "",
    "pronunciation_variants": {
      "classical": "description",
      "ecclesiastical": "description"
    },
    "phoneme_inventory": {
      "vowels": [],
      "consonants": [],
      "quantity_system": "",
      "distinctive_features": ""
    },
    "ipa_reconstructed": {
      "sample_text": "Arma virumque cano, Troiae qui primus ab oris",
      "transcription": "",
      "confidence": "",
      "confidence_note": ""
    },
    "stress_rules": "",
    "prosody": {
      "rhythm": "",
      "pitch": "",
      "pacing": "",
      "meter_note": ""
    },
    "grok_imagine_guidance": "",
    "tutoring_hooks": [],
    "sources": []
  },
  "ancient-greek": {
    "language": "ancient-greek",
    "status": "dead",
    "research_type": "pronunciation",
    "scholarly_consensus": "",
    "pronunciation_variants": {
      "attic": "description",
      "koine": "description",
      "byzantine": "description"
    },
    "phoneme_inventory": {
      "vowels": [],
      "consonants": [],
      "quantity_system": "",
      "distinctive_features": ""
    },
    "ipa_reconstructed": {
      "sample_text": "μῆνιν ἄειδε θεά, Πηληϊάδεω Ἀχιλῆος",
      "transcription": "",
      "confidence": "",
      "confidence_note": ""
    },
    "stress_rules": "",
    "prosody": {
      "rhythm": "",
      "pitch": "",
      "pacing": "",
      "pitch_accent_note": ""
    },
    "grok_imagine_guidance": "",
    "tutoring_hooks": [],
    "sources": []
  }
}
```

Be thorough. Cite real scholarly sources. Mark any disputed reconstructions explicitly.

---

## CLI R1 handoff instructions

After receiving browser JSON output:

1. Save raw output to `research_ops/outputs/R1_latin_greek_raw.json`
2. Create `languages/dead/classical-latin/pronunciation/pronunciation_profile.json`
3. Create `languages/dead/ancient-greek/pronunciation/pronunciation_profile.json`
4. Update both training packs — add `## Pronunciation Guide` section using the `ipa_reconstructed` and `grok_imagine_guidance` fields
5. Update `language_registry.json` — add `"ipa_coverage": "full"` and `"phonology_status": "reconstructed_high_confidence"` for both
6. Note any disputed fields for follow-up research queue
