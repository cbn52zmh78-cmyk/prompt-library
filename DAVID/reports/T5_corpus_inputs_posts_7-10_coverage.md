# T5 corpus inputs — Posts 7–10 coverage note (#73)

_Batch `T5_corpus_inputs_posts_7-10` · catalogued 2026-06-18 · **4/4 ok**._

Scope: Biblical Hebrew, Linear A, Classical Sanskrit, Hittite — each with attested excerpt, source citation, cited lesson IPA, and on-screen text/pronunciation labels per `content_concepts_v1.md`. Linear A explicitly flagged **undeciphered / speculative**.

Guardrails: public scholarly corpora and CC BY-SA reference phonology only; Linear A audio is speculative syllabic reading — no translation claim.

## Per-post matrix

| Post | Language | Excerpt | Source | Lesson IPA | Text label | Pron label |
|------|----------|---------|--------|------------|------------|------------|
| 7 | Biblical Hebrew | *בְּרֵאשִׁית בָּרָא אֱלֹהִים* | WLC Genesis 1:1 | `[bə.ɾeː.ʃiːθ baː.ɾaː ʔɛ.loː.hiːm]` | Attested | Attested tradition (Tiberian) |
| 8 | Linear A | *a-sa-sa-ra-me* | GORILA / Hagia Triada | `[ˈa ˈsa ˈsa ˈɾa ˈme]` ⚠️ | Attested script / undeciphered language | Reconstructed / speculative |
| 9 | Classical Sanskrit | *अग्निमीळे पुरोहितं* | Rig Veda 1.1.1 | `[ˈɐɡnɪm iːɭe pʊroːɦɪt̪ɐm]` | Attested | Reconstructed (Vedic) |
| 10 | Hittite | *nu-za-kán ḫa-a[n-…]* | Hittite Laws §1 | `[ˈnu ˈza ˈkaːn ˈxaː]` | Attested | Reconstructed |

## Corpus paths

| Slug | `known_texts.json` | Prior state |
|------|-------------------|-------------|
| `biblical-hebrew` | `languages/dead/biblical-hebrew/corpus/known_texts.json` | empty |
| `linear-a` | `languages/undeciphered/linear-a/corpus/known_texts.json` | **no corpus dir** |
| `classical-sanskrit` | `languages/dead/classical-sanskrit/corpus/known_texts.json` | empty |
| `hittite` | `languages/extinct/hittite/corpus/known_texts.json` | empty |

## Linear A uncertainty (Post 8)

- `confidence`: `unknown` (language/meaning undeciphered)
- `text_confidence`: `attested_script_undeciphered`
- `decipherment_status`: `undeciphered`
- `uncertainty_flags`: undeciphered, phonetic_values_partly_inferred, proposed, debated
- Cross-link: `communication-modalities/writing-systems/linear-a-script/research/brain/latest_scrape.json`
- **Render rule:** avatar may speak syllables; do **not** claim translation or attested phonology

## Batch artifact

`DAVID/data/T5_corpus_inputs_posts_7-10.json`

## Notes

- Hebrew lesson IPA uses Tiberian scholarly convention (attested reading tradition), not Modern Hebrew revival.
- Sanskrit lesson IPA is Vedic reconstruction per content spec, not modern Indic pronunciation.
- Hittite excerpt truncated at lacuna; IPA covers speakable opener `nu za kán ḫa-a` only.
- Ready for render scripts and `grok_training_pack_builder.py` refresh per language.