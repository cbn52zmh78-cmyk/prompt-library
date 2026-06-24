# DAVID Run Commands Reference
*DAVID/training/DAVID_Run_Commands.md | Updated: June 2026*

---

## Hardware
| GPU | VRAM | Profile | LoRA | Batch × Accum | LR | Notes |
|-----|------|---------|------|---------------|-----|-------|
| L40s | 48GB | `--hardware l40s` | rank=32, α=16 | 2 × 8 | 1e-4 | **RunPod primary** — 14B comfortable |
| RTX 4090 | 24GB | `--hardware 4090` | rank=32, α=16 | 1 × 16 | 1e-4 | 14B fallback — effective batch 16 |
| RTX 2060 | 12GB | `--hardware 2060` | rank=32, α=16 | 1 × 16 | **2e-5** | **Local overnight** — close other apps; lower LR |
| RTX 4060 | 8GB | `--model deepseek-7b-lite` | rank=16, α=16 | 1 × 8 | 2e-4 | Legacy 7B path only (no `--config`) |

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

Adapter is ~6–7GB for deepseek-7b. **DO NOT use runpodctl. DO NOT stop the pod before both files are downloaded.**

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
| 706   | 8      | ~352                   | If loss still dropping at end of Run 1 |
| 1,500+| 5      | ~470                   | After next browser research pass |
| 1,500+| 5      | ~470                   | Target for sub-0.50 loss |

Compare to HELIX: 3,643 pairs × 5 epochs = 1,140 steps → 0.5617 loss.
DAVID Run 1 will have far fewer steps — bump epochs if loss plateaus high.

---

## Run Log

| Run | Model | Rank | Epochs | Dataset Pairs | Final Loss | Elapsed | Notes |
|-----|-------|------|--------|--------------|------------|---------|-------|
| Run 1 | deepseek-7b | 64 | 5 | 706 | 1.0119 | — | First DAVID run — baseline |
| Run 2 | deepseek-7b | 64 | 8 | 706 | 0.6932 | — | L40S · loss still dropping — expand dataset for Run 3 |
| Run 3a | deepseek-7b | 64 | 5 | 1,493 | 1.2837 | 777.8s | L40S · adapter: david-7b_20260623_230354_run3 · LOST (pod killed before download) · loss regression — dataset quality review needed |
| Run 3b | deepseek-7b | 64 | 5 | 1,493 | — | — | L40S · adapter: david-7b_20260623_234920_run3 · redo run — download in progress |

---

## Dataset Generation Workflow (CANONICAL)

**DeepSeek API (PowerShell) → RunPod training → local adapter download via file manager UI**

`DEEPSEEK_API_KEY` must be set in Windows User env vars before running generators.

| Dataset | Command |
|---------|---------|
| Classical Latin translation | `python training/generate_latin_translation_150.py` |
| Etymology | `python training/generate_etymology_training.py` |
| Phonetics | `python training/generate_phonetics_150.py` |
| Ancient Greek translation | `python training/generate_greek_translation_150.py` |

Run from repo root in a PowerShell terminal. Output goes to `training/*.jsonl`.
Do NOT use Grok terminals for dataset generation — DeepSeek API only.

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
| `training/ancient_greek_translation_150.jsonl` | 150 | `training/generate_greek_translation_150.py` | Homer, Plato, Thucydides, Aristotle, Sophocles, Xenophon, Euripides, Herodotus | ⏳ generating |

**Total supplemental so far:** 450 pairs (600 when R2 delivers)
**Run 4 target dataset:** ~2,093 pairs (1,493 existing + 600 supplemental)
