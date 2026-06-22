#!/usr/bin/env python3
"""
Prompt Refinement Pipeline v1.1 — Director | Profile Integration
Can enhance the base prompt using data from a saved Model Profile.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from lib.bootstrap import ensure_paths
ensure_paths()
from lib.studio_paths import pipeline_path

from datetime import datetime

# --- qa_gate wiring ---
_AI_FED = Path(__file__).resolve().parents[2] / "AI" / "federation"
if str(_AI_FED) not in sys.path:
    sys.path.insert(0, str(_AI_FED))
try:
    from qa_gate import qa_check as _qa_gate_check
    _QA_GATE_AVAILABLE = True
except ImportError:
    _QA_GATE_AVAILABLE = False
# --- end qa_gate wiring ---



try:
    from profile.model_profile_manager import ModelProfileManager
except ImportError:
    ModelProfileManager = None


class PromptRefinementPipeline:
    def __init__(self, output_dir=None):
        self.output_dir = output_dir or pipeline_path("Refined_Prompts")
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.profile_mgr = ModelProfileManager() if ModelProfileManager else None

    def refine(self, base_prompt: str, stages: list = None, profile_name: str = None):
        if stages is None:
            stages = ["physics", "camera", "lighting", "composition", "negative_space"]

        prompt = base_prompt.strip()
        applied = []

        if profile_name and self.profile_mgr:
            profile = self.profile_mgr.get_profile_data(profile_name)
            if profile:
                prompt = f"{profile.get('visual', '')}, {prompt}"
                if profile.get("default_physics"):
                    prompt += f", {profile['default_physics']}"
                print(f"→ Enhanced with profile: {profile_name}")

        if "physics" in stages:
            prompt += ", natural fabric and body physics, realistic cloth movement"
            applied.append("physics")
        if "camera" in stages:
            prompt += ", motivated camera movement with precise framing progression"
            applied.append("camera")
        if "lighting" in stages:
            prompt += ", dramatic cinematic lighting with clear key and subtle rim"
            applied.append("lighting")
        if "composition" in stages:
            prompt += ", clean single-subject composition, intentional negative space"
            applied.append("composition")
        if "negative_space" in stages:
            prompt += ", generous negative space, balanced frame, no crowding"
            applied.append("negative_space")

        # --- qa_gate: QA refined prompt, block on RED ---
        if _QA_GATE_AVAILABLE and prompt and prompt.strip():
            try:
                _qa_rp = _qa_gate_check(
                    content=prompt,
                    content_type="general",
                    subject="refined prompt",
                )
                if _qa_rp["gate"] == "RED":
                    print(
                        f"[QA HOLD] prompt_refinement_pipeline.py: {_qa_rp['summary']} | Issues: {_qa_rp['issues']}",
                        file=sys.stderr,
                    )
                    raise RuntimeError(f"QA gate RED on refined prompt — output held: {_qa_rp['issues']}")
                elif _qa_rp["gate"] == "YELLOW":
                    print(
                        f"[QA WARN] prompt_refinement_pipeline.py: {_qa_rp['summary']}",
                        file=sys.stderr,
                    )
            except RuntimeError:
                raise
            except Exception as _exc:
                print(f"[QA WARN] prompt_refinement_pipeline.py: qa_gate error: {_exc}", file=sys.stderr)
        # --- end qa_gate ---
        return prompt, applied

    def save(self, name: str, refined_prompt: str, applied_stages: list):
        timestamp = datetime.now().strftime("%Y%m%d_%H%M")
        filepath = self.output_dir / f"{name.replace(' ', '_')}_{timestamp}.txt"
        content = f"# Stages: {', '.join(applied_stages)}\n\n{refined_prompt}"
        filepath.write_text(content, encoding="utf-8")
        print(f"✅ Refined prompt saved: {filepath}")


if __name__ == "__main__":
    pipeline = PromptRefinementPipeline()
    base = "adult woman in elegant gown, sustained eye contact"
    refined, stages = pipeline.refine(base, profile_name="Test_Editorial")
    pipeline.save("Hero_Refined_From_Profile", refined, stages)