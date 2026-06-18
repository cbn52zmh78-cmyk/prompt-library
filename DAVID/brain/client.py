"""Rate-limited HTTP client for DAVID Brain public APIs."""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any

import requests

_CONFIG = Path(__file__).resolve().parents[1] / "data" / "brain_sources.json"
_cfg = json.loads(_CONFIG.read_text(encoding="utf-8"))

USER_AGENT = _cfg["user_agent"]
RATE_LIMIT = float(_cfg.get("rate_limit_seconds", 1.0))
_last_request = 0.0


def _throttle() -> None:
    global _last_request
    elapsed = time.monotonic() - _last_request
    if elapsed < RATE_LIMIT:
        time.sleep(RATE_LIMIT - elapsed)
    _last_request = time.monotonic()


def get_json(
    url: str,
    params: dict[str, Any] | None = None,
    timeout: int = 30,
    retries: int = 5,
) -> dict[str, Any]:
    headers = {"User-Agent": USER_AGENT}
    last_exc: Exception | None = None
    for attempt in range(retries):
        _throttle()
        try:
            response = requests.get(url, params=params, headers=headers, timeout=timeout)
            if response.status_code == 429:
                wait = max(5, 2 ** (attempt + 2))
                time.sleep(wait)
                continue
            response.raise_for_status()
            return response.json()
        except requests.RequestException as exc:
            last_exc = exc
            if attempt < retries - 1:
                time.sleep(max(2, 2 * (attempt + 1)))
    raise last_exc  # type: ignore[misc]


def mediawiki_api(base_url: str, **params: Any) -> dict[str, Any]:
    payload = {"format": "json", **params}
    return get_json(base_url, payload)