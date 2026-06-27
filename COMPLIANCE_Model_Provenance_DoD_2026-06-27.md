# Model Provenance & Remediation Record — Llama-only Baseline (DoD/DOJ)

**Date:** 2026-06-27
**Scope:** All product repos in this monorepo — `AI`, `DAVID`, `Stonebridge`, `Nexus` — and the parent.
**Owner:** Benjamin Cartwright

## 1. Statement of compliance
All products are standardized on a **US-origin (Meta Llama) model baseline**. No People's
Republic of China (PRC) jurisdiction model, distillation, API backend, or credential is
referenced in the deployed code of any repo as of the remediation commits below.

**Canonical bases:**
- ELEANOR / NEXUS (70B): `meta-llama/Llama-3.3-70B-Instruct` (`unsloth/Llama-3.3-70B-Instruct-bnb-4bit`)
- DAVID / MATILDA / ATREIDES 7B-class agents / studio (8B): `meta-llama/Meta-Llama-3.1-8B-Instruct` (`unsloth/Meta-Llama-3.1-8B-Instruct-bnb-4bit`)
- Source of truth: `AI/tools/eleanor_model_registry.json`

## 2. What was found and removed
1. **Remote inference backend** posting to a PRC-jurisdiction API endpoint in the reasoning
   pipeline — removed; reasoning now routes to a US provider (Anthropic) or a local stub only.
2. **Base-model pointers** to a non-US distill (7B/14B) across training pipelines, inference
   scripts, configs, registries, and docs — repointed to the Llama baselines above.
3. **Derived model artifacts (Stonebridge/ATREIDES):** 18 LoRA adapter directories whose base
   was the non-US distill (committed weights + configs) — **deleted**. Provenance is preserved
   by deletion, not by relabeling (relabeling would falsify the training record).
4. **Datasets generated for that pipeline** (ATREIDES ELEANOR v1–v6, ELEANOR component corpora,
   ELIOT/ARGUS dataset_v1) and relabeled run-logs — **deleted** (regenerable on the Llama baseline).
5. **Billing guard** renamed to a provider-agnostic `billing_guard.py` (env: `BILLING_MAX_CALLS`,
   `ANTHROPIC_API_KEY`) in all 5 locations; importers updated.
6. **Dead credential string** — a previously-revoked API key string recorded in a NEXUS doc note
   was removed. (The live key was env-var managed and revoked; this was an inert record, not a
   leaked secret.)

## 3. Remediation commits (clean HEADs)
| Repo | Commit |
|------|--------|
| AI | `798d4a6` |
| DAVID | `1fa5c34` |
| Stonebridge | `83f1610` |
| Nexus | `328fd03` |
| Parent (gitlink bumps + DAVID files) | `4df7f6b` |

## 4. Verification
- Method: `git grep -i deepseek` and `git grep -i "xi jinping"` over each repo's tracked tree.
- Result: **0 matches** in all four repos. All changed `.py` compile; all `.json`/`.jsonl` parse.
- Submodule pointers: parent gitlinks == submodule HEADs == origin for AI/Nexus/Stonebridge.

## 5. Scope notes (intentional non-actions)
- **"China" as subject matter is preserved.** Educational/historical content (e.g. Chinese
  writing systems and sign language in DAVID; historical figures such as Confucius, Qin Shi
  Huang, Genghis Khan in HISTORY feeders; incidental mentions in compliance research scrapes)
  is legitimate product content and is **not** in scope. The rail targets PRC-jurisdiction AI
  *vendor/model/API*, not the topic of China.
- **Git history** retains the pre-remediation references. This is an honest, dated remediation
  trail; the *deployed artifacts* (current HEADs) are clean. A history rewrite is not performed
  unless a specific contract clause requires zero historical references — it is fleet-wide
  disruptive (rewrites SHAs, breaks gitlinks and concurrent work) and providers cache old
  commits post-force-push regardless.

## 6. Recommended ongoing control
Extend the model-consistency gate (`AI/tools/check_model_consistency.py` against
`eleanor_model_registry.json`) to cover the operative defaults in `finetune_pipeline.py` and
every `*_infer.py`, so a future edit cannot silently revert a base model to a non-US source
while the gate stays green.
