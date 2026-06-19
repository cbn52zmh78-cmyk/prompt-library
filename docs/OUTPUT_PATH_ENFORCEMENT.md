# Output-Path Enforcement (#259)

**The permanent fix for output fragmentation.** Terminals fan out, each writes where it
feels like, and someone runs a consolidation pass afterward. This replaces that with a
*registry + validator + path-stamping* so outputs land canonically the first time and any
stray output is caught by a gate instead of a human.

Modules (pure stdlib, `tools/`):

| Module | Role |
|--------|------|
| `tools/output_registry.py` | Canonical-path **registry** + **path-stamping** |
| `tools/output_validator.py` | **Validator**: scan for scatter / verify stamps |

---

## 1. Registry — where an output *belongs*

One declarative map of logical *output kinds* → canonical location + filename template.
Terminals ask the registry instead of hardcoding a path.

```python
import sys; sys.path.insert(0, "tools")
from output_registry import resolve, classify, rel_canonical

resolve("gate_report",   filename="GATE_GREEN_x_20260619_editorial.md")
#   → .../Studio/Legal/Gate_Reports/GATE_GREEN_x_20260619_editorial.md   (parents created)
resolve("batch_manifest", batch_id="T4_181_science_molecular")
#   → .../DAVID/batches/T4_181_science_molecular/manifest.json
resolve("production", lane="Narrative", slug="pi_story")          # is_dir kind
classify("DAVID/batches/B/manifest.json")     # → "batch_manifest"
```

Registered kinds: `python tools/output_registry.py list`. Add a kind by appending one
`OutputKind(...)` to `_KINDS` — never invent a path in a producer.

### Canonical casing

The workspace was addressed as both `Studio/` and `STUDIO/` (same dir on Windows, two
strings in code) — a primary fragmentation source. The registry declares one canonical
spelling per top-level dir (`CANONICAL_TOP`). `canonicalize()` / `rel_canonical()` rewrite
drift; `has_case_drift()` and `is_canonical()` flag it.

---

## 2. Path-stamping — every output *declares* where it lives

`write_stamped()` resolves the canonical path, writes the payload, embeds an
`_output_stamp` provenance block (JSON payloads) or a `<file>.stamp.json` sidecar (text /
binary), and appends one line to the append-only ledger `data/output_ledger.jsonl`.

```python
from output_registry import write_stamped
write_stamped("compliance_report",
              {"verdict": "GREEN", "...": "..."},
              params={"filename": "CARA_foo_20260619.json"},
              terminal="C3")
```

Each ledger line records `key`, `kind_root`, `canonical_path`, `stamped_at`, and
`terminal`. Producers that already write to a canonical sink can adopt incrementally by
calling `record_ledger(make_stamp(kind, path, ...))` after their write — as the Editorial
Gate (`artifacts/legal/editorial_gate.py`, #213) now does.

---

## 3. Validator — the gate that replaces consolidation passes

```bash
python tools/output_validator.py scan          # sweep workspace; exit 1 on any scatter
python tools/output_validator.py scan --fix    # also remove EMPTY stray root files (e.g. "=")
python tools/output_validator.py check <path>... [--kind gate_report]
```

`scan` flags:

- **`ROOT_SCATTER`** — files dumped at the workspace root (redirection artifacts like `=`,
  loose `*.json` reports). Dotfiles + an explicit allowlist (`README.md`, `requirements.txt`,
  `*.ps1`/`*.toml`, …) are permitted.
- **`LEDGER_NONCANON`** — a stamped output whose on-disk path drifted from canonical.
- **`LEDGER_CORRUPT`** — an unparseable ledger line.

`--fix` only removes *empty* stray root files; it never deletes non-empty data.

`lint` flags:

- **`SOURCE_DRIFT`** — a non-canonical top-level path literal in producer source, e.g.
  `"STUDIO/Productions/…"` (should be `Studio/`). Tests and the registry/validator are
  excluded (they reference drift spellings deliberately). This is the gate that keeps the
  #282 migration from regressing — every producer stays canonical or `lint` exits 1.

### Run it as a round-boundary gate

Run `python tools/output_validator.py scan` at every fan-out boundary (or in CI / the wave
commit hook). Exit 1 means scatter exists — fix the producer (point it at `resolve()`),
don't run a manual consolidation pass.

---

## Adoption checklist for a producer

1. Replace any hardcoded output path with `resolve(kind, **params)` (add a kind if needed).
2. Prefer `write_stamped(...)`; or keep your write and add `record_ledger(make_stamp(...))`.
3. Add a test asserting your path is canonical:
   `assert output_validator.check_paths([p], expected_kind="<kind>") == []`.
4. Ensure `python tools/output_validator.py scan` stays green.

## Adoption status (#282)

The 27 producers that hardcoded non-canonical path literals have been migrated to canonical
casing, and the **compliance / GroundTruth / render** writers now ledger-stamp every output
via `note()`:

- compliance — `artifacts/compliance/content_rating_compliance_guard.py`
- render — `DAVID/scripts/{render_longform,batch_runner,science_batch_runner}.py`
- GroundTruth — `Science/scripts/groundtruth_knowledge_gate_v2.py` (kind `groundtruth_pack`)

Drift handlers (`.replace`/`.startswith` on legacy path strings) were made case-tolerant
(`split("/")[0].lower() == "studio"`) or routed through `rel_canonical()`. `lint` is green
across all producer trees and is the standing regression gate.

*Issue #259 — registry + validator + path-stamping. Issue #282 — 32 producers migrated.
No more consolidation passes after every fan-out.*
