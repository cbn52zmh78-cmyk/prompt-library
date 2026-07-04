"""sb_registry.py — Stonebridge synthetic employee registry (@SB***** IDs).

Separate namespace from product catalogs (@TYPE_NNN). MATILDA and future
synthetic spokespersons / employees get @SB00001-style permanent IDs —
Stonebridge unique, cross-product, never deleted (archived after retirement),
merge chains for duplicates.

Usage:
    from sb_registry import SBRegistry, SBPersonnel, resolve_any_id

    reg = SBRegistry.load()                   # or SBRegistry.load(custom_path)
    matilda = reg.register("Matilda", "narrator", state={...})
    print(matilda.id)                         # @SB00001

    # Cross-namespace: resolve @CHAR_001 or @SB00001 in one call
    from production_catalog import Catalog
    catalog = Catalog.load(some_path)
    entity = resolve_any_id(catalog, "@SB00001", reg)
"""
from __future__ import annotations

import json
import re
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from _paths import WORKSPACE

# ── ID format ────────────────────────────────────────────────────────────────
# @SB***** — 5-digit zero-padded. Stonebridge's own namespace.

SB_ID_PATTERN = re.compile(r"@SB(\d{5})")
_SB_NEXT_KEY = "_sb_next_id"
SB_PERSONNEL_PATH = WORKSPACE / "Stonebridge" / "Products" / "sb_personnel_registry.json"


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


# ── Personnel entry ──────────────────────────────────────────────────────────
#
# State dict schema for synthetic personnel:
#   model_base: str          — "llama-3.1-8b", "llama-3.1-70b", etc.
#   adapter: str             — adapter name (no paths, no secrets)
#   training_run: str        — "run1", "run2", etc.
#   corpus_version: str      — "266_pairs", "802_pairs", etc.
#   languages: list[str]     — ["en"], ["en", "es"]
#   product_affiliations: list[str] — ["movie", "scout", "atreides"]
#   compliance_tier: str     — "internal" | "customer_facing" | "restricted"
#   deployment_status: str   — "training" | "staging" | "production" | "retired"

@dataclass
class SBPersonnel:
    """One Stonebridge synthetic employee — @SB00001 format."""
    id: str                          # @SB00001, @SB00002, etc.
    name: str                        # Human-readable: "Matilda", etc.
    role: str                        # narrator, spokesperson, analyst, etc.
    created: str = ""
    status: str = "active"           # active | archived | merged
    version: int = 1
    aliases: list[str] = field(default_factory=list)
    merged_into: str | None = None
    state: dict[str, Any] = field(default_factory=dict)
    history: list[dict[str, Any]] = field(default_factory=list)
    notes: str = ""

    def archive(self, reason: str = "") -> None:
        """Retire — ID preserved permanently."""
        self.status = "archived"
        self.history.append({
            "action": "archived", "at": _now(),
            "reason": reason, "version": self.version,
        })

    def merge_into(self, target_id: str, reason: str = "") -> None:
        """Two records → one ID. Source becomes alias of target."""
        self.status = "merged"
        self.merged_into = target_id
        self.history.append({
            "action": "merged", "at": _now(),
            "target": target_id, "reason": reason,
        })

    def bump_version(self, new_state: dict[str, Any], reason: str = "") -> None:
        """New training run, new adapter, new language capability."""
        self.history.append({
            "action": "version_bump", "at": _now(),
            "from_version": self.version,
            "old_state": dict(self.state),
            "reason": reason,
        })
        self.version += 1
        self.state.update(new_state)


# ── Registry ─────────────────────────────────────────────────────────────────

class SBRegistry:
    """Stonebridge synthetic employee registry — @SB***** IDs.

    Permanent-ID religion (never deleted, archived, merge chains) in
    Stonebridge's own namespace. Cross-product: a @SB persona can appear
    in movie scripts, SCOUT narration, ATREIDES reports, etc.
    """

    def __init__(self) -> None:
        self.personnel: dict[str, SBPersonnel] = {}
        self._next_id: int = 1
        self.created: str = _now()

    # ── Persistence ───────────────────────────────────────────────────────

    def save(self, path: Path | str | None = None) -> None:
        path = Path(path or SB_PERSONNEL_PATH)
        path.parent.mkdir(parents=True, exist_ok=True)
        data = {
            "registry_version": "1.0",
            "registry_type": "stonebridge_personnel",
            "created": self.created,
            "saved_at": _now(),
            "personnel_count": len(self.personnel),
            _SB_NEXT_KEY: self._next_id,
            "personnel": {pid: asdict(p) for pid, p in self.personnel.items()},
        }
        path.write_text(
            json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8",
        )

    @classmethod
    def load(cls, path: Path | str | None = None) -> "SBRegistry":
        path = Path(path or SB_PERSONNEL_PATH)
        if not path.is_file():
            reg = cls()
            reg.save(path)
            return reg
        data = json.loads(path.read_text(encoding="utf-8"))
        reg = cls()
        reg.created = data.get("created", _now())
        reg._next_id = data.get(_SB_NEXT_KEY, 1)
        for pid, pdata in data.get("personnel", {}).items():
            reg.personnel[pid] = SBPersonnel(**pdata)
        return reg

    # ── ID operations ─────────────────────────────────────────────────────

    def register(
        self,
        name: str,
        role: str,
        state: dict[str, Any] | None = None,
        notes: str = "",
    ) -> SBPersonnel:
        """Mint a new @SB***** ID for a synthetic employee."""
        pid = f"@SB{self._next_id:05d}"
        self._next_id += 1
        person = SBPersonnel(
            id=pid, name=name, role=role,
            created=_now(), state=state or {}, notes=notes,
        )
        self.personnel[pid] = person
        return person

    def resolve(self, sb_id: str) -> SBPersonnel | None:
        """Look up by @SB***** ID. Follows merge chains."""
        person = self.personnel.get(sb_id)
        if person and person.status == "merged" and person.merged_into:
            return self.resolve(person.merged_into)
        return person

    def find_by_name(self, name: str) -> list[SBPersonnel]:
        """Find personnel by name (case-insensitive)."""
        name_lower = name.lower()
        return [
            p for p in self.personnel.values()
            if p.status != "merged"
            and (p.name.lower() == name_lower
                 or name_lower in [a.lower() for a in p.aliases])
        ]

    def active_personnel(self, role: str = "") -> list[SBPersonnel]:
        """All non-merged personnel, optionally filtered by role."""
        return [
            p for p in self.personnel.values()
            if p.status != "merged"
            and (not role or p.role == role)
        ]

    def by_product(self, product: str) -> list[SBPersonnel]:
        """All personnel affiliated with a product."""
        key = product.strip().lower()
        return [
            p for p in self.personnel.values()
            if p.status != "merged"
            and key in [a.lower() for a in p.state.get("product_affiliations", [])]
        ]


# ── Cross-namespace resolution ───────────────────────────────────────────────

def resolve_any_id(
    catalog: "Any",
    entity_id: str,
    sb_registry: SBRegistry | None = None,
) -> "Any":
    """Resolve @TYPE_NNN (product catalog) or @SB***** (personnel) IDs.

    Movie scripts can reference both @CHAR_001 and @SB00001 — this resolves
    either namespace in one call.

    Args:
        catalog: A production_catalog.Catalog instance.
        entity_id: The @ID to resolve.
        sb_registry: Optional SBRegistry for @SB***** lookups.
    """
    if SB_ID_PATTERN.match(entity_id):
        return sb_registry.resolve(entity_id) if sb_registry else None
    return catalog.resolve(entity_id)


def sb_registry_path() -> Path:
    """Standard path for the Stonebridge personnel registry."""
    return SB_PERSONNEL_PATH


# ── CLI smoke ────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import tempfile

    reg = SBRegistry()
    m = reg.register("Matilda", "narrator", state={
        "model_base": "llama-3.1-8b",
        "adapter": "matilda-v1",
        "languages": ["en"],
        "product_affiliations": ["movie", "scout"],
        "compliance_tier": "internal",
        "deployment_status": "training",
    })
    assert m.id == "@SB00001"
    print(f"{m.id} = {m.name} ({m.role})")

    s = reg.register("Future Spokesperson", "spokesperson", state={
        "product_affiliations": ["atreides"],
        "compliance_tier": "customer_facing",
        "deployment_status": "staging",
    })
    assert s.id == "@SB00002"
    print(f"{s.id} = {s.name} ({s.role})")

    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td) / "test.json"
        reg.save(tmp)
        loaded = SBRegistry.load(tmp)
        assert loaded.resolve("@SB00001").name == "Matilda"
        assert len(loaded.by_product("movie")) == 1
        assert len(loaded.by_product("scout")) == 1
        assert len(loaded.active_personnel("narrator")) == 1
        print("persistence: OK")

    # Version bump
    m.bump_version({"adapter": "matilda-v2", "corpus_version": "802_pairs"}, reason="Run 2")
    assert m.version == 2
    print(f"version_bump: v{m.version} OK")

    # Archive + merge
    s.archive("Replaced")
    assert s.status == "archived"
    print(f"archive: {s.id} OK")

    reg2 = SBRegistry()
    a = reg2.register("Dup1", "analyst")
    b = reg2.register("Dup2", "analyst")
    a.merge_into(b.id)
    assert reg2.resolve(a.id).id == b.id
    print("merge: OK")

    print("ALL SB TESTS PASSED")
