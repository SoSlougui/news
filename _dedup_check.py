import json, re
with open('/home/ubuntu/workspace/news_repo/articles.js', 'r', encoding='utf-8') as f:
    m = re.search(r'window\.ARTICLES\s*=\s*(\[.*\]);?\s*$', f.read(), re.S)
    articles = json.loads(m.group(1))
existing_ids = {a['id'] for a in articles}
existing_urls = {a.get('url', '') for a in articles}
print(f'{len(existing_ids)} existing articles, {len(existing_urls)} URLs')
# Print last 5 article IDs and dates
for a in articles[:5]:
    print(f"  ID={a['id']} | date={a.get('date','')} | cat={a.get('cat','')}")
