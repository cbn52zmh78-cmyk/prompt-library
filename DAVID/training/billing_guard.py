"""
Billing guard — prevents runaway / unauthorized paid-LLM spend.

EVERY paid LLM caller (Anthropic, OpenAI, xAI — any billable endpoint) must route
through this before making a paid call. Provider-agnostic: the three locks apply to
any billable API.

CANONICAL COPY. Self-contained, byte-identical copies live next to the callers in
other submodules (AI/federation/billing_guard.py,
Stonebridge/Operations/Scripts/billing_guard.py) so each submodule imports its own
without cross-submodule path hacks. Keep them in sync.

Three locks:
  1. ALLOW_BILLABLE=1 required        → default OFF, so an autonomous agent can't spend at all.
  2. Per-run call cap (BILLING_MAX_CALLS, default 30) → hard kill-switch on volume.
  3. Key loaded here only             → from env (caller passes the provider env var), else training/.billing_key.

Two usage patterns:

  A. Known batch size — preflight once, tick per call:
        from billing_guard import preflight, tick, load_key
        API_KEY = load_key("ANTHROPIC_API_KEY")
        def main():
            preflight(expected_calls=len(BATCHES))   # once, before the loop
            for ...:
                tick()                                # before EACH api call
                call_api(...)

  B. Choke point / unknown total — gate per call (authorizes on first call, caps every call):
        from billing_guard import gate
        def complete(...):
            gate()                                    # before EACH paid api call
            call_api(...)
"""
import os

_CALLS = 0
_AUTHORIZED = False


def _cap() -> int:
    try:
        return int(os.environ.get("BILLING_MAX_CALLS", "30"))
    except ValueError:
        return 30


def load_key(env_var: str = "ANTHROPIC_API_KEY") -> str:
    """Load the provider key from env first (env_var), then the (gitignored) training/.billing_key."""
    k = os.environ.get(env_var, "").strip()
    if not k:
        kf = os.path.join(os.path.dirname(__file__), ".billing_key")
        if os.path.exists(kf):
            k = open(kf, encoding="utf-8-sig").read().strip()
    return k


def _authorize() -> None:
    """Hard-stop unless billing is explicitly authorized for this run."""
    if os.environ.get("ALLOW_BILLABLE") != "1":
        raise SystemExit(
            "BLOCKED: paid LLM billing is not authorized.\n"
            "  This is a paid call path. Set ALLOW_BILLABLE=1 to enable — HUMAN-RUN ONLY.\n"
            "  Never enable this inside an autonomous agent / CLI session."
        )


def preflight(expected_calls: int, *, key=None) -> None:
    """Call ONCE before a generation run with a known call count.

    Hard-stops unless explicitly authorized + within cap. Pass `key` to validate a
    provider key you resolved yourself (e.g. xAI/Anthropic); omit it to use load_key().
    """
    global _AUTHORIZED
    _authorize()
    cap = _cap()
    if expected_calls > cap:
        raise SystemExit(
            f"BLOCKED: this run wants {expected_calls} paid LLM calls but the cap is {cap}.\n"
            f"  Raise it deliberately with BILLING_MAX_CALLS={expected_calls} if you really mean it."
        )
    if key is None:
        key = load_key()
    if not key:
        raise SystemExit("BLOCKED: no API key (set the provider key env var or training/.billing_key).")
    _AUTHORIZED = True
    print(f"[billing_guard] authorized · up to {expected_calls} calls (cap {cap}).")


def tick() -> None:
    """Call before EACH individual API call. Hard kill-switch if the per-run cap is exceeded."""
    global _CALLS
    _CALLS += 1
    cap = _cap()
    if _CALLS > cap:
        raise SystemExit(f"BLOCKED: kill-switch — exceeded {cap} paid LLM calls this run.")


def gate() -> None:
    """Choke-point guard for callers that don't know the total up front.

    Authorizes on the first paid call (requires ALLOW_BILLABLE=1), then enforces the
    per-run cap on every call. Use this inside a shared client / backend .complete().
    """
    global _AUTHORIZED
    if not _AUTHORIZED:
        _authorize()
        _AUTHORIZED = True
        print(f"[billing_guard] authorized · cap {_cap()} calls/run.")
    tick()
