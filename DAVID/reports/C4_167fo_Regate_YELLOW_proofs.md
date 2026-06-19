# C4 #167 follow-on — Housekeeping: de-dupe + re-gate of the 2 YELLOW STUDIO proofs

**Owner:** C4 · **Date:** 2026-06-19 · **Scope:** clear C4's own #167 Appendix-A flags
**Gate def:** `DAVID/reports/C4_167_PrePublish_QA_Gate.md`

## 1. De-dupe — DONE
Two stray `gfe_companion_*` proof folders under `DAVID/productions/` removed; canonical pair
retained under `STUDIO/Productions/Companion/`.

| Removed (stray) | Why safe | Canonical kept |
|---|---|---|
| `DAVID/productions/gfe_companion_sage_proof_v1_longform_v1` | script.json was a **stripped/stale partial** (no `intake.gate_0`, no guardrails/production_meta); `qa_report.json` **byte-identical** to STUDIO's (same render). | `STUDIO/.../gfe_companion_sage_proof_v1_longform_v1` (carries `production_dir`, full intake, own seamless master) |
| `DAVID/productions/gfe_companion_violet_proof_480p_v1_longform_v1` | contained only a stray `render_log.txt`; the log itself sources script/identity/avatar from the **STUDIO** copy. | `STUDIO/.../gfe_companion_violet_proof_480p_v1_longform_v1` (full output + 36 chains) |

No code/manifest referenced the DAVID copies (grep clean). Removed via `git rm`.

> Note on the #167 flag: Appendix A described DAVID/sage as "renders, **no script.json**". A
> stripped script.json had since appeared in that folder — surfaced here rather than ignored.
> It is **not** canonical (missing the whole intake block), so the de-dupe call stands.

## 2. Re-gate — DONE (both remain YELLOW, human-signed)

| Proof | Re-gate path | Verdict | Latest report |
|---|---|:---:|---|
| `david_julius_caesar_figure_proof_480p_v1` | `production_intake.py` from concept (canonical) | **YELLOW** | `GATE_YELLOW_..._015013.json` |
| `gfe_companion_sage_proof_v1` | embedded `intake.gate_0` (no concept exists) | **YELLOW** | governed by script `intake.gate_0` |

Both are **legitimately YELLOW (human-signed)** — fine for proof use, **HOLD for any real publish**.
YELLOW driver in each is the same: checklist rows `row_1_synthetic_ownership` / `row_3_no_real_likeness`
sit MANUAL + numerical performer age not stated. To reach **GREEN** a proof must: (a) state the
synthetic performer's numerical age, (b) burn/declare the AI-disclosure, (c) sign the synthetic-
ownership + no-real-likeness manual rows.

### Gate-bug surfaced (do NOT re-introduce)
Running the **raw** `artifacts/legal/legal_gate.py` CLI directly on a *finished script.json* produces
**false** verdicts and must not be used as the re-gate path for proofs:
- **sage → false COUNSEL:** `COUNSEL_PATTERNS` are **negation-blind** (unlike `CHANNEL_CHECKS`,
  they don't use `_affirmed_pattern_match`), so the guardrail line *"no real person likeness"*
  trips the living-person-likeness COUNSEL flag. This is the exact pitfall already documented in
  the #167 gate doc (Dimension 2).
- **julius → false RED:** the free-text scan can't read the **structured** `historical_figure.death_year`
  (−44) that the concept/script carries, so it raises `[HISTFIG] death_year missing`. The canonical
  `production_intake` path reads the structured field and correctly returns YELLOW.

**Cleanup:** the 3 false-positive reports this pass generated (sage ×2 COUNSEL, julius ×1 RED) plus
their `.md`/CARA byproducts were pruned so the **latest-wins** gate rule is not poisoned. The only
fresh standalone report kept is the canonical julius **YELLOW** (015013).

## Cross-refs
- Pre-Publish gate: `DAVID/reports/C4_167_PrePublish_QA_Gate.md`
- Latin SHIP verdict: `DAVID/reports/C4_167_VERDICT_david_latin_corpus_v1.md`
- Gate CLI / intake: `artifacts/legal/legal_gate.py` · `STUDIO/Pipeline/production_intake.py`
