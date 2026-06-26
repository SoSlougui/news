import json, re
with open('articles.js','r',encoding='utf-8') as f:
    m = re.search(r'window\.ARTICLES\s*=\s*(\[.*\]);?\s*$', f.read(), re.S)
    articles = json.loads(m.group(1))
existing_urls = {a.get('url','') for a in articles}
planned = [
    'https://www.reuters.com/legal/transactional/onsemi-buy-synaptics-7-billion-all-stock-deal-2026-06-25/',
    'https://bitcoinmagazine.com/news/sbi-holdings-agrees-to-acquire-bitbank',
    'https://news.xbox.com/en-us/2026/06/19/next-week-on-xbox-new-games-for-june-22-to-26/',
    'https://www.aljazeera.com/news/2026/6/25/oil-prices-back-to-pre-war-levels-on-rising-middle-east-supply',
    'https://www.bbc.com/news/articles/cy4181pkxl2o',
]
for url in planned:
    status = 'DUPLICATE' if url in existing_urls else 'OK'
    print(f'{status}: {url[:100]}')
