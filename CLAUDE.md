# Grok Projects (parent monorepo)

Parent monorepo aggregating submodules (AI, FLASH, History, MAGAZINE, Nexus,
Science/SAGAN, Stonebridge, Studio) plus nested repos (DAVID) and shared tooling.
Each submodule has its own CLAUDE.md; this file governs the parent root.

## Commit & test discipline
- **AUTO-COMMIT SWEEP: DISABLED (2026-06-26).** Agents MUST NOT run `git add -A`
  / "Hard commit sweep ... in-flight capture" checkpoint commits. The sweep
  bundled unrelated files into commits and polluted history across multiple
  submodules. **Manual, path-scoped commits only** -- stage explicit paths,
  never `-A`. Run `git diff --name-only --cached` immediately before every
  commit. To re-enable later, delete this directive.
- Submodule pointer bumps: stage only the submodule path, verify with
  `git diff --name-only --cached` before committing. One session owns parent
  commits at a time -- coordinate with concurrent sessions before pushing parent.
