#!/usr/bin/env python3
"""Generate RSS feed from AziNews HTML"""

import re
import html
from datetime import datetime

# Read the index.html
with open('index.html', 'r', encoding='utf-8') as f:
    content = f.read()

news_items = []

def escape_xml(text):
    """Escape special XML characters"""
    text = text.replace('&', '&amp;')
    text = text.replace('<', '&lt;')
    text = text.replace('>', '&gt;')
    text = text.replace('"', '&quot;')
    text = text.replace("'", '&apos;')
    return text

# Try new static HTML format first
news_cards = re.findall(r'<div class="news-card"[^>]*data-url="([^"]+)"[^>]*>.*?<div class="news-source"><a[^>]*>([^<]+)</a>.*?<div class="news-title">([^<]+)</div>', content, re.DOTALL)

if news_cards:
    for url, source, title in news_cards:
        title = re.sub(r'<[^>]+>', '', title).strip()
        title = title.replace('&#8222;', '"').replace('&#8221;', '"').replace('&#8217;', "'").replace('&#8211;', '–')
        title = escape_xml(title)
        news_items.append({'source': source.strip(), 'url': url.strip(), 'title': title})

# Fallback: try old JS array format
if not news_items:
    match = re.search(r'const news = \[(.*?)\];', content, re.DOTALL)
    if match:
        news_text = match.group(1)
        item_pattern = r"{ source: '([^']+)', url: '([^']+)', title: \"([^\"]+)\""
        for m in re.finditer(item_pattern, news_text):
            source, url, title = m.groups()
            title = title.replace('&#8222;', '"').replace('&#8221;', '"').replace('&#8217;', "'").replace('&#8211;', '–')
            title = escape_xml(title)
            news_items.append({'source': source, 'url': url, 'title': title})

# Always check JS array as fallback
if not news_items:
    match = re.search(r'const news = \[(.*?)\];', content, re.DOTALL)
    if match:
        news_text = match.group(1)
        item_pattern = r"{ source: '([^']+)', url: '([^']+)', title: \"([^\"]+)\""
        for m in re.finditer(item_pattern, news_text):
            source, url, title = m.groups()
            title = title.replace('&#8222;', '"').replace('&#8221;', '"').replace('&#8217;', "'").replace('&#8211;', '–')
            title = escape_xml(title)
            news_items.append({'source': source, 'url': url, 'title': title})

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

for i, item in enumerate(news_items[:60]):
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