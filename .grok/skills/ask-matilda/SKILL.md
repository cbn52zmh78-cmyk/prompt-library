---
name: ask-matilda
description: >
  Route Stonebridge narration and trilingual content to MATILDA 8B (local Ollama).
  Use when: ask MATILDA, ask_matilda, Stonebridge client-facing text, security consulting
  narration, trilingual DE/EN/FR presentation, synthetic VP Matilda Kirchner voice,
  /ask-matilda, or content that should sound like Stonebridge staff not Grok.
  Do NOT use for coding, architecture, general research, image/video, or web search.
metadata:
  short-description: "Delegate Stonebridge/trilingual work to local MATILDA"
---

# Ask MATILDA (local Ollama)

MATILDA is Stonebridge's local 8B trilingual presenter (German, English, Swiss French).
She runs on **Ollama** at `http://localhost:11434`, model name `matilda` (Run 10).
**No data leaves the machine.**

## When to call her

**Send to MATILDA:** Stonebridge client-facing narration, trilingual DE/EN/FR, security consulting presentation text, Stonebridge employee voice.

**Keep in Grok:** coding, architecture, research, web search, images/video, non-Stonebridge work.

## Invoke

```powershell
python "C:\Users\NCG\Videos\Grok Projects\AI\ADMIN\MATILDA\matilda_ollama_router.py" --lang <de|en|fr|auto> "PROMPT"
```

Check: `python "...\matilda_ollama_router.py" --check`

Return her text as-is (her voice). If offline: `ollama serve` + ensure model `matilda` is listed.
