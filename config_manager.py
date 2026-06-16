#!/usr/bin/env python3
import json
from pathlib import Path

CONFIG_FILE = Path.home() / "prompt_library" / "config.json"

DEFAULT_CONFIG = {
    "stonebridge_path": str(Path.home() / "Stonebridge_Operations"),
    "flash_path": str(Path.home() / "FLASH"),
    "prompt_library_path": str(Path.home() / "prompt_library"),
    "default_agent": "AI_Systems_Agent"
}

def load_config():
    if CONFIG_FILE.exists():
        return json.loads(CONFIG_FILE.read_text())
    return DEFAULT_CONFIG

def save_config(config):
    CONFIG_FILE.write_text(json.dumps(config, indent=2))
    print("Config saved.")

def show_config():
    config = load_config()
    print("\n=== CURRENT CONFIG ===\n")
    for key, value in config.items():
        print(f"{key}: {value}")

if __name__ == "__main__":
    show_config()