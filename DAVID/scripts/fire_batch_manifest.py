#!/usr/bin/env python3
"""Fire a pre-built batch manifest — preflight validation or full 720p render+package.

Usage:
    python DAVID/scripts/fire_batch_manifest.py DAVID/batches/B183_benjamin_go/manifest.json --preflight
    python DAVID/scripts/fire_batch_manifest.py DAVID/batches/B183_benjamin_go/manifest.json --go
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
RENDER = ROOT / "DAVID" / "scripts" / "render_longform.py"


def _utc() -> str:
    return datetime.now(timezone.utc).isoformat()


def _rel(p: Path) -> str:
    try:
        return str(p.relative_to(ROOT)).replace("\\", "/")
    except ValueError:
        return str(p)


def load_manifest(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def save_manifest(path: Path, manifest: dict[str, Any]) -> None:
    path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")


def gate_ok(script: dict[str, Any]) -> tuple[bool, str]:
    gate = (script.get("intake") or {}).get("gate_0") or {}
    if gate.get("blocked") or gate.get("verdict") == "RED":
        return False, "RED"
    if gate.get("requires_human_signoff") and not gate.get("human_signoff"):
        return False, "needs_signoff"
    return True, str(gate.get("verdict", "UNKNOWN"))


def preflight_item(item: dict[str, Any]) -> dict[str, Any]:
    script_path = ROOT / item["script_path"]
    row = {**item, "preflight_at": _utc()}
    if not script_path.is_file():
        row["preflight"] = "fail"
        row["preflight_issues"] = [f"missing script: {item['script_path']}"]
        return row
    script = json.loads(script_path.read_text(encoding="utf-8"))
    issues: list[str] = []
    ok, verdict = gate_ok(script)
    if not ok:
        issues.append(f"gate_0 blocked: {verdict}")
    if not script.get("shots"):
        issues.append("script has no shots")
    lock = (script.get("config") or {}).get("identity_lock")
    if lock and not (ROOT / "DAVID" / lock if not Path(lock).is_absolute() else Path(lock)).is_file():
        lock_path = ROOT / "DAVID" / lock if not str(lock).startswith("productions") else ROOT / "DAVID" / lock
        if not lock_path.is_file():
            alt = ROOT / lock
            if not alt.is_file():
                issues.append(f"identity_lock missing: {lock}")
    res = (script.get("config") or {}).get("resolution", "")
    if res != "720p":
        issues.append(f"resolution is {res!r}, expected 720p")
    row["gate_0_verdict"] = (script.get("intake") or {}).get("gate_0", {}).get("verdict", verdict)
    row["preflight"] = "pass" if not issues else "fail"
    row["preflight_issues"] = issues
    return row


def run_render(item: dict[str, Any], flags: list[str]) -> dict[str, Any]:
    script_path = ROOT / item["script_path"]
    cmd = [sys.executable, str(RENDER), str(script_path), *flags]
    proc = subprocess.run(cmd, cwd=str(ROOT), capture_output=True, text=True, encoding="utf-8", errors="replace")
    out = (proc.stdout or "") + (proc.stderr or "")
    prod = ROOT / item["production_dir"]
    qa_path = prod / "qa_report.json"
    qa = json.loads(qa_path.read_text(encoding="utf-8")) if qa_path.is_file() else {}
    row = {
        **item,
        "fired_at": _utc(),
        "render_exit": proc.returncode,
        "qa_pass": qa.get("pass"),
        "qa_issues": qa.get("issues", []),
        "status": "shipped" if proc.returncode == 0 and qa.get("pass") else "fail",
    }
    row["render_tail"] = out[-2000:]
    return row


def cmd_preflight(manifest_path: Path, manifest: dict[str, Any]) -> int:
    items = [preflight_item(i) for i in manifest.get("items", [])]
    manifest["items"] = items
    manifest["preflight_at"] = _utc()
    manifest["preflight_summary"] = {
        "pass": sum(1 for i in items if i.get("preflight") == "pass"),
        "fail": sum(1 for i in items if i.get("preflight") == "fail"),
        "armed": len(items),
    }
    save_manifest(manifest_path, manifest)
    print(json.dumps(manifest["preflight_summary"], indent=2))
    for item in items:
        icon = "✓" if item.get("preflight") == "pass" else "✗"
        counsel = " [COUNSEL]" if item.get("counsel_flag") else ""
        print(f"  {icon} {item['order']:02d} {item['slug']}{counsel} gate={item.get('gate_0_verdict')}")
        for issue in item.get("preflight_issues") or []:
            print(f"      ! {issue}")
    return 0 if manifest["preflight_summary"]["fail"] == 0 else 1


def cmd_go(manifest_path: Path, manifest: dict[str, Any], *, stop_on_fail: bool) -> int:
    if manifest.get("status") == "FIRED":
        print("[fire] manifest already FIRED — use --force to re-run")
        return 1
    flags = manifest.get("render_flags") or [
        "--seamless", "--match-color", "--cut-on-motion", "--package",
    ]
    items = manifest.get("items", [])
    print(f"[fire] GO — {len(items)} episodes @ {manifest.get('resolution', '720p')}")
    results: list[dict[str, Any]] = []
    for item in sorted(items, key=lambda x: x.get("order", 0)):
        pf = preflight_item(item)
        if pf.get("preflight") != "pass":
            print(f"  ✗ {item['slug']}: preflight fail — {pf.get('preflight_issues')}")
            results.append({**pf, "status": "preflight_fail"})
            if stop_on_fail:
                break
            continue
        if item.get("counsel_flag"):
            print(f"  ⚖ {item['slug']}: COUNSEL gate — proceeding on Benjamin go")
        print(f"  ▶ {item['order']:02d} {item['slug']} …")
        row = run_render(item, flags)
        results.append(row)
        icon = "✅" if row.get("status") == "shipped" else "✗"
        print(f"    {icon} exit={row.get('render_exit')} qa_pass={row.get('qa_pass')}")
        if row.get("status") != "shipped" and stop_on_fail:
            break

    manifest["items"] = results
    manifest["status"] = "FIRED"
    manifest["fired_at"] = _utc()
    manifest["fire_summary"] = {
        "shipped": sum(1 for i in results if i.get("status") == "shipped"),
        "fail": sum(1 for i in results if i.get("status") in ("fail", "preflight_fail")),
        "total": len(results),
    }
    save_manifest(manifest_path, manifest)
    print(f"\n[fire] summary: {manifest['fire_summary']}")
    return 0 if manifest["fire_summary"]["fail"] == 0 else 1


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Preflight or fire a DAVID batch manifest")
    p.add_argument("manifest", type=Path, help="Path to manifest.json")
    p.add_argument("--preflight", action="store_true", help="Validate only; no API spend")
    p.add_argument("--go", action="store_true", help="Execute render+package for all armed items")
    p.add_argument("--force", action="store_true", help="Allow re-fire of FIRED manifest")
    p.add_argument("--continue-on-fail", action="store_true", help="Keep going after a failed episode")
    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    manifest_path = args.manifest if args.manifest.is_absolute() else ROOT / args.manifest
    if not manifest_path.is_file():
        raise SystemExit(f"Manifest not found: {manifest_path}")
    manifest = load_manifest(manifest_path)

    if not args.preflight and not args.go:
        print(manifest.get("go_command", "Use --preflight or --go"))
        return 0
    if args.go and manifest.get("status") == "FIRED" and not args.force:
        raise SystemExit("Manifest status=FIRED. Pass --force to re-run.")
    if args.preflight:
        return cmd_preflight(manifest_path, manifest)
    return cmd_go(manifest_path, manifest, stop_on_fail=not args.continue_on_fail)


if __name__ == "__main__":
    raise SystemExit(main())