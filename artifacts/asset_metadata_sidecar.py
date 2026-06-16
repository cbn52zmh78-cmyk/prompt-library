#!/usr/bin/env python3
"""
Asset Metadata Sidecar Generator v1.0 — Director | New Tool
Creates .json sidecar metadata files for generated images/assets. Fully general.
"""

import json
from datetime import datetime
from pathlib import Path

from studio_paths import studio_path

class AssetMetadataSidecar:
    def __init__(self, metadata_dir=None):
        self.metadata_dir = metadata_dir or studio_path("Asset_Metadata")
        self.metadata_dir.mkdir(parents=True, exist_ok=True)

    def create_sidecar(self, image_path: str, prompt: str, tags: list = None, extra: dict = None):
        base = Path(image_path).stem
        meta = {
            "source_image": image_path,
            "prompt": prompt,
            "tags": tags or [],
            "created": datetime.now().isoformat(),
            "version": "1.0"
        }
        if extra:
            meta.update(extra)
        out_path = self.metadata_dir / f"{base}.json"
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(meta, f, indent=2)
        print(f"✅ Sidecar created: {out_path}")
        return out_path

if __name__ == "__main__":
    sidecar = AssetMetadataSidecar()
    # Demo
    sidecar.create_sidecar(
        str(studio_path("test_hero.jpg")),
        "adult woman, hero studio shot, dramatic side lighting, elegant pose, natural physics",
        tags=["hero", "editorial", "studio"],
        extra={"lighting": "dramatic side", "camera": "static hero", "single_subject": True}
    )