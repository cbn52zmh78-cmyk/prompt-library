# Language Atlas — Dead Tongues, Lost Scripts, Continuous Research

**Core question:** *What did they actually say — and how do we prove it?*

The Language module is the David protocol layer: corpus-first linguistic research, dead-language revival scaffolding, and Grok training packs built from attested texts — not invention.

```
User / Editor (foreign languages)
        ↓
   Language Atlas — registry · corpus · research · training packs
        ↓
   History (figure-linked primary sources) · Grok (context injection)
```

---

## What it owns

| Language Atlas | Other layers |
|----------------|--------------|
| Language registry & revival tiers | Historical figure narratives → **History** |
| Attested corpus cataloguing | Cinematic output → **Studio** |
| Research query generation | Multi-agent routing → **AI** |
| Grok training packs from known texts | Ecosystem registry → **Nexus** |
| David linguist system prompt | Living-language editorial → **Editor** |

## Structure

```
Language/
├── data/
│   ├── language_registry.json    # Master language index
│   └── research_queue.json       # Continuous research backlog
├── languages/
│   ├── living/ | dead/ | extinct/ | reconstructed/ | undeciphered/
│   └── {slug}/
│       ├── profile.json
│       ├── corpus/known_texts.json
│       ├── research/             # notes, sources, search queries
│       └── grok_training/        # Generated training packs
├── scripts/                      # CLI tools
└── prompts/david_linguist_system.md
```

## Quick start

```bash
python Language/scripts/revival_status_reporter.py
python Language/scripts/language_registry_manager.py list
python Language/scripts/language_registry_manager.py list --tier high
python Language/scripts/research_query_generator.py --language etruscan
python Language/scripts/grok_training_pack_builder.py --language classical-latin
python Language/scripts/language_launcher.py

# From workspace root
python tools/language_status.py
```

## Add a new language

```bash
python Language/scripts/language_initializer.py \
  --slug hittite --name "Hittite" --status dead \
  --family "Indo-European (Anatolian)" --period "c. 1650–1200 BCE"

python Language/scripts/corpus_cataloguer.py \
  --language hittite --title "Treaty of Kadesh excerpt" \
  --transliteration "..." --translation "..." \
  --source "Boğazköy archive"

python Language/scripts/grok_training_pack_builder.py --language hittite
```

## Revival tiers

| Tier | Meaning |
|------|---------|
| `active` | Living or continuous liturgical use |
| `high` | Extinct but strong attested corpus |
| `medium` | Partial corpus or heavy reconstruction |
| `research` | Undeciphered or purely reconstructed |

## Seeded languages (v1.0)

Etruscan, Gothic, Linear A, Sumerian, Proto-Indo-European, Classical Latin, Classical Nahuatl, Akkadian, Old English, Classical Japanese.

Latin and Classical Japanese link to **History** figures (Caesar, Aurelius, Murasaki Shikibu).

---

*Bring the dead tongues back one attestation at a time.*