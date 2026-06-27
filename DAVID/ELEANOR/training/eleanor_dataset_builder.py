"""eleanor_dataset_builder.py -- ELEANOR-DAVID variant dataset builder (SCAFFOLD STUB).

Variant of AI/ELEANOR/training/eleanor_dataset/eleanor_dataset_builder.py, scoped
to the ELEANOR-DAVID governance layer over DAVID's Llama 3.1 8B language product.

SCAFFOLD: no variant corpus shards exist yet. Place variant-specific shards in
DAVID/ELEANOR/training/eleanor_dataset/ named eleanor_david_*_corpus.jsonl.
Do NOT copy the base ELEANOR corpus into this folder -- the variant trains only
on DAVID-product-specific governance pairs, layered on the base adapter.

Usage (once variant shards exist):
    python eleanor_dataset_builder.py --check
    python eleanor_dataset_builder.py --stats
    python eleanor_dataset_builder.py --write

Output:
    DAVID/ELEANOR/models/datasets/eleanor_david_dataset.jsonl
"""
from __future__ import annotations

import argparse
import glob
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
SHARD_DIR = os.path.join(HERE, "eleanor_dataset")
SHARD_GLOB = "eleanor_david_*_corpus.jsonl"  # variant-specific shards only
OUT = os.path.normpath(os.path.join(HERE, "..", "models", "datasets", "eleanor_david_dataset.jsonl"))


def load_shards() -> list[dict]:
    rows: list[dict] = []
    for path in sorted(glob.glob(os.path.join(SHARD_DIR, SHARD_GLOB))):
        with open(path, encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    rows.append(json.loads(line))
    return rows


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="ELEANOR-DAVID variant dataset builder (scaffold stub)")
    p.add_argument("--check", action="store_true", help="validate shards parse")
    p.add_argument("--stats", action="store_true", help="print pair count")
    p.add_argument("--write", action="store_true", help="merge shards -> dataset jsonl")
    a = p.parse_args(argv)

    rows = load_shards()
    if not rows:
        print(f"[scaffold] no variant shards matching {SHARD_GLOB!r} in {SHARD_DIR}")
        print("[scaffold] add eleanor_david_*_corpus.jsonl shards, then re-run.")
        print("[scaffold] STUB -- no base ELEANOR corpus is bundled here by design.")
        return 0

    if a.check or a.stats:
        print(f"[check] {len(rows)} variant pairs parsed across shards")
        return 0

    if a.write:
        os.makedirs(os.path.dirname(OUT), exist_ok=True)
        with open(OUT, "w", encoding="utf-8", newline="\n") as f:
            for r in rows:
                f.write(json.dumps(r, ensure_ascii=True) + "\n")
        print(f"[write] {len(rows)} pairs -> {OUT}")
        return 0

    p.print_help()
    return 0


if __name__ == "__main__":
    sys.exit(main())
