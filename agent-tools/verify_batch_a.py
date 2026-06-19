import json
from pathlib import Path
from datetime import datetime

root = Path(r"C:\Users\NCG\Videos\Grok Projects\Studio\Cast")
reg = json.loads((root / "Casting_Bible/registry/casting_registry.json").read_text())
batch = reg["actors"][:35]
print("Batch A verification:")
new_count = 0
for a in batch:
    _p = a["reference_image_primary"].replace("\\", "/").split("/")  # strip 'Studio/Cast/' any casing
    p = root / ("/".join(_p[2:]) if len(_p) > 2 and _p[0].lower() == "studio" else "/".join(_p))
    if p.exists():
        mtime = datetime.fromtimestamp(p.stat().st_mtime)
        if mtime.date().day >= 18 and mtime.year == 2026:
            new_count += 1
        ts = mtime.strftime("%Y-%m-%d %H:%M")
    else:
        ts = "MISSING"
    flags = a.get("compliance_flags", [])
    print(
        f"{a['actor_id']:18} {a['stage_name']:22} age={a['age_locked']} "
        f"plate={a['reference_image_status']} mtime={ts} flags={flags}"
    )
print(f"\nNew plates (Jun 18+): {new_count}/35")
print("Summary:", reg["summary"])