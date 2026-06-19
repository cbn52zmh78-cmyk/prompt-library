#!/usr/bin/env python3
"""Re-gate full production slate post-clamp-fix — intake + script-only per concept."""

from __future__ import annotations

import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PIPELINE = ROOT / "Studio" / "Pipeline"
INTAKE = PIPELINE / "production_intake.py"
RENDER = ROOT / "DAVID" / "scripts" / "render_longform.py"
SCRIPTS = ROOT / "DAVID" / "scripts" / "longform_scripts"

SLATES: dict[str, Path] = {
    "dead_languages": PIPELINE / "Concepts" / "dead_languages",
    "royal_tongues": PIPELINE / "Concepts" / "royal_tongues",
    "astro_mini_slate": PIPELINE / "Concepts" / "astro_mini_slate",
    "molecular_mini_slate": PIPELINE / "Concepts" / "molecular_mini_slate",
}


def main() -> int:
    entries: list[dict] = []

    for slate, concepts_dir in SLATES.items():
        for concept in sorted(concepts_dir.glob("*.concept.json")):
            slug = json.loads(concept.read_text(encoding="utf-8"))["slug"]
            script = SCRIPTS / f"{slug}_script.json"
            proc = subprocess.run(
                [sys.executable, str(INTAKE), str(concept), "-o", str(script)],
                cwd=ROOT,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
            )
            intake_ok = proc.returncode == 0
            gate: dict = {}
            script_only_ok: bool | None = None
            if script.is_file():
                data = json.loads(script.read_text(encoding="utf-8"))
                gate = (data.get("intake") or {}).get("gate_0") or {}
                sp = subprocess.run(
                    [sys.executable, str(RENDER), str(script), "--script-only"],
                    cwd=ROOT,
                    capture_output=True,
                    text=True,
                    encoding="utf-8",
                    errors="replace",
                )
                script_only_ok = sp.returncode == 0

            entries.append(
                {
                    "slate": slate,
                    "slug": slug,
                    "verdict": gate.get("verdict", "RED" if not intake_ok else "?"),
                    "intake_ok": intake_ok,
                    "intake_exit": proc.returncode,
                    "script_only_ok": script_only_ok,
                    "report": gate.get("report_path"),
                    "warnings": gate.get("warnings") or [],
                    "human_signoff": gate.get("human_signoff"),
                    "checklist": gate.get("checklist_summary"),
                }
            )

    verdicts: dict[str, int] = {}
    for e in entries:
        v = str(e["verdict"])
        verdicts[v] = verdicts.get(v, 0) + 1

    all_green = all(
        e["verdict"] == "GREEN" and e["intake_ok"] and e["script_only_ok"] for e in entries
    )
    report = {
        "issue": 181,
        "task": "T4 — re-gate full slate post-clamp-fix",
        "regated_at": datetime.now(timezone.utc).isoformat(),
        "clamp_fix": "shot_duration.apply_duration_clamp_to_shots via production_intake",
        "summary": {
            "total": len(entries),
            **{k.lower(): v for k, v in verdicts.items()},
            "all_green": all_green,
            "intake_pass": sum(1 for e in entries if e["intake_ok"]),
            "script_only_pass": sum(1 for e in entries if e["script_only_ok"]),
        },
        "entries": entries,
    }
    out = PIPELINE / "Concepts" / "gate_0_regate_T4_181.json"
    out.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")

    print(json.dumps(report["summary"], indent=2))
    for e in entries:
        ok = e["verdict"] == "GREEN" and e["intake_ok"] and e["script_only_ok"]
        icon = "OK" if ok else "!!"
        print(
            f"{icon} [{e['slate']}] {e['slug']}: {e['verdict']} "
            f"intake={e['intake_ok']} script={e['script_only_ok']}"
        )
    print(f"Wrote {out}")
    return 0 if all_green else 1


if __name__ == "__main__":
    raise SystemExit(main())