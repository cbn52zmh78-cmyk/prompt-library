import re
import json
import urllib.request

UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"

def fetch(url):
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "text/html,application/json,*/*"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.read().decode("utf-8", errors="replace")

html = fetch("https://www.peopleperhour.com/freelance-jobs")
print("html len", len(html))
scripts = re.findall(r'src="([^"]+\.js)"', html)
print("scripts", len(scripts))
for s in scripts:
    if "app." in s or "28." in s:
        print("bundle", s)

# probe search/category URLs
candidates = [
    "https://www.peopleperhour.com/freelance-jobs?query=python",
    "https://www.peopleperhour.com/freelance-jobs/python",
    "https://www.peopleperhour.com/freelance-jobs/technology-programming",
    "https://www.peopleperhour.com/api/v2/projects",
    "https://www.peopleperhour.com/api/projects",
    "https://www.peopleperhour.com/api/v1/projects",
    "https://www.peopleperhour.com/v2/api/projects",
]
for url in candidates:
    try:
        body = fetch(url)
        print(url, "->", len(body), body[:120].replace("\n", " "))
    except Exception as e:
        print(url, "-> ERR", e)

# scan app js for api paths
if scripts:
    app = [s for s in scripts if "/app." in s]
    if app:
        js = fetch(app[0] if app[0].startswith("http") else "https://d1a29h5kxv3oc2.cloudfront.net" + app[0])
        paths = sorted(set(re.findall(r'["\'](/api[^"\']+)["\']', js)))
        paths += sorted(set(re.findall(r'["\'](https?://[^"\']*peopleperhour[^"\']*api[^"\']*)["\']', js)))
        print("api paths in app js", len(paths))
        for p in paths[:40]:
            print(" ", p[:140])