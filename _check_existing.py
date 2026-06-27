import json, re
with open('/home/ubuntu/workspace/news_repo/articles.js', 'r', encoding='utf-8') as f:
    m = re.search(r'window\.ARTICLES\s*=\s*(\[.*\]);?\s*$', f.read(), re.S)
    articles = json.loads(m.group(1))

# Check for topics we might cover
keywords = ['openai', 'gpt-5', 'micron', 'bitcoin', 'btc', 'spacex', 'star fox', 'nintendo', 'ukraine']
existing_urls = set()
for a in articles:
    existing_urls.add(a.get('url',''))
    title_lower = a['title'].lower()
    for kw in keywords:
        if kw in title_lower or kw in a.get('excerpt','').lower():
            print(f"MATCH '{kw}': ID={a['id'][:60]} | title={a['title'][:80]} | url={a.get('url','')[:80]}")

print(f"\nTotal articles: {len(articles)}")
print(f"Total URLs: {len(existing_urls)}")

# Print last 10 article details for reference
print("\n--- LAST 10 ARTICLES ---")
for a in articles[:10]:
    print(f"  [{a.get('cat','?')}] {a['title'][:70]} | {a.get('date','?')}")
