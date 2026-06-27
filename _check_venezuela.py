import json, re

with open('/home/ubuntu/workspace/news_repo/articles.js','r',encoding='utf-8') as f:
    m = re.search(r'window\.ARTICLES\s*=\s*(\[.*\]);?\s*$', f.read(), re.S)
    articles = json.loads(m.group(1))

# Check Venezuela and related terms
for topic in ['Venezuela', 'séisme', 'tremblement', 'earthquake', 'Caracas']:
    matches = []
    for a in articles:
        body = a.get('body','')
        title = a.get('title','')
        if topic.lower() in title.lower() or topic.lower() in body[:300]:
            matches.append(f"  {a['id'][:60]} | {a.get('date','?')}")
    if matches:
        print(f"'{topic}' in {len(matches)} articles:")
        for m in matches[:5]:
            print(m)
    else:
        print(f"'{topic}': NOT found")

print("\n=== All articles published today (June 26) ===")
for a in articles:
    if '26 Jun 2026' in a.get('date',''):
        print(f"  [{a.get('cat','?')}] {a['id'][:65]} | {a.get('date','?')}")
