# API Billing Rules — Claude / paid LLM calls (MANDATORY)

**2026-06-24 · Adopted after an autonomous agent burned the Claude key.** These rules are non-negotiable
for every script that makes a paid LLM API call (Claude, OpenAI, or any billable endpoint).

## The standing rule
1. **Every paid caller routes through `billing_guard.py`** — `load_key()`, `preflight()`, and `tick()`.
   No script calls a billable API directly.
2. **`ALLOW_BILLABLE=1` is required, per run, set by a human.** Default is OFF. An autonomous agent / CLI
   session that does not have this set **cannot make a paid call** — it hard-stops.
3. **`BILLING_MAX_CALLS` defaults to 30** (per-run cap + kill-switch). A bigger run must raise it
   *deliberately* (`BILLING_MAX_CALLS=N`) — a conscious human decision, never an agent default.
4. **Keys come from the environment only** (`ANTHROPIC_API_KEY`). No hardcoded keys; no key files committed
   (`.billing_key`, `*.key`, `*.env`, `*secret*` are gitignored). The old burned key is revoked.
5. **Account-level spend cap is set in the Claude dashboard** as the universal backstop — protects against
   any unguarded or ad-hoc script, found or not.
6. **No autonomous agent holds the live billable key.** Dataset generation is a human-initiated, capped step.

## How to run a generator (the only sanctioned way)
```powershell
$env:ALLOW_BILLABLE = "1"          # this session only; never bake in
$env:BILLING_MAX_CALLS = "8"      # set to the run's real call count
python generate_<lang>_<n>.py
```
Without `ALLOW_BILLABLE=1`, the guard blocks. Over the cap, the kill-switch fires.

## Why
An agent inheriting the env + a live key with no cap = a runaway bill (and a near-miss on a client key).
These rules make that structurally impossible: agents can't spend by default, and every run is bounded.
