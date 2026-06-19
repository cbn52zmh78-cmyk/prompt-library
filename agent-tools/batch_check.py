import json
from pathlib import Path
from datetime import datetime

root = Path(r"C:\Users\NCG\Videos\Grok Projects\Studio")
reg = json.loads((root / "Cast/Casting_Bible/registry/casting_registry.json").read_text())
actors = reg["actors"]
batch_a = actors[:35]
batch_b = actors[35:]


def _under_studio(ref):
    # strip leading 'Studio/' (any casing); root already points at Studio/
    parts = ref.replace("\\", "/").split("/")
    return "/".join(parts[1:]) if parts and parts[0].lower() == "studio" else ref


def img_mtime(a):
    p = root / _under_studio(a["reference_image_primary"]).replace("/", "\\")
    if p.exists():
        return p.stat().st_mtime
    return None


print("=== BATCH A sample ===")
for a in batch_a[:3]:
    m = img_mtime(a)
    print(a["stage_name"], datetime.fromtimestamp(m) if m else "MISSING")

print("\n=== BATCH B (all 35) ===")
for a in batch_b:
    m = img_mtime(a)
    ts = datetime.fromtimestamp(m).strftime("%Y-%m-%d %H:%M") if m else "MISSING"
    print(f"{a['stage_name']:25} {ts}")

for name in [
    "casting_registry.json",
    "gfe_casting_registry.json",
    "magazine_casting_registry.json",
]:
    r = json.loads((root / "Cast/Casting_Bible/registry" / name).read_text())
    pend = [x for x in r["actors"] if x.get("reference_image_status") == "pending"]
    print(f"\n{name}: pending={len(pend)}")
    for p in pend:
        print(" ", p["stage_name"], p.get("actor_id"))