# Grok Projects (parent monorepo)

Parent monorepo aggregating submodules (AI, FLASH, History, MAGAZINE, Nexus,
Science/SAGAN, Stonebridge, Studio) plus nested repos (DAVID) and shared tooling.
Each submodule has its own CLAUDE.md; this file governs the parent root.

## Rules (auto-loaded from `.claude/rules/`)
- `commit-discipline.md` — staging, diff-check, submodule pointer protocol (all files)
- `meridian-handoff.md` — STATUS.md/preflight/one-task-per-session (Stonebridge/Products/MERIDIAN/ only)

## Hooks (`.claude/hooks/`)
- `pre-commit.sh` — blocks bulk staging, submodule pointer rides, invalid registry JSON

## Local MATILDA (Ollama)

MATILDA 8B Run 10 is available at `localhost:11434` (`matilda` model). For Stonebridge
client-facing narration or trilingual DE/EN/FR content, use skill **ask-matilda** / call:

```
python AI/ELEANOR/products/matilda/matilda_ollama_router.py --lang <de|en|fr|auto> "prompt"
```

Do not use MATILDA for coding, research, or non-Stonebridge tasks. Data stays local.
