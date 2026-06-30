#!/usr/bin/env bash
# eleanor_david_run.sh -- ELEANOR-DAVID Variant RunPod launch script
#
# First officially-built ELEANOR wrapper variant. Trains Llama 3.3 70B
# on combined base ELEANOR corpus + DAVID-domain governance corpus.
#
# REQUIRES (set in RunPod env vars panel -- never paste in chat):
#   HUGGING_FACE_HUB_TOKEN   -- gated Llama 3.3 70B access
#   ALLOW_GPU_TRAIN=1
#
# Hardware: H100 SXM5 80GB | H200 80GB (preferred) | A100 SXM4 80GB (minimum)
# Expected runtime: ~35-45 min on H100, ~30 min on H200
#
# Upload to /workspace/ before running:
#   eleanor_david_train.py
#   eleanor_david_run.sh
#   eleanor_david_dataset.jsonl
#
# Usage:
#   chmod +x eleanor_david_run.sh
#   ALLOW_GPU_TRAIN=1 bash eleanor_david_run.sh

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
  echo "  Set it in the RunPod environment variables panel."
  exit 1
fi

ELEANOR_TAG="${ELEANOR_TAG:-eleanor-david-run1}"
WORKSPACE="/workspace"
DATASET="${WORKSPACE}/eleanor_david_dataset.jsonl"
SCRIPT="${WORKSPACE}/eleanor_david_train.py"

echo "============================================================"
echo "  ELEANOR-DAVID Variant -- Llama 3.3 70B QLoRA"
echo "  Run tag  : ${ELEANOR_TAG}"
echo "  Workspace: ${WORKSPACE}"
echo "============================================================"

# ---------------------------------------------------------------------------
# 1. Strip CRLF
# ---------------------------------------------------------------------------

echo "[1/5] Stripping CRLF..."
for f in "${SCRIPT}" "${DATASET}"; do
  [[ -f "${f}" ]] && sed -i 's/\r//' "${f}" && echo "  stripped: ${f}"
done

# ---------------------------------------------------------------------------
# 2. Install dependencies
# ---------------------------------------------------------------------------

echo "[2/5] Installing dependencies..."
pip install --quiet --upgrade pip
pip install --quiet \
  "unsloth[colab-new] @ git+https://github.com/unslothai/unsloth.git"
pip install --quiet \
  trl peft datasets "transformers>=4.40.0" "accelerate>=0.28.0" bitsandbytes
echo "  deps installed"

# ---------------------------------------------------------------------------
# 3. Verify dataset
# ---------------------------------------------------------------------------

echo "[3/5] Verifying dataset..."

if [[ ! -f "${DATASET}" ]]; then
  echo "[ERROR] Dataset not found: ${DATASET}"
  echo "  Upload eleanor_david_dataset.jsonl to /workspace/"
  exit 1
fi

N_PAIRS=$(python3 -c "
n = sum(1 for ln in open('${DATASET}', encoding='utf-8') if ln.strip())
print(n)
")
echo "  ${N_PAIRS} pairs found"

if [[ "${N_PAIRS}" -lt 500 ]]; then
  echo "[ERROR] Dataset too small (${N_PAIRS}). Expected ~2011 pairs."
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
    --tag "${ELEANOR_TAG}"

echo ""
echo "  Training complete."

# ---------------------------------------------------------------------------
# 5. Smoke test + bundle
# ---------------------------------------------------------------------------

echo "[5/5] Post-training: smoke test + bundle..."

ADAPTER_DIR=$(ls -td /workspace/adapters/llama-3.3-70b_*/ 2>/dev/null | head -1)
if [[ -z "${ADAPTER_DIR}" ]]; then
  echo "[ERROR] No adapter directory found under /workspace/adapters/"
  exit 1
fi
echo "  Adapter: ${ADAPTER_DIR}"

[[ ! -f "${ADAPTER_DIR}/adapter_config.json" ]] && echo "[WARN] adapter_config.json missing"

echo "  Running smoke test..."
python3 - <<'SMOKE'
import sys, os, glob, json
os.environ["ALLOW_GPU_TRAIN"] = "1"
try:
    from unsloth import FastLanguageModel

    adapter_dirs = sorted(
        glob.glob("/workspace/adapters/llama-3.3-70b_*/"),
        reverse=True,
    )
    adapter_dir = adapter_dirs[0] if adapter_dirs else None
    if not adapter_dir:
        print("[SMOKE] FAIL: no adapter dir")
        sys.exit(1)

    model, tokenizer = FastLanguageModel.from_pretrained(
        model_name=adapter_dir,
        max_seq_length=2048,
        dtype=None,
        load_in_4bit=True,
    )
    FastLanguageModel.for_inference(model)

    # Test 1: DAVID routing
    prompt1 = (
        "### Instruction:\n"
        "A researcher asks DAVID to reconstruct phonemes from a Proto-Semitic root. "
        "Which ELEANOR subagent should validate the linguistic accuracy claim before DAVID responds?\n\n"
        "### Response:\n"
    )
    # Test 2: governance assertion
    prompt2 = (
        "### Instruction:\n"
        "Should DAVID auto-execute a translation of a sacred Indigenous text without researcher consent?\n\n"
        "### Response:\n"
    )

    passed = 0
    for i, prompt in enumerate([prompt1, prompt2], 1):
        inputs = tokenizer(prompt, return_tensors="pt").to("cuda")
        outputs = model.generate(
            **inputs,
            max_new_tokens=100,
            temperature=0.3,
            do_sample=True,
            repetition_penalty=1.15,
            pad_token_id=tokenizer.eos_token_id,
        )
        response = tokenizer.decode(outputs[0], skip_special_tokens=True)
        resp_only = response[len(prompt):].strip()
        if len(resp_only) > 20:
            passed += 1
            print(f"  [T{i}] PASS  ({len(resp_only)} chars)")
        else:
            print(f"  [T{i}] FAIL  (response too short)")

    if passed == 2:
        print("[SMOKE] 2/2 PASS")
    else:
        print(f"[SMOKE] {passed}/2 PASS -- review responses")
        sys.exit(1)

except Exception as exc:
    print(f"[SMOKE] ERROR: {exc}")
    sys.exit(1)
SMOKE

SMOKE_EXIT=$?

BUNDLE_NAME="eleanor_david_adapter_${ELEANOR_TAG}.tar.gz"
BUNDLE_PATH="/workspace/${BUNDLE_NAME}"
echo "  Bundling to ${BUNDLE_PATH}..."
ADAPTER_CLEAN="${ADAPTER_DIR%/}"
tar --exclude='checkpoint-*' -czf "${BUNDLE_PATH}" -C "$(dirname "${ADAPTER_CLEAN}")" "$(basename "${ADAPTER_CLEAN}")"
echo "  Bundle size: $(du -sh "${BUNDLE_PATH}" | cut -f1)"

echo ""
echo "============================================================"
if [[ "${SMOKE_EXIT}" -eq 0 ]]; then
  echo "  ELEANOR-DAVID COMPLETE -- SMOKE: PASS"
else
  echo "  ELEANOR-DAVID COMPLETE -- SMOKE: FAIL (review logs)"
fi
echo "  Adapter : ${ADAPTER_DIR}"
echo "  Bundle  : ${BUNDLE_PATH}"
echo "============================================================"
echo ""
echo "Download: ${BUNDLE_PATH}"
