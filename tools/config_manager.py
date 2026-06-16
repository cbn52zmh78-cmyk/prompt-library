#!/usr/bin/env python3
import _bootstrap  # noqa: F401
import json
from workspace_paths import CONFIG_FILE, FLASH, STONEBRIDGE_OPS, WORKSPACE

DEFAULT_CONFIG = {
    "workspace_path": str(WORKSPACE),
    "stonebridge_path": str(STONEBRIDGE_OPS),
    "flash_path": str(FLASH),
    "default_agent": "AI_Systems_Agent",
}

def load_config():
    if CONFIG_FILE.exists():
        return json.loads(CONFIG_FILE.read_text())
    return DEFAULT_CONFIG

def save_config(config):
    CONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)
    CONFIG_FILE.write_text(json.dumps(config, indent=2))
    print("Config saved.")

def show_config():
    config = load_config()
    print("\n=== CURRENT CONFIG ===\n")
    for key, value in config.items():
        print(f"{key}: {value}")

if __name__ == "__main__":
    show_config()