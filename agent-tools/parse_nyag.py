import re
import urllib.request

req = urllib.request.Request(
    "https://ag.ny.gov/search?search=deed%20theft",
    headers={"User-Agent": "Mozilla/5.0"},
)
html = urllib.request.urlopen(req, timeout=25).read().decode("utf-8", "replace")
links = re.findall(r'href="(/[^"]+)"[^>]*>([^<]{5,120})</a>', html)
seen = set()
for href, txt in links:
    if "deed" in (txt + href).lower() and href not in seen:
        seen.add(href)
        print("https://ag.ny.gov" + href, txt.strip()[:90])