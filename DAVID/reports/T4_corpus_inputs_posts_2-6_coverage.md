# T4 corpus inputs — Posts 2–6 coverage note (#72)

_Batch `T4_corpus_inputs_posts_2-6` · catalogued 2026-06-18 · **5/5 ok**._

Scope: Sumerian, Ancient Greek, Old Norse, Akkadian, Middle Egyptian — each with attested excerpt, source citation, cited lesson IPA, and on-screen text/pronunciation labels per `content_concepts_v1.md`.

Guardrails: public scholarly corpora and CC BY-SA reference phonology only; brain-scrape language-name IPA not used as excerpt IPA where content spec supplies lesson reconstruction.

## Per-post matrix

| Post | Language | Excerpt | Source | Lesson IPA | Text label | Pron label |
|------|----------|---------|--------|------------|------------|------------|
| 2 | Sumerian | *ud re-a ud su-ra re-a* | ETCSL 5.6.1 L1 | `[ˈud ˈreː.a ˈud ˈsuː.ra ˈreː.a]` | Attested | Reconstructed |
| 3 | Ancient Greek | *γνῶθι σεαυτόν* | Diogenes Laertius *Lives* 1.40 | `[ɡnôːti seautón]` | Attested | Reconstructed (Classical) |
| 4 | Old Norse | *Hljóðs bið ek allar* | Völuspá st. 1, Codex Regius | `[ˈhljoːðs ˈbið ˈek ˈɑlːɑr]` | Attested | Reconstructed (Old Icelandic) |
| 5 | Akkadian | *ša nagba imuru* | Gilgamesh SB Tablet I | `[ʃaː ˈnag.ba iˈmu.ru]` | Attested | Reconstructed |
| 6 | Middle Egyptian | *ꜥnḫ wḏꜣ snb* | Allen/Gardiner; NK stelae | `[ˈʕaːnax ˈwaːḏaʕ ˈsanax]` | Attested | Reconstructed |

## Corpus paths

| Slug | `known_texts.json` | Prior state |
|------|-------------------|-------------|
| `sumerian` | `languages/dead/sumerian/corpus/known_texts.json` | no corpus dir |
| `ancient-greek` | `languages/dead/ancient-greek/corpus/known_texts.json` | empty |
| `old-norse` | `languages/extinct/old-norse/corpus/known_texts.json` | empty |
| `akkadian` | `languages/dead/akkadian/corpus/known_texts.json` | no corpus dir |
| `middle-egyptian` | `languages/extinct/middle-egyptian/corpus/known_texts.json` | empty |

## Batch artifact

`DAVID/data/T4_corpus_inputs_posts_2-6.json`

## Notes

- Each entry includes `line_ipa_derivation` linking lesson IPA to brain scrape and public citation.
- Sumerian and Akkadian lesson IPA uses Wikipedia phonology from `latest_scrape.json` plus attested transliteration; vowels are reconstructed throughout.
- Greek, Old Norse, and Middle Egyptian lesson IPA follows `content_concepts_v1.md` card values (not Wiktionary language-name entries).
- Ready for T5 render scripts and `grok_training_pack_builder.py` refresh per language.