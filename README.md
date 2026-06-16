# Grok Projects — AI Systems Workspace

**Canonical path:** `C:\Users\NCG\Videos\Grok Projects`  
**Legacy alias:** `~/prompt_library` (junction → this folder)

Central workspace for the Nexus ecosystem: ops tooling, Studio production pipeline, prompts, and multi-repo coordination.

## Ecosystem map

```
Grok Projects/
├── tools/               # Nexus ops utilities (status, tasks, git, X API)
├── artifacts/         # Studio production toolchain (prompt gen, video compile)
├── scripts/           # Convenience entry points → tools/
├── data/              # JSON state (tasks, decisions, changelog, queues)
├── prompts/           # Central orchestration prompts (system, orchestration, compliance)
├── Studio/            # Cinematic production assets & outputs (submodule)
├── AI/                # Multi-agent federation (submodule)
├── Science/           # Scientific visualization principles
├── Nexus/             # Registry & workflows
├── History/           # Documentary research & timelines (submodule)
├── Stonebridge/       # Security consulting & compliance (submodule)
├── DAVID/             # Dead-language research, corpus, revival, Grok training
├── GFE/               # GFE video assets
├── MAGAZINE/          # Editorial supermodel assets
└── FLASH/             # Sabermetrics project
```

| Layer | Owns |
|-------|------|
| **Nexus** (`tools/`) | Ecosystem health, tasks, decisions, repo sync, central prompts |
| **artifacts/** | Studio CLI pipeline — profiles, prompts, video packs, compliance |
| **Studio/** | Visual production — references, canons, model profiles, renders |
| **AI** | Multi-agent orchestration, federation routing |
| **Science** | Domain visualization validation (Jantzen, astrophysics, etc.) |
| **Stonebridge** | Client ops, compliance research, SOPs |
| **DAVID** | Dead/extinct language research, attested corpora, Grok training packs |

## Quick start

```bash
# Dependencies
pip install -r requirements.txt
pip install -e artifacts/

# Submodule init (first clone)
git submodule update --init --recursive

# Health & status
python tools/nexus_status.py
python tools/agent_health_monitor.py
python tools/repo_sync_checker.py
python tools/structure_validator.py

# Unified launcher (Nexus ops + Studio pipeline)
python tools/launcher.py

# Studio production tools
python artifacts/core/master_launcher.py

# DAVID (corpus-first dead language research — Prometheus protocol)
python tools/david_status.py
python DAVID/scripts/david_launcher.py
```

## DAVID

Continuous research into living, dead, extinct, and undeciphered languages. Builds Grok training packs from **attested texts only** — revival through evidence, not invention.

```bash
python DAVID/scripts/language_registry_manager.py list --tier high
python DAVID/scripts/grok_training_pack_builder.py --language etruscan
python DAVID/scripts/corpus_cataloguer.py --help
python DAVID/scripts/david_brain_scraper.py --language etruscan --deep --report
python DAVID/scripts/david_research_reporter.py
python DAVID/scripts/david_brain_scheduler.py --daemon --interval 3600
```

See [DAVID/README.md](DAVID/README.md). System prompt: `DAVID/prompts/david_linguist_system.md`.

## Prompt storage

| Location | Use |
|----------|-----|
| `prompts/{category}/` | Central orchestration prompts — add via `prompt_manager.py` |
| `Studio/prompts/` | Studio production bibles & domain prompts (read via `--all`) |

```bash
python tools/prompt_manager.py list --all
python tools/prompt_manager.py add system my_agent "prompt text"
python tools/prompt_manager.py get studio ASTROPHYSICS_PROMPT_BIBLE --studio
```

## Tools (`tools/`)

| Script | Purpose |
|--------|---------|
| `launcher.py` | Unified ecosystem launcher |
| `nexus_status.py` | Repo branches, dirty counts, prompt totals |
| `agent_health_monitor.py` | Folder + nested repo health |
| `repo_sync_checker.py` | Git cleanliness (root + nested repos) |
| `structure_validator.py` | Expected folder scaffold |
| `prompt_manager.py` | Central prompt CRUD + Studio prompt listing |
| `task_manager.py` | Tasks (`data/tasks.json`) |
| `decision_log.py` | Decisions (`data/decisions.json`) |
| `x_publisher.py` | Post tweets + DMs via Developer API |
| `project_indexer.py` | Ecosystem project index (`data/project_index.json`) |

## Artifacts (`artifacts/`)

27+ CLI tools for Studio production. See [artifacts/README.md](artifacts/README.md).

Categories: workspace setup, profiles, prompt generation, video compile, catalog, compliance, export.

## Submodules

Registered in `.gitmodules`:

| Path | Remote |
|------|--------|
| `AI/` | github.com/cbn52zmh78-cmyk/AI |
| `History/` | github.com/cbn52zmh78-cmyk/HISTORY |
| `Stonebridge/` | github.com/cbn52zmh78-cmyk/Stonebridge-Security-Consultants |
| `Studio/` | github.com/cbn52zmh78-cmyk/STUDIO |

**Workflow:** Commit inside each submodule repo separately, then update the pointer in Grok Projects:

```bash
git -C Studio status
git -C Studio add -A && git -C Studio commit -m "message"
git add Studio && git commit -m "Bump Studio submodule"
```

## Tests

```bash
pytest tests/test_artifacts_smoke.py -v
```

## X API setup

Fill `.env` from `.env.example` with OAuth 1.0a tokens from [console.x.com](https://console.x.com), then:

```bash
python tools/x_publisher.py verify
```

Requires app permissions: **Read and write and Direct message**.

## GitHub

https://github.com/cbn52zmh78-cmyk/prompt-library