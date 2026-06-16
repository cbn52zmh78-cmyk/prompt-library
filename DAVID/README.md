# DAVID — Dead Language Research & Revival

Named for the Prometheus protocol: obsessive, patient, corpus-first.

**Core question:** *What did they actually say — and how do we prove it?*

DAVID is the linguistic research layer: continuous language study, dead-tongue revival scaffolding, and Grok training packs built from attested texts — not invention.

```
User / Editor (foreign languages)
        ↓
   DAVID — registry · corpus · research · training packs
        ↓
   History (figure-linked primary sources) · Grok (context injection)
```

---

## What DAVID owns

| DAVID | Other layers |
|-------|--------------|
| Language registry & revival tiers | Historical figure narratives → **History** |
| Attested corpus cataloguing | Cinematic output → **Studio** |
| Research query generation | Multi-agent routing → **AI** |
| Grok training packs from known texts | Ecosystem registry → **Nexus** |
| David linguist system prompt | Living-language editorial → **Editor** |

## Structure

```
DAVID/
├── data/
│   ├── language_registry.json
│   └── research_queue.json
├── languages/
│   ├── living/ | dead/ | extinct/ | reconstructed/ | undeciphered/
│   └── {slug}/
│       ├── profile.json
│       ├── corpus/known_texts.json
│       ├── research/
│       └── grok_training/
├── scripts/
└── prompts/david_linguist_system.md
```

## Quick start

```bash
python tools/david_status.py
python DAVID/scripts/david_launcher.py
python DAVID/scripts/language_registry_manager.py list --tier high
python DAVID/scripts/grok_training_pack_builder.py --language etruscan
```

## Add a new language

```bash
python DAVID/scripts/language_initializer.py \
  --slug hittite --name "Hittite" --status dead \
  --family "Indo-European (Anatolian)" --period "c. 1650–1200 BCE"

python DAVID/scripts/corpus_cataloguer.py \
  --language hittite --title "Treaty excerpt" \
  --transliteration "..." --translation "..." --source "Boğazköy"

python DAVID/scripts/grok_training_pack_builder.py --language hittite
```

## Revival tiers

| Tier | Meaning |
|------|---------|
| `active` | Living or continuous liturgical use |
| `high` | Extinct but strong attested corpus |
| `medium` | Partial corpus or heavy reconstruction |
| `research` | Undeciphered or purely reconstructed |

---

*Bring the dead tongues back one attestation at a time.*