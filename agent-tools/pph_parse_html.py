import re
import json
import html as htmlmod
import urllib.request

UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"

def fetch(url):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=60) as r:
        return r.read().decode("utf-8", errors="replace")

html = fetch("https://www.peopleperhour.com/freelance-jobs/technology-programming")

# Find script tags with large content
scripts = re.findall(r'<script[^>]*>(.*?)</script>', html, re.DOTALL)
print('script tags', len(scripts))
for i, s in enumerate(scripts):
    if len(s) > 5000:
        print(' big script', i, len(s), s[:120].replace('\n',' '))

# search for project objects pattern
for key in ['"slug"', '"budget"', '"numBids"', '"bidCount"', '"rating"', '"skills"', '"createdAt"', '"posted"', '"url"']:
    print(key, html.count(key))

# try to find JSON array after projects key
m = re.search(r'"projects"\s*:\s*(\{.*?\})\s*,\s*"', html)
if m:
    print('projects obj snippet', m.group(1)[:500])

# extract all title/url pairs from embedded state - look for id+title patterns
chunks = re.findall(r'\{"id":\d+[^}]{0,2000}?\}', html)
print('id chunks', len(chunks))
if chunks:
    print(chunks[0][:400])

# broader: objects with title and slug
objs = re.findall(r'\{[^{}]*"title"\s*:\s*"[^"]+"[^{}]*"slug"\s*:\s*"[^"]+"[^{}]*\}', html)
print('title+slug objs', len(objs))
if objs:
    print(objs[0][:500])

# nested objects - find listAll response shape in html
idx = html.find('listAll')
print('listAll idx', idx, html[idx:idx+200] if idx>=0 else '')

# save sample around first title
tidx = html.find('"title"')
print('first title area', html[tidx:tidx+800])