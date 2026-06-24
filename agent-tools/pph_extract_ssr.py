import re
import json
import urllib.request

UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"

def fetch(url):
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "text/html"})
    with urllib.request.urlopen(req, timeout=60) as r:
        return r.read().decode("utf-8", errors="replace")

pages = [
    "https://www.peopleperhour.com/freelance-jobs",
    "https://www.peopleperhour.com/freelance-jobs/technology-programming",
    "https://www.peopleperhour.com/freelance-jobs?query=python",
    "https://www.peopleperhour.com/freelance-jobs?query=automation",
    "https://www.peopleperhour.com/freelance-jobs?query=web%20development",
    "https://www.peopleperhour.com/freelance-jobs?query=AI",
    "https://www.peopleperhour.com/freelance-jobs?query=script",
    "https://www.peopleperhour.com/freelance-jobs?query=bug%20fix",
]

for url in pages:
    html = fetch(url)
    print("URL", url, "len", len(html))
    # look for JSON-like project data
    for pat in [
        r'window\.__[A-Z_]+__\s*=\s*(\{.*?\});',
        r'"projects"\s*:\s*(\[.*?\])',
        r'data-reactroot[^>]*>(.*?)</div>',
    ]:
        pass
    # find title patterns in HTML
    titles = re.findall(r'card__job-title[^>]*>([^<]+)<', html)
    print(" card titles", len(titles), titles[:3])
    # alternate patterns
    titles2 = re.findall(r'"title"\s*:\s*"([^"]{5,200})"', html)
    print(" json titles", len(titles2), titles2[:3])
    # big json arrays with budget
    if '"budget"' in html or '"maxBudget"' in html:
        idx = html.find('"budget"')
        print(" budget context", html[idx-100:idx+200][:250])
    # extract all occurrences of project slug urls
    links = re.findall(r'href="(/freelance-jobs/[^"]+)"', html)
    print(" job links", len(set(links)), list(set(links))[:5])
    # search for bidCount, clientRating etc
    for field in ["bidCount", "clientRating", "maxBudget", "postedDate", "skills"]:
        print(" ", field, html.count(field))
    print()