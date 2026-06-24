import re, json, urllib.request
UA='Mozilla/5.0'
prof = urllib.request.urlopen(urllib.request.Request(
    'https://www.peopleperhour.com/freelancer/jay-khan-yxwmayj', headers={'User-Agent': UA})).read().decode()
# find PPHReact data blocks
for pat in [r'window\.PPHReact\.(\w+)\s*=\s*(\{.*?\});', r'window\.PPHReact\.(\w+)\s*=\s*\'([^\']+)\'']:
    for m in re.finditer(pat, prof, re.DOTALL):
        print('block', m.group(1), 'len', len(m.group(2)))
        if m.group(1) in ('initialState', 'pageData', 'userData'):
            print(m.group(2)[:1500])
# og stars and rating meta
for m in re.finditer(r'<meta[^>]+peopleperhour[^>]+>', prof):
    print(m.group(0))