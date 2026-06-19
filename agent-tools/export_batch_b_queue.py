import json
import sys
from pathlib import Path

root = Path(r"C:\Users\NCG\Videos\Grok Projects\Studio")
ws = Path(r"C:\Users\NCG\Videos\Grok Projects")

sys.path.insert(0, str(ws / "tools"))
from output_registry import rel_canonical  # canonical pointers (fixes casing drift)

casting = json.loads((root / "Cast/Casting_Bible/registry/casting_registry.json").read_text())
mag = json.loads((root / "Cast/Casting_Bible/registry/magazine_casting_registry.json").read_text())

batch_b = casting["actors"][35:]
pending_mag = [a for a in mag["actors"] if a.get("reference_image_status") == "pending"]

queue = []

for a in batch_b:
    rel = rel_canonical(a["reference_image_primary"])
    out = ws / rel.replace("/", "\\")
    queue.append({
        "lane": "roster",
        "actor_id": a["actor_id"],
        "stage_name": a["stage_name"],
        "gender": a["gender"],
        "age_locked": a["age_locked"],
        "out_path": str(out),
        "prompt": a["appearance_lock_verbatim"],
        "roster_path": a["roster_path"],
    })

for a in pending_mag:
    rp = rel_canonical(a["roster_path"])
    out = ws / rp.replace("/", "\\") / "01_casting_shots" / "casting_turnaround_v1.jpg"
    queue.append({
        "lane": "magazine",
        "actor_id": a["actor_id"],
        "stage_name": a["stage_name"],
        "gender": a["gender"],
        "age_locked": a["age_locked"],
        "out_path": str(out),
        "prompt": a["appearance_lock_verbatim"],
        "roster_path": a["roster_path"],
    })

out_file = ws / "agent-tools" / "batch_b_queue.json"
out_file.write_text(json.dumps(queue, indent=2), encoding="utf-8")
print(f"Queue: {len(queue)} items ({len(batch_b)} roster batch B + {len(pending_mag)} magazine pending)")
for i, q in enumerate(queue):
    print(f"{i+1:2}. [{q['lane']}] {q['stage_name']} age={q['age_locked']}")