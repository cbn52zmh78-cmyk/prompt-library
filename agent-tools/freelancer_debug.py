import re
from pathlib import Path

html = Path(r"C:\Users\NCG\Videos\Grok Projects\agent-tools\freelancer_sample.html").read_text(encoding="utf-8")
print("split1", len(re.split(r'<div class="JobSearchCard-item-inner"', html)))
print("split2", len(re.split(r"JobSearchCard-item-inner", html)))
m = re.search(
    r'class="JobSearchCard-primary-heading-link"[^>]*href="(/projects/[^"]+)"[^>]*>(.*?)</a>',
    html,
    re.S,
)
print("match", bool(m))
if m:
    print("path", m.group(1))
    print("title", m.group(2)[:80])