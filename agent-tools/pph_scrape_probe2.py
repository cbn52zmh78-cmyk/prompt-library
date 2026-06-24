import re
import json
import urllib.request

UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"

def fetch(url):
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "*/*"})
    with urllib.request.urlopen(req, timeout=60) as r:
        return r.read().decode("utf-8", errors="replace")

for name in ["28.3ce14b3b.js", "app.a444e0bd.js"]:
    js = fetch(f"https://d1a29h5kxv3oc2.cloudfront.net/dist/{name}")
    print("===", name, "len", len(js))
    for term in ["project", "freelance", "job", "graphql", "api/", "/v2/", "hourlie", "budget", "bid"]:
        print(term, js.lower().count(term))
    # interesting string literals
    hits = set()
    for m in re.finditer(r'["\']([a-zA-Z0-9_\-./]{4,120})["\']', js):
        s = m.group(1)
        if any(k in s.lower() for k in ["project", "job", "freelance", "api", "search", "graphql"]):
            hits.add(s)
    for h in sorted(hits)[:80]:
        print(" ", h)

# check HTML for embedded JSON state
html = fetch("https://www.peopleperhour.com/freelance-jobs/technology-programming")
for pat in ["__PRELOADED", "__INITIAL", "window.__", "preloadedState", "projects", "jobList"]:
    print(pat, html.find(pat))
# script type application/json
for m in re.finditer(r'<script[^>]*type="application/json"[^>]*>(.*?)</script>', html, re.DOTALL):
    blob = m.group(1)[:500]
    print("json blob", blob[:200])