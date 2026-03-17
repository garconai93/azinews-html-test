#!/usr/bin/env python3
"""Generate RSS feed from AziNews HTML"""

import re
from datetime import datetime

# Read the index.html
with open('index.html', 'r', encoding='utf-8') as f:
    content = f.read()

# Extract news array
match = re.search(r'const news = \[(.*?)\];', content, re.DOTALL)
if not match:
    print("No news found!")
    exit(1)

news_text = match.group(1)

# Parse news items
news_items = []
# Match news items with optional fields
item_pattern = r"{ source: '([^']+)', url: '([^']+)', title: \"([^\"]+)\"(?:, image: \"([^\"]*)\")?(?:, time: \"([^\"]*)\")?(?:, content: \"([^\"]*)\")?"

for m in re.finditer(item_pattern, news_text):
    source = m.group(1)
    url = m.group(2)
    title = m.group(3) or ""
    # Decode HTML entities
    title = title.replace('&#8222;', '"').replace('&#8221;', '"').replace('&#8217;', "'").replace('&#8211;', '–')
    news_items.append({
        'source': source,
        'url': url,
        'title': title
    })

if not news_items:
    print("No news found!")
    exit(0)  # Don't fail, just skip

# Generate RSS
rss = '''<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0" xmlns:atom="http://www.w3.org/2005/Atom">
<channel>
    <title>AziNews - Știri din România</title>
    <link>https://azinews.ro</link>
    <description>Ultimele știri din România</description>
    <language>ro</language>
    <lastBuildDate>{date}</lastBuildDate>
    <atom:link href="https://azinews.ro/feed.xml" rel="self" type="application/rss+xml"/>
'''.format(date=datetime.now().strftime('%a, %d %b %Y %H:%M:%S +0200'))

for i, item in enumerate(news_items[:10]):
    rss += '''    <item>
        <title>{title}</title>
        <link>{url}</link>
        <description>{source}</description>
        <guid isPermaLink="true">{url}</guid>
    </item>
'''.format(title=item['title'], url=item['url'], source=item['source'])

rss += '''</channel>
</rss>'''

# Write RSS file
with open('feed.xml', 'w', encoding='utf-8') as f:
    f.write(rss)

print(f"Generated RSS with {len(news_items)} items")