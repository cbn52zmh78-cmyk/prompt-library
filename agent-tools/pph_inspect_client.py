import re, json, urllib.request
UA = "Mozilla/5.0"
html = urllib.request.urlopen(urllib.request.Request(
    "https://www.peopleperhour.com/freelance-jobs/technology-programming?page=2",
    headers={"User-Agent": UA})).read().decode()
state = json.loads(re.search(r'window\.PPHReact\.initialState\s*=\s*(\{.*)', html).group(1).split('</script>')[0].strip().rstrip(';'))
proj = next(iter(state['entities']['projects'].values()))
print(json.dumps(proj['attributes']['client'], indent=2))
print('budget', proj['attributes'].get('budget'))
print('proposalCount', proj['attributes'].get('proposalCount'))
print('posted_dt', proj['attributes'].get('posted_dt'))
print('url', proj['attributes'].get('url'))
print('etiquettes', proj['attributes'].get('etiquettes'))
print('meta', state['freelanceJobs']['main'].get('meta'))
# members in entities?
print('entity keys', state['entities'].keys())
for k in state['entities']:
    if k != 'projects':
        obj = state['entities'][k]
        if isinstance(obj, dict) and obj:
            print(k, 'count', len(obj), 'sample', json.dumps(next(iter(obj.values())), indent=2)[:600])