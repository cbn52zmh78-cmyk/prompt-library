#!/usr/bin/env python3
"""
Prompt Specificity & Quality Scorer v1.1 — Director | New Tool
Scores prompts on cinematic strength and suggests improvements. Fully general.
"""

import re
import sys
from pathlib import Path as _Path

# --- qa_gate wiring ---
_AI_FED = _Path(__file__).resolve().parents[2] / "AI" / "federation"
if str(_AI_FED) not in sys.path:
    sys.path.insert(0, str(_AI_FED))
try:
    from qa_gate import qa_check as _qa_gate_check
    _QA_GATE_AVAILABLE = True
except ImportError:
    _QA_GATE_AVAILABLE = False
# --- end qa_gate wiring ---

CHECKS = [
    (
        "physics",
        r"natural fabric physics|fabric movement|fabric physics|cloth simulation|natural physics",
        "natural fabric physics",
    ),
    (
        "camera",
        r"slow push-in|push-in|camera move|camera movement|tracking shot|dolly|crane shot|pan ",
        "slow push-in camera movement",
    ),
    (
        "lighting",
        r"side lighting|dramatic lighting|high contrast|directional lighting|rim light|key light",
        "dramatic side lighting",
    ),
    (
        "single_subject",
        r"single subject|single-subject|one subject|solo subject|no extra figures|only one (?:person|woman|man|subject)",
        "single subject, no extra figures",
    ),
    (
        "framing",
        r"16:9|16x9|clean composition|negative space|balanced framing|wide cinematic frame",
        "16:9 clean composition",
    ),
    (
        "eye_contact",
        r"eye contact|sustained gaze|sustained eye contact|direct gaze|locked eyes",
        "sustained eye contact",
    ),
]


class PromptQualityScorer:
    def _evaluate(self, prompt: str) -> tuple[list[str], list[str], list[str]]:
        text = prompt.lower()
        passed: list[str] = []
        missing: list[str] = []
        suggestions: list[str] = []

        for key, pattern, filler in CHECKS:
            if re.search(pattern, text):
                passed.append(key)
            else:
                missing.append(key)
                suggestions.append(filler)

        return passed, missing, suggestions

    def score(self, prompt: str) -> dict:
        passed, missing, suggestions = self._evaluate(prompt)
        final_score = round((len(passed) / len(CHECKS)) * 100) if CHECKS else 0
        result = {
            "score": final_score,
            "passed": passed,
            "missing": missing,
            "suggestions": suggestions,
        }
        # --- qa_gate: enrich with reasoning_qa (non-blocking) ---
        if _QA_GATE_AVAILABLE and prompt and prompt.strip():
            try:
                result["reasoning_qa"] = _qa_gate_check(
                    content=prompt,
                    content_type="general",
                    subject="prompt quality",
                )
            except Exception as _exc:
                result["reasoning_qa"] = {"error": str(_exc)}
        # --- end qa_gate ---
        return result

    def improve(self, prompt: str) -> str:
        """Append missing cinematic elements until the prompt scores 100."""
        _, _, suggestions = self._evaluate(prompt)
        if not suggestions:
            return prompt.strip()

        additions = ", ".join(suggestions)
        base = prompt.strip().rstrip(",.")
        return f"{base}, {additions}"


if __name__ == "__main__":
    scorer = PromptQualityScorer()

    test = (
        "adult woman, sustained eye contact, soft directional lighting, "
        "elegant pose, natural fabric movement"
    )
    if len(sys.argv) > 1:
        test = " ".join(sys.argv[1:])

    before = scorer.score(test)
    improved = scorer.improve(test)
    after = scorer.score(improved)

    print(f"Original score: {before['score']}/100")
    if before["missing"]:
        print(f"Missing: {', '.join(before['missing'])}")
        print("Suggestions:")
        for s in before["suggestions"]:
            print(f"  - {s}")

    print(f"\nImproved prompt:\n  {improved}")
    print(f"\nImproved score: {after['score']}/100")