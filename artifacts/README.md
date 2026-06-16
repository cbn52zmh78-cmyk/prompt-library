# artifacts — Studio Production Toolchain

Python CLI tools for Studio video and editorial production. Outputs land in `Studio/Pipeline/`. Compliance reports land in `Studio/Producers_Office/Compliance_Reports/`.

## Install

```bash
pip install -e artifacts/
```

Optional dashboard deps: `pip install -e "artifacts/[dashboard]"`

## Launch

```bash
python artifacts/core/master_launcher.py
# or from workspace root:
python tools/launcher.py   # → option 2
```

## Layout

| Folder | Purpose |
|--------|---------|
| `core/` | Workspace init, status, integration helpers, master launcher |
| `profile/` | Model profile CRUD |
| `prompts/` | Prompt generation, refinement, scoring |
| `video/` | Multi-shot compile, one-take choreography, shot lists |
| `catalog/` | Reference indexing, metadata sidecars, asset catalog |
| `compliance/` | Version control, canon bibles, consistency auditors |
| `export/` | Grok video pack exporter |

Paths are canonical in `tools/workspace_paths.py`.