"""david_finetune_pipeline.py — DAVID Unsloth QLoRA Fine-Tune Pipeline

Trains DeepSeek-R1-Distill-Qwen-7B on the DAVID instruction dataset using
Unsloth's memory-efficient QLoRA implementation.

DAVID is the Human Communication Agent: Forensic Linguistics, Speech &
Phonology, Pedagogy, and Translation Services across 28 languages.

Graceful degradation: if Unsloth is not installed, runs in STUB mode —
validates dataset, prints what it would do, exits cleanly.

Hardware targets (config-driven via runpod_train_config.json hardware_slots):
  L40s  48GB  : rank=32, batch=2, grad_accum=8,  LR=1e-4  — RunPod primary
  RTX 4090 24GB: rank=32, batch=1, grad_accum=16, LR=1e-4  — comfortable
  RTX 2060 12GB: rank=32, batch=1, grad_accum=16, LR=2e-5  — local overnight
  RTX 4060  8GB : rank=16, batch=1, grad_accum=8  — legacy 7B path only

Usage:
    python3 training/david_finetune_pipeline.py --run --epochs 5 --tag run1
    python3 training/david_finetune_pipeline.py --check
    python3 training/david_finetune_pipeline.py --status
    python3 training/david_finetune_pipeline.py --merge <adapter_path>

Config / hardware profiles (see train_david.sh):
    python3 training/david_finetune_pipeline.py --run --hardware 2060 --tag run5-local
    bash training/train_david.sh --check
    bash training/train_david.sh --stub --tag inspect1
    ALLOW_GPU_TRAIN=1 bash training/train_david.sh --live --tag run4
    ALLOW_GPU_TRAIN=1 bash training/train_david.sh --live --hardware 2060 --tag run5-local

Legacy inline config:
    python3 training/david_finetune_pipeline.py --run --epochs 5 --tag run1
"""

from __future__ import annotations

import json
import os
import sys
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

# ── Python 3.14 / dill compatibility shim ─────────────────────────────────────
# dill._batch_setitems signature changed in Python 3.14 — patch before datasets
try:
    import dill._dill as _dill_mod
    _orig_batch = _dill_mod.Pickler._batch_setitems
    def _batch_setitems_py314(self, items, obj=None):
        return _orig_batch(self, items)
    _dill_mod.Pickler._batch_setitems = _batch_setitems_py314
except Exception:
    pass
# ──────────────────────────────────────────────────────────────────────────────

# ── Paths ─────────────────────────────────────────────────────────────────────
_HERE         = Path(__file__).resolve().parent          # training/
_DAVID        = _HERE.parent                             # DAVID/
_ADAPTERS_DIR = _DAVID / "models" / "adapters"
_MERGED_DIR   = _DAVID / "models" / "merged"
_DATASETS_DIR = _DAVID / "training"
_LOGS_DIR     = _HERE / "logs"
_RUNS_DIR     = _HERE / "runs"
_DEFAULT_DS   = _HERE / "david_dataset.jsonl"
_RUNPOD_CONFIG = _HERE / "runpod_train_config.json"

# RunPod override: if running on RunPod, adapters go to /DAVID/models/adapters
_RUNPOD_ADAPTERS = Path("/DAVID/models/adapters")
if _RUNPOD_ADAPTERS.parent.exists() and not _ADAPTERS_DIR.parent.exists():
    _ADAPTERS_DIR = _RUNPOD_ADAPTERS
    _MERGED_DIR   = Path("/DAVID/models/merged")

# ── Model config ──────────────────────────────────────────────────────────────
_MODEL_CONFIGS = {
    "deepseek-7b": {
        "model_name":     "unsloth/deepseek-r1-distill-qwen-7b-bnb-4bit",
        "max_seq_length": 2048,
        "lora_rank":      64,      # L40s/4090 target; drop to 16 on RTX 4060
        "lora_alpha":     32,      # alpha = rank/2 — standard for 7b
        "target_modules": [
            "q_proj", "v_proj", "k_proj", "o_proj",
            "gate_proj", "up_proj", "down_proj",
        ],
        "batch_size":   4,
        "grad_accum":   4,
        "vram_note":    "L40s 48GB / RTX 4090 24GB — rank=64 comfortable",
    },
    "deepseek-7b-lite": {
        # 8GB fallback — same model, reduced rank + batch
        "model_name":     "unsloth/deepseek-r1-distill-qwen-7b-bnb-4bit",
        "max_seq_length": 2048,
        "lora_rank":      16,
        "lora_alpha":     16,
        "target_modules": [
            "q_proj", "v_proj", "k_proj", "o_proj",
            "gate_proj", "up_proj", "down_proj",
        ],
        "batch_size":   1,
        "grad_accum":   8,
        "vram_note":    "RTX 4060 8GB — marginal; close all other apps",
    },
}
_DEFAULT_MODEL = "deepseek-7b"

# ── Training hyperparams ──────────────────────────────────────────────────────
_DEFAULT_EPOCHS       = 5       # 706 pairs × 5 epochs ≈ 220 steps on L40s
_DEFAULT_LR           = 2e-4
_DEFAULT_LR_SCHEDULER = "cosine"
_DEFAULT_WARMUP_RATIO = 0.05
_DEFAULT_SAVE_STEPS   = 50
_SEED                 = 42

# ── Stub detection ────────────────────────────────────────────────────────────
try:
    import unsloth  # type: ignore  # noqa: F401
    _UNSLOTH_AVAILABLE = True
except (ImportError, NotImplementedError, OSError, RuntimeError):
    _UNSLOTH_AVAILABLE = False


# ── Result dataclass ──────────────────────────────────────────────────────────

@dataclass
class FinetuneResult:
    run_id:       str
    model_key:    str
    dataset_path: str
    adapter_path: str   = ""
    merged_path:  str   = ""
    stub:         bool  = False
    epochs:       int   = 0
    steps:        int   = 0
    final_loss:   float = 0.0
    elapsed_s:    float = 0.0
    success:      bool  = False
    errors:       list  = field(default_factory=list)
    meta:         dict  = field(default_factory=dict)

    def summary(self) -> str:
        mode   = "STUB" if self.stub else "LIVE"
        status = "OK"   if self.success else "FAILED"
        parts  = [
            f"[{mode}] {status}  run={self.run_id}",
            f"  model      : {self.model_key}",
            f"  dataset    : {self.dataset_path}",
            f"  epochs     : {self.epochs}  steps: {self.steps}",
        ]
        if not self.stub:
            parts.append(f"  final_loss : {self.final_loss:.4f}")
            parts.append(f"  adapter    : {self.adapter_path}")
        if self.merged_path:
            parts.append(f"  merged     : {self.merged_path}")
        parts.append(f"  elapsed    : {self.elapsed_s:.1f}s")
        if self.errors:
            parts.append(f"  errors     : {self.errors}")
        return "\n".join(parts)


# ── Helpers ───────────────────────────────────────────────────────────────────

def _count_dataset(path: Path) -> int:
    if not path.exists():
        return 0
    count = 0
    with open(path, encoding="utf-8") as f:
        for line in f:
            if line.strip():
                count += 1
    return count


def _apply_alpaca_template(example: dict, tokenizer) -> dict:
    """Alpaca instruction format used by david_dataset_builder."""
    instruction = example.get("instruction", "").strip()
    inp         = example.get("input", "").strip()
    output      = example.get("output", "").strip()

    if inp:
        prompt = (
            f"### Instruction:\n{instruction}\n\n"
            f"### Input:\n{inp}\n\n"
            f"### Response:\n{output}"
        )
    else:
        prompt = (
            f"### Instruction:\n{instruction}\n\n"
            f"### Response:\n{output}"
        )
    return {"text": prompt}


def check_gpu() -> dict:
    info = {"available": False, "name": "N/A", "vram_gb": 0.0, "recommendation": ""}
    try:
        import torch  # type: ignore
        if torch.cuda.is_available():
            info["available"] = True
            info["name"]      = torch.cuda.get_device_name(0)
            info["vram_gb"]   = torch.cuda.get_device_properties(0).total_memory / 1e9
            vram = info["vram_gb"]
            if vram >= 40:
                info["recommendation"] = "Use --hardware l40s (RunPod primary)"
            elif vram >= 20:
                info["recommendation"] = "Use --hardware 4090"
            elif vram >= 11:
                info["recommendation"] = "Use --hardware 2060 for local overnight runs"
            elif vram >= 8:
                info["recommendation"] = "Use deepseek-7b-lite, rank=16 — RTX 4060 legacy 7B only"
            else:
                info["recommendation"] = f"VRAM too low ({vram:.1f}GB) — use cloud GPU"
    except ImportError:
        info["recommendation"] = "PyTorch not installed"
    return info


# ── Core pipeline ─────────────────────────────────────────────────────────────

def run_finetune(
    dataset_path: Path          = _DEFAULT_DS,
    model_key:    str           = _DEFAULT_MODEL,
    epochs:       int           = _DEFAULT_EPOCHS,
    lr:           float         = _DEFAULT_LR,
    stub:         bool          = False,
    max_samples:  Optional[int] = None,
    output_tag:   str           = "",
) -> FinetuneResult:
    ts     = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    run_id = f"david-7b_{ts}"
    if output_tag:
        run_id = f"{run_id}_{output_tag}"

    result = FinetuneResult(
        run_id       = run_id,
        model_key    = model_key,
        dataset_path = str(dataset_path),
        stub         = stub or not _UNSLOTH_AVAILABLE,
    )

    t0 = time.time()
    _LOGS_DIR.mkdir(parents=True, exist_ok=True)
    _RUNS_DIR.mkdir(parents=True, exist_ok=True)

    cfg = _MODEL_CONFIGS.get(model_key)
    if not cfg:
        result.errors.append(f"Unknown model key: {model_key}")
        result.elapsed_s = time.time() - t0
        return result

    n_samples        = _count_dataset(dataset_path)
    effective        = min(n_samples, max_samples) if max_samples else n_samples
    steps_per_epoch  = max(1, effective // (cfg["batch_size"] * cfg["grad_accum"]))
    total_steps      = steps_per_epoch * epochs

    result.meta.update({
        "dataset_samples":  n_samples,
        "effective_samples": effective,
        "model_name":       cfg["model_name"],
        "lora_rank":        cfg["lora_rank"],
        "estimated_steps":  total_steps,
        "gpu":              check_gpu(),
    })

    if n_samples == 0:
        result.errors.append(f"Dataset not found or empty: {dataset_path}")
        result.elapsed_s = time.time() - t0
        return result

    # ── Stub mode ─────────────────────────────────────────────────────────────
    if result.stub:
        reason = "Unsloth not installed" if not _UNSLOTH_AVAILABLE else "stub=True"
        print(f"\n{'='*60}")
        print(f"  DAVID Fine-Tune Pipeline — STUB MODE ({reason})")
        print(f"{'='*60}")
        print(f"  Run ID         : {run_id}")
        print(f"  Model          : {cfg['model_name']}")
        print(f"  Dataset        : {dataset_path} ({effective} pairs)")
        print(f"  LoRA rank      : {cfg['lora_rank']}  alpha: {cfg['lora_alpha']}")
        print(f"  Epochs         : {epochs}  Steps: ~{total_steps}")
        print(f"  Learning rate  : {lr}")
        print(f"  Batch          : {cfg['batch_size']} × grad_accum {cfg['grad_accum']}")
        print(f"  VRAM note      : {cfg['vram_note']}")
        gpu = result.meta["gpu"]
        if gpu["available"]:
            print(f"  GPU            : {gpu['name']} ({gpu['vram_gb']:.1f}GB)")
            print(f"  Recommendation : {gpu['recommendation']}")
        else:
            print(f"  GPU            : NOT DETECTED — cloud GPU required")
        print(f"\n  # INSTALL:")
        print(f"  pip install 'unsloth[colab-new] @ git+https://github.com/unslothai/unsloth.git'")
        print(f"  pip install --no-deps trl peft accelerate bitsandbytes")
        print(f"{'='*60}")

        result.epochs    = epochs
        result.steps     = total_steps
        result.success   = True
        result.elapsed_s = time.time() - t0

        log_path = _RUNS_DIR / f"{run_id}.json"
        log_path.write_text(json.dumps({
            "run_id": run_id, "mode": "stub", "timestamp": ts,
            "meta": result.meta,
            "config": {k: v for k, v in cfg.items() if k != "target_modules"},
            "epochs": epochs, "lr": lr,
        }, indent=2, ensure_ascii=False))
        return result

    # ── LIVE TRAINING ─────────────────────────────────────────────────────────
    print(f"\n{'='*60}")
    print(f"  DAVID Fine-Tune Pipeline — LIVE TRAINING")
    print(f"  Run ID  : {run_id}")
    print(f"  Model   : {cfg['model_name']}")
    print(f"  Pairs   : {effective}  Steps: ~{total_steps}")
    print(f"{'='*60}")

    try:
        from unsloth import FastLanguageModel  # type: ignore
        from trl import SFTTrainer            # type: ignore
        import torch                          # type: ignore

        try:
            from trl import SFTConfig as _TrainCls  # type: ignore
        except ImportError:
            from transformers import TrainingArguments as _TrainCls  # type: ignore

        # 1. Load base model
        print("[1/5] Loading base model...")
        model, tokenizer = FastLanguageModel.from_pretrained(
            model_name     = cfg["model_name"],
            max_seq_length = cfg["max_seq_length"],
            dtype          = None,
            load_in_4bit   = True,
        )

        # 2. LoRA adapters
        print("[2/5] Adding LoRA adapters...")
        model = FastLanguageModel.get_peft_model(
            model,
            r                          = cfg["lora_rank"],
            lora_alpha                 = cfg["lora_alpha"],
            target_modules             = cfg["target_modules"],
            lora_dropout               = 0.05,
            bias                       = "none",
            use_gradient_checkpointing = "unsloth",
            random_state               = _SEED,
        )

        # 3. Load + format dataset
        print("[3/5] Loading dataset...")
        import json as _json
        from datasets import Dataset as _Dataset  # type: ignore
        records = [_json.loads(ln) for ln in open(dataset_path, encoding="utf-8") if ln.strip()]
        raw_ds  = _Dataset.from_list(records)
        if max_samples:
            raw_ds = raw_ds.select(range(min(max_samples, len(raw_ds))))

        tokenizer.padding_side = "right"
        formatted_ds = raw_ds.map(
            lambda ex: _apply_alpaca_template(ex, tokenizer),
            batched=False,
        )

        # 4. Configure trainer
        print("[4/5] Configuring SFTTrainer...")
        _ADAPTERS_DIR.mkdir(parents=True, exist_ok=True)
        adapter_path  = str(_ADAPTERS_DIR / run_id)
        training_args = _TrainCls(
            output_dir                  = adapter_path,
            num_train_epochs            = epochs,
            per_device_train_batch_size = cfg["batch_size"],
            gradient_accumulation_steps = cfg["grad_accum"],
            learning_rate               = lr,
            lr_scheduler_type           = _DEFAULT_LR_SCHEDULER,
            warmup_ratio                = _DEFAULT_WARMUP_RATIO,
            fp16                        = not torch.cuda.is_bf16_supported(),
            bf16                        = torch.cuda.is_bf16_supported(),
            logging_steps               = 10,
            save_steps                  = _DEFAULT_SAVE_STEPS,
            save_total_limit            = 3,
            seed                        = _SEED,
            report_to                   = "none",
            dataloader_pin_memory       = False,
        )

        trainer = SFTTrainer(
            model              = model,
            tokenizer          = tokenizer,
            train_dataset      = formatted_ds,
            dataset_text_field = "text",
            max_seq_length     = cfg["max_seq_length"],
            args               = training_args,
        )

        # 5. Train
        print("[5/5] Training...")
        train_result = trainer.train()
        final_loss   = train_result.training_loss

        model.save_pretrained(adapter_path)
        tokenizer.save_pretrained(adapter_path)

        result.adapter_path = adapter_path
        result.epochs       = epochs
        result.steps        = int(train_result.global_step)
        result.final_loss   = final_loss
        result.success      = True

        print(f"\n  Adapter saved → {adapter_path}")
        print(f"  Final loss    : {final_loss:.4f}")

        log_path = _RUNS_DIR / f"{run_id}.json"
        log_path.write_text(json.dumps({
            "run_id":       run_id,
            "mode":         "live",
            "timestamp":    ts,
            "adapter_path": adapter_path,
            "steps":        result.steps,
            "final_loss":   final_loss,
            "meta":         result.meta,
        }, indent=2, ensure_ascii=False))

    except Exception as e:
        result.errors.append(str(e))
        result.success = False
        print(f"\n  [ERROR] {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()

    result.elapsed_s = time.time() - t0
    return result


# ── Merge ─────────────────────────────────────────────────────────────────────

def merge_adapter(adapter_path: Path, output_name: str = "") -> str:
    if not _UNSLOTH_AVAILABLE:
        print("[STUB] Unsloth not installed — cannot merge.")
        return ""

    cfg        = _MODEL_CONFIGS["deepseek-7b"]
    ts         = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    name       = output_name or f"david_7b_merged_{ts}"
    _MERGED_DIR.mkdir(parents=True, exist_ok=True)
    out        = str(_MERGED_DIR / name)

    print(f"\nMerging adapter into base model...")
    print(f"  Adapter : {adapter_path}")
    print(f"  Output  : {out}")

    try:
        from unsloth import FastLanguageModel  # type: ignore
        model, tokenizer = FastLanguageModel.from_pretrained(
            model_name     = str(adapter_path),
            max_seq_length = cfg["max_seq_length"],
            dtype          = None,
            load_in_4bit   = True,
        )
        model.save_pretrained_merged(out, tokenizer, save_method="merged_16bit")
        print(f"  Merged model saved → {out}")
        return out
    except Exception as e:
        print(f"[ERROR] Merge failed: {e}", file=sys.stderr)
        return ""


# ── Status ────────────────────────────────────────────────────────────────────

def show_status() -> None:
    adapters = sorted(_ADAPTERS_DIR.glob("*/"))  if _ADAPTERS_DIR.exists() else []
    merged   = sorted(_MERGED_DIR.glob("*/"))    if _MERGED_DIR.exists()   else []

    print("\n-- DAVID Model Inventory --")
    print(f"\n  Adapters ({len(adapters)}):")
    for a in adapters:
        size_mb = sum(f.stat().st_size for f in a.rglob("*") if f.is_file()) / 1e6
        print(f"    {a.name:48s} {size_mb:7.1f} MB")

    print(f"\n  Merged models ({len(merged)}):")
    for m in merged:
        size_gb = sum(f.stat().st_size for f in m.rglob("*") if f.is_file()) / 1e9
        print(f"    {m.name:48s} {size_gb:7.1f} GB")

    n_pairs = _count_dataset(_DEFAULT_DS)
    print(f"\n  Dataset : {_DEFAULT_DS.name} ({n_pairs} pairs)")
    print(f"  Unsloth : {'YES' if _UNSLOTH_AVAILABLE else 'NO (stub mode)'}")
    gpu = check_gpu()
    if gpu["available"]:
        print(f"  GPU     : {gpu['name']} ({gpu['vram_gb']:.1f}GB)")
        print(f"  Rec     : {gpu['recommendation']}")
    else:
        print(f"  GPU     : not detected")


# ── RunPod config-driven path (runpod_train_config.json) ─────────────────────

def load_runpod_config(path: Path = _RUNPOD_CONFIG) -> Dict[str, Any]:
    if not path.is_file():
        raise FileNotFoundError(f"RunPod config not found: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def _load_jsonl_pairs(dataset_path: Path) -> List[Dict[str, Any]]:
    if not dataset_path.is_file():
        return []
    pairs: List[Dict[str, Any]] = []
    with open(dataset_path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                pairs.append(json.loads(line))
    return pairs


def resolve_epochs_from_config(n_pairs: int, cfg: Dict[str, Any]) -> int:
    tiers = cfg["training"]["epochs_tiers"]
    if n_pairs >= 2000:
        return int(tiers["2000_plus"])
    if n_pairs >= 1000:
        return int(tiers["1000_1999"])
    return int(tiers["under_1000"])


_HARDWARE_CHOICES = ("l40s", "4090", "2060")


def resolve_hardware_slot(cfg: Dict[str, Any], hardware: str = "l40s") -> Dict[str, Any]:
    """Merge hardware_slots[hardware] over top-level lora/training defaults."""
    slot_key = hardware if hardware in _HARDWARE_CHOICES else cfg.get("hardware", {}).get(
        "default_slot", "l40s"
    )
    slots = cfg.get("hardware_slots") or {}
    slot = slots.get(slot_key)
    if not slot:
        raise ValueError(f"Unknown hardware slot: {slot_key!r} — expected one of {list(slots)}")

    lora = dict(cfg.get("lora", {}))
    lora.update(slot.get("lora", {}))

    train_shared = {k: v for k, v in cfg.get("training", {}).items()
                    if k not in ("batch_size", "gradient_accumulation_steps", "learning_rate")}
    train_slot = dict(slot.get("training", {}))
    batch = int(train_slot.get("batch_size", 1))
    grad_accum = int(train_slot.get("gradient_accumulation_steps", 16))
    lr = float(train_slot.get("learning_rate", 2e-4))

    return {
        "slot": slot_key,
        "label": slot.get("label", slot_key),
        "lora": lora,
        "training": {**train_shared, "batch_size": batch, "gradient_accumulation_steps": grad_accum, "learning_rate": lr},
        "vram_note": train_slot.get("vram_note", ""),
    }


def run_finetune_from_config(
    *,
    config_path: Path = _RUNPOD_CONFIG,
    dataset_path: Optional[Path] = None,
    epochs: Optional[int] = None,
    stub: bool = False,
    output_tag: str = "",
    lite: bool = False,
    hardware: str = "l40s",
) -> FinetuneResult:
    cfg = load_runpod_config(config_path)
    ds_rel = cfg["dataset"]["path"]
    ds_path = dataset_path or (_DAVID / ds_rel if not Path(ds_rel).is_absolute() else Path(ds_rel))
    if not ds_path.is_file():
        ds_path = _DEFAULT_DS

    ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    prefix = cfg["paths"]["adapter_prefix"]
    run_id = f"{prefix}_{ts}"
    if output_tag:
        run_id = f"{run_id}_{output_tag}"

    pairs = _load_jsonl_pairs(ds_path)
    n_pairs = len(pairs)
    epoch_count = epochs if epochs is not None else resolve_epochs_from_config(n_pairs, cfg)

    if lite:
        fb = cfg["hardware"]["fallback_lite"]
        lora = dict(cfg.get("lora", {}))
        lora["rank"] = fb["rank"]
        lora["alpha"] = fb["alpha"]
        train_cfg = cfg["training"]
        batch = int(fb["batch_size"])
        grad_accum = int(fb["gradient_accumulation_steps"])
        lr = float(fb.get("learning_rate", train_cfg.get("learning_rate", 2e-4)))
        hw_label = "fallback_lite"
        vram_note = fb.get("vram_note", "")
    else:
        resolved = resolve_hardware_slot(cfg, hardware)
        lora = resolved["lora"]
        train_cfg = resolved["training"]
        batch = int(train_cfg["batch_size"])
        grad_accum = int(train_cfg["gradient_accumulation_steps"])
        lr = float(train_cfg["learning_rate"])
        hw_label = resolved["label"]
        vram_note = resolved["vram_note"]

    steps_per_epoch = max(1, n_pairs // (batch * grad_accum))
    total_steps = steps_per_epoch * epoch_count

    result = FinetuneResult(
        run_id=run_id,
        model_key=cfg["model"]["key"],
        dataset_path=str(ds_path),
        stub=stub or not _UNSLOTH_AVAILABLE,
        epochs=epoch_count,
        steps=total_steps,
        meta={
            "n_pairs": n_pairs,
            "scope": cfg["scope"],
            "model": cfg["model"]["unsloth_model_name"],
            "hardware": hardware if not lite else "lite",
            "hardware_label": hw_label,
            "lora_rank": lora["rank"],
            "lora_alpha": lora["alpha"],
            "learning_rate": lr,
            "batch_size": batch,
            "grad_accum": grad_accum,
            "estimated_steps": total_steps,
            "vram_note": vram_note,
            "gpu": check_gpu(),
        },
    )

    t0 = time.time()
    _RUNS_DIR.mkdir(parents=True, exist_ok=True)
    _ADAPTERS_DIR.mkdir(parents=True, exist_ok=True)

    if n_pairs == 0:
        result.errors.append(f"Dataset empty or missing: {ds_path}")
        result.elapsed_s = time.time() - t0
        return result

    adapter_path = str(_ADAPTERS_DIR / run_id)

    if result.stub:
        reason = "Unsloth not installed" if not _UNSLOTH_AVAILABLE else "stub=True"
        print(f"\n{'=' * 60}")
        print(f"  DAVID Fine-Tune — STUB MODE ({reason})")
        print(f"{'=' * 60}")
        print(f"  Run ID         : {run_id}")
        print(f"  Scope          : {cfg['scope']}")
        print(f"  Model          : {cfg['model']['unsloth_model_name']}")
        print(f"  Dataset        : {ds_path} ({n_pairs} pairs)")
        print(f"  Hardware       : {hw_label}")
        print(f"  LoRA rank      : {lora['rank']}  alpha: {lora['alpha']}")
        print(f"  Epochs         : {epoch_count}  (~{total_steps} steps)")
        print(f"  Learning rate  : {lr}")
        print(f"  Batch          : {batch} × grad_accum {grad_accum}")
        if vram_note:
            print(f"  VRAM note      : {vram_note}")
        print(f"  Adapter out    : {adapter_path}")
        print(f"  Infer (RunPod) : python3 {_HERE / 'david_infer.py'} --adapter {adapter_path} --all")
        gpu = result.meta["gpu"]
        if gpu["available"]:
            print(f"  GPU            : {gpu['name']} ({gpu['vram_gb']:.1f}GB)")
        else:
            print("  GPU            : NOT DETECTED — RunPod L40S required for --live")
        if cfg.get("dry_run", {}).get("live_requires_env"):
            print(f"\n  LIVE requires: {cfg['dry_run']['live_requires_env']}")
        print(f"{'=' * 60}")
        result.adapter_path = adapter_path
        result.success = True
        result.elapsed_s = time.time() - t0
        log_path = _RUNS_DIR / f"{run_id}.json"
        log_path.write_text(
            json.dumps(
                {
                    "run_id": run_id,
                    "mode": "stub",
                    "config": str(config_path),
                    "meta": result.meta,
                    "adapter_path": adapter_path,
                },
                indent=2,
            ),
            encoding="utf-8",
        )
        return result

    print(f"\n{'=' * 60}")
    print("  DAVID Fine-Tune — LIVE TRAINING (RunPod config)")
    print(f"  Run ID  : {run_id}")
    print(f"  Pairs   : {n_pairs}  Steps: ~{total_steps}")
    print(f"{'=' * 60}")

    try:
        from unsloth import FastLanguageModel  # type: ignore
        from trl import SFTTrainer  # type: ignore
        import torch  # type: ignore

        try:
            from trl import SFTConfig as _TrainCls  # type: ignore
        except ImportError:
            from transformers import TrainingArguments as _TrainCls  # type: ignore

        from datasets import Dataset as HFDataset  # type: ignore

        model, tokenizer = FastLanguageModel.from_pretrained(
            model_name=cfg["model"]["unsloth_model_name"],
            max_seq_length=cfg["model"]["max_seq_length"],
            dtype=None,
            load_in_4bit=cfg["model"].get("load_in_4bit", True),
        )

        model = FastLanguageModel.get_peft_model(
            model,
            r=lora["rank"],
            lora_alpha=lora["alpha"],
            target_modules=lora["target_modules"],
            lora_dropout=lora.get("dropout", 0.05),
            bias="none",
            use_gradient_checkpointing="unsloth",
            random_state=int(train_cfg.get("seed", 42)),
        )

        formatted = [_apply_alpaca_template(p, tokenizer) for p in pairs]
        train_ds = HFDataset.from_list(formatted)

        training_args = _TrainCls(
            output_dir=adapter_path,
            num_train_epochs=epoch_count,
            per_device_train_batch_size=batch,
            gradient_accumulation_steps=grad_accum,
            learning_rate=lr,
            lr_scheduler_type=train_cfg.get("lr_scheduler", "cosine"),
            warmup_ratio=float(train_cfg.get("warmup_ratio", 0.05)),
            fp16=not torch.cuda.is_bf16_supported(),
            bf16=torch.cuda.is_bf16_supported(),
            logging_steps=10,
            save_steps=int(train_cfg.get("save_steps", 50)),
            save_total_limit=int(train_cfg.get("save_total_limit", 3)),
            seed=int(train_cfg.get("seed", 42)),
            report_to="none",
            dataloader_pin_memory=False,
        )

        trainer = SFTTrainer(
            model=model,
            tokenizer=tokenizer,
            train_dataset=train_ds,
            dataset_text_field="text",
            max_seq_length=cfg["model"]["max_seq_length"],
            args=training_args,
        )

        train_result = trainer.train()
        model.save_pretrained(adapter_path)
        tokenizer.save_pretrained(adapter_path)

        result.adapter_path = adapter_path
        result.final_loss = float(train_result.training_loss)
        result.steps = int(train_result.global_step)
        result.success = True
        print(f"\n  Adapter saved → {adapter_path}")
        print(f"  Final loss    : {result.final_loss:.4f}")

    except Exception as exc:
        result.errors.append(str(exc))
        result.success = False
        print(f"\n  [ERROR] {exc}", file=sys.stderr)
        import traceback
        traceback.print_exc()

    result.elapsed_s = time.time() - t0
    return result


def show_runpod_check(config_path: Path = _RUNPOD_CONFIG, hardware: str = "l40s") -> int:
    cfg = load_runpod_config(config_path)
    ds_path = _DAVID / cfg["dataset"]["path"]
    if not ds_path.is_file():
        ds_path = _DEFAULT_DS
    pairs = _load_jsonl_pairs(ds_path)
    n = len(pairs)
    epochs = resolve_epochs_from_config(n, cfg)
    resolved = resolve_hardware_slot(cfg, hardware)
    lora = resolved["lora"]
    train = resolved["training"]
    batch = int(train["batch_size"])
    ga = int(train["gradient_accumulation_steps"])
    lr = float(train["learning_rate"])
    steps = max(1, n // (batch * ga)) * epochs
    gpu = check_gpu()

    print("\n-- DAVID RunPod Train Config Check --")
    print(f"  Config   : {config_path}")
    print(f"  Hardware : {resolved['label']} (slot={resolved['slot']})")
    print(f"  Dataset  : {ds_path} ({n} pairs)")
    print(f"  Scope    : {cfg['scope']}")
    print(f"  Model    : {cfg['model']['unsloth_model_name']}")
    print(f"  LoRA     : rank={lora['rank']} alpha={lora['alpha']}")
    print(f"  Train    : batch={batch} grad_accum={ga} lr={lr}")
    print(f"  Epochs   : {epochs} (tier for {n} pairs)")
    print(f"  Steps    : ~{steps}")
    if resolved.get("vram_note"):
        print(f"  Note     : {resolved['vram_note']}")
    print(f"  Adapters : {_ADAPTERS_DIR}")
    print(f"  Unsloth  : {'YES' if _UNSLOTH_AVAILABLE else 'NO (stub only)'}")
    print(f"  GPU      : {gpu.get('name', 'none')} {gpu.get('vram_gb', 0):.1f}GB")
    if gpu.get("recommendation"):
        print(f"  Rec      : {gpu['recommendation']}")
    print(f"  Infer    : python3 {_HERE / 'david_infer.py'} --adapter {_ADAPTERS_DIR}/david-7b_*")
    slots = cfg.get("hardware_slots") or {}
    if slots:
        print(f"  Slots    : {', '.join(slots)}")
    return 0


# ── CLI ───────────────────────────────────────────────────────────────────────

def main(argv=None) -> int:
    import argparse
    parser = argparse.ArgumentParser(description="DAVID Unsloth QLoRA Fine-Tune Pipeline")
    parser.add_argument("--run",         action="store_true",  help="Run fine-tune")
    parser.add_argument("--stub",        action="store_true",  help="Dry-run (no training)")
    parser.add_argument("--check",       action="store_true",  help="GPU + dataset check")
    parser.add_argument("--status",      action="store_true",  help="Show adapter inventory")
    parser.add_argument("--merge",       metavar="ADAPTER",    help="Merge adapter path")
    parser.add_argument("--dataset",     default=str(_DEFAULT_DS), metavar="FILE")
    parser.add_argument("--model",       default=_DEFAULT_MODEL,
                        choices=list(_MODEL_CONFIGS.keys()))
    parser.add_argument("--epochs",      type=int,   default=_DEFAULT_EPOCHS)
    parser.add_argument("--lr",          type=float, default=_DEFAULT_LR)
    parser.add_argument("--max-samples", type=int,   default=None, metavar="N")
    parser.add_argument("--tag",         default="", help="Output name suffix (e.g. run1)")
    parser.add_argument("--config",      default="", metavar="FILE",
                        help="RunPod config JSON (enables config-driven stub/run)")
    parser.add_argument("--hardware",    default="", choices=["", "l40s", "4090", "2060"],
                        help="Hardware profile from runpod_train_config.json hardware_slots")
    parser.add_argument("--lite",        action="store_true",
                        help="Use fallback_lite VRAM hyperparams from config")
    args = parser.parse_args(argv)

    use_config = bool(args.config or args.hardware)
    if use_config:
        config_path = Path(args.config) if args.config else _RUNPOD_CONFIG
        cfg = load_runpod_config(config_path)
        hardware = args.hardware or cfg.get("hardware", {}).get("default_slot", "l40s")
        if args.check:
            return show_runpod_check(config_path, hardware=hardware)
        stub = args.stub or not args.run
        if args.run and not stub:
            gate = cfg.get("dry_run", {}).get("live_requires_env", "ALLOW_GPU_TRAIN=1")
            env_key = gate.split("=")[0] if "=" in gate else gate
            if os.environ.get(env_key) != "1":
                print(f"BLOCKED: set {gate} before live GPU training.")
                return 1
        dataset_path = Path(args.dataset) if args.dataset else None
        result = run_finetune_from_config(
            config_path=config_path,
            dataset_path=dataset_path,
            epochs=args.epochs if args.epochs != _DEFAULT_EPOCHS else None,
            stub=stub,
            output_tag=args.tag,
            lite=args.lite,
            hardware=hardware,
        )
        print(result.summary())
        return 0 if result.success else 1

    if args.status:
        show_status()
        return 0

    if args.check:
        gpu = check_gpu()
        n   = _count_dataset(Path(args.dataset))
        print(f"\n-- DAVID System Check --")
        print(f"  Unsloth : {'installed' if _UNSLOTH_AVAILABLE else 'NOT installed'}")
        print(f"  Dataset : {args.dataset} ({n} pairs)")
        print(f"  GPU     : {gpu.get('name','none')} {gpu.get('vram_gb',0):.1f}GB")
        print(f"  Rec     : {gpu.get('recommendation','N/A')}")
        return 0

    if args.merge:
        out = merge_adapter(Path(args.merge))
        return 0 if out else 1

    if args.run:
        result = run_finetune(
            dataset_path = Path(args.dataset),
            model_key    = args.model,
            epochs       = args.epochs,
            lr           = args.lr,
            stub         = args.stub,
            max_samples  = args.max_samples,
            output_tag   = args.tag,
        )
        print(f"\n{result.summary()}")
        return 0 if result.success else 1

    parser.print_help()
    return 0


if __name__ == "__main__":
    sys.exit(main())
