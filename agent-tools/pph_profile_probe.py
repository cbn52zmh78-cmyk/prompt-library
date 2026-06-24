import re, json, urllib.request
UA='Mozilla/5.0'
url='https://www.peopleperhour.com/freelancer/jay-khan-yxwmayj'
html=urllib.request.urlopen(urllib.request.Request(url,headers={'User-Agent':UA})).read().decode()
print('len', len(html))
if 'initialState' in html:
    state=json.loads(re.search(r'window\.PPHReact\.initialState\s*=\s*(\{.*)', html).group(1).split('</script>')[0].strip().rstrip(';'))
    def walk(obj, path=''):
        if isinstance(obj, dict):
            for k,v in obj.items():
                if any(x in k.lower() for x in ['rating','review','feedback','score']):
                    if not isinstance(v, (dict,list)) or (isinstance(v,dict) and len(v)<5):
                        print(path+'.'+k, '=', v)
                if len(path) < 80:
                    walk(v, path+'.'+k)
    walk(state)
else:
    for pat in ['rating','review','feedback']:
        print(pat, [html[m.start():m.start()+80] for m in re.finditer(pat, html, re.I)][:5])