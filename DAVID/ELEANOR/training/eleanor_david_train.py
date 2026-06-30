"""eleanor_david_train.py -- ELEANOR-DAVID Variant: Llama 3.3 70B QLoRA Training.

ELEANOR-DAVID is the first officially-built ELEANOR wrapper variant.
She carries the full base ELEANOR governance corpus (routing, compliance,
legal, LE, adversarial, multi-turn, subagent behaviors) layered with
DAVID-domain governance: educational compliance, synthetic media rules,
vision governance, language accuracy standards, dead/living/extinct language
oversight, dialect forensics, and video script governance.

Her exclusive subagent cadre transfers with her: Memory, Deliberation,
Voice, Planner, Watcher. She additionally governs DAVID's internal subagents.

Hardware:  H100 SXM5 80GB | H200 80GB (preferred) | A100 SXM4 80GB (minimum)
Base:      unsloth/Llama-3.3-70B-Instruct-bnb-4bit
LoRA:      rank=64, alpha=64
Epochs:    3  (1000_plus tier; ~189 steps at 2011 pairs, eff_batch=32)
Dataset:   /workspace/eleanor_david_dataset.jsonl  (1794 base + 220 domain = 2011 clean)
Output:    /workspace/adapters/llama-3.3-70b_{timestamp}_eleanor-david-run1/

REQUIRES before launch:
  export ALLOW_GPU_TRAIN=1
  export HUGGING_FACE_HUB_TOKEN=<token>   # Llama 3.3 70B is gated

Usage (called by eleanor_david_run.sh):
  ALLOW_GPU_TRAIN=1 python3 /workspace/eleanor_david_train.py \\
      --dataset /workspace/eleanor_david_dataset.jsonl \\
      --tag eleanor-david-run1
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path


# ---------------------------------------------------------------------------
# Gates
# ---------------------------------------------------------------------------

def _require_allow_gpu_train() -> None:
    if os.environ.get("ALLOW_GPU_TRAIN") != "1":
        sys.exit(
            "[BLOCKED] ALLOW_GPU_TRAIN=1 is required before live GPU training.\n"
            "  Set it with: export ALLOW_GPU_TRAIN=1"
        )


def _require_hf_token() -> None:
    if not os.environ.get("HUGGING_FACE_HUB_TOKEN", ""):
        sys.exit(
            "[BLOCKED] HUGGING_FACE_HUB_TOKEN not set.\n"
            "  Llama 3.3 70B is gated -- token must be from an approved HF account."
        )


# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

MODEL_NAME     = "unsloth/Llama-3.3-70B-Instruct-bnb-4bit"
LORA_RANK      = 64
LORA_ALPHA     = 64
LORA_DROPOUT   = 0.05
TARGET_MODULES = [
    "q_proj", "k_proj", "v_proj", "o_proj",
    "gate_proj", "up_proj", "down_proj",
]
LEARNING_RATE  = 2e-4
LR_SCHEDULER   = "cosine"
WARMUP_RATIO   = 0.05
BATCH_SIZE     = 4
GRAD_ACCUM     = 8           # eff_batch = 32  (70B needs smaller per-device batch)
GRAD_CKPT      = True
SAVE_STEPS     = 50
SAVE_LIMIT     = 2
SEED           = 42
MAX_SEQ_LEN    = 2048


def resolve_epochs(n_pairs: int) -> int:
    if n_pairs >= 1000:
        return 3
    if n_pairs >= 400:
        return 5
    return 6


# ---------------------------------------------------------------------------
# Dataset
# ---------------------------------------------------------------------------

def count_jsonl(path: str) -> int:
    return sum(1 for ln in open(path, encoding="utf-8") if ln.strip())


def load_alpaca_records(path: str) -> list[dict]:
    records = []
    with open(path, encoding="utf-8") as f:
        for lineno, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError as exc:
                sys.exit(f"[ERROR] Bad JSON at line {lineno}: {exc}")
            if not row.get("instruction") or not row.get("output"):
                sys.exit(f"[ERROR] Line {lineno}: missing 'instruction' or 'output'.")
            records.append({"text": _fmt_alpaca(row)})
    return records


def _fmt_alpaca(row: dict) -> str:
    inst = row["instruction"].strip()
    inp  = row.get("input", "").strip()
    out  = row["output"].strip()
    if inp:
        return (
            f"### Instruction:\n{inst}\n\n"
            f"### Input:\n{inp}\n\n"
            f"### Response:\n{out}"
        )
    return f"### Instruction:\n{inst}\n\n### Response:\n{out}"


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="ELEANOR-DAVID Variant -- Llama 3.3 70B QLoRA training"
    )
    parser.add_argument("--dataset", required=True, help="Path to eleanor_david_dataset.jsonl")
    parser.add_argument("--tag",     default="eleanor-david-run1")
    parser.add_argument("--max-seq-length", type=int, default=MAX_SEQ_LEN)
    args = parser.parse_args(argv)

    _require_allow_gpu_train()
    _require_hf_token()

    if not Path(args.dataset).is_file():
        sys.exit(f"[ERROR] Dataset not found: {args.dataset}")

    n_pairs     = count_jsonl(args.dataset)
    epochs      = resolve_epochs(n_pairs)
    eff_batch   = BATCH_SIZE * GRAD_ACCUM
    total_steps = max(1, n_pairs // eff_batch) * epochs

    ts          = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    run_id      = f"llama-3.3-70b_{ts}_{args.tag}"
    adapter_out = f"/workspace/adapters/{run_id}"

    print(f"\n{'='*62}")
    print("  ELEANOR-DAVID Variant -- Llama 3.3 70B QLoRA  [LIVE]")
    print(f"{'='*62}")
    print(f"  Base model   : {MODEL_NAME}")
    print(f"  Dataset      : {args.dataset}  ({n_pairs} pairs)")
    print(f"  LoRA         : rank={LORA_RANK}  alpha={LORA_ALPHA}  dropout={LORA_DROPOUT}")
    print(f"  Epochs       : {epochs}  (~{total_steps} steps)")
    print(f"  Batch        : {BATCH_SIZE} x grad_accum={GRAD_ACCUM}  eff_batch={eff_batch}")
    print(f"  LR           : {LEARNING_RATE}  scheduler={LR_SCHEDULER}")
    print(f"  Adapter out  : {adapter_out}")
    print(f"{'='*62}\n")

    # --- imports ---
    try:
        from unsloth import FastLanguageModel  # type: ignore
    except (ImportError, RuntimeError) as exc:
        sys.exit(f"[ERROR] Unsloth not available: {exc}")
    try:
        from trl import SFTTrainer  # type: ignore
        try:
            from trl import SFTConfig as _TrainArgs  # type: ignore
        except ImportError:
            from transformers import TrainingArguments as _TrainArgs  # type: ignore
        import torch  # type: ignore
        from datasets import Dataset  # type: ignore
    except ImportError as exc:
        sys.exit(f"[ERROR] Missing dependency: {exc}")

    # [1/6] Load base model
    print("[1/6] Loading base model (4-bit)...")
    model, tokenizer = FastLanguageModel.from_pretrained(
        model_name=MODEL_NAME,
        max_seq_length=args.max_seq_length,
        dtype=None,
        load_in_4bit=True,
    )

    # [2/6] Attach LoRA
    print("[2/6] Attaching LoRA adapters...")
    model = FastLanguageModel.get_peft_model(
        model,
        r=LORA_RANK,
        lora_alpha=LORA_ALPHA,
        target_modules=TARGET_MODULES,
        lora_dropout=LORA_DROPOUT,
        bias="none",
        use_gradient_checkpointing="unsloth",
        random_state=SEED,
    )

    # [3/6] Load dataset
    print("[3/6] Loading and formatting dataset...")
    records = load_alpaca_records(args.dataset)
    ds = Dataset.from_list(records)
    tokenizer.padding_side = "right"
    print(f"         {len(records)} records loaded")

    # [4/6] Configure trainer
    print("[4/6] Configuring SFTTrainer...")
    Path(adapter_out).mkdir(parents=True, exist_ok=True)

    use_bf16 = torch.cuda.is_bf16_supported()
    training_args = _TrainArgs(
        output_dir=adapter_out,
        num_train_epochs=epochs,
        per_device_train_batch_size=BATCH_SIZE,
        gradient_accumulation_steps=GRAD_ACCUM,
        gradient_checkpointing=GRAD_CKPT,
        learning_rate=LEARNING_RATE,
        lr_scheduler_type=LR_SCHEDULER,
        warmup_ratio=WARMUP_RATIO,
        fp16=not use_bf16,
        bf16=use_bf16,
        logging_steps=10,
        save_steps=SAVE_STEPS,
        save_total_limit=SAVE_LIMIT,
        seed=SEED,
        report_to="none",
        dataloader_pin_memory=False,
    )

    trainer = SFTTrainer(
        model=model,
        tokenizer=tokenizer,
        train_dataset=ds,
        dataset_text_field="text",
        max_seq_length=args.max_seq_length,
        args=training_args,
    )

    # [5/6] Train on responses only
    try:
        from unsloth.chat_templates import train_on_responses_only as _apply_tor  # type: ignore
        trainer = _apply_tor(
            trainer,
            instruction_part="### Instruction:\n",
            response_part="### Response:\n",
        )
        print("[5/6] train_on_responses_only: ENABLED")
    except Exception as tor_exc:
        print(f"[5/6] train_on_responses_only: SKIPPED ({tor_exc})")

    # [6/6] Train
    print("[6/6] Training...\n")
    t0 = time.time()
    train_result = trainer.train()
    elapsed = time.time() - t0

    model.save_pretrained(adapter_out)
    tokenizer.save_pretrained(adapter_out)

    steps       = int(train_result.global_step)
    final_loss  = float(train_result.training_loss)
    elapsed_min = elapsed / 60.0

    print(f"\n{'='*62}")
    print("  TRAINING COMPLETE")
    print(f"  Run ID       : {run_id}")
    print(f"  Steps        : {steps}")
    print(f"  Final loss   : {final_loss:.4f}")
    print(f"  Elapsed      : {elapsed_min:.1f} min")
    print(f"  Adapter      : {adapter_out}")
    print(f"{'='*62}")

    run_record = {
        "run_id":        run_id,
        "variant":       "ELEANOR-DAVID",
        "base_model":    MODEL_NAME,
        "corpus": {
            "base_eleanor_pairs": 1794,
            "david_domain_pairs": 220,
            "total_pairs":        n_pairs,
        },
        "epochs":        epochs,
        "steps":         steps,
        "avg_train_loss": final_loss,
        "elapsed_min":   round(elapsed_min, 1),
        "adapter_out":   adapter_out,
        "lora":          {"rank": LORA_RANK, "alpha": LORA_ALPHA},
    }
    record_path = Path(adapter_out) / "eleanor_david_run_record.json"
    record_path.write_text(
        json.dumps(run_record, indent=2, ensure_ascii=True),
        encoding="ascii",
    )
    print(f"  Run record   : {record_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
