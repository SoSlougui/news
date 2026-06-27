import json, re

with open('/home/ubuntu/workspace/news_repo/articles.js','r',encoding='utf-8') as f:
    m = re.search(r'window\.ARTICLES\s*=\s*(\[.*\]);?\s*$', f.read(), re.S)
    articles = json.loads(m.group(1))

# Check for existing articles on these topics
topics = ['Anthropic', 'Trump', 'Bitcoin', 'BTC', 'Xbox', 'Ukraine', 'drone', 'executive order', 'IA ordre']
for topic in topics:
    matches = []
    for a in articles:
        if topic.lower() in a.get('title','').lower() or topic.lower() in a.get('body','').lower()[:200]:
            matches.append(f"  - {a['id'][:60]} | {a.get('date','?')}")
    if matches:
        print(f"'{topic}' found in {len(matches)} articles:")
        for m in matches:
            print(m)
    else:
        print(f"'{topic}' NOT found in any article")

print("\n--- Check source URLs for my planned stories ---")
planned_urls = [
    'https://www.cnbc.com/2026/06/26/bitcoin-below-59000.html',
    'https://finance.yahoo.com/markets/crypto/articles/bitcoin-collapses-below-59-000-151620003.html',
    'https://bitcoinmagazine.com/markets/bitcoin-price-collapses-to-59000',
    'https://247wallst.com/investing/2026/06/25/bitcoin-collapses-below-59000-just-how-deep-is-this-hole/',
    'https://news.xbox.com/en-us/2026/06/25/xbox-console-price-update/',
    'https://www.ign.com/articles/microsoft-announces-significant-price-rises-for-xbox-series-x-and-s-2tb-model-discontinued',
    'https://www.forbes.com/sites/paultassi/2026/06/25/following-apple-microsoft-dramatically-hikes-xbox-prices-again/',
    'https://apnews.com/article/russia-ukraine-war-biggest-drone-attack-a356e2a119f3cb9422ede6acbedf56f3',
    'https://united24media.com/war-in-ukraine/ukraines-drone-swarms-are-overloading-russian-air-defense-june-sets-record-for-deep-strikes-20199',
]
existing_urls = {a.get('url','') for a in articles}
for url in planned_urls:
    if url in existing_urls:
        print(f"DUPLICATE: {url[:100]}")
    else:
        print(f"OK: {url[:100]}")
