#!/usr/bin/env python3
"""Observable science batch runner — stand up the science slates into the batch runner.

#173 finishes wiring the science pipeline across ALL three science slates:

    astro_mini_slate        (astro)            — #153 Observable launch slate
    molecular_mini_slate    (molecular)        — #160/#172 plate-locked
    chem_physics_mini_slate (chemistry/physics)— #180 chem/physics slate

For each slate it runs a science-specific *readiness gate* in front of the shared
``batch_runner`` loop:

  1. harvest gate  — the plate each episode consumes is HARVESTED/OK in its domain
                     reference manifest (astro/molecular/chemistry/physics manifests
                     all have different shapes — normalised here);
  2. plate gate    — the on-disk reference image the concept points at actually
                     exists and is a real image (not a broken few-hundred-byte
                     placeholder). The #158 honesty rail checks the *script*; this
                     checks the *plate*, closing the gap between them.

``--repair`` repoints a concept whose plate is broken/missing to the domain's
locked ``*_reference.jpg`` when one is available, then re-checks.

Once a slate is ready it delegates to ``batch_runner run`` (intake → 480p draft →
manifest), and ``standup --all`` aggregates every slate's manifest into one
combined ``science_manifest.json`` with per-slate / per-domain / honesty roll-ups.

Usage:
    python DAVID/scripts/science_batch_runner.py slates
    python DAVID/scripts/science_batch_runner.py check
    python DAVID/scripts/science_batch_runner.py check --slate chem_physics
    python DAVID/scripts/science_batch_runner.py standup --all --dry-run
    python DAVID/scripts/science_batch_runner.py standup --slate molecular --dry-run
    python DAVID/scripts/science_batch_runner.py standup --all --dry-run --repair
    # astro R1 back-compat:
    python DAVID/scripts/science_batch_runner.py stage-plates
    python DAVID/scripts/science_batch_runner.py render-first --resolution 720p
"""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

ROOT = Path(__file__).resolve().parents[2]
DAVID = ROOT / "DAVID"
PIPELINE = ROOT / "STUDIO" / "Pipeline"
SCIENCE = ROOT / "Science"
CONCEPTS_ROOT = PIPELINE / "Concepts"
SCRIPTS_DIR = DAVID / "scripts" / "longform_scripts"
INTAKE = PIPELINE / "production_intake.py"
RENDER = DAVID / "scripts" / "render_longform.py"
BATCH = DAVID / "scripts" / "batch_runner.py"
REF_ROOT = SCIENCE / "reference_plates"

DRAFT_RES = "480p"
# A real reference plate is never this small; broken harvest stubs are a few
# hundred bytes (e.g. an HTML error page saved as .png).
MIN_REF_BYTES = 5_000

# Domain harvest manifests — three different shapes, normalised by _harvest_map().
DOMAIN_MANIFESTS: dict[str, Path] = {
    "astro": REF_ROOT / "astro_reference_manifest.json",
    "molecular": REF_ROOT / "molecular" / "molecular_reference_manifest.json",
    "chemistry": REF_ROOT / "chemistry_reference_manifest.json",
    "physics": REF_ROOT / "physics_reference_manifest.json",
}

# Statuses that count as "plate harvested and available" across manifest shapes.
HARVEST_OK = {"OK", "HARVESTED", "LOCKED", "READY"}

# A science_subject.domain string ("Chemistry — Chemical Bonding") → harvest domain.
SUBJECT_DOMAIN_PREFIXES: list[tuple[str, str]] = [
    ("astro", "astro"),
    ("molecular", "molecular"),
    ("chemistry", "chemistry"),
    ("physics", "physics"),
]

# The science slates wired into the batch runner.
SLATES: list[dict[str, str]] = [
    {
        "id": "astro",
        "title": "Astrophysics mini-slate (#153 Observable launch)",
        "concepts_dir": "Studio/Pipeline/Concepts/astro_mini_slate",
    },
    {
        "id": "molecular",
        "title": "Molecular biology mini-slate (#160/#172)",
        "concepts_dir": "Studio/Pipeline/Concepts/molecular_mini_slate",
    },
    {
        "id": "chem_physics",
        "title": "Chemistry & physics mini-slate (#180)",
        "concepts_dir": "Studio/Pipeline/Concepts/chem_physics_mini_slate",
    },
]


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _ledger_note(path, **meta):
    """#259 path-stamping: record an output in the canonical ledger (best-effort)."""
    try:
        tools = ROOT / "tools"
        if str(tools) not in sys.path:
            sys.path.insert(0, str(tools))
        from output_registry import note

        note(path, **meta)
    except Exception:
        pass


def _write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    _ledger_note(path)


def _rel(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT)).replace("\\", "/")
    except ValueError:
        return str(path).replace("\\", "/")


def _force_utf8_stdout() -> None:
    """batch_runner prints emoji/arrows; the Windows console defaults to cp1252."""
    for stream in (sys.stdout, sys.stderr):
        reconfig = getattr(stream, "reconfigure", None)
        if reconfig is not None:
            try:
                reconfig(encoding="utf-8")
            except (ValueError, OSError):
                pass


# --------------------------------------------------------------------------- gates
_HARVEST_CACHE: dict[str, dict[str, bool]] = {}


def _harvest_map(domain: str) -> dict[str, bool]:
    """slug → harvested? for a domain manifest, normalising its shape.

    astro      : ``entries[]``  with ``harvest_status``
    molecular  : ``subjects[]`` with ``status``
    chemistry  : ``subjects[]`` with ``status``
    physics    : ``subjects[]`` with ``status``
    """
    if domain in _HARVEST_CACHE:
        return _HARVEST_CACHE[domain]

    manifest_path = DOMAIN_MANIFESTS.get(domain)
    result: dict[str, bool] = {}
    if manifest_path and manifest_path.is_file():
        manifest = _load_json(manifest_path)
        rows = manifest.get("entries") or manifest.get("subjects") or manifest.get("plates") or []
        for row in rows:
            slug = row.get("slug")
            if not slug:
                continue
            status = str(row.get("harvest_status") or row.get("status") or "").upper()
            result[slug] = status in HARVEST_OK
    _HARVEST_CACHE[domain] = result
    return result


def domain_for_subject(subject_domain: Optional[str]) -> Optional[str]:
    text = (subject_domain or "").strip().lower()
    for prefix, domain in SUBJECT_DOMAIN_PREFIXES:
        if text.startswith(prefix):
            return domain
    return None


def _abs_ref(ref_rel: Optional[str]) -> Optional[Path]:
    if not ref_rel:
        return None
    return ROOT / str(ref_rel).replace("\\", "/")


def _ref_bytes(ref_rel: Optional[str]) -> int:
    path = _abs_ref(ref_rel)
    if path and path.is_file():
        return path.stat().st_size
    return 0


def find_locked_reference(domain: Optional[str], plate_slug: Optional[str]) -> Optional[str]:
    """Locate a valid locked ``*_reference.jpg`` for a plate (repair fallback)."""
    if not domain or not plate_slug:
        return None
    domain_dir = REF_ROOT / domain
    stems = {plate_slug, plate_slug.replace("-", "_"), plate_slug.replace("_", "-")}
    for stem in stems:
        for ext in (".jpg", ".jpeg", ".png"):
            cand = domain_dir / f"{stem}_reference{ext}"
            if cand.is_file() and cand.stat().st_size >= MIN_REF_BYTES:
                return _rel(cand)
    return None


def discover_episodes(concepts_dir: Path) -> list[dict[str, Any]]:
    """Read every science concept's science_subject wiring in a slate folder."""
    episodes: list[dict[str, Any]] = []
    for concept_path in sorted(concepts_dir.glob("*.concept.json")):
        concept = _load_json(concept_path)
        ss = concept.get("science_subject") or {}
        episodes.append(
            {
                "slug": concept.get("slug"),
                "concept_path": _rel(concept_path),
                "plate_slug": ss.get("plate_slug"),
                "plate_id": ss.get("plate_id"),
                "subject_domain": ss.get("domain"),
                "domain": domain_for_subject(ss.get("domain")),
                "visualization_ref": ss.get("visualization_ref"),
            }
        )
    return episodes


def check_episode(ep: dict[str, Any]) -> dict[str, Any]:
    """Harvest gate + plate-integrity gate for one episode."""
    domain = ep.get("domain")
    plate_slug = ep.get("plate_slug")
    harvest = _harvest_map(domain) if domain else {}
    harvest_ok = bool(harvest.get(plate_slug)) if plate_slug else False

    ref = ep.get("visualization_ref")
    ref_bytes = _ref_bytes(ref)
    ref_ok = ref_bytes >= MIN_REF_BYTES

    reasons: list[str] = []
    if not domain:
        reasons.append(f"unmapped domain {ep.get('subject_domain')!r}")
    elif not plate_slug:
        reasons.append("concept has no science_subject.plate_slug")
    elif plate_slug not in harvest:
        reasons.append(f"plate {plate_slug!r} absent from {domain} reference manifest")
    elif not harvest_ok:
        reasons.append(f"plate {plate_slug!r} not harvested in {domain} manifest")
    if not ref:
        reasons.append("no visualization_ref wired")
    elif ref_bytes == 0:
        reasons.append(f"reference file missing on disk: {ref}")
    elif not ref_ok:
        reasons.append(f"reference file too small ({ref_bytes} B) — broken plate: {ref}")

    return {
        **ep,
        "harvest_ok": harvest_ok,
        "ref_bytes": ref_bytes,
        "ref_ok": ref_ok,
        "ready": harvest_ok and ref_ok,
        "reasons": reasons,
    }


def check_slate(slate: dict[str, str]) -> dict[str, Any]:
    concepts_dir = ROOT / slate["concepts_dir"]
    if not concepts_dir.is_dir():
        return {
            "slate": slate["id"],
            "title": slate["title"],
            "concepts_dir": slate["concepts_dir"],
            "ready": False,
            "error": "concepts folder not found",
            "episodes": [],
        }
    episodes = [check_episode(ep) for ep in discover_episodes(concepts_dir)]
    blocked = [e for e in episodes if not e["ready"]]
    return {
        "slate": slate["id"],
        "title": slate["title"],
        "concepts_dir": slate["concepts_dir"],
        "episode_count": len(episodes),
        "ready_count": len(episodes) - len(blocked),
        "ready": bool(episodes) and not blocked,
        "blocked_slugs": [e["slug"] for e in blocked],
        "episodes": episodes,
        "checked_at": _utc_now(),
    }


def check_all(slate_id: Optional[str] = None) -> dict[str, Any]:
    slates = [s for s in SLATES if not slate_id or s["id"] == slate_id]
    if slate_id and not slates:
        raise SystemExit(f"Unknown slate {slate_id!r} (have: {', '.join(s['id'] for s in SLATES)})")
    reports = [check_slate(s) for s in slates]
    return {
        "generated_at": _utc_now(),
        "ready": all(r["ready"] for r in reports),
        "slates": reports,
    }


# --------------------------------------------------------------------------- repair
def repair_slate(slate: dict[str, str]) -> list[dict[str, Any]]:
    """Repoint concepts whose plate is broken/missing to a locked reference."""
    concepts_dir = ROOT / slate["concepts_dir"]
    repaired: list[dict[str, Any]] = []
    for ep in discover_episodes(concepts_dir):
        checked = check_episode(ep)
        if checked["ref_ok"]:
            continue
        prev = ep.get("visualization_ref")
        locked = find_locked_reference(ep.get("domain"), ep.get("plate_slug"))
        if not locked or locked == prev:
            continue

        concept_path = ROOT / ep["concept_path"]
        # Surgical text swap of the ref value only — preserves the concept's exact
        # formatting and ascii-escaping (avoids a whole-file reserialise diff).
        # Covers both science_subject.visualization_ref and any config mirror.
        if prev:
            raw = concept_path.read_text(encoding="utf-8")
            updated = raw.replace(f'"{prev}"', f'"{locked}"')
            concept_path.write_text(updated, encoding="utf-8")
        else:
            concept = _load_json(concept_path)
            concept.setdefault("science_subject", {})["visualization_ref"] = locked
            _write_json(concept_path, concept)
        repaired.append(
            {
                "slug": ep["slug"],
                "plate_slug": ep.get("plate_slug"),
                "previous_ref": prev,
                "previous_bytes": checked["ref_bytes"],
                "repaired_ref": locked,
                "repaired_bytes": _ref_bytes(locked),
            }
        )
    return repaired


# --------------------------------------------------------------------------- run
def _run_batch_for_slate(
    slate: dict[str, str],
    *,
    batch_dir: Path,
    batch_id: str,
    dry_run: bool,
    no_seamless: bool,
) -> tuple[int, Optional[dict[str, Any]]]:
    """Drive batch_runner.cmd_run in-process for one slate; return (rc, manifest)."""
    sys.path.insert(0, str(DAVID / "scripts"))
    import batch_runner  # noqa: WPS433

    args = argparse.Namespace(
        concepts_dir=slate["concepts_dir"],
        batch_id=batch_id,
        batch_dir=str(batch_dir),
        dry_run=dry_run,
        no_seamless=no_seamless,
        max_attempts=1,
        backoff_base=1.0,
        backoff_max=1.0,
    )
    rc = batch_runner.cmd_run(args)
    manifest_path = batch_dir / "manifest.json"
    manifest = _load_json(manifest_path) if manifest_path.is_file() else None
    return rc, manifest


def _merge_counts(dest: dict[str, int], src: dict[str, int]) -> None:
    for key, val in src.items():
        dest[key] = dest.get(key, 0) + val


def cmd_standup(args: argparse.Namespace) -> int:
    _force_utf8_stdout()

    if args.all:
        slates = list(SLATES)
    elif args.slate:
        slates = [s for s in SLATES if s["id"] == args.slate]
        if not slates:
            raise SystemExit(f"Unknown slate {args.slate!r}")
    else:
        slates = [SLATES[0]]  # astro default (back-compat)

    batch_id = args.batch_id or (
        "science_all_dryrun" if args.all and args.dry_run
        else datetime.now(timezone.utc).strftime("science_%Y%m%d_%H%M%S")
    )
    combined_dir = Path(args.batch_dir) if args.batch_dir else (DAVID / "batches" / batch_id)
    if not combined_dir.is_absolute():
        combined_dir = ROOT / combined_dir

    print(f"[science] standup slates={[s['id'] for s in slates]} dry_run={args.dry_run} repair={args.repair}")

    slate_reports: list[dict[str, Any]] = []
    all_items: list[dict[str, Any]] = []
    summary: dict[str, int] = {}
    science_summary = {"science_episodes": 0, "honesty_pass": 0, "honesty_fail": 0}
    worst_rc = 0

    for slate in slates:
        print(f"\n[science] === {slate['id']} — {slate['title']} ===")

        repaired: list[dict[str, Any]] = []
        if args.repair:
            repaired = repair_slate(slate)
            for r in repaired:
                print(f"  ⛑ repaired {r['slug']}: {r['previous_ref']} "
                      f"({r['previous_bytes']} B) → {r['repaired_ref']} ({r['repaired_bytes']} B)")

        readiness = check_slate(slate)
        status_icon = "✅" if readiness["ready"] else "⛔"
        print(f"  {status_icon} readiness {readiness['ready_count']}/{readiness['episode_count']} ready")
        for ep in readiness["episodes"]:
            if not ep["ready"]:
                print(f"      ⛔ {ep['slug']}: {'; '.join(ep['reasons'])}")

        if not readiness["ready"] and not args.allow_unready:
            print(f"  ⏭  {slate['id']} blocked — skipping batch (use --allow-unready to force)")
            slate_reports.append(
                {
                    "slate": slate["id"],
                    "title": slate["title"],
                    "ready": readiness["ready"],
                    "blocked_slugs": readiness["blocked_slugs"],
                    "repaired": repaired,
                    "readiness": readiness,
                    "manifest": None,
                    "batch_rc": None,
                    "ran": False,
                }
            )
            worst_rc = max(worst_rc, 1)
            continue

        slate_batch_dir = combined_dir / slate["id"]
        rc, manifest = _run_batch_for_slate(
            slate,
            batch_dir=slate_batch_dir,
            batch_id=f"{batch_id}_{slate['id']}",
            dry_run=args.dry_run,
            no_seamless=args.no_seamless,
        )
        worst_rc = max(worst_rc, rc)

        items = manifest.get("items", []) if manifest else []
        for item in items:
            item["slate"] = slate["id"]
        all_items.extend(items)
        if manifest:
            _merge_counts(summary, manifest.get("summary", {}))
            for key, val in manifest.get("science_summary", {}).items():
                science_summary[key] = science_summary.get(key, 0) + val

        slate_reports.append(
            {
                "slate": slate["id"],
                "title": slate["title"],
                "ready": readiness["ready"],
                "blocked_slugs": readiness["blocked_slugs"],
                "repaired": repaired,
                "readiness": readiness,
                "manifest": _rel(slate_batch_dir / "manifest.json") if manifest else None,
                "summary": manifest.get("summary") if manifest else None,
                "science_summary": manifest.get("science_summary") if manifest else None,
                "batch_rc": rc,
                "ran": True,
            }
        )

    by_domain = _domain_rollup(all_items)
    combined = {
        "batch_id": batch_id,
        "kind": "science_combined_manifest",
        "generated_at": _utc_now(),
        "dry_run": args.dry_run,
        "repair": args.repair,
        "resolution": DRAFT_RES,
        "slates": slate_reports,
        "items": all_items,
        "summary": summary,
        "science_summary": science_summary,
        "by_domain": by_domain,
        "ready": all(r["ready"] for r in slate_reports),
    }
    combined_path = combined_dir / "science_manifest.json"
    _write_json(combined_path, combined)

    print(f"\n[science] combined manifest → {_rel(combined_path)}")
    print(f"[science] slates ready: {sum(1 for r in slate_reports if r['ready'])}/{len(slate_reports)}")
    print(f"[science] summary: {summary}")
    print(f"[science] science: {science_summary}")
    print(f"[science] by_domain: {by_domain}")
    return worst_rc


def _domain_rollup(items: list[dict[str, Any]]) -> dict[str, dict[str, int]]:
    rollup: dict[str, dict[str, int]] = {}
    for item in items:
        gate = item.get("science_gate") or {}
        # Recover the domain from the production dir / slate where possible.
        domain = item.get("slate", "unknown")
        bucket = rollup.setdefault(domain, {"episodes": 0, "honesty_pass": 0, "honesty_fail": 0})
        bucket["episodes"] += 1
        if item.get("honesty_pass") is True:
            bucket["honesty_pass"] += 1
        elif item.get("honesty_pass") is False:
            bucket["honesty_fail"] += 1
    return rollup


def cmd_check(args: argparse.Namespace) -> int:
    report = check_all(args.slate)
    print(json.dumps(report, indent=2, ensure_ascii=False))
    if not report["ready"]:
        blocked = [
            f"{s['slate']}:{s.get('blocked_slugs')}"
            for s in report["slates"] if not s["ready"]
        ]
        print(f"\n[science] NOT READY — {'; '.join(blocked)}")
        return 1
    total = sum(s.get("episode_count", 0) for s in report["slates"])
    print(f"\n[science] READY — {total} episode(s) across {len(report['slates'])} slate(s)")
    return 0


def cmd_slates(_: argparse.Namespace) -> int:
    for slate in SLATES:
        concepts_dir = ROOT / slate["concepts_dir"]
        episodes = discover_episodes(concepts_dir) if concepts_dir.is_dir() else []
        print(f"{slate['id']:14} {len(episodes)} ep  {slate['concepts_dir']}")
        for ep in episodes:
            print(f"   - {ep['slug']:32} [{ep.get('domain')}] {ep.get('plate_slug')}")
    return 0


# ------------------------------------------------------- astro R1 staging (back-compat)
R1_MANIFEST = REF_ROOT / "astro_reference_manifest.json"
PLATE_LIBRARY = REF_ROOT / "science_plate_library_v1.json"
HARVEST_DIR = REF_ROOT / "astro" / "harvest"
ASTRO_CONCEPTS_DIR = CONCEPTS_ROOT / "astro_mini_slate"
OBSERVABLE_SLATE: list[dict[str, Any]] = [
    {"order": 1, "slug": "science_black_hole_anatomy_v1", "plate_slug": "black-hole"},
    {"order": 2, "slug": "science_star_lifecycle_v1", "plate_slug": "supernova"},
    {"order": 3, "slug": "science_galaxy_formation_v1", "plate_slug": "galaxy"},
]
FIRST_EPISODE = OBSERVABLE_SLATE[0]["slug"]


def load_plate_library() -> dict[str, Any]:
    return _load_json(PLATE_LIBRARY)


def find_plate(library: dict[str, Any], slug: str) -> dict[str, Any]:
    key = slug.strip().lower()
    for plate in library.get("plates", []):
        if plate.get("slug", "").lower() == key:
            return plate
    astro = [p["slug"] for p in library.get("plates", []) if p.get("domain") == "astro"]
    raise KeyError(f"No plate {slug!r} (astro: {', '.join(astro)})")


def check_r1() -> dict[str, Any]:
    if not R1_MANIFEST.is_file():
        raise SystemExit(f"R1 manifest missing: {R1_MANIFEST}")
    manifest = _load_json(R1_MANIFEST)
    expected = int(manifest.get("subject_count") or 0)
    harvested = int(manifest.get("harvested_count") or 0)
    entries = manifest.get("entries") or []
    failed = [e for e in entries if e.get("harvest_status") != "OK"]
    return {
        "ready": harvested >= expected and expected > 0 and not failed,
        "task": manifest.get("task"),
        "expected": expected,
        "harvested": harvested,
        "failed_slugs": [e.get("slug") for e in failed],
        "manifest": _rel(R1_MANIFEST),
        "checked_at": _utc_now(),
    }


def _harvest_path(plate_slug: str) -> Path:
    return HARVEST_DIR / f"{plate_slug}_harvest.jpg"


def stage_plates(*, force: bool = False) -> list[dict[str, Any]]:
    r1 = check_r1()
    if not r1["ready"]:
        raise SystemExit(
            f"R1 not ready: {r1['harvested']}/{r1['expected']} harvested; failed={r1['failed_slugs']}"
        )
    library = load_plate_library()
    manifest = _load_json(R1_MANIFEST)
    harvest_by_slug = {e["slug"]: e for e in manifest.get("entries", [])}
    staged: list[dict[str, Any]] = []

    for plate in library.get("plates", []):
        if plate.get("domain") != "astro":
            continue
        slug = plate["slug"]
        ref_rel = plate["plate_spec"]["reference_file"]
        ref_path = _abs_ref(ref_rel)
        harvest = _harvest_path(slug)
        harvest_meta = harvest_by_slug.get(slug, {})

        if ref_path.is_file() and ref_path.stat().st_size > MIN_REF_BYTES and not force:
            staged.append({"plate_slug": slug, "plate_id": plate["plate_id"],
                           "reference_file": ref_rel, "action": "reused",
                           "bytes": ref_path.stat().st_size})
            continue
        if not harvest.is_file():
            staged.append({"plate_slug": slug, "plate_id": plate["plate_id"],
                           "reference_file": ref_rel, "action": "missing_harvest",
                           "harvest": _rel(harvest)})
            continue

        ref_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(harvest, ref_path)
        meta = {
            "plate_id": plate["plate_id"], "slug": slug, "subject": plate.get("subject"),
            "path": str(ref_path), "source": "R1_harvest", "harvest_file": _rel(harvest),
            "image_url": harvest_meta.get("image_url"), "source_url": harvest_meta.get("source_url"),
            "primary_citation": harvest_meta.get("primary_citation") or plate.get("source", {}).get("primary_citation"),
            "license": harvest_meta.get("license") or plate.get("source", {}).get("license"),
            "staged_at": _utc_now(),
        }
        _write_json(ref_path.with_suffix(".json"), meta)
        staged.append({"plate_slug": slug, "plate_id": plate["plate_id"],
                       "reference_file": ref_rel, "action": "staged_from_harvest",
                       "bytes": ref_path.stat().st_size})

    _write_json(ASTRO_CONCEPTS_DIR / "r1_plate_staging_report.json",
                {"generated_at": _utc_now(), "r1": r1, "plates": staged})
    return staged


def wire_concepts() -> list[dict[str, Any]]:
    library = load_plate_library()
    wired: list[dict[str, Any]] = []
    for row in OBSERVABLE_SLATE:
        slug = row["slug"]
        plate = find_plate(library, row["plate_slug"])
        ref_rel = plate["plate_spec"]["reference_file"]
        concept_path = ASTRO_CONCEPTS_DIR / f"{slug}.concept.json"
        if not concept_path.is_file():
            raise FileNotFoundError(concept_path)
        concept = _load_json(concept_path)
        ss = concept.setdefault("science_subject", {})
        prev = ss.get("visualization_ref")
        ss["visualization_ref"] = ref_rel
        ss.setdefault("plate_id", plate["plate_id"])
        ss.setdefault("plate_slug", plate["slug"])
        _write_json(concept_path, concept)

        script_path = SCRIPTS_DIR / f"{slug}_script.json"
        proc = subprocess.run(
            [sys.executable, str(INTAKE), str(concept_path), "-o", str(script_path)],
            cwd=str(ROOT), capture_output=True, text=True, encoding="utf-8", errors="replace",
        )
        wired.append({"slug": slug, "plate_slug": row["plate_slug"], "plate_id": plate["plate_id"],
                      "visualization_ref": ref_rel, "previous_ref": prev,
                      "intake_exit": proc.returncode, "script_path": _rel(script_path)})
        if proc.returncode != 0:
            raise SystemExit(f"Intake failed for {slug} (exit {proc.returncode}):\n{proc.stdout}\n{proc.stderr}")
    _write_json(ASTRO_CONCEPTS_DIR / "observable_wiring_report.json",
                {"generated_at": _utc_now(), "episodes": wired})
    return wired


def cmd_stage_plates(args: argparse.Namespace) -> int:
    staged = stage_plates(force=args.force)
    for row in staged:
        print(f"  {row['action']:22} {row['plate_slug']} → {row.get('reference_file', '?')}")
    missing = [r for r in staged if r["action"] == "missing_harvest"]
    if missing:
        print(f"[stage] warning: {len(missing)} plate(s) lack R1 harvest copies")
        return 1
    print(f"[stage] {len(staged)} astro plate(s) checked")
    return 0


def _patch_resolution(script_path: Path, resolution: str) -> Path:
    script = _load_json(script_path)
    script.setdefault("config", {})["resolution"] = resolution
    out = script_path.with_name(script_path.stem.replace("_script", f"_{resolution}_script") + ".json")
    if out == script_path:
        out = script_path.with_name(f"{script['slug']}_{resolution}_script.json")
    _write_json(out, script)
    return out


def cmd_render_first(args: argparse.Namespace) -> int:
    _force_utf8_stdout()
    r1 = check_r1()
    if not r1["ready"]:
        raise SystemExit("R1 incomplete")
    stage_plates()
    wire_concepts()

    slug = args.slug or FIRST_EPISODE
    script_path = SCRIPTS_DIR / f"{slug}_script.json"
    if not script_path.is_file():
        raise SystemExit(f"Script missing after intake: {script_path}")

    resolution = args.resolution or DRAFT_RES
    render_script = _patch_resolution(script_path, resolution)
    validate = subprocess.run(
        [sys.executable, str(RENDER), str(render_script), "--script-only"],
        cwd=str(ROOT), capture_output=True, text=True, encoding="utf-8", errors="replace",
    )
    if validate.returncode != 0:
        print(validate.stdout)
        print(validate.stderr)
        raise SystemExit(f"--script-only failed (exit {validate.returncode})")

    print(f"[render-first] {slug} @ {resolution}")
    cmd = [sys.executable, str(RENDER), str(render_script)]
    if not args.no_seamless:
        cmd.extend(["--seamless", "--match-color", "--cut-on-motion"])
    if args.package:
        cmd.append("--package")
    proc = subprocess.run(cmd, cwd=str(ROOT))
    if proc.returncode != 0:
        return proc.returncode

    prod_dir = ROOT / "STUDIO" / "Productions" / "Editorial" / f"{slug}_longform_v1"
    qa_path = prod_dir / "qa_report.json"
    if qa_path.is_file():
        qa = _load_json(qa_path)
        print(f"[render-first] qa_pass={qa.get('pass')} issues={qa.get('issues', [])}")
    out_dir = prod_dir / "output"
    if out_dir.is_dir():
        mp4s = sorted(out_dir.glob("*.mp4"), key=lambda p: p.stat().st_mtime, reverse=True)
        if mp4s:
            print(f"[render-first] output → {mp4s[0]}")
    return 0


# --------------------------------------------------------------------------- cli
def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Observable science batch — multi-slate readiness gate + batch_runner stand-up"
    )
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("slates", help="List configured science slates and episodes").set_defaults(func=cmd_slates)

    check_p = sub.add_parser("check", help="Readiness gate (harvest + plate integrity) over slates")
    check_p.add_argument("--slate", help="Limit to one slate id")
    check_p.set_defaults(func=cmd_check)

    stand_p = sub.add_parser("standup", help="Readiness → (repair) → batch_runner run; aggregate manifest")
    stand_p.add_argument("--all", action="store_true", help="All science slates")
    stand_p.add_argument("--slate", help="Single slate id (default: astro)")
    stand_p.add_argument("--dry-run", action="store_true")
    stand_p.add_argument("--no-seamless", action="store_true")
    stand_p.add_argument("--repair", action="store_true", help="Repoint broken plate refs to locked references")
    stand_p.add_argument("--allow-unready", action="store_true", help="Run batch even if readiness gate fails")
    stand_p.add_argument("--batch-id", help="Batch id (default: science_all_dryrun / timestamp)")
    stand_p.add_argument("--batch-dir", help="Output dir (default: DAVID/batches/<batch-id>)")
    stand_p.set_defaults(func=cmd_standup)

    stage_p = sub.add_parser("stage-plates", help="[astro] Stage R1 harvest → @2 reference files")
    stage_p.add_argument("--force", action="store_true", help="Overwrite existing reference files")
    stage_p.set_defaults(func=cmd_stage_plates)

    rf = sub.add_parser("render-first", help=f"[astro] Prep + render first episode ({FIRST_EPISODE})")
    rf.add_argument("--slug", help="Override first-episode slug")
    rf.add_argument("--resolution", default=DRAFT_RES, help="Render resolution (default 480p)")
    rf.add_argument("--no-seamless", action="store_true")
    rf.add_argument("--package", action="store_true", help="Run package_episode after render")
    rf.set_defaults(func=cmd_render_first)

    return parser


def main(argv: Optional[list[str]] = None) -> int:
    args = build_parser().parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
