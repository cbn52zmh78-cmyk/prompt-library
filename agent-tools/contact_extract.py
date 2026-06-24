import json
import re
import html
import urllib.request

item = json.load(urllib.request.urlopen("https://hn.algolia.com/api/v1/items/47975571"))
comments = []

def walk(c):
    if c.get("text"):
        comments.append(c["text"])
    for ch in c.get("children", []):
        walk(ch)

for c in item.get("children", []):
    walk(c)

targets = [
    "Form AI", "Revieve", "Dablam", "Orenva", "In The Loop", "Octozi",
    "BrandMultiplier", "HME Technologies", "Learnwise", "Railtown", "E2B",
    "Fractional AI", "Hyperspell", "Sycamore", "Starbridge", "Addepar",
    "Featurebase", "FunnelStory", "Kanary", "Kinelo", "We The Flywheel",
]

for t in comments:
    clean = re.sub("<[^<]+?>", " ", html.unescape(t))
    for name in targets:
        if name.lower() in clean.lower():
            emails = re.findall(r"[\w\.-]+@[\w\.-]+\.\w+", clean)
            urls = re.findall(r"https?://[^\s<>\"]+", clean)
            print(f"=== {name} ===")
            print("Emails:", emails[:5])
            print("URLs:", urls[:6])
            print(clean[:500])
            print()
            break