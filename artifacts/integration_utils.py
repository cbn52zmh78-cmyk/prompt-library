#!/usr/bin/env python3
"""
Integration Utils v1.0 — Director | Shared Helper
Common functions for profile loading, prompt injection, and logging.
"""

import os
import json
from datetime import datetime

try:
    from model_profile_manager import ModelProfileManager
except ImportError:
    ModelProfileManager = None

def load_profile(profile_name: str):
    if not ModelProfileManager:
        return None
    mgr = ModelProfileManager()
    return mgr.get_profile_data(profile_name)

def inject_profile_into_prompt(base_prompt: str, profile_name: str):
    profile = load_profile(profile_name)
    if not profile:
        return base_prompt, False
    enhanced = f"{profile.get('visual', '')}, {base_prompt}"
    if profile.get("default_physics"):
        enhanced += f", {profile['default_physics']}"
    return enhanced, True

def log_action(tool_name: str, message: str):
    log_dir = "studio/Tool_Logs"
    os.makedirs(log_dir, exist_ok=True)
    log_file = os.path.join(log_dir, f"{datetime.now().strftime('%Y%m%d')}.log")
    with open(log_file, "a", encoding="utf-8") as f:
        f.write(f"[{datetime.now().strftime('%H:%M:%S')}] [{tool_name}] {message}\n")

if __name__ == "__main__":
    print("Integration Utils loaded. Other tools can now import from this module.")