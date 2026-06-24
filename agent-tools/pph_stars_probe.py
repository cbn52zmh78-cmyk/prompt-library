import re, json, urllib.request
h = urllib.request.urlopen(urllib.request.Request(
    'https://www.peopleperhour.com/freelance-jobs?keyword=python',
    headers={'User-Agent': 'Mozilla/5.0'})).read().decode()
state = json.loads(re.search(r'window\.PPHReact\.initialState\s*=\s*(\{.*)', h).group(1).split('</script>')[0].strip().rstrip(';'))
dump = json.dumps(state)
print('stars count', dump.count('stars'))
print('rating count', dump.count('rating'))
for m in re.finditer(r'"stars"\s*:\s*"?[^",}]+', dump):
    print(m.group(0))
# check meta stars on profile
prof = urllib.request.urlopen(urllib.request.Request(
    'https://www.peopleperhour.com/freelancer/jay-khan-yxwmayj',
    headers={'User-Agent': 'Mozilla/5.0'})).read().decode()
meta = re.findall(r'peopleperhourcom:stars[^>]+', prof)
print('profile meta', meta)