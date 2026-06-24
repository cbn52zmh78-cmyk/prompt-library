#!/usr/bin/env bash
# train_david.sh — DAVID RunPod / local QLoRA training wrapper
#
# Default: dry-run (stub). Live GPU requires --live AND ALLOW_GPU_TRAIN=1.
#
# Usage:
#   bash training/train_david.sh                    # stub dry-run
#   bash training/train_david.sh --check            # validate config + dataset
#   bash training/train_david.sh --stub --tag inspect1
#   bash training/train_david.sh --install          # print RunPod deps one-liner
#   ALLOW_GPU_TRAIN=1 bash training/train_david.sh --live --tag run4
#   ALLOW_GPU_TRAIN=1 bash training/train_david.sh --live --hardware 2060 --tag run5-local
#
# RunPod (from /workspace after upload):
#   bash /workspace/train_david.sh --install
#   ALLOW_GPU_TRAIN=1 bash /workspace/train_david.sh --live --tag run4

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DAVID_DIR="$(dirname "$SCRIPT_DIR")"
PIPELINE="${SCRIPT_DIR}/david_finetune_pipeline.py"
CONFIG="${SCRIPT_DIR}/runpod_train_config.json"

MODE="stub"
TAG=""
HARDWARE=""
LITE=""
EXTRA=()

usage() {
  cat <<EOF
DAVID training wrapper (default: stub dry-run)

  --check          Validate runpod_train_config.json + dataset
  --stub           Dry-run plan (default)
  --live           Live GPU training (requires ALLOW_GPU_TRAIN=1)
  --install        Run RunPod dependency install from runpod_train_config.json
  --tag NAME       Suffix adapter dir (e.g. run4)
  --hardware SLOT  GPU profile: l40s | 4090 | 2060 (from runpod_train_config.json)
  --lite           Reduced VRAM hyperparams from config fallback_lite
  -h, --help       Show this help

Adapter output: models/adapters/david-7b_YYYYMMDD_HHMMSS_<tag>
Infer (RunPod): python3 training/david_infer.py --adapter /DAVID/models/adapters/david-7b_*
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --live)  MODE="live"; shift ;;
    --stub)  MODE="stub"; shift ;;
    --check)
      CHECK_CMD=(python3 "$PIPELINE" --check --config "$CONFIG")
      [[ -n "$HARDWARE" ]] && CHECK_CMD+=(--hardware "$HARDWARE")
      exec "${CHECK_CMD[@]}"
      ;;
    --install)
      python3 -c "import json; from pathlib import Path; cfg=json.loads(Path('${CONFIG}').read_text()); print(cfg['runpod_install'])"
      exit 0
      ;;
    --tag)
      TAG="${2:?--tag requires a value}"
      shift 2
      ;;
    --hardware)
      HARDWARE="${2:?--hardware requires a value}"
      shift 2
      ;;
    --lite)  LITE="--lite"; shift ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)  EXTRA+=("$1"); shift ;;
  esac
done

CMD=(python3 "$PIPELINE" --config "$CONFIG")

if [[ "$MODE" == "live" ]]; then
  if [[ "${ALLOW_GPU_TRAIN:-}" != "1" ]]; then
    echo "BLOCKED: set ALLOW_GPU_TRAIN=1 before live GPU training."
    exit 1
  fi
  CMD+=(--run)
else
  CMD+=(--stub)
fi

[[ -n "$TAG" ]] && CMD+=(--tag "$TAG")
[[ -n "$HARDWARE" ]] && CMD+=(--hardware "$HARDWARE")
[[ -n "$LITE" ]] && CMD+=($LITE)
[[ ${#EXTRA[@]} -gt 0 ]] && CMD+=("${EXTRA[@]}")

echo "[train_david] DAVID_DIR=${DAVID_DIR}"
echo "[train_david] mode=${MODE} tag=${TAG:-<none>} hardware=${HARDWARE:-l40s}"
exec "${CMD[@]}"