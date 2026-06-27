# ELEANOR-DAVID (variant)

The **ELEANOR-DAVID governance layer** -- the ELEANOR variant scoped to the DAVID
language product. This is **not** a full standalone agent; it is a thin governance
/ compliance layer that sits on top of DAVID's base model and inherits its
architecture from the base ELEANOR.

- **Variant of:** `AI/ELEANOR/` (the base model -- see that tree for the canonical
  architecture, the five intrinsic subagents Memory / Deliberation / Voice /
  Planner / Watcher, and the base training corpus).
- **Base model:** `meta-llama/Llama-3.1-8B-Instruct` (DAVID's base; the base
  ELEANOR is Llama 3.3 70B -- the variant is 8B, layered on DAVID).
- **Scope:** `language_product_governance` -- DAVID-product-specific governance of
  language / translation / archive tasks (e.g. provenance, licensing, and
  use-scope rails for the language product). The variant is hypertrained on
  DAVID-specific compliance, the way ELEANOR-ATREIDES is for the LE fleet.
- **Status:** `scaffold` -- structure only; no variant corpus or adapter yet.

## Layout

```
DAVID/ELEANOR/
  training/
    eleanor_dataset/            variant-specific corpus shards (eleanor_david_*_corpus.jsonl)
    eleanor_train_config.json   variant train config (Llama 3.1 8B)
    eleanor_dataset_builder.py  variant dataset builder (stub)
    eleanor_infer.py            variant adapter inference (stub)
  research/                     variant research docs
  models/adapters/              variant adapter outputs (eleanor-david-8b_*)
```

## Rules

- Do **not** copy the base ELEANOR corpus into this folder. The variant trains
  only on DAVID-product-specific governance pairs, layered on the base.
- All files here are ASCII-safe.
- Mirror the base ELEANOR tooling (`AI/ELEANOR/training/`) when fleshing out the
  stubs; keep the variant scoped and minimal.
