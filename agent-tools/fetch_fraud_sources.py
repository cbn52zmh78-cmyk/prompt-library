import re
import urllib.request

def fetch(url):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    return urllib.request.urlopen(req, timeout=25).read().decode("utf-8", "replace")

# PA OAG taking action
html = fetch("https://www.attorneygeneral.gov/taking-action/")
links = re.findall(r'href="([^"]+)"[^>]*>([^<]{10,120})</a>', html)
print("=== PA OAG real estate links ===")
for href, txt in links:
    t = (txt + " " + href).lower()
    if any(k in t for k in ["deed", "title", "real estate", "wire", "rental", "mortgage", "foreclosure", "property", "housing", "landlord"]):
        print(href, txt.strip()[:100])

# FTC rental report line
html = fetch("https://consumer.ftc.gov/articles/rental-listing-scams")
for m in re.finditer(r"report\.ftc\.gov[^\"\s<]+", html, re.I):
    print("FTC REPORT URL:", m.group(0))