import re, urllib.request
UA='Mozilla/5.0'
html=urllib.request.urlopen(urllib.request.Request(
    'https://www.peopleperhour.com/freelance-jobs?keyword=python', headers={'User-Agent':UA})).read().decode()
# extract job card sections
cards=re.findall(r'card__job-title.*?card__freelancer-ratings.*?(?=card__job-title|$)', html, re.DOTALL)
print('cards', len(cards))
if cards:
    print(cards[0][:1500])
# alternative: buyer rating in JSON API included data
for term in ['buyer_rating','buyerRating','client_rating','clientRating','mem_rating','member_rating','feedback_score','reviews_count']:
    print(term, html.find(term))