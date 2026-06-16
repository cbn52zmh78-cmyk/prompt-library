# AGENTS

Director agent scaffolds and NEXUS tooling wrappers (moved from `My_Grok_Projects`).

## Contents

| Path | Role |
|------|------|
| `2026-06-16_Test_Agent_Starter_v1/` | Standard agent project scaffold |
| `2026-06-16_Visualization_Agent_V2/` | Science visualization agent |
| `tools/nexus_launcher.py` | Interactive NEXUS tools menu |
| `tools/market_edge/` | Market Edge issue generator wrapper |
| `tools/x_mcp/` | X API auth check (delegates to `Grok Projects/tools/x_publisher.py`) |

## Quick start

```powershell
python AGENTS\tools\nexus_launcher.py
```

New agent projects: `python Nexus\scripts\nexus_project_starter.py agent "Project Name"`