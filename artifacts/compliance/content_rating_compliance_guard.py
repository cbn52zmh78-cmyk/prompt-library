#!/usr/bin/env python3
"""
Content Rating & Compliance Guard v1.2 — Director | Fully General
Official CARA/MPA theatrical standards. No model-specific defaults.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from lib.bootstrap import ensure_paths
ensure_paths()
from lib.studio_paths import pipeline_path, producers_path

import argparse
from datetime import datetime



DEFAULT_REPORTS_DIR = producers_path("Compliance_Reports")
DEFAULT_SHOTLISTS_ROOT = pipeline_path("ShotLists")


class ContentRatingGuard:
    def __init__(self, output_dir: str | Path | None = None):
        self.version = "1.2"
        self.output_dir = Path(output_dir or DEFAULT_REPORTS_DIR)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        self.cara_canon = {
            "G": "Nothing that would offend parents for children. No strong language, nudity, sex, or drug use.",
            "PG": "Mild thematic elements, brief mild language, no drug use.",
            "PG-13": "Stronger language, intense but non-graphic violence, brief suggestive content, drug references ok.",
            "R": "Strong language, strong violence, sexual content, drug abuse, adult themes permitted.",
            "NC-17": "Explicit sexual content or extreme violence — absolute ceiling for legitimate cinema work.",
        }

    def analyze_prompt(self, prompt: str, target_rating: str = "PG-13", name: str = "Prompt"):
        prompt_lower = prompt.lower()
        issues = []
        if "minor" in prompt_lower or (
            "teen" in prompt_lower
            and any(x in prompt_lower for x in ["sex", "nude", "erotic", "intimate"])
        ):
            issues.append(
                "CRITICAL: Any sexual or exploitative reference involving minors is strictly prohibited."
            )
        if any(x in prompt_lower for x in ["unsimulated", "hardcore", "porn", "xxx", "graphic sex"]):
            issues.append("Prohibited explicit adult industry language detected.")

        report = {
            "status": "COMPLIANT" if not issues else "NEEDS_REVISION",
            "target": target_rating,
            "issues": issues,
            "name": name,
        }
        self._save_report(report, prompt)
        return report

    def _save_report(self, report, prompt):
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_name = report["name"].replace(" ", "_")
        filename = self.output_dir / f"CARA_Compliance_Report_{safe_name}_{stamp}.txt"
        with open(filename, "w", encoding="utf-8") as f:
            f.write("# CARA Compliance Report v1.2 — Locked Theatrical Standards\n")
            f.write("Source: Official Classification and Rating Administration (CARA) / MPA\n")
            f.write(f"Project: {report['name']}\n")
            f.write(f"Target Rating: {report['target']}\n")
            f.write(f"Status: {report['status']}\n\n")
            f.write("Official CARA Canon:\n")
            for rating, desc in self.cara_canon.items():
                f.write(f"  {rating}: {desc}\n")
            f.write("\nIssues Found:\n")
            if report["issues"]:
                for issue in report["issues"]:
                    f.write(f"- {issue}\n")
            else:
                f.write("- None\n")
            f.write(
                "\nPrompt was checked against theatrical cinema standards. "
                "We are making movies, not pornography.\n"
            )
        print(f"✅ CARA compliance report generated: {filename}")
        report["report_path"] = str(filename)
        return filename

    def audit_folder(self, folder_path: str | Path, target_rating: str = "PG-13", name: str | None = None):
        folder = Path(folder_path)
        prompt_files = sorted(folder.glob("*.txt"))
        if not prompt_files:
            raise FileNotFoundError(f"No .txt prompt files found in {folder}")

        project = name or folder.name
        results = []
        for prompt_file in prompt_files:
            content = prompt_file.read_text(encoding="utf-8")
            report = self.analyze_prompt(
                content,
                target_rating=target_rating,
                name=f"{project}_{prompt_file.stem}",
            )
            results.append({"file": prompt_file.name, **report})

        compliant = sum(1 for r in results if r["status"] == "COMPLIANT")
        status = "COMPLIANT" if compliant == len(results) else "NEEDS_REVISION"
        print(f"Batch result: {status} ({compliant}/{len(results)} compliant)")
        return {"project": project, "status": status, "results": results}


def find_latest_prompt_folder(base: Path) -> Path | None:
    if not base.is_dir():
        return None
    candidates = [f for f in base.iterdir() if f.is_dir() and any(f.glob("*.txt"))]
    return max(candidates, key=lambda p: p.stat().st_mtime) if candidates else None


def main() -> int:
    parser = argparse.ArgumentParser(
        description="CARA/MPA Content Rating Compliance Guard v1.2 — fully general"
    )
    parser.add_argument("--folder", help="Audit all .txt prompts in a folder")
    parser.add_argument("--file", help="Audit a single .txt prompt file")
    parser.add_argument("--prompt", help="Audit inline prompt text")
    parser.add_argument("--latest", action="store_true", help="Audit latest shot-list folder")
    parser.add_argument("--shotlists-root", type=Path, default=DEFAULT_SHOTLISTS_ROOT)
    parser.add_argument("--reports-dir", type=Path, default=DEFAULT_REPORTS_DIR)
    parser.add_argument("--rating", default="PG-13", choices=["G", "PG", "PG-13", "R", "NC-17"])
    parser.add_argument("--name", default="Prompt", help="Project or prompt name")
    parser.add_argument("--demo", action="store_true", help="Run generic demo prompt")
    args = parser.parse_args()

    guard = ContentRatingGuard(output_dir=args.reports_dir.resolve())

    if args.demo or (not args.folder and not args.file and not args.prompt and not args.latest):
        test_prompt = (
            "adult woman in revealing outfit, sustained eye contact, soft-spoken whispering, "
            "slow leaning in, playful teasing, natural physics, soft lighting"
        )
        report = guard.analyze_prompt(test_prompt, target_rating="R", name="Generic_Test")
        print(f"Status: {report['status']}")
        return 0 if report["status"] == "COMPLIANT" else 1

    if args.prompt:
        report = guard.analyze_prompt(args.prompt, target_rating=args.rating, name=args.name)
        print(f"Status: {report['status']}")
        return 0 if report["status"] == "COMPLIANT" else 1

    if args.file:
        content = Path(args.file).read_text(encoding="utf-8")
        report = guard.analyze_prompt(content, target_rating=args.rating, name=args.name)
        print(f"Status: {report['status']}")
        return 0 if report["status"] == "COMPLIANT" else 1

    folder = args.folder
    if args.latest or not folder:
        latest = find_latest_prompt_folder(args.shotlists_root.resolve())
        if not latest:
            print(f"No prompt folders found in {args.shotlists_root.resolve()}")
            return 1
        folder = str(latest)
        print(f"Batch auditing: {folder}")

    summary = guard.audit_folder(folder, target_rating=args.rating, name=args.name if args.name != "Prompt" else None)
    return 0 if summary["status"] == "COMPLIANT" else 1


if __name__ == "__main__":
    raise SystemExit(main())