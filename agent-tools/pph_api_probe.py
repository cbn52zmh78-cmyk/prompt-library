import re
import json
import urllib.request

UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"

def fetch(url, accept="application/json,*/*"):
    req = urllib.request.Request(url, headers={
        "User-Agent": UA,
        "Accept": accept,
        "Referer": "https://www.peopleperhour.com/freelance-jobs",
        "X-Requested-With": "XMLHttpRequest",
    })
    with urllib.request.urlopen(req, timeout=60) as r:
        data = r.read()
        ctype = r.headers.get("Content-Type", "")
        return ctype, data

js = urllib.request.urlopen(
    urllib.request.Request("https://d1a29h5kxv3oc2.cloudfront.net/dist/app.a444e0bd.js", headers={"User-Agent": UA})
).read().decode("utf-8", errors="replace")

# extract context around listAll
for m in re.finditer(r'.{0,200}listAll.{0,400}', js):
    snippet = m.group(0)
    if "project" in snippet.lower():
        print("---")
        print(snippet[:500])

urls = [
    "https://www.peopleperhour.com/v2/projects/listAll",
    "https://www.peopleperhour.com/v2/projects/listAll?page=1",
    "https://www.peopleperhour.com/v2/projects/listAll?page=1&limit=50",
    "https://www.peopleperhour.com/v2/projects/listAll?search=python",
    "https://www.peopleperhour.com/v2/projects/listAll?query=python",
    "https://www.peopleperhour.com/v2/projects/listAll?keywords=python",
    "https://www.peopleperhour.com/v2/projects?page=1",
    "https://www.peopleperhour.com/v2/projects?search=python&page=1",
]
for url in urls:
    try:
        ctype, data = fetch(url)
        text = data.decode("utf-8", errors="replace")
        print(url)
        print(" ctype", ctype, "len", len(text))
        print(" preview", text[:300])
        if text.strip().startswith("{"):
            obj = json.loads(text)
            print(" keys", list(obj.keys())[:20])
    except Exception as e:
        print(url, "ERR", e)