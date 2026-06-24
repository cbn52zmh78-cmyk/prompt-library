import re
import urllib.request

req = urllib.request.Request("https://ag.ny.gov/", headers={"User-Agent": "Mozilla/5.0"})
html = urllib.request.urlopen(req, timeout=20).read().decode("utf-8", "replace")
links = sorted(set(re.findall(r'href="(/media/[^"]+)"', html)))
print("media links", len(links))
for l in links[:20]:
    print(l)

# try press-releases listing
for path in ["/press-releases", "/news/press-releases", "/media"]:
    u = "https://ag.ny.gov" + path
    try:
        req = urllib.request.Request(u, headers={"User-Agent": "Mozilla/5.0"})
        r = urllib.request.urlopen(req, timeout=15)
        print("OK", path, r.status)
    except Exception as e:
        print("ERR", path, e)