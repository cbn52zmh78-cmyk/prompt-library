# Browser Pass R2 — Gothic, Old Norse, Old English
**CLI assignment:** R2
**Research depth:** Heavy — scholarly sources, comparative Germanic linguistics, not surface summaries

---

## Browser Prompt (paste this into Grok browser)

You are doing deep linguistic research for DAVID — a dead language revival and human communication agent. Your job is to produce a detailed, scholarly JSON dataset on the reconstructed pronunciation of three extinct Germanic languages: **Gothic**, **Old Norse**, and **Old English**.

These three share a common ancestor (Proto-Germanic) which gives comparative reconstruction more confidence than isolated languages. Use that family relationship — cite comparative evidence when it strengthens a reconstruction. Go deep into academic sources: Braune's *Gothic Grammar*, Gordon's *Introduction to Old Norse*, Mitchell & Robinson's *Guide to Old English*, university linguistics syllabi for historical Germanic courses, and scholarly reconstruction papers.

**For each language, research and output:**

1. **Phoneme inventory** with IPA, noting where Proto-Germanic comparison boosts confidence
2. **The Gothic alphabet** — Wulfila's script and how it maps to reconstructed sounds (critical for video captioning)
3. **Old Norse** — distinguish between runic period and manuscript period pronunciation; West Norse vs East Norse split
4. **Old English** — distinguish early West Saxon from late West Saxon; note Northumbrian dialect differences
5. **Canonical IPA transcriptions:**
   - Gothic: "Atta unsar þu in himinam, weihnai namo þein" (Lord's Prayer opening)
   - Old Norse: "Hljóðs bið ek allar, helgar kindir" (Völuspá 1)
   - Old English: "Hwæt! We Gardena in geardagum" (Beowulf 1)
6. **The thorn/eth distinction** (þ/ð) — critical for Old Norse and Old English audio: when each is voiced vs unvoiced
7. **Stress patterns** — Proto-Germanic root-initial stress and how each language evolved from it
8. **Grok Imagine audio guidance** — specific phonemes that English speakers (and AI audio systems) get wrong, timing for long vowels marked with macrons, how to handle the Gothic laryngeals
9. **Tutoring hooks** — 3–5 surprising facts per language for a YouTube series (e.g., Old Norse had no silent letters; Gothic is our only complete East Germanic text)
10. **Top scholarly sources** per language

Output as a single JSON object with three top-level keys: `"gothic"`, `"old-norse"`, `"old-english"`.

```json
{
  "gothic": {
    "language": "gothic",
    "status": "extinct",
    "research_type": "pronunciation",
    "scholarly_consensus": "",
    "script_notes": "",
    "phoneme_inventory": {
      "vowels": [],
      "consonants": [],
      "proto_germanic_correspondences": "",
      "distinctive_features": ""
    },
    "ipa_reconstructed": {
      "sample_text": "Atta unsar þu in himinam, weihnai namo þein",
      "transcription": "",
      "confidence": "",
      "confidence_note": ""
    },
    "stress_rules": "",
    "prosody": {
      "rhythm": "",
      "pitch": "",
      "pacing": ""
    },
    "grok_imagine_guidance": "",
    "tutoring_hooks": [],
    "sources": []
  },
  "old-norse": {
    "language": "old-norse",
    "status": "extinct",
    "research_type": "pronunciation",
    "scholarly_consensus": "",
    "dialect_notes": {
      "west_norse": "",
      "east_norse": ""
    },
    "phoneme_inventory": {
      "vowels": [],
      "consonants": [],
      "thorn_eth_distinction": "",
      "distinctive_features": ""
    },
    "ipa_reconstructed": {
      "sample_text": "Hljóðs bið ek allar, helgar kindir",
      "transcription": "",
      "confidence": "",
      "confidence_note": ""
    },
    "stress_rules": "",
    "prosody": {
      "rhythm": "",
      "pitch": "",
      "pacing": "",
      "alliterative_meter_note": ""
    },
    "grok_imagine_guidance": "",
    "tutoring_hooks": [],
    "sources": []
  },
  "old-english": {
    "language": "old-english",
    "status": "extinct",
    "research_type": "pronunciation",
    "scholarly_consensus": "",
    "dialect_notes": {
      "west_saxon": "",
      "northumbrian": "",
      "mercian": ""
    },
    "phoneme_inventory": {
      "vowels": [],
      "consonants": [],
      "thorn_eth_distinction": "",
      "distinctive_features": ""
    },
    "ipa_reconstructed": {
      "sample_text": "Hwæt! We Gardena in geardagum",
      "transcription": "",
      "confidence": "",
      "confidence_note": ""
    },
    "stress_rules": "",
    "prosody": {
      "rhythm": "",
      "pitch": "",
      "pacing": "",
      "alliterative_meter_note": ""
    },
    "grok_imagine_guidance": "",
    "tutoring_hooks": [],
    "sources": []
  }
}
```

Be thorough. Use comparative Germanic evidence where it strengthens reconstructions. Mark all disputed forms.

---

## CLI R2 handoff instructions

After receiving browser JSON output:

1. Save raw output to `research_ops/outputs/R2_germanic_raw.json`
2. Create `pronunciation/pronunciation_profile.json` in each language's folder:
   - `languages/extinct/gothic/pronunciation/`
   - `languages/extinct/old-norse/pronunciation/`
   - `languages/extinct/old-english/pronunciation/`
3. Update training packs for Gothic and Old Norse (Old English training pack doesn't exist yet — create stub)
4. Update `language_registry.json` with IPA coverage for all three
5. Gothic's `script_notes` field feeds the video captioning system — flag this for STUDIO handoff
