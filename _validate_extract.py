import re
with open('index.html', 'r', encoding='utf-8') as f:
    content = f.read()

# Extract all script blocks and concatenate
scripts = re.findall(r'<script[^>]*>(.*?)</script>', content, re.DOTALL)
with open('/tmp/test_js.js', 'w', encoding='utf-8') as f:
    for s in scripts:
        f.write(s + '\n')
print(f"Extracted {len(scripts)} script blocks")
