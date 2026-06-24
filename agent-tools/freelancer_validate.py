import json
from pathlib import Path

p = Path(r"C:\Users\NCG\Claude\Projects\NEXUS\freelance\freelancer_live_scan_2026-06-24.json")
d = json.loads(p.read_text(encoding="utf-8"))
jobs = d["jobs"]
fields = ["title", "budget_min", "budget_max", "skills", "bids", "posted", "url"]
for f in fields:
    missing = sum(1 for j in jobs if j.get(f) in (None, [], ""))
    print(f"{f}: missing={missing}/{len(jobs)}")
bad = [j for j in jobs if j.get("title", "").lower() == "bid now"]
print("bad_titles", len(bad))
print("first", json.dumps(jobs[0], indent=2))
print("with_range", next((j for j in jobs if j.get("budget_min") != j.get("budget_max")), None))
print("hourly", next((j for j in jobs if j.get("posted") and "hr" in str(j)), None))