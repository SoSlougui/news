import json, re
with open('/home/ubuntu/workspace/news_repo/articles.js') as f:
    m = re.search(r'window\.ARTICLES\s*=\s*(\[.*\]);?\s*$', f.read(), re.S)
    articles = json.loads(m.group(1))
print(f'Total: {len(articles)}')
for a in articles[:3]:
    print(f'ID: {a["id"][:70]}')
    print(f'  cat={a["cat"]} | date={a.get("date","?")}')
    print()
