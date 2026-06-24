"""david_infer.py — DAVID Adapter Inference Tester

Load a DAVID QLoRA adapter and run test prompts across all four pillars to
validate the fine-tune before committing to download.

Usage:
    python3 /workspace/david_infer.py --adapter /DAVID/models/adapters/david-7b_YYYYMMDD_HHMMSS_run1
    python3 /workspace/david_infer.py --adapter <path> --prompt "Translate this Latin text."
    python3 /workspace/david_infer.py --adapter <path> --pillar speech
    python3 /workspace/david_infer.py --adapter <path> --all      # run all pillar tests
"""

from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

# ── Built-in test prompts (one per pillar + meta) ─────────────────────────────

_TESTS = {
    "forensic": [
        {
            "label":       "P1-A — Latin corpus analysis",
            "instruction": "Translate this Classical Latin text and provide a full corpus analysis.",
            "input":       "Arma virumque cano, Troiae qui primus ab oris",
        },
        {
            "label":       "P1-B — Confidence tag",
            "instruction": "What confidence tag should be applied to this Classical Latin claim, and why?",
            "input":       '"Arma virumque cano" (Source: Vergil, Aeneid I.1)',
        },
        {
            "label":       "P1-C — Anglo-Norman source ID",
            "instruction": "Identify the source, date, and context of this Anglo-Norman text.",
            "input":       "En cest livre troverez / La vie des sainz escrite",
        },
    ],
    "speech": [
        {
            "label":       "P2-A — Latin IPA",
            "instruction": "Provide IPA transcription for this Classical Latin text for audio production.",
            "input":       "Arma virumque cano",
        },
        {
            "label":       "P2-B — Biblical Hebrew cantillation",
            "instruction": "Describe the cantillation system for this Biblical Hebrew text and its audio production implications.",
            "input":       "בְּרֵאשִׁית בָּרָא אֱלֹהִים",
        },
        {
            "label":       "P2-C — Grok Imagine prompt",
            "instruction": "Generate a Grok Imagine audio visualisation prompt for this Classical Latin text.",
            "input":       "Arma virumque cano, Troiae qui primus ab oris",
        },
    ],
    "pedagogy": [
        {
            "label":       "P3-A — Anglo-Norman series hook",
            "instruction": "Write a YouTube series hook for Anglo-Norman as a direct ancestral language.",
            "input":       "",
        },
        {
            "label":       "P3-B — Lesson plan",
            "instruction": "Design a beginner lesson plan for Classical Latin focusing on the verb system.",
            "input":       "",
        },
        {
            "label":       "P3-C — Episode outline",
            "instruction": "Outline a 10-minute episode introducing Classical Latin pronunciation to a modern English speaker.",
            "input":       "",
        },
    ],
    "translation": [
        {
            "label":       "P4-A — Latin register",
            "instruction": "What translation register is appropriate for a Classical Latin legal text, and why?",
            "input":       "Senatus Populusque Romanus",
        },
        {
            "label":       "P4-B — Japanese Keigo",
            "instruction": "Explain the Keigo register hierarchy in Japanese and its implications for document translation.",
            "input":       "",
        },
        {
            "label":       "P4-C — Translation traps",
            "instruction": "What are the top translation traps when working with Biblical Hebrew into English?",
            "input":       "",
        },
    ],
    "meta": [
        {
            "label":       "M — Identity",
            "instruction": "Who are you and what are your four operational pillars?",
            "input":       "",
        },
    ],
}

_ALL_PILLARS = ["forensic", "speech", "pedagogy", "translation", "meta"]


# ── Inference ─────────────────────────────────────────────────────────────────

def load_model(adapter_path: str):
    try:
        from unsloth import FastLanguageModel  # type: ignore
    except ImportError:
        print("[ERROR] Unsloth not installed. Run on the RunPod instance.")
        sys.exit(1)

    print(f"Loading adapter: {adapter_path}")
    model, tokenizer = FastLanguageModel.from_pretrained(
        model_name     = adapter_path,
        max_seq_length = 2048,
        dtype          = None,
        load_in_4bit   = True,
    )
    FastLanguageModel.for_inference(model)
    return model, tokenizer


def run_prompt(model, tokenizer, instruction: str, input_text: str, max_new_tokens: int = 512) -> str:
    if input_text.strip():
        prompt = (
            f"### Instruction:\n{instruction.strip()}\n\n"
            f"### Input:\n{input_text.strip()}\n\n"
            f"### Response:\n"
        )
    else:
        prompt = (
            f"### Instruction:\n{instruction.strip()}\n\n"
            f"### Response:\n"
        )

    try:
        import torch  # type: ignore
        inputs = tokenizer(prompt, return_tensors="pt").to("cuda")
        with torch.no_grad():
            outputs = model.generate(
                **inputs,
                max_new_tokens = max_new_tokens,
                temperature    = 0.3,
                do_sample      = True,
                pad_token_id   = tokenizer.eos_token_id,
            )
        generated = tokenizer.decode(outputs[0], skip_special_tokens=True)
        # Strip the prompt prefix — return only the response
        marker = "### Response:\n"
        idx = generated.rfind(marker)
        if idx != -1:
            return generated[idx + len(marker):].strip()
        return generated.strip()
    except Exception as e:
        return f"[ERROR] {e}"


def run_tests(model, tokenizer, pillars: list[str]) -> None:
    total = sum(len(_TESTS[p]) for p in pillars if p in _TESTS)
    done  = 0

    for pillar in pillars:
        tests = _TESTS.get(pillar, [])
        if not tests:
            print(f"\n[WARN] Unknown pillar: {pillar}")
            continue

        print(f"\n{'═'*60}")
        print(f"  PILLAR: {pillar.upper()}")
        print(f"{'═'*60}")

        for t in tests:
            done += 1
            print(f"\n[{done}/{total}] {t['label']}")
            print(f"  Instruction : {t['instruction']}")
            if t["input"]:
                print(f"  Input       : {t['input']}")
            print(f"  {'─'*56}")
            t0       = time.time()
            response = run_prompt(model, tokenizer, t["instruction"], t["input"])
            elapsed  = time.time() - t0
            print(f"  Response ({elapsed:.1f}s):")
            for line in response.splitlines():
                print(f"    {line}")

    print(f"\n{'═'*60}")
    print(f"  Done — {done} test(s) across {len(pillars)} pillar(s).")
    print(f"{'═'*60}")


# ── CLI ───────────────────────────────────────────────────────────────────────

def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="DAVID adapter inference tester")
    parser.add_argument("--adapter",        required=True, metavar="PATH",
                        help="Path to DAVID QLoRA adapter directory")
    parser.add_argument("--prompt",         default="",    metavar="TEXT",
                        help="Single instruction to run (ad-hoc test)")
    parser.add_argument("--input",          default="",    metavar="TEXT",
                        help="Input text for --prompt")
    parser.add_argument("--pillar",         default="",
                        choices=_ALL_PILLARS,
                        help="Run built-in tests for one pillar")
    parser.add_argument("--all",            action="store_true",
                        help="Run all built-in pillar tests")
    parser.add_argument("--max-new-tokens", type=int, default=512)
    args = parser.parse_args(argv)

    model, tokenizer = load_model(args.adapter)

    if args.prompt:
        print(f"\nRunning ad-hoc prompt...")
        response = run_prompt(model, tokenizer, args.prompt, args.input, args.max_new_tokens)
        print(f"\n{'─'*60}")
        print(response)
        print(f"{'─'*60}")
        return 0

    if args.all:
        run_tests(model, tokenizer, _ALL_PILLARS)
        return 0

    if args.pillar:
        run_tests(model, tokenizer, [args.pillar])
        return 0

    # Default: run one test from each pillar as a quick smoke test
    print("\nRunning quick smoke test (one prompt per pillar)...")
    for pillar in _ALL_PILLARS:
        tests = _TESTS.get(pillar, [])
        if tests:
            run_tests(model, tokenizer, [pillar])
            break  # just the first pillar for the default — change if desired

    # Actually run all pillars for smoke test (1 test each)
    print("\nRunning smoke test — first prompt from each pillar...")
    for pillar in _ALL_PILLARS:
        tests = _TESTS.get(pillar, [])
        if not tests:
            continue
        t = tests[0]
        print(f"\n[{pillar.upper()}] {t['label']}")
        response = run_prompt(model, tokenizer, t["instruction"], t["input"], 256)
        for line in response.splitlines()[:6]:   # cap at 6 lines for smoke test
            print(f"  {line}")
        if len(response.splitlines()) > 6:
            print(f"  ... ({len(response.splitlines()) - 6} more lines)")

    return 0


if __name__ == "__main__":
    sys.exit(main())
