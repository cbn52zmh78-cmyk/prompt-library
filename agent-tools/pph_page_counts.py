import re, json, urllib.request, urllib.parse, time
UA='Mozilla/5.0'
keywords = ['python','automation','web development','web dev','AI','script','bug fix','bugfix']

def meta_for(keyword, page=1):
    q = urllib.parse.urlencode({'keyword': keyword, 'page': page})
    url = f'https://www.peopleperhour.com/freelance-jobs?{q}'
    html = urllib.request.urlopen(urllib.request.Request(url, headers={'User-Agent': UA}), timeout=60).read().decode()
    state = json.loads(re.search(r'window\.PPHReact\.initialState\s*=\s*(\{.*)', html).group(1).split('</script>')[0].strip().rstrip(';'))
    m = state['freelanceJobs']['main']['meta']
    return m.get('total-items'), m.get('total-pages'), len(state['entities']['projects'])

for kw in keywords:
    try:
        total, pages, n = meta_for(kw)
        print(f'{kw!r}: {total} items, {pages} pages, first_page={n}')
        time.sleep(0.3)
    except Exception as e:
        print(kw, 'ERR', e)

# tech category
html = urllib.request.urlopen(urllib.request.Request(
    'https://www.peopleperhour.com/freelance-jobs/technology-programming', headers={'User-Agent': UA})).read().decode()
state = json.loads(re.search(r'window\.PPHReact\.initialState\s*=\s*(\{.*)', html).group(1).split('</script>')[0].strip().rstrip(';'))
m = state['freelanceJobs']['main']['meta']
print('tech-programming:', m.get('total-items'), m.get('total-pages'))