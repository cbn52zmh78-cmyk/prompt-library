# Grok Projects — AI Systems Workspace

**Canonical path:** `C:\Users\NCG\Videos\Grok Projects`  
**Legacy alias:** `~/prompt_library` (junction → this folder)

Central prompt store and Nexus ecosystem health tools.

## Layout

```
Grok Projects/
├── scripts/             # grok.ps1, launcher.py, dual_ai_helper.py (convenience entry points)
├── tools/               # Python utilities + workspace_paths.py
├── data/                # JSON state (tasks, queues, changelog, etc.)
├── docs/                # generated reference docs
├── prompts/             # categorized prompt library
├── outputs/             # tool output scratch
├── notes/               # quick notes
├── Content_Production/  # editorials + professional document projects
└── …                    # Stonebridge, Nexus, MAGAZINE, etc.
```

## Tools (`tools/`)

| Script | Purpose |
|--------|---------|
| `prompt_manager.py` | Add, list, and retrieve categorized prompts |
| `agent_health_monitor.py` | Folder existence check across Grok repos |
| `nexus_status.py` | Repo git status + prompt counts |
| `new_repo.py` | Scaffold a new git repo in home directory |
| `professional_editorial_writer.py` | v2.0 academic scaffold + content generation prompt |
| `decision_log.py` | Log and list project decisions (`data/decisions.json`) |
| `task_manager.py` | Add, list, and complete tasks (`data/tasks.json`) |
| `compliance_report.py` | Generate state compliance reports from raw markdown |
| `repo_sync_checker.py` | Git cleanliness check for home-directory repos |
| `x_publisher.py` | Post tweets + send DMs via Developer API |

## Prompt categories

```
prompts/
  system/
  orchestration/
  studio/
  compliance/
```

## Quick start

```bash
python tools/prompt_manager.py list
python tools/prompt_manager.py add system my_agent "prompt text here"
python tools/nexus_status.py
python tools/agent_health_monitor.py
python tools/new_repo.py My-New-Repo "Short description"
python tools/professional_editorial_writer.py --title "PA Market Q2" --summary "Research notes here" --style APA --domain market --author "Benjamin Cartwright"
python tools/decision_log.py add "Repo layout" "Default new repos to home directory"
python tools/decision_log.py list
python tools/task_manager.py add "Review PA market brief" "Benjamin"
python tools/task_manager.py list
python tools/task_manager.py done 1
python tools/x_publisher.py verify
python tools/repo_sync_checker.py
python tools/x_publisher.py queue add "Draft post text"
python tools/x_publisher.py publish
python tools/quick_ref.py
```

### X API setup

Grok login with X is separate from the Developer API. Fill in `.env` in this folder with your four OAuth 1.0a tokens from [console.x.com](https://console.x.com), then run `python tools/x_publisher.py verify`.

**Post on command (ask Grok):** `Post to X: Your message` or `DM @user: Your message`

Requires app permissions: **Read and write and Direct message**. Regenerate access tokens after saving permissions.

## GitHub

https://github.com/cbn52zmh78-cmyk/prompt-library