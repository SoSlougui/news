import json, re
with open('articles.js','r',encoding='utf-8') as f:
    m = re.search(r'window\.ARTICLES\s*=\s*(\[.*\]);?\s*$', f.read(), re.S)
    articles = json.loads(m.group(1))
existing_ids = {a['id'] for a in articles}
existing_urls = {a.get('url','') for a in articles}
cats = {}
for a in articles:
    c = a.get('cat','unknown')
    cats[c] = cats.get(c,0) + 1
print(f'{len(articles)} total articles')
print(f'{len(existing_urls)} unique URLs')
print('Categories:', cats)
for a in articles[:10]:
    print(f'  [{a["cat"]}] {a["date"]} | {a["title"][:90]}')
# Print all URLs for dedup
for a in articles:
    print(f'URL: {a.get("url","")}')
