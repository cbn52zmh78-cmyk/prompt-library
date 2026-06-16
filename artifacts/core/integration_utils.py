#!/usr/bin/env python3
"""
Integration Utils v1.0 — Director | Shared Helper
Common functions for profile loading, prompt injection, and logging.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from lib.bootstrap import ensure_paths
ensure_paths()
from lib.studio_paths import studio_path

from datetime import datetime



try:
    from model_profile_manager import ModelProfileManager
except ImportError:
    ModelProfileManager = None


def load_profile(profile_name: str):
    if not ModelProfileManager:
        return None
    return ModelProfileManager().get_profile_data(profile_name)


def inject_profile_into_prompt(base_prompt: str, profile_name: str):
    profile = load_profile(profile_name)
    if not profile:
        return base_prompt, False
    enhanced = f"{profile.get('visual', '')}, {base_prompt}"
    if profile.get("default_physics"):
        enhanced += f", {profile['default_physics']}"
    return enhanced, True


def log_action(tool_name: str, message: str):
    log_dir = studio_path("Tool_Logs")
    log_file = log_dir / f"{datetime.now().strftime('%Y%m%d')}.log"
    with open(log_file, "a", encoding="utf-8") as f:
        f.write(f"[{datetime.now().strftime('%H:%M:%S')}] [{tool_name}] {message}\n")


if __name__ == "__main__":
    print("Integration Utils loaded. Other tools can import from core.integration_utils.")