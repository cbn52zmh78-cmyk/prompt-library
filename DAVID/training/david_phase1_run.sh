#!/usr/bin/env bash
# david_phase1_run.sh -- DAVID Phase 1 RunPod launch script
#
# Provisions the pod, installs deps, trains Llama 3.1 8B on david_dataset.jsonl,
# runs a smoke test, and bundles the finished adapter.
#
# REQUIRES (set before upload / in RunPod env):
#   HUGGING_FACE_HUB_TOKEN   -- gated Llama 3.1 access (never prompt, never echo)
#   ALLOW_GPU_TRAIN=1        -- explicit live-train gate
#
# Optional overrides:
#   DAVID_HW        -- label for run record (default: h100_80gb)
#   DAVID_TAG       -- adapter name tag   (default: david-run1)
#
# Usage (on RunPod pod after uploading all three files):
#   chmod +x david_phase1_run.sh
#   ALLOW_GPU_TRAIN=1 bash david_phase1_run.sh

set -euo pipefail
IFS=$'\n\t'

# ---------------------------------------------------------------------------
# 0. Env gates
# ---------------------------------------------------------------------------

if [[ "${ALLOW_GPU_TRAIN:-}" != "1" ]]; then
  echo "[BLOCKED] Set ALLOW_GPU_TRAIN=1 before running."
  exit 1
fi

if [[ -z "${HUGGING_FACE_HUB_TOKEN:-}" ]]; then
  echo "[BLOCKED] HUGGING_FACE_HUB_TOKEN is not set."
  echo "  Meta Llama 3.1 8B is gated. Token required."
  exit 1
fi

DAVID_HW="${DAVID_HW:-h100_80gb}"
DAVID_TAG="${DAVID_TAG:-david-run1}"
WORKSPACE="/workspace"
DATASET="${WORKSPACE}/david_dataset.jsonl"
SCRIPT="${WORKSPACE}/david_phase1_train.py"

echo "============================================================"
echo "  DAVID Phase 1 -- Llama 3.1 8B QLoRA"
echo "  HW tag   : ${DAVID_HW}"
echo "  Run tag  : ${DAVID_TAG}"
echo "  Workspace: ${WORKSPACE}"
echo "============================================================"

# ---------------------------------------------------------------------------
# 1. Strip CRLF from uploaded files (Windows editor artefacts)
# ---------------------------------------------------------------------------

echo "[1/5] Stripping CRLF..."
for f in "${SCRIPT}" "${DATASET}"; do
  if [[ -f "${f}" ]]; then
    sed -i 's/\r//' "${f}"
    echo "  stripped: ${f}"
  fi
done

# ---------------------------------------------------------------------------
# 2. Install dependencies
# ---------------------------------------------------------------------------

echo "[2/5] Installing dependencies..."

pip install --quiet --upgrade pip

# Unsloth (latest) -- handles torch/cuda compat automatically
pip install --quiet \
  "unsloth[colab-new] @ git+https://github.com/unslothai/unsloth.git"

# Core training stack
pip install --quiet \
  trl \
  peft \
  datasets \
  "transformers>=4.40.0" \
  "accelerate>=0.28.0" \
  bitsandbytes

echo "  deps installed"

# ---------------------------------------------------------------------------
# 3. Verify dataset
# ---------------------------------------------------------------------------

echo "[3/5] Verifying dataset..."

if [[ ! -f "${DATASET}" ]]; then
  echo "[ERROR] Dataset not found: ${DATASET}"
  echo "  Upload david_dataset.jsonl to /workspace/ before running."
  exit 1
fi

N_PAIRS=$(python3 -c "
import sys
n = sum(1 for ln in open('${DATASET}', encoding='utf-8') if ln.strip())
print(n)
")
echo "  ${N_PAIRS} pairs found"

if [[ "${N_PAIRS}" -lt 100 ]]; then
  echo "[ERROR] Dataset too small (${N_PAIRS} pairs). Minimum 100 required."
  exit 1
fi

# ---------------------------------------------------------------------------
# 4. Train
# ---------------------------------------------------------------------------

echo "[4/5] Launching training..."
echo ""

ALLOW_GPU_TRAIN=1 \
HUGGING_FACE_HUB_TOKEN="${HUGGING_FACE_HUB_TOKEN}" \
  python3 "${SCRIPT}" \
    --dataset "${DATASET}" \
    --tag "${DAVID_TAG}"

echo ""
echo "  Training script returned cleanly."

# ---------------------------------------------------------------------------
# 5. Locate adapter, smoke test, bundle
# ---------------------------------------------------------------------------

echo "[5/5] Post-training: smoke test + bundle..."

# Find the newest adapter dir
ADAPTER_DIR=$(ls -td /workspace/adapters/llama-3.1-8b_*/ 2>/dev/null | head -1)
if [[ -z "${ADAPTER_DIR}" ]]; then
  echo "[ERROR] No adapter directory found under /workspace/adapters/"
  exit 1
fi
echo "  Adapter: ${ADAPTER_DIR}"

# Quick sanity: adapter_config.json must exist
if [[ ! -f "${ADAPTER_DIR}/adapter_config.json" ]]; then
  echo "[WARN] adapter_config.json not found -- LoRA save may have failed"
fi

# Smoke test: generate one response
echo "  Running smoke test..."
python3 - <<'SMOKE'
import sys, os
os.environ["ALLOW_GPU_TRAIN"] = "1"
try:
    from unsloth import FastLanguageModel
    import glob, json

    adapter_dirs = sorted(
        glob.glob("/workspace/adapters/llama-3.1-8b_*/"),
        key=lambda p: p,
        reverse=True,
    )
    adapter_dir = adapter_dirs[0] if adapter_dirs else None
    if not adapter_dir:
        print("[SMOKE] FAIL: no adapter dir found")
        sys.exit(1)

    model, tokenizer = FastLanguageModel.from_pretrained(
        model_name=adapter_dir,
        max_seq_length=2048,
        dtype=None,
        load_in_4bit=True,
    )
    FastLanguageModel.for_inference(model)

    prompt = (
        "### Instruction:\n"
        "Describe the key features of Proto-Indo-European as a reconstructed language.\n\n"
        "### Response:\n"
    )
    inputs = tokenizer(prompt, return_tensors="pt").to("cuda")
    outputs = model.generate(
        **inputs,
        max_new_tokens=120,
        temperature=0.4,
        do_sample=True,
        repetition_penalty=1.1,
        pad_token_id=tokenizer.eos_token_id,
    )
    response = tokenizer.decode(outputs[0], skip_special_tokens=True)
    response_only = response[len(prompt):].strip()

    if len(response_only) < 20:
        print("[SMOKE] FAIL: response too short")
        sys.exit(1)

    print("[SMOKE] PASS")
    print(f"  len={len(response_only)} chars")
    print(f"  preview: {response_only[:120]}...")
except Exception as exc:
    print(f"[SMOKE] ERROR: {exc}")
    sys.exit(1)
SMOKE

SMOKE_EXIT=$?

# Bundle adapter as tar.gz
BUNDLE_NAME="david_adapter_${DAVID_TAG}.tar.gz"
BUNDLE_PATH="/workspace/${BUNDLE_NAME}"
echo "  Bundling adapter to ${BUNDLE_PATH}..."
tar -czf "${BUNDLE_PATH}" -C "$(dirname "${ADAPTER_DIR}")" "$(basename "${ADAPTER_DIR}")"
echo "  Bundle size: $(du -sh "${BUNDLE_PATH}" | cut -f1)"

# Final summary
echo ""
echo "============================================================"
if [[ "${SMOKE_EXIT}" -eq 0 ]]; then
  echo "  DAVID PHASE 1 COMPLETE -- SMOKE: PASS"
else
  echo "  DAVID PHASE 1 COMPLETE -- SMOKE: FAIL (review logs)"
fi
echo "  Adapter : ${ADAPTER_DIR}"
echo "  Bundle  : ${BUNDLE_PATH}"
echo "  Run record: ${ADAPTER_DIR}david_run_record.json"
echo "============================================================"
echo ""
echo "Download from RunPod:"
echo "  ${BUNDLE_PATH}"
