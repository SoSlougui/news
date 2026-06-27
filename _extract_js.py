import re
with open('/home/ubuntu/workspace/news_repo/index.html', 'r', encoding='utf-8') as f:
    content = f.read()
    
# Find all script tags and combine
scripts = re.findall(r'<script[^>]*>(.*?)</script>', content, re.DOTALL)
combined = '\n'.join(scripts)

with open('/home/ubuntu/workspace/news_repo/_test_js.js', 'w', encoding='utf-8') as f:
    f.write(combined)

print(f"Extracted {len(scripts)} script blocks, {len(combined)} chars total")
