# prompt_library

Central prompt store and Nexus ecosystem health tools for Grok Projects.

## Tools

| Script | Purpose |
|--------|---------|
| `prompt_manager.py` | Add, list, and retrieve categorized prompts |
| `agent_health_monitor.py` | Folder existence check across Grok repos |
| `nexus_status.py` | Repo git status + prompt counts |

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
```

## GitHub

https://github.com/cbn52zmh78-cmyk/prompt-library