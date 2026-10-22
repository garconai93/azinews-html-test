#!/usr/bin/env python3
"""Generează feed.xml din data/latest.json"""

import json
from datetime import datetime, timezone
from email.utils import format_datetime
from xml.sax.saxutils import escape

with open('data/latest.json', encoding='utf-8') as f:
    items = json.load(f).get('items', [])

if not items:
    print("No news found!")
    raise SystemExit(0)


def pub_date(n):
    for key in ('ts', 'fetched_at'):
        try:
            return format_datetime(datetime.fromisoformat(n[key].replace('Z', '+00:00')))
        except (KeyError, ValueError, AttributeError):
            pass
    return ''


now = format_datetime(datetime.now(timezone.utc))
parts = [f'''<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0" xmlns:atom="http://www.w3.org/2005/Atom">
<channel>
    <title>AziNews - Știri din România</title>
    <link>https://azinews.ro</link>
    <description>Ultimele știri din România</description>
    <language>ro</language>
    <lastBuildDate>{now}</lastBuildDate>
    <atom:link href="https://azinews.ro/feed.xml" rel="self" type="application/rss+xml"/>
''']
for n in items[:60]:
    pd = pub_date(n)
    parts.append(f'''    <item>
        <title>{escape(n['title'])}</title>
        <link>{escape(n['url'])}</link>
        <description>{escape(n.get('content') or n['source'])}</description>
        <source url="https://azinews.ro/feed.xml">{escape(n['source'])}</source>
        <guid isPermaLink="true">{escape(n['url'])}</guid>{f"""
        <pubDate>{pd}</pubDate>""" if pd else ''}
    </item>
''')
parts.append('</channel>\n</rss>\n')

with open('feed.xml', 'w', encoding='utf-8') as f:
    f.write(''.join(parts))
print(f"Generated RSS with {min(len(items), 60)} items")
