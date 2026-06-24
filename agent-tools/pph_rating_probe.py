import re, urllib.request
UA='Mozilla/5.0'
url='https://www.peopleperhour.com/freelance-jobs/technology-programming/databases/app-based-kpi-dashboard-4503510'
html=urllib.request.urlopen(urllib.request.Request(url,headers={'User-Agent':UA})).read().decode()
for pat in ['"rating"', '"reviews"', '"review_count"', '"feedback"', '"score"', 'buyerRating', 'clientRating', 'avg_rating']:
    idx = html.find(pat)
    if idx >= 0:
        print(pat, html[idx:idx+120])
# listing page client block - any rating field across all clients
html2=urllib.request.urlopen(urllib.request.Request(
    'https://www.peopleperhour.com/freelance-jobs?keyword=python', headers={'User-Agent':UA})).read().decode()
import json
state=json.loads(re.search(r'window\.PPHReact\.initialState\s*=\s*(\{.*)', html2).group(1).split('</script>')[0].strip().rstrip(';'))
for p in state['entities']['projects'].values():
    c=p['attributes'].get('client',{})
    for k,v in c.items():
        if any(x in k.lower() for x in ['rat','review','feed','score','star']):
            print('FOUND', k, v)
print('done client key scan')
# scan entire state for rating keys
def walk(obj, path=''):
    if isinstance(obj, dict):
        for k,v in obj.items():
            if 'rating' in k.lower() or 'review' in k.lower():
                print('path', path+'.'+k, '=', v)
            walk(v, path+'.'+k)
    elif isinstance(obj, list):
        for i,v in enumerate(obj[:3]):
            walk(v, path+f'[{i}]')
walk(state.get('entities',{}).get('projects',{}))