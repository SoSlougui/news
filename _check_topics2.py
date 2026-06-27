import json, re

with open('/home/ubuntu/workspace/news_repo/articles.js','r',encoding='utf-8') as f:
    m = re.search(r'window\.ARTICLES\s*=\s*(\[.*\]);?\s*$', f.read(), re.S)
    articles = json.loads(m.group(1))

print("=== Check for IRGC / Iran targeting big tech ===")
for topic in ['IRGC', 'Iran', 'cible', 'legitimate target', 'Revolutionary Guard', 'Gardiens']:
    matches = []
    for a in articles:
        body = a.get('body','')
        title = a.get('title','')
        if topic.lower() in title.lower() or topic.lower() in body[:500]:
            matches.append(f"  {a['id'][:60]} | {a.get('date','?')}")
    if matches:
        print(f"'{topic}' in {len(matches)} articles:")
        for m in matches[:5]:
            print(m)
    else:
        print(f"'{topic}': NOT found")

print("\n=== Check for Micron ===")
for topic in ['Micron', 'mémoire', 'chip', 'puce']:
    matches = []
    for a in articles:
        body = a.get('body','')
        title = a.get('title','')
        if topic.lower() in title.lower() or topic.lower() in body[:500]:
            matches.append(f"  {a['id'][:60]} | {a.get('date','?')}")
    if matches:
        print(f"'{topic}' in {len(matches)} articles (showing first 5):")
        for m in matches[:5]:
            print(m)
    else:
        print(f"'{topic}': NOT found")

print("\n=== Check for CISA / Lantronix / cybersecurity ===")
for topic in ['CISA', 'Lantronix', 'cybersécurité', 'vulnérabilité']:
    matches = []
    for a in articles:
        body = a.get('body','')
        title = a.get('title','')
        if topic.lower() in title.lower() or topic.lower() in body[:500]:
            matches.append(f"  {a['id'][:60]} | {a.get('date','?')}")
    if matches:
        print(f"'{topic}' in {len(matches)} articles:")
        for m in matches[:5]:
            print(m)
    else:
        print(f"'{topic}': NOT found")
