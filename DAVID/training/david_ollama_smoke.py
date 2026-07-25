"""david_ollama_smoke.py — DAVID 8B Ollama smoke test

Runs all 13 pillar tests against the local Ollama 'david' model,
applies assertion-based scoring, and prints a summary.

Usage:
    python david_ollama_smoke.py
    python david_ollama_smoke.py --model david --temp 0.7
"""

import argparse
import json
import re
import sys
import time
import urllib.request
import urllib.error

# ── Test definitions (mirrors david_infer.py) ────────────────────────────────

TESTS = [
    # Forensic
    {
        "id": "P1A", "pillar": "forensic", "label": "P1-A — Latin corpus analysis",
        "instruction": "Translate this Classical Latin text and provide a full corpus analysis.",
        "input": "Arma virumque cano, Troiae qui primus ab oris",
        "assertions": [
            ("re", r"(?i)virgil|vergil|aeneid|arms|man|sing", "Should reference Virgil/Aeneid or translate"),
        ],
    },
    {
        "id": "P1B", "pillar": "forensic", "label": "P1-B — Confidence tag",
        "instruction": "What confidence tag should be applied to this Classical Latin claim, and why?",
        "input": '"Arma virumque cano" (Source: Vergil, Aeneid I.1)',
        "assertions": [
            ("re", r"(?i)confiden|certain|verified|high|attested", "Should assign a confidence level"),
        ],
    },
    {
        "id": "P1C", "pillar": "forensic", "label": "P1-C — Anglo-Norman source ID",
        "instruction": "Identify the source, date, and context of this Anglo-Norman text.",
        "input": "En cest livre troverez / La vie des sainz escrite",
        "assertions": [
            ("re", r"(?i)anglo.?norman|norman.?french|medieval|12th|13th|hagiograph", "Should identify Anglo-Norman context"),
        ],
        "known_fail": True,
    },
    # Speech
    {
        "id": "P2A", "pillar": "speech", "label": "P2-A — Latin IPA",
        "instruction": "Provide IPA transcription for this Classical Latin text for audio production.",
        "input": "Arma virumque cano",
        "assertions": [
            ("re", r"[/\[].+[/\]]|ˈ|ɑ|ʊ|ŋ|kʷ", "Should contain IPA notation"),
        ],
    },
    {
        "id": "P2B", "pillar": "speech", "label": "P2-B — Biblical Hebrew cantillation",
        "instruction": "Describe the cantillation system for this Biblical Hebrew text and its audio production implications.",
        "input": "בְּרֵאשִׁית בָּרָא אֱלֹהִים",
        "assertions": [
            ("re", r"(?i)cantillat|ta.?am|trope|chant|accents|masoret", "Should reference cantillation system"),
        ],
    },
    {
        "id": "P2C", "pillar": "speech", "label": "P2-C — Grok Imagine prompt",
        "instruction": "Generate a Grok Imagine audio visualisation prompt for this Classical Latin text.",
        "input": "Arma virumque cano, Troiae qui primus ab oris",
        "assertions": [
            ("re", r"(?i)visual|scene|image|render|cinematic|prompt|ancient|roman", "Should generate visual/prompt language"),
        ],
    },
    # Pedagogy
    {
        "id": "P3A", "pillar": "pedagogy", "label": "P3-A — Anglo-Norman series hook",
        "instruction": "Write a YouTube series hook for Anglo-Norman as a direct ancestral language.",
        "input": "",
        "assertions": [
            ("re", r"(?i)anglo.?norman|english|french|ancestor|history|language", "Should reference Anglo-Norman"),
        ],
    },
    {
        "id": "P3B", "pillar": "pedagogy", "label": "P3-B — Lesson plan",
        "instruction": "Design a beginner lesson plan for Classical Latin focusing on the verb system.",
        "input": "",
        "assertions": [
            ("re", r"(?i)verb|conjugat|tense|declens|lesson|student|exercise", "Should cover verb system pedagogy"),
        ],
    },
    {
        "id": "P3C", "pillar": "pedagogy", "label": "P3-C — Episode outline",
        "instruction": "Outline a 10-minute episode introducing Classical Latin pronunciation to a modern English speaker.",
        "input": "",
        "assertions": [
            ("re", r"(?i)pronunciat|vowel|consonant|phonet|speak|sound", "Should cover pronunciation"),
        ],
    },
    # Translation
    {
        "id": "P4A", "pillar": "translation", "label": "P4-A — Latin register",
        "instruction": "What translation register is appropriate for a Classical Latin legal text, and why?",
        "input": "Senatus Populusque Romanus",
        "assertions": [
            ("re", r"(?i)register|formal|legal|official|solemn|senate|SPQR", "Should discuss register for legal Latin"),
        ],
    },
    {
        "id": "P4B", "pillar": "translation", "label": "P4-B — Japanese Keigo",
        "instruction": "Explain the Keigo register hierarchy in Japanese and its implications for document translation.",
        "input": "",
        "assertions": [
            ("re", r"(?i)keigo|sonkei|kenj[oō]|teineigo|honorif|polite|humble", "Should reference Keigo registers"),
        ],
    },
    {
        "id": "P4C", "pillar": "translation", "label": "P4-C — Translation traps",
        "instruction": "What are the top translation traps when working with Biblical Hebrew into English?",
        "input": "",
        "assertions": [
            ("re", r"(?i)hebrew|translat|idiom|tense|aspect|semantic|word.?order", "Should discuss Hebrew translation challenges"),
        ],
    },
    # Meta
    {
        "id": "M", "pillar": "meta", "label": "M — Identity",
        "instruction": "Who are you and what are your four operational pillars?",
        "input": "",
        "assertions": [
            ("re", r"(?i)DAVID|forensic|speech|pedagog|translat|pillar|linguistic", "Should identify as DAVID with pillars"),
        ],
    },
]


def call_ollama(model: str, instruction: str, input_text: str, temp: float) -> str:
    """Call Ollama /api/chat and return the response text."""
    if input_text.strip():
        content = f"{instruction}\n\nInput: {input_text}"
    else:
        content = instruction

    payload = json.dumps({
        "model": model,
        "messages": [{"role": "user", "content": content}],
        "stream": False,
        "options": {"temperature": temp},
    }).encode()

    req = urllib.request.Request(
        "http://localhost:11434/api/chat",
        data=payload,
        headers={"Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            data = json.loads(resp.read())
            return data.get("message", {}).get("content", "")
    except Exception as e:
        return f"[ERROR] {e}"


def check_assertions(response: str, assertions: list) -> tuple[bool, str]:
    """Run assertions against response. Returns (pass, reason)."""
    for kind, pattern, desc in assertions:
        if kind == "re":
            if not re.search(pattern, response):
                return False, f"FAIL: {desc} (pattern: {pattern})"
        elif kind == "not_re":
            if re.search(pattern, response):
                return False, f"FAIL: should NOT match {desc}"
    return True, "PASS"


def main():
    parser = argparse.ArgumentParser(description="DAVID 8B Ollama smoke test")
    parser.add_argument("--model", default="david", help="Ollama model name")
    parser.add_argument("--temp", type=float, default=0.7, help="Temperature")
    args = parser.parse_args()

    print(f"{'='*60}")
    print(f"  DAVID 8B Ollama Smoke Test")
    print(f"  Model: {args.model}  |  Temp: {args.temp}")
    print(f"{'='*60}")

    results = []
    total = len(TESTS)

    for i, t in enumerate(TESTS, 1):
        print(f"\n[{i}/{total}] {t['label']}")
        t0 = time.time()
        response = call_ollama(args.model, t["instruction"], t["input"], args.temp)
        elapsed = time.time() - t0

        if response.startswith("[ERROR]"):
            passed = False
            reason = response
        else:
            passed, reason = check_assertions(response, t["assertions"])

        known = t.get("known_fail", False)
        score = 100 if passed else 0
        tag = "PASS" if passed else ("KNOWN-FAIL" if known else "FAIL")

        results.append({
            "id": t["id"], "label": t["label"], "pillar": t["pillar"],
            "score": score, "passed": passed, "known_fail": known,
            "tag": tag, "reason": reason, "elapsed": elapsed,
        })

        print(f"  [{tag}] {reason}  ({elapsed:.1f}s)")
        # Print first 200 chars of response for review
        preview = response[:200].replace("\n", " ")
        print(f"  Response: {preview}{'...' if len(response) > 200 else ''}")

    # Summary
    print(f"\n{'='*60}")
    print(f"  SUMMARY")
    print(f"{'='*60}")

    passed_count = sum(1 for r in results if r["passed"])
    known_fails = sum(1 for r in results if r["known_fail"] and not r["passed"])
    real_fails = sum(1 for r in results if not r["passed"] and not r["known_fail"])
    total_score = sum(r["score"] for r in results)
    max_score = total * 100

    for r in results:
        icon = "+" if r["passed"] else ("~" if r["known_fail"] else "X")
        print(f"  [{icon}] {r['id']:4s} {r['label']:40s} {r['score']:3d}/100  ({r['elapsed']:.1f}s)")

    print(f"\n  Score: {total_score}/{max_score} ({total_score * 100 // max_score}/100)")
    print(f"  Assertions: {passed_count}/{total}")
    if known_fails:
        print(f"  Known fails: {known_fails} (P1-C Anglo-Norman)")
    if real_fails:
        print(f"  NEW FAILURES: {real_fails}")
    print(f"{'='*60}")

    return 0 if real_fails == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
