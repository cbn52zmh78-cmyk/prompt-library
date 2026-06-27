"""
Generate 150 Alpaca-format Ancient Greek translation training pairs via Claude API.
Usage: ALLOW_BILLABLE=1 python training/generate_greek_translation_150.py
Output: training/ancient_greek_translation_150.jsonl
"""
import json, os, time
import urllib.request, urllib.error
from billing_guard import load_key, preflight, tick   # billing guard (ALLOW_BILLABLE + call cap)

API_KEY = load_key()
OUT = os.path.join(os.path.dirname(__file__), "ancient_greek_translation_150.jsonl")

SYSTEM = (
    "You generate Ancient Greek translation training data in strict Alpaca JSONL format. "
    "Each line is a self-contained JSON object with exactly three keys: instruction, input, output. "
    "instruction: A translation instruction naming the register or dialect. "
    "input: An authentic attested Ancient Greek passage using Greek Unicode characters. "
    "output: Must follow this EXACT template (use literal \\n): "
    "**Translation:** [English]\\n\\n**Translator's note:** [2+ sentences on dialect, key terms, grammar, literary features]\\n\\n**Source:** [Author, Work ref] [attested] "
    "Rules: Output ONLY raw JSON lines. No markdown, no arrays, no wrappers. "
    "Each line must be valid JSON. Escape internal quotes. Never fabricate passages."
)

BATCHES = [
    ("Homer",       30, "Iliad, Odyssey",                                        "Use hexameter passages, epithets, extended similes, speeches from both epics."),
    ("Plato",       25, "Apology, Republic, Symposium, Phaedo, Meno",            "Include key terms: arete, eudaimonia, psyche, logos, doxa, episteme, mimesis."),
    ("Thucydides",  20, "History of the Peloponnesian War",                      "Funeral Oration, Melian Dialogue, plague. Note periodic syntax and antithesis."),
    ("Aristotle",   20, "Nicomachean Ethics, Politics, Poetics, Metaphysics",    "Include: phronesis, eudaimonia, mimesis, ousia, techne, prohairesis, logos."),
    ("Sophocles",   20, "Antigone, Oedipus Rex, Electra, Ajax",                  "Include choral odes, stichomythia, tragic irony. Note Attic dialect forms."),
    ("Xenophon",    15, "Anabasis, Memorabilia, Cyropaedia",                     "Simpler Attic prose. Note contrast with Thucydidean complexity."),
    ("Euripides",   15, "Medea, Bacchae, Hecuba, Hippolytus",                    "Emotional monologues, divine prologues, stichomythia, iambic trimeter."),
    ("Herodotus",    5, "Histories",                                             "Ionic dialect. Croesus/Solon, Melian debate precursors, ethnographic passages."),
]

def call_api(author, count, works, note):
    prompt = f"Generate exactly {count} Ancient Greek translation training pairs for {author}. Works: {works}. {note} Output {count} raw JSON lines only."
    body = json.dumps({
        "model": "claude-sonnet-4-6",
        "messages": [{"role": "system", "content": SYSTEM}, {"role": "user", "content": prompt}],
        "temperature": 0.3,
        "max_tokens": 8000,
    }).encode()
    req = urllib.request.Request(
        "https://api.anthropic.com/v1/messages",
        data=body,
        headers={"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=120) as r:
        return json.loads(r.read())["choices"][0]["message"]["content"].strip()

def main():
    preflight(expected_calls=len(BATCHES))   # billing guard: requires ALLOW_BILLABLE=1 + within BILLING_MAX_CALLS
    pairs = []
    for author, count, works, note in BATCHES:
        print(f"  {author} ({count} pairs)...", end=" ", flush=True)
        try:
            tick()                               # billing guard: per-call kill-switch
            text = call_api(author, count, works, note)
            batch = []
            for line in text.splitlines():
                line = line.strip()
                if line.startswith("{") and line.endswith("}"):
                    try:
                        json.loads(line)
                        batch.append(line)
                    except json.JSONDecodeError:
                        pass
            pairs.extend(batch)
            print(f"got {len(batch)} | total {len(pairs)}")
        except Exception as e:
            print(f"ERROR: {e}")
        time.sleep(2)

    with open(OUT, "w", encoding="utf-8") as f:
        f.write("\n".join(pairs) + "\n")
    print(f"\nDone. {len(pairs)} pairs -> {OUT}")

if __name__ == "__main__":
    main()
