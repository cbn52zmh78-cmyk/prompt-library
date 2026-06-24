import re
import urllib.request

candidates = [
    "https://ag.ny.gov/press-release/2022/attorney-general-james-announces-new-initiative-combat-deed-theft",
    "https://ag.ny.gov/press-release/2023/attorney-general-james-announces-guilty-plea-deed-theft-scheme",
    "https://ag.ny.gov/press-release/2024/attorney-general-james-warns-homeowners-about-deed-theft",
    "https://oag.ca.gov/news/press-releases/attorney-general-bonta-announces-home-equity-theft-restitution",
    "https://oag.ca.gov/consumers/housing/home-equity-theft",
    "https://www.texasattorneygeneral.gov/news/releases/attorney-general-ken-paxton-warns-texans-about-deed-fraud",
    "https://www.michigan.gov/ag/initiatives/protecting-homeowners",
]
for u in candidates:
    try:
        req = urllib.request.Request(u, headers={"User-Agent": "Mozilla/5.0"})
        r = urllib.request.urlopen(req, timeout=15)
        html = r.read().decode("utf-8", "replace")
        title = re.search(r"<title>([^<]+)</title>", html, re.I)
        print("OK", r.status, (title.group(1) if title else "")[:70], u)
        text = re.sub(r"<[^>]+>", " ", html)
        for kw in ["deed", "title", "home equity", "property owner"]:
            if kw in text.lower():
                i = text.lower().find(kw)
                print(" ", kw, ":", text[max(0, i - 60) : i + 180].strip()[:200])
                break
    except Exception as e:
        print("ERR", str(e)[:55], u)