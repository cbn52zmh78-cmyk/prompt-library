# prompt_library

Central prompt store and Nexus ecosystem health tools for Grok Projects.

## Tools

| Script | Purpose |
|--------|---------|
| `prompt_manager.py` | Add, list, and retrieve categorized prompts |
| `agent_health_monitor.py` | Folder existence check across Grok repos |
| `nexus_status.py` | Repo git status + prompt counts |
| `new_repo.py` | Scaffold a new git repo in home directory |
| `professional_editorial_writer.py` | v2.0 academic scaffold + content generation prompt |
| `decision_log.py` | Log and list project decisions (`decisions.json`) |
| `task_manager.py` | Add, list, and complete tasks (`tasks.json`) |
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
python prompt_manager.py list
python prompt_manager.py add system my_agent "prompt text here"
python nexus_status.py
python agent_health_monitor.py
python new_repo.py My-New-Repo "Short description"
python professional_editorial_writer.py --title "PA Market Q2" --summary "Research notes here" --style APA --domain market --author "Benjamin Cartwright"
python decision_log.py add "Repo layout" "Default new repos to home directory"
python decision_log.py list
python task_manager.py add "Review PA market brief" "Benjamin"
python task_manager.py list
python task_manager.py done 1
python x_publisher.py verify
python repo_sync_checker.py
python x_publisher.py queue add "Draft post text"
python x_publisher.py publish
```

### X API setup

Grok login with X is separate from the Developer API. Fill in `prompt_library/.env` with your four OAuth 1.0a tokens from [console.x.com](https://console.x.com), then run `python x_publisher.py verify`.

**Post on command (ask Grok):** `Post to X: Your message` or `DM @user: Your message`

Requires app permissions: **Read and write and Direct message**. Regenerate access tokens after saving permissions.

## GitHub

https://github.com/cbn52zmh78-cmyk/prompt-library