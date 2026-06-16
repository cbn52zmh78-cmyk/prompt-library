#!/usr/bin/env python3
import sys

def test_prompt(prompt_text):
    print("\n=== PROMPT TEST ===\n")
    print("Prompt:")
    print("-" * 50)
    print(prompt_text)
    print("-" * 50)
    print("\n[This is a placeholder. In the future, this can send the prompt to a model for testing.]")
    print("For now, just review the prompt above for clarity and structure.\n")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: prompt_tester.py \"Your prompt text here\"")
        sys.exit(1)

    prompt = sys.argv[1]
    test_prompt(prompt)