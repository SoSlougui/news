import json, re
with open('articles.js','r',encoding='utf-8') as f:
    m = re.search(r'window\.ARTICLES\s*=\s*(\[.*\]);?\s*$', f.read(), re.S)
    articles = json.loads(m.group(1))
existing_urls = {a.get('url','') for a in articles}
# Planned URLs
planned = [
    'https://www.reuters.com/legal/transactional/onsemi-buy-synaptics-7-billion-all-stock-deal-2026-06-25/',
    'https://digital-markets-act.ec.europa.eu/commission-reaches-preliminary-position-amazons-and-microsofts-market-leading-cloud-services-should-2026-06-25_en',
    'https://news.xbox.com/en-us/2026/06/19/next-week-on-xbox-new-games-for-june-22-to-26/',
    'https://www.theglobeandmail.com/investing/markets/stocks/CVX/pressreleases/2651043/stock-market-news-for-jun-25-2026/',
    'https://www.reuters.com/technology/',
]
for url in planned:
    status = 'DUPLICATE' if url in existing_urls else 'OK'
    print(f'{status}: {url[:100]}')
