"""T5 — deepseek_guard enforcement: byte-identical copies + paid-caller import audit.

Locks the 2026-06-24 billing security fix. Fails if:
  - any canonical deepseek_guard.py copy drifts from the others
  - any Python file that directly references a paid LLM endpoint does not import the guard
"""

from __future__ import annotations

import hashlib
import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]

CANONICAL_GUARD_COPIES: tuple[Path, ...] = (
    ROOT / "DAVID" / "training" / "deepseek_guard.py",
    ROOT / "AI" / "federation" / "deepseek_guard.py",
    ROOT / "Stonebridge" / "Operations" / "Scripts" / "deepseek_guard.py",
)

# Files that must exist and route paid traffic through deepseek_guard.
KNOWN_PAID_CALLERS: frozenset[str] = frozenset({
    "DAVID/training/generate_greek_translation_150.py",
    "AI/training/synthetic_generator.py",
    "AI/federation/reasoning_config.py",
    "Stonebridge/Operations/Scripts/llm_client.py",
})

PAID_ENDPOINT_PATTERNS: tuple[re.Pattern[str], ...] = (
    re.compile(r"chat/completions"),
    re.compile(r"api\.deepseek\.com"),
    re.compile(r"api\.openai\.com"),
    re.compile(r"api\.anthropic\.com"),
    re.compile(r"api\.x\.ai"),
)

GUARD_IMPORT_MARKERS: tuple[str, ...] = (
    "deepseek_guard",
    "_billing_gate",
)

SCAN_ROOTS: tuple[Path, ...] = (
    ROOT / "AI",
    ROOT / "DAVID",
    ROOT / "Stonebridge",
)

SKIP_DIR_NAMES: frozenset[str] = frozenset({
    ".git",
    "__pycache__",
    ".pytest_cache",
    "node_modules",
    ".venv",
    "venv",
    "ml_env",
    "site-packages",
    "Lib",
    "_archive",
})

SKIP_PATH_PARTS: frozenset[str] = frozenset({
    "tests",
    "agent-tools",
})


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _rel_posix(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def _is_paid_caller_source(text: str) -> bool:
    return any(pat.search(text) for pat in PAID_ENDPOINT_PATTERNS)


def _imports_guard(text: str) -> bool:
    return any(marker in text for marker in GUARD_IMPORT_MARKERS)


def _iter_python_sources() -> list[Path]:
    found: list[Path] = []
    for scan_root in SCAN_ROOTS:
        if not scan_root.is_dir():
            continue
        for path in scan_root.rglob("*.py"):
            if path.name == "deepseek_guard.py":
                continue
            if any(part in SKIP_PATH_PARTS for part in path.parts):
                continue
            if any(part in SKIP_DIR_NAMES for part in path.parts):
                continue
            found.append(path)
    return found


def _find_unguarded_paid_callers() -> list[str]:
    violations: list[str] = []
    for path in _iter_python_sources():
        text = path.read_text(encoding="utf-8", errors="replace")
        if not _is_paid_caller_source(text):
            continue
        if not _imports_guard(text):
            violations.append(_rel_posix(path))
    return sorted(violations)


# --- guard copies -----------------------------------------------------------


def test_canonical_guard_copies_exist() -> None:
    missing = [p for p in CANONICAL_GUARD_COPIES if not p.is_file()]
    assert not missing, "Missing deepseek_guard.py copies:\n" + "\n".join(
        f"  - {_rel_posix(p)}" for p in missing
    )


def test_canonical_guard_copies_are_byte_identical() -> None:
    digests = {_sha256(p): p for p in CANONICAL_GUARD_COPIES}
    assert len(digests) == 1, (
        "deepseek_guard.py copies have drifted — keep all three byte-identical:\n"
        + "\n".join(f"  {_sha256(p)}  {_rel_posix(p)}" for p in CANONICAL_GUARD_COPIES)
    )


def test_guard_copies_expose_required_api() -> None:
    required = {"load_key", "preflight", "tick", "gate"}
    for path in CANONICAL_GUARD_COPIES:
        text = path.read_text(encoding="utf-8")
        missing = sorted(fn for fn in required if f"def {fn}" not in text)
        assert not missing, f"{_rel_posix(path)} missing: {', '.join(missing)}"


# --- paid caller audit ------------------------------------------------------


def test_known_paid_callers_present() -> None:
    missing = sorted(
        rel for rel in KNOWN_PAID_CALLERS
        if not (ROOT / rel).is_file()
    )
    assert not missing, "Expected paid callers missing from repo:\n" + "\n".join(
        f"  - {rel}" for rel in missing
    )


@pytest.mark.parametrize("rel_path", sorted(KNOWN_PAID_CALLERS))
def test_known_paid_caller_imports_guard(rel_path: str) -> None:
    path = ROOT / rel_path
    text = path.read_text(encoding="utf-8")
    assert _is_paid_caller_source(text), f"{rel_path} no longer references a paid endpoint"
    assert _imports_guard(text), (
        f"{rel_path} must import deepseek_guard (gate/preflight/tick/load_key) before paid calls"
    )


def test_no_unguarded_paid_callers_in_submodules() -> None:
    violations = _find_unguarded_paid_callers()
    assert not violations, (
        "Paid LLM endpoint(s) found without deepseek_guard import — route through the guard:\n"
        + "\n".join(f"  - {rel}" for rel in violations)
    )