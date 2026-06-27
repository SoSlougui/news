import json, re
with open('/home/ubuntu/workspace/news_repo/articles.js', 'r', encoding='utf-8') as f:
    m = re.search(r'window\.ARTICLES\s*=\s*(\[.*\]);?\s*$', f.read(), re.S)
    articles = json.loads(m.group(1))

# Check specific topics
for kw in ['binance', 'samsung', 'apple prix', 'microsoft prix', 'mica', 'deepseek embauche']:
    matches = []
    for a in articles:
        tl = (a['title'] + ' ' + a.get('excerpt','')).lower()
        if kw in tl:
            matches.append(f"  ID={a['id'][:55]} | {a['title'][:70]}")
    if matches:
        print(f"MATCH '{kw}':")
        for m in matches:
            print(m)
    else:
        print(f"NO MATCH for '{kw}'")
