# Browser Pass R3 — Etruscan, Hittite, Middle Egyptian
**CLI assignment:** R3
**Research depth:** Heavy — these are the hard ones. Go into specialist sources, epigraphy papers, archaeolinguistics journals. Surface Wikipedia is not enough here.

---

## Browser Prompt (paste this into Grok browser)

You are doing deep linguistic research for DAVID — a dead language revival and human communication agent. Your job is to produce a detailed, scholarly JSON dataset on the reconstructed pronunciation of three extinct languages: **Etruscan**, **Hittite**, and **Middle Egyptian**.

These are harder reconstruction targets than Latin or Greek — Etruscan is a language isolate with no living relatives, Hittite is the oldest attested Indo-European language but many phoneme values are disputed, and Middle Egyptian pronunciation is entirely reconstructed from Coptic and comparative Semitic evidence. This is exactly the kind of deep reconstruction work DAVID specializes in.

Go into specialist academic sources: Bonfante & Bonfante *The Etruscan Language*, Kimball *Hittite Historical Phonology*, Allen *The Ancient Egyptian Language*, Loprieno *Ancient Egyptian: A Linguistic Introduction*, Fortson *Indo-European Language and Culture*, epigraphy journals (Glotta, JNES, ZA), university Egyptology and Hittitology course materials.

**For each language, research and output:**

1. **What we know vs what we don't** — honest assessment of reconstruction confidence per phoneme
2. **How pronunciation was reconstructed** — the methodology (Coptic survival for Egyptian, cuneiform spelling conventions for Hittite, Etruscan-Latin bilingual inscriptions)
3. **Phoneme inventory** — what can be stated with confidence, what is hypothesis
4. **Script-to-sound mapping:**
   - Etruscan: alphabet adapted from Greek — which letter values are secure?
   - Hittite: cuneiform logograms, Sumerograms, Akkadograms — how do scholars extract Hittite sounds?
   - Middle Egyptian: hieroglyphic consonantal skeleton — what vowels are inferred from Coptic and Semitic?
5. **Canonical IPA transcriptions (best scholarly reconstruction):**
   - Etruscan: "mi mulu larisal" (common dedication formula) or best attested phrase
   - Hittite: "namma antuhsas andan esdu" (a phrase from Hittite ritual texts) or best attested phrase
   - Middle Egyptian: "m rn.f n ra" (in the name of Ra, a common formula) or best attested phrase
6. **The vowel problem** — all three languages have vowel systems that are partially or entirely reconstructed. Explain the state of evidence and mark confidence clearly.
7. **Grok Imagine audio guidance** — given the reconstruction uncertainty, provide conservative pronunciation guidelines: what to commit to, what to approximate, what to avoid. Flag phonemes that have no English equivalent and need description.
8. **Tutoring hooks** — 3–5 fascinating facts per language (e.g., Etruscan had no voiced stops — b/d/g didn't exist; Hittite preserved the Proto-Indo-European laryngeals that vanished in every other IE branch)
9. **Top specialist sources** — not general linguistics textbooks, the specific monographs and papers

Output as a single JSON object with three top-level keys: `"etruscan"`, `"hittite"`, `"middle-egyptian"`.

```json
{
  "etruscan": {
    "language": "etruscan",
    "status": "extinct",
    "research_type": "pronunciation",
    "reconstruction_method": "how pronunciation was reconstructed",
    "scholarly_consensus": "",
    "confidence_overview": "overall confidence assessment",
    "phoneme_inventory": {
      "vowels": [],
      "consonants": [],
      "notable_absences": "e.g. no voiced stops",
      "disputed_phonemes": [],
      "distinctive_features": ""
    },
    "ipa_reconstructed": {
      "sample_text": "",
      "transcription": "",
      "confidence": "low|medium|high",
      "confidence_note": "",
      "alternatives": "any competing reconstructions"
    },
    "stress_rules": "",
    "prosody": {
      "rhythm": "",
      "pacing": "",
      "notes": ""
    },
    "grok_imagine_guidance": "",
    "tutoring_hooks": [],
    "sources": []
  },
  "hittite": {
    "language": "hittite",
    "status": "extinct",
    "research_type": "pronunciation",
    "reconstruction_method": "",
    "scholarly_consensus": "",
    "confidence_overview": "",
    "laryngeal_notes": "Hittite preserved PIE laryngeals — explain their phonetic value",
    "phoneme_inventory": {
      "vowels": [],
      "consonants": [],
      "laryngeals": [],
      "disputed_phonemes": [],
      "distinctive_features": ""
    },
    "ipa_reconstructed": {
      "sample_text": "",
      "transcription": "",
      "confidence": "",
      "confidence_note": "",
      "alternatives": ""
    },
    "stress_rules": "",
    "prosody": {
      "rhythm": "",
      "pacing": "",
      "notes": ""
    },
    "grok_imagine_guidance": "",
    "tutoring_hooks": [],
    "sources": []
  },
  "middle-egyptian": {
    "language": "middle-egyptian",
    "status": "extinct",
    "research_type": "pronunciation",
    "reconstruction_method": "Coptic phonological survival + comparative Afroasiatic",
    "scholarly_consensus": "",
    "confidence_overview": "",
    "vowel_reconstruction_note": "Egyptian writing omitted vowels — explain how vowels are reconstructed",
    "phoneme_inventory": {
      "vowels": [],
      "consonants": [],
      "ayin_aleph_distinction": "",
      "disputed_phonemes": [],
      "distinctive_features": ""
    },
    "ipa_reconstructed": {
      "sample_text": "",
      "transcription": "",
      "confidence": "",
      "confidence_note": "",
      "alternatives": ""
    },
    "stress_rules": "",
    "prosody": {
      "rhythm": "",
      "pacing": "",
      "notes": ""
    },
    "grok_imagine_guidance": "",
    "tutoring_hooks": [],
    "sources": []
  }
}
```

These are hard reconstructions — honesty about uncertainty is more valuable than false confidence. Mark every disputed form. This data feeds video production and language tutoring — accuracy matters.

---

## CLI R3 handoff instructions

After receiving browser JSON output:

1. Save raw output to `research_ops/outputs/R3_extinct_raw.json`
2. Create pronunciation folders:
   - `languages/extinct/etruscan/pronunciation/pronunciation_profile.json`
   - `languages/extinct/hittite/pronunciation/pronunciation_profile.json`
   - `languages/extinct/middle-egyptian/pronunciation/pronunciation_profile.json`
3. Update all three training packs — add `## Pronunciation Guide` and `## Reconstruction Notes` sections
4. Flag all `"confidence": "low"` phonemes in a separate `disputed_phonemes.json` per language — these become research queue items
5. Update `language_registry.json`
6. Etruscan's `notable_absences` field (no voiced stops) is a high-value tutoring hook — flag for series planning
