#!/usr/bin/env python3
"""
Master CLI Launcher v1.2 — Director | New Tool
Single entry point to discover and run all tools in this project.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from lib.bootstrap import ensure_paths
ensure_paths()

import subprocess


ARTIFACTS_DIR = Path(__file__).resolve().parents[1]

TOOLS = {
    "Workspace Setup": [
        ("core/workspace_initializer.py", "Workspace Initializer (Studio folder scaffold)"),
        ("core/workspace_status_reporter.py", "Workspace Status Reporter"),
    ],
    "Profile Management": [
        ("profile/model_profile_manager.py", "Model Profile Manager v1.2 (integration-ready)"),
    ],
    "Prompt Generation & Quality": [
        ("prompts/fashion_modeling_prompt_generator.py", "Fashion/Modeling Prompt Generator v1.1"),
        ("prompts/batch_prompt_generator.py", "Batch Prompt Generator v1.1 (profile-aware)"),
        ("prompts/prompt_quality_scorer.py", "Prompt Specificity & Quality Scorer"),
        ("prompts/negative_prompt_builder.py", "Compliance-Aware Negative Prompt Builder"),
        ("prompts/physics_lighting_injector.py", "Physics & Lighting Reference Injector"),
        ("prompts/prompt_refinement_pipeline.py", "Prompt Refinement Pipeline v1.1 (profile-aware)"),
    ],
    "Shot Listing & Video Tools": [
        ("video/magazine_shotlist_templater.py", "Magazine Shot List Templater"),
        ("video/multishot_video_compiler.py", "Multi-Shot Video Compiler v1.1 (profile-aware)"),
        ("video/onetake_choreography_builder.py", "One-Take Choreography Builder v1.1 (profile-aware)"),
        ("video/image_to_video_bridge.py", "Image-to-Video Continuity Bridge"),
        ("video/sequence_video_compiler.py", "Sequence Video Compiler"),
    ],
    "Reference, Metadata & Catalog": [
        ("catalog/visual_asset_catalog.py", "Visual Asset Catalog (SQLite)"),
        ("catalog/asset_metadata_sidecar.py", "Asset Metadata Sidecar Generator"),
        ("catalog/reference_library_indexer.py", "Reference Library Indexer & Suggester"),
        ("catalog/template_library_manager.py", "Template Library Manager v1.1 (physics blocks)"),
        ("catalog/catalog_dashboard.py", "Catalog Dashboard (Streamlit)"),
    ],
    "Versioning, History & Compliance": [
        ("compliance/prompt_version_control.py", "Prompt Version Control & Diff Tool"),
        ("compliance/canon_bible_manager.py", "Canon & Bible Version Manager"),
        ("compliance/sequence_consistency_auditor.py", "Shot Sequence Consistency Auditor"),
        ("compliance/prompt_consistency_auditor.py", "Prompt Consistency Auditor"),
        ("compliance/content_rating_compliance_guard.py", "Content Rating & Compliance Guard (CARA)"),
    ],
    "Export & Packaging": [
        ("export/grok_video_pack_exporter.py", "Grok Video Prompt Pack Exporter"),
    ],
}


def show_menu():
    print("\n" + "=" * 70)
    print("MASTER CLI LAUNCHER v1.2 — Grok Projects")
    print("=" * 70)
    idx = 1
    flat_tools = []
    for category, tools in TOOLS.items():
        print(f"\n[{category}]")
        for script, desc in tools:
            print(f"  {idx:2}. {desc}")
            flat_tools.append((script, desc))
            idx += 1
    print("\n  0. Exit")
    print("=" * 70)
    return flat_tools


def main():
    while True:
        flat_tools = show_menu()
        try:
            choice = int(input("\nSelect tool number (0 to exit): ").strip())
        except ValueError:
            print("Invalid input. Please enter a number.")
            continue

        if choice == 0:
            print("Exiting Master Launcher. Stay locked.")
            break

        if 1 <= choice <= len(flat_tools):
            script, desc = flat_tools[choice - 1]
            script_path = ARTIFACTS_DIR / script
            if script_path.exists():
                print(f"\n▶ Launching: {desc}")
                try:
                    subprocess.run(
                        [sys.executable, str(script_path)],
                        cwd=ARTIFACTS_DIR,
                        check=True,
                    )
                except subprocess.CalledProcessError as e:
                    print(f"Script exited with error: {e}")
            else:
                print(f"❌ Script not found: {script_path}")
        else:
            print("Invalid selection.")


if __name__ == "__main__":
    main()