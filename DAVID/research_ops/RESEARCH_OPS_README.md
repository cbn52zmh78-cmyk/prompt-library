# DAVID Research Ops — Browser Pass Protocol

## Workflow
```
Grok Browser (heavy pass) → JSON output → R1-R4 CLI researchers → DAVID data structures
```

1. Open Grok browser with heavy research enabled
2. Paste the browser prompt from the relevant pass file
3. Browser outputs structured JSON
4. Save JSON output to `research_ops/outputs/` with filename matching the pass
5. Hand JSON to assigned CLI researcher (R1–R4)
6. CLI researcher processes JSON → populates `languages/{status}/{slug}/pronunciation/` and updates training packs

## Pass assignments

| Pass | File | CLI | Languages |
|------|------|-----|-----------|
| R1 | BROWSER_PASS_R1_latin_greek.md | R1 | Classical Latin, Ancient Greek |
| R2 | BROWSER_PASS_R2_germanic.md | R2 | Gothic, Old Norse, Old English |
| R3 | BROWSER_PASS_R3_extinct.md | R3 | Etruscan, Hittite, Middle Egyptian |
| R4 | BROWSER_PASS_R4_ancient.md | R4 | Biblical Hebrew, Sanskrit, Akkadian, Sumerian |

## Output schema (all passes use same structure)

Each language block in the JSON output follows:
```json
{
  "language": "slug",
  "status": "dead|extinct|reconstructed",
  "research_type": "pronunciation",
  "scholarly_consensus": "one paragraph summary of how scholars reconstruct pronunciation",
  "phoneme_inventory": {
    "vowels": ["list of IPA vowel symbols with notes"],
    "consonants": ["list of IPA consonant symbols with notes"],
    "distinctive_features": "what makes this language's sound system unusual"
  },
  "ipa_reconstructed": {
    "sample_text": "canonical phrase or line",
    "transcription": "/IPA transcription/",
    "confidence": "high|medium|low",
    "confidence_note": "why this confidence level"
  },
  "stress_rules": "description of stress/accent system",
  "prosody": {
    "rhythm": "stress-timed|syllable-timed|mora-timed|unknown",
    "pitch": "notes on pitch accent or tone if any",
    "pacing": "slow|moderate|fast relative to English, with rationale"
  },
  "grok_imagine_guidance": "Specific instructions for audio/lip sync generation — phonemes to watch, timing notes, common mistakes to avoid",
  "tutoring_hooks": [
    "interesting or counterintuitive fact about pronunciation for a tutoring series"
  ],
  "sources": [
    {"title": "", "author": "", "year": "", "url_or_doi": "", "reliability": "high|medium"}
  ]
}
```

## CLI researcher instructions
After receiving browser JSON output:
1. Validate schema completeness — flag any `"unknown"` fields for follow-up
2. Create `languages/{status}/{slug}/pronunciation/` folder for each language
3. Save the language block as `pronunciation_profile.json`
4. Update `language_registry.json` with `ipa_coverage` and `phonology_status` fields
5. Add pronunciation block to existing `grok_training/training_pack_{slug}.md`
6. Report gaps back to NEXUS for queueing
