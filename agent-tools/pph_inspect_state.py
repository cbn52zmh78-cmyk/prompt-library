import re
import json
import urllib.request

UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"

def fetch(url):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=60) as r:
        return r.read().decode("utf-8", errors="replace")

html = fetch("https://www.peopleperhour.com/freelance-jobs/technology-programming")
m = re.search(r'window\.PPHReact\.initialState\s*=\s*(\{.*?\});\s*\n', html, re.DOTALL)
if not m:
    m = re.search(r'window\.PPHReact\.initialState\s*=\s*(\{.*)', html, re.DOTALL)
state_text = m.group(1)
# trim to valid json - find balanced braces from start
# state may continue until </script>
state_text = state_text.split('</script>')[0].strip()
if state_text.endswith(';'):
    state_text = state_text[:-1]

state = json.loads(state_text)
print('top keys', list(state.keys())[:30])

entities = state.get('entities', {})
print('entities keys', entities.keys())
projects = entities.get('projects', {})
print('entities.projects count', len(projects))

pid = next(iter(projects))
proj = projects[pid]
print('sample keys', proj.keys())
attrs = proj.get('attributes', proj)
print('attr keys', sorted(attrs.keys()))
print(json.dumps(attrs, indent=2)[:3000])

fj = state.get('freelanceJobs', {})
print('freelanceJobs keys', fj.keys() if isinstance(fj, dict) else fj)
print('freelanceJobs sample', json.dumps(fj, indent=2)[:1500])

rels = state.get('relationships', {})
print('relationships keys', rels.keys() if isinstance(rels, dict) else rels)
# search listAll links in raw html
links = re.findall(r'projects/listAll\?[^"\']+', html)
print('listAll links', links[:5])