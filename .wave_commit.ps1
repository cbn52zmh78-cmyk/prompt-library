# DISABLED 2026-06-26 -- auto-commit sweep neutralized.
# Original body ran `git add -A` (Science/Studio submodules) and
# `git push --force origin main` on parent + Science + Studio, which
# clobbered submodule pointers and polluted history. Gutted so it can
# never sweep regardless of the T4_244 pause-gate state.
# Manual, path-scoped commits only. See CLAUDE.md sweep directive.
Write-Host "DISABLED -- see CLAUDE.md sweep directive"
exit 0
