import re, json, urllib.request, urllib.parse
UA='Mozilla/5.0'

def titles(url):
    html = urllib.request.urlopen(urllib.request.Request(url, headers={'User-Agent': UA})).read().decode()
    m = re.search(r'window\.PPHReact\.initialState\s*=\s*(\{.*)', html)
    if not m:
        return None, []
    state = json.loads(m.group(1).split('</script>')[0].strip().rstrip(';'))
    projs = state.get('entities', {}).get('projects', {})
    titles = [p['attributes']['title'] for p in projs.values()]
    meta = state.get('freelanceJobs', {}).get('main', {}).get('meta', {})
    qf = state.get('freelanceJobs', {}).get('queryFilters', {})
    return meta, titles[:5], qf

searches = [
    'https://www.peopleperhour.com/freelance-jobs',
    'https://www.peopleperhour.com/freelance-jobs?keyword=python',
    'https://www.peopleperhour.com/freelance-jobs?search_term=python',
    'https://www.peopleperhour.com/freelance-jobs?filter[keyword]=python',
    'https://www.peopleperhour.com/freelance-jobs?q=python',
    'https://www.peopleperhour.com/freelance-jobs/search/python',
    'https://www.peopleperhour.com/freelance-jobs/tag/python',
]
for url in searches:
    try:
        meta, t, qf = titles(url)
        print(url)
        print(' meta', meta.get('total-items'), meta.get('applied_filters'))
        print(' qf', qf)
        print(' titles', t)
    except Exception as e:
        print(url, 'ERR', e)
    print()