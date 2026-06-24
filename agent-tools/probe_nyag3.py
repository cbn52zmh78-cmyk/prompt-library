import re
import urllib.request

html = urllib.request.urlopen(
    urllib.request.Request("https://ag.ny.gov/press-releases", headers={"User-Agent": "Mozilla/5.0"}),
    timeout=25,
).read().decode("utf-8", "replace")
print("len", len(html))
for kw in ["deed", "title theft", "real estate", "wire fraud", "rental"]:
    if kw in html.lower():
        print("found", kw)

links = re.findall(r'href="(https://ag\.ny\.gov/[^"]+)"', html)
deed_links = [l for l in links if "deed" in l.lower() or "title" in l.lower() or "real-estate" in l.lower()]
print("deed/title links", deed_links[:15])

# extract visible text chunks with deed
text = re.sub(r"<script[^>]*>.*?</script>", " ", html, flags=re.S | re.I)
text = re.sub(r"<[^>]+>", "\n", text)
for line in text.split("\n"):
    s = line.strip()
    if len(s) > 30 and ("deed" in s.lower() or "title theft" in s.lower()):
        print("-", s[:200])