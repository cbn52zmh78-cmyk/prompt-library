#!/usr/bin/env python3
"""
Prompt Specificity & Quality Scorer v1.1 — Director | New Tool
Scores prompts on cinematic strength and suggests improvements. Fully general.
"""

import re
import sys

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
        return {
            "score": final_score,
            "passed": passed,
            "missing": missing,
            "suggestions": suggestions,
        }

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