# Run 3 Dataset Quality Audit — `david_dataset.jsonl`

*DAVID/training/run3_dataset_audit.md · Generated 2026-06-23*

## TL;DR

Run 3 regressed to **loss 1.2837** from Run 2's **0.6932** despite +787 pairs and
the same model/rank. The regression is a **data-quality**, not a capacity, problem.
The new pairs introduced three concrete defects that directly raise loss:

1. **38 contradictory duplicates** — new pairs that re-answer a prompt already in
   the Run 2 set with a *different* gold output. The model sees one prompt → two
   targets. This is the single largest loss driver.
2. **Phantom-input / hallucinated-source pairs** — analysis instructions that say
   "this text" but ship an **empty `input` field**, with outputs that invent a
   specific source (Beowulf, Völuspá, Shuruppak). Teaches the model to fabricate.
3. **Format convention break** — Run 2 put source text in the `input` field on
   **31%** of pairs; the Run 3 additions use `input` on **0.9%**. The
   instruction/input contract the model learned in Run 2 is now contradicted.

Plus a **domain skew**: Gothic + Classical Latin = **43%** of all new pairs.

**Recommended action: hard-cut 48 pairs (lines listed below) and down-sample
Gothic/Latin by ~150 before Run 4.** Expected effect: removes the direct
prompt→conflicting-target contradictions that inflate loss.

---

## 1. Methodology

The Run 3 training file is the working-tree `training/david_dataset.jsonl`
(1,493 pairs). The Run 2 baseline (706 pairs, the committed version `e0e5acd`)
was extracted from git and used as the reference. Pairs were classified
**carried** (exact instruction+input+output match to Run 2) vs **new**.

| Set | Pairs |
|-----|-------|
| Run 3 total | 1,493 |
| Carried unchanged from Run 2 | 697 |
| **New / changed in Run 3** | **796** |
| (Net additions over Run 2: 787; +9 Run 2 pairs were edited in place) | |

Schema is uniform `{instruction, input, output}`; **0 JSON parse errors**. The
defects below are semantic, not structural.

---

## 2. Findings

### 2.1 Contradictory duplicate instructions — 38 pairs ⚠️ PRIMARY

Each of these is a **new** pair whose `instruction` exactly matches a Run 2 pair
but whose `output` differs — often in length, format, *and* facts. The model is
trained on the same prompt mapped to two different gold answers, which mechanically
raises loss on those prompts.

Representative cases:

| Instruction | Run 2 (kept) | Run 3-new (conflicts) | Nature of conflict |
|---|---|---|---|
| *What are the distinctive phonological features of Classical Latin?* | ln24 (100t) "r always **vibrant**" | ln928 (71t) "r always **trilled**" | Paraphrase + reworded fact |
| *…AI audio errors when generating Ancient Greek speech?* | ln19 (58t, prose) | ln1156 (71t, numbered list) | Format divergence |
| *Distinctive phonological features of Middle Egyptian?* | ln287 (80t) | ln860 (40t) | Truncated re-answer |
| *Generate Grok Imagine audio guidance … Middle Egyptian …* | ln6 (96t) | ln859 (58t) | Shortened paraphrase |
| *Distinctive phonological features of Biblical Hebrew?* | ln302 (46t) | ln1124 (25t) | Truncated re-answer |

All 38 follow the same pattern: a Run 2 answer that helped reach 0.69 loss now has
a competing Run 3 variant. **Cut the new variant, keep the Run 2 one.**

New-pair lines to cut (38):
```
698 699 700 702 738 739 740 742 778 779 780 782 818 819 820 822
858 859 860 862 928 983 994 1078 1124 1143 1156 1171 1299 1302
1328 1383 1488 1489 1490 1491 1492 1493
```

> Note: a separate **16 "Living" template groups** and ~30 "surprising-fact /
> memorable-feature" template groups also normalize to one instruction string with
> many outputs — but these are **pre-existing Run 2 design** (intentional variety
> across languages/variants) and Run 2 still hit 0.69, so they are **not** the
> regression cause and are **not** recommended for cutting.

### 2.2 Phantom-input / hallucinated-source pairs — 10 pairs ⚠️

These new instructions reference a text ("Produce a DAVID corpus entry for **this**
Old Norse text", "Situate **this** text…") but the `input` field is **empty**. The
output then fabricates a specific, unprompted source:

| Line | Instruction | Invented source in output |
|---|---|---|
| 707 / 708 | Old Norse corpus entry / situate | Völuspá st. 1 |
| 747 / 748 | Old English corpus entry / situate | Beowulf l. 1 |
| 787 / 788 | Sumerian corpus entry / situate | Instructions of Shuruppak |
| 827 / 828 | (Akkadian) | (fabricated) |
| 867 / 868 | (Middle Egyptian) | (fabricated) |

In Run 2 this exact instruction type **always** carried the source in `input`
(e.g. ln "Situate this Ancient Greek text" + `input: "γνῶθι σεαυτόν"`). The Run 3
generator dropped the input, so the pair now teaches the model to **invent a
source when none is given** — direct hallucination training. Cut or repair (move
the fabricated text into `input`).

Lines to cut (10): `707 708 747 748 787 788 827 828 867 868`

Broader symptom: **79** new analysis/translation-style instructions ("translate /
render / parse / gloss / produce corpus entry … this text") have an empty `input`.
The 10 above are the worst (they hallucinate a named source); the rest are generic
enough to be lower-risk but still violate the convention.

### 2.3 Format inconsistency vs Run 2

| Metric | Run 2 | Run 3-new | Read |
|---|---|---|---|
| Non-empty `input` field | **31.4%** | **0.9%** | **Major break** — input contract abandoned |
| Output starts with `**bold header**` | 62.6% | 68.0% | Minor drift |
| Output contains markdown | 72.8% | 81.2% | Minor drift |
| Output tokens (median / mean / max) | 33 / 38 / 154 | 26 / 28 / 85 | New pairs systematically shorter |

The dominant issue is the **`input` field collapse**. Run 2 taught a two-slot
contract (instruction = task, input = source text → analysis of that source). The
Run 3 additions fold everything into `instruction` and leave `input` empty, so the
model receives contradictory structural signal across the merged set. New outputs
are also ~25% shorter on average, consistent with the truncated re-answers in §2.1.

### 2.4 Domain overrepresentation

| Language | Run 2 share | Run 3-new share | New count |
|---|---|---|---|
| **Gothic** | 5.7% | **22.5%** | **179** |
| **Classical Latin** | 11.2% | **20.7%** | **165** |
| Classical Sanskrit | 5.4% | 9.2% | 73 |
| Ancient Greek | 5.1% | 8.2% | 65 |
| Biblical Hebrew | 5.7% | 7.8% | 62 |
| Akkadian | 5.7% | 6.4% | 51 |
| Old Norse | 5.0% | 4.9% | 39 |
| Middle Egyptian | 5.1% | 4.6% | 37 |
| Old English | 3.4% | 4.4% | 35 |
| Sumerian | 4.0% | 3.3% | 26 |
| Hittite / Etruscan / Anglo-Norman | ~5% each | **0 new** | 0 |

Run 2 was deliberately balanced (no language above ~11%). The Run 3 additions are
**43% Gothic+Latin** and add **nothing** for Hittite, Etruscan, or Anglo-Norman.
This skews the gradient toward two languages and dilutes the others — not a direct
loss driver, but a quality/coverage regression worth correcting.

### 2.5 Short outputs (<10 tokens) — informational, NOT a Run 3 cause

95 pairs have outputs under 10 tokens — but **all 95 are carried from Run 2**
(min new-pair output = exactly 10 tokens; the Run 3 generator enforced a floor).
They are terse-by-design tutoring one-liners (e.g. *"Qu = single /kʷ/ sound like
'quick'."*, 7t). Since Run 2 trained to 0.69 *with* these present, they are **not**
the regression and cutting them is **optional cleanup**, not a fix. The only
short-output concern that matters is where they sit inside the §2.1/§2.3 conflict
groups, which the cuts above already address.

---

## 3. Recommended cuts before Run 4

### Tier 1 — Hard cut (48 pairs) — directly removes loss-inflating contradiction
- **38** contradictory-duplicate new pairs (§2.1)
- **10** phantom-input hallucination pairs (§2.2)

Union of line numbers to delete from `david_dataset.jsonl`:
```
698 699 700 702 707 708 738 739 740 742 747 748 778 779 780 782
787 788 818 819 820 822 827 828 858 859 860 862 867 868 928 983
994 1078 1124 1143 1156 1171 1299 1302 1328 1383 1488 1489 1490
1491 1492 1493
```
(No overlap between the two sets; 48 distinct lines. This drops Run 3 from 1,493 →
1,445 pairs and eliminates every same-prompt/conflicting-target collision the new
data introduced.)

### Tier 2 — Rebalance (down-sample ~150 pairs)
- Cap **Gothic** (179 new) and **Classical Latin** (165 new) at ~70–80 each,
  keeping the highest-quality/most-distinct examples. Removes ~150–190 pairs and
  restores the Run-2 balance (no language >~12%).
- Prefer to keep, per language, one canonical answer per instruction template;
  drop near-duplicate template re-fills.

### Tier 3 — Repair (don't cut, fix the generator)
- Restore the **`input`-field convention**: for any instruction that references
  "this text / passage / the following," the source belongs in `input`. Either
  re-emit the ~79 affected new pairs with a populated `input`, or rephrase the
  instruction to be self-contained. This is the structural fix that prevents §2.2
  and §2.3 from recurring in Run 4's generation.

### Expected outcome
Tier 1 alone should recover most of the regression (it removes the literal
prompt→two-targets contradictions). Tier 2+3 restore balance and the
instruction/input contract, and should push Run 4 back below Run 2's 0.6932 given
the larger, de-noised corpus. Re-run `david_dataset_builder.py` with the input-field
fix rather than hand-deleting if the builder is the source of truth — the line
numbers above are for the current materialized file.

---

## 4. Reproduction

```bash
# baseline = committed (Run 2, 706 pairs); working tree = Run 3 (1,493)
git show e0e5acd:training/david_dataset.jsonl > run2_baseline.jsonl
# audit scripts: scratchpad/audit.py, audit2.py, audit3.py, cutlist.py
```
Classification is exact-match diff of normalized (instruction, input, output)
triples; domain tagging is first-language-keyword match over the concatenated
fields. Counts: 1,493 total · 697 carried · 796 new/changed · 0 parse errors ·
38 contradictory dupes · 10 phantom-input · 95 short (all carried).
