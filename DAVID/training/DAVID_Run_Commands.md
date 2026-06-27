# DAVID Run Commands Reference
*DAVID/training/DAVID_Run_Commands.md | Updated: June 2026*

---

## Hardware
| GPU | VRAM | Profile | LoRA | Batch × Accum | LR | Notes |
|-----|------|---------|------|---------------|-----|-------|
| L40s | 48GB | `--hardware l40s` | rank=32, α=16 | 2 × 8 | 1e-4 | **RunPod primary** — 14B comfortable |
| RTX 4090 | 24GB | `--hardware 4090` | rank=32, α=16 | 1 × 16 | 1e-4 | 14B fallback — effective batch 16 |
| RTX 2060 | 12GB | `--hardware 2060` | rank=32, α=16 | 1 × 16 | **2e-5** | **Local overnight** — close other apps; lower LR |
| RTX 4060 | 8GB | `--model llama-3.1-8b-lite` | rank=16, α=16 | 1 × 8 | 2e-4 | Legacy 7B path only (no `--config`) |

Slots defined in `training/runpod_train_config.json` → `hardware_slots`.

---

## Run Sequence (RunPod)

### 1. Upload to RunPod
Upload both files to `/workspace/` before starting:
- `david_finetune_pipeline.py`
- `david_dataset.jsonl` ← **For Run 3, upload `david_dataset_run3.jsonl` renamed to `david_dataset.jsonl`**

Optionally upload for post-training inference testing:
- `david_infer.py`

### 2. Train (L40s / RTX 4090)
```bash
pip install "unsloth[colab-new] @ git+https://github.com/unslothai/unsloth.git" --quiet && pip install --no-deps trl peft accelerate bitsandbytes --quiet && mkdir -p /DAVID/models/adapters && python3 /workspace/david_finetune_pipeline.py --run --epochs 5 --tag run1
```
- Update `--tag` each run (run1, run2, …)
- Adapter output: `/DAVID/models/adapters/david-7b_YYYYMMDD_HHMMSS_run1`

### 3. (Optional) Test inference before download
```bash
python3 /workspace/david_infer.py --adapter /DAVID/models/adapters/david-7b_YYYYMMDD_HHMMSS_run1 --all
```
Quick smoke test (one prompt per pillar):
```bash
python3 /workspace/david_infer.py --adapter /DAVID/models/adapters/david-7b_YYYYMMDD_HHMMSS_run1
```
Ad-hoc prompt:
```bash
python3 /workspace/david_infer.py --adapter /DAVID/models/adapters/david-7b_YYYYMMDD_HHMMSS_run1 --prompt "Translate this Classical Latin text." --input "Arma virumque cano"
```

### 4. Stage adapter for download
```bash
cp -r /DAVID/models/adapters/david-7b_YYYYMMDD_HHMMSS_run3 /workspace/
```
Update the folder name to match actual run output. Dataset (`david_dataset.jsonl`) is already in `/workspace/` — no copy needed.

### 5. Download
Use the **RunPod file manager UI** to download from `/workspace/`:
- Adapter folder (e.g. `david-7b_20260623_234920_run3/`)
- `david_dataset.jsonl`

Adapter is ~6–7GB for llama-3.1-8b. **DO NOT use runpodctl. DO NOT stop the pod before both files are downloaded.**

### 6. Kill the pod
Kill immediately after download — no idle time.

---

## Local adapter storage
```
C:\Users\NCG\Videos\Grok Projects\DAVID\models\adapters\
```

---

## Dry-run / check (local)
```bash
python3 training/david_finetune_pipeline.py --check --hardware 2060
python3 training/david_finetune_pipeline.py --stub --hardware 2060 --tag inspect-2060
```

## Local overnight (RTX 2060 12GB — no pod)
```bash
# Stub first — verify hyperparams + step estimate
python training/david_finetune_pipeline.py --stub --hardware 2060 --tag run5-local

# Live — close other GPU apps; expect ~735 steps @ 2,351 pairs × 5 epochs
ALLOW_GPU_TRAIN=1 python training/david_finetune_pipeline.py --run --hardware 2060 --tag run5-local
```
Wrapper equivalent:
```bash
ALLOW_GPU_TRAIN=1 bash training/train_david.sh --live --hardware 2060 --tag run5-local
```
Adapter output: `models/adapters/david-7b_YYYYMMDD_HHMMSS_run5-local`

---

## Epoch strategy
| Pairs | Epochs | ~Steps (L40s, rank=64) | Notes |
|-------|--------|------------------------|-------|
| 706   | 5      | ~220                   | **Run 1 baseline** |
| 706   | 8      | ~352                   | **Run 2** — prior best at 0.6932 |
| 1,493 | 5      | ~470                   | **Run 3a** — undertrained at new scale; regressed |
| 2,351 | 5      | ~730                   | **Run 4** — insufficient epochs; loss 1.1772 |
| 2,351 | 10     | ~1,470                 | **Run 5** — correct epoch budget for dataset size |

Compare to ELEANOR: 3,643 pairs × 5 epochs = 1,140 steps → 0.5617 loss.
**Rule:** when dataset size increases, bump epochs proportionally — 5 epochs on 706 pairs ≠ 5 epochs on 2,351 pairs.

---

## Run Log

| Run | Model | Rank | Epochs | LR | Dataset Pairs | Final Loss | Adapter | Status |
|-----|-------|------|--------|-----|--------------|------------|---------|--------|
| Run 1 | llama-3.1-8b | 64 | 5 | 1e-4 | 706 | **1.0119** | — | Baseline |
| Run 2 | llama-3.1-8b | 64 | 8 | 1e-4 | 706 | **0.6932** | — | **Prior best** — loss still dropping at end |
| Run 3a | llama-3.1-8b | 64 | 5 | 1e-4 | 1,493 | **1.2837** | `david-7b_20260623_230354_run3` | **LOST** — pod killed before download |
| Run 4 | llama-3.1-8b | 64 | 5 | 1e-4 | 2,351 | **1.1772** | `david-7b_20260624_035711_run4` | Dataset mismatch — undertrained at 5 epochs |
| Run 5 | llama-3.1-8b | 64 | **10** | **2e-4** | 2,351 | *in progress* | `david-7b_20260624_045918_run5` | **New best** — broke 0.6932 at epoch 3.1 |

### Runs 3–4 regression — root cause

Runs 3 and 4 regressed from Run 2's **0.6932** because the dataset was scaled up (706 → 1,493 → 2,351 pairs) while **epoch count stayed at 5**. Each pair sees fewer gradient updates per epoch relative to the total corpus; at 2,351 pairs, 5 epochs (~730 steps on L40s) is insufficient to converge — the model is undertrained, not under-capacity. Run 3a also introduced new-pair quality issues (see `training/run3_dataset_audit.md`), but the primary fix for Run 4's continued regression was epoch budget, not more data.

**Run 5 correction:** 2,351 pairs × **10 epochs** × LR **2e-4** — doubled training steps to match dataset scale. Loss crossed below 0.6932 at **epoch 3.1**; run still in progress at time of writing.

### Run 5 hyperparameters (L40s)
```
--epochs 10
--learning-rate 2e-4   # pipeline default for L40s slot
--tag run5
Dataset: david_dataset.jsonl (2,351 pairs)
Adapter: david-7b_20260624_045918_run5
~1,470 steps (L40s, rank=64, batch 2 × accum 8)
```

```bash
pip install "unsloth[colab-new] @ git+https://github.com/unslothai/unsloth.git" --quiet && pip install --no-deps trl peft accelerate bitsandbytes --quiet && mkdir -p /DAVID/models/adapters && python3 /workspace/david_finetune_pipeline.py --run --epochs 10 --tag run5
```

---

## Dataset Generation Workflow (CANONICAL)

**Claude API (PowerShell) → RunPod training → local adapter download via file manager UI**

`ANTHROPIC_API_KEY` must be set in Windows User env vars before running generators.

| Dataset | Command |
|---------|---------|
| Classical Latin translation | `python training/generate_latin_translation_150.py` |
| Etymology | `python training/generate_etymology_training.py` |
| Phonetics | `python training/generate_phonetics_150.py` |
| Ancient Greek translation | `python training/generate_greek_translation_150.py` |

Run from repo root in a PowerShell terminal. Output goes to `training/*.jsonl`.
Do NOT use Grok terminals for dataset generation — Claude API only.

---

## Dataset rebuild (after new browser research passes)
```bash
python3 training/david_dataset_builder.py          # dry-run (stats)
python3 training/david_dataset_builder.py --write  # regenerate JSONL
```
Dataset grows automatically as new corpus texts / pronunciation profiles / translation profiles are added to `languages/*/`.

---

## Supplemental Training Data (R-terminal generated)

| File | Pairs | Generator | Coverage | Status |
|------|-------|-----------|----------|--------|
| `training/classical_latin_translation_150.jsonl` | 150 | `training/generate_latin_translation_150.py` | Cicero, Virgil, Caesar, Livy, Seneca, Horace, Ovid, Tacitus, Catullus — oratory, epic, military, Stoic | ✅ R1 done |
| `training/etymology_training_150.jsonl` | 150 | `training/generate_etymology_training.py` | Latin, Greek, Old French, Germanic, Arabic — legal, scientific, philosophical, everyday | ✅ R3 done |
| `training/phonetics_training_150.jsonl` | 150 | `training/generate_phonetics_150.py` | English GA/RP, Classical Latin, Ecclesiastical Latin, Attic Greek, minimal pairs, pitch accent | ✅ R4 done |
| `training/ancient_greek_translation_150.jsonl` | 150 | `training/generate_greek_translation_150.py` | Homer, Plato, Thucydides, Aristotle, Sophocles, Xenophon, Euripides, Herodotus | ✅ R2 done |

**Total supplemental so far:** 600 pairs (Latin + etymology + phonetics + Greek translation)
**Current training dataset:** 2,351 pairs (`david_dataset.jsonl`) — used for Run 4 and Run 5
