import json
from datetime import datetime
from pathlib import Path

root = Path(r"C:\Users\NCG\Videos\Grok Projects\Studio")
reg = json.loads((root / "Cast/Casting_Bible/registry/casting_registry.json").read_text())
gfe = json.loads((root / "Cast/Casting_Bible/registry/gfe_casting_registry.json").read_text())
mag = json.loads((root / "Cast/Casting_Bible/registry/magazine_casting_registry.json").read_text())

bb = reg["actors"][35:]
recent = 0
for a in bb:
    p = root / a["reference_image_primary"].replace("STUDIO/", "").replace("/", "\\")
    m = datetime.fromtimestamp(p.stat().st_mtime)
    if m.date().isoformat() >= "2026-06-18":
        recent += 1

print(f"Batch B refreshed (>=2026-06-18): {recent}/{len(bb)}")
print(f"Roster plate_locked: {reg['summary']['plate_locked']}/{reg['total']}")
print(f"GFE plate_locked: {gfe['summary']['plate_locked']}/{gfe['total']}")
print(f"Magazine plate_locked: {mag['summary']['plate_locked']}/{mag['total']}")
print(f"#100 talent total: {reg['total'] + gfe['total'] + mag['total']}")

pending_locks = list((root / "Cast/Casting_Bible/lock_cards").glob("*.md"))
pending = [p for p in pending_locks if "PENDING" in p.read_text(encoding="utf-8")]
print(f"Lock cards still PENDING: {len(pending)}")