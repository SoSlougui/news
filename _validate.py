import re
with open('index.html','r') as f:
    content = f.read()
m = re.search(r'<script>(.*?)</script>', content, re.DOTALL)
if m:
    with open('/tmp/test_js.js','w') as f2:
        f2.write(m.group(1))
    print(f"Extracted JS: {len(m.group(1))} chars")
else:
    print("ERROR: No script tag found")
