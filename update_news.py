#!/usr/bin/env python3
"""Update AziNews HTML with news from RSS feeds"""

import requests
import xml.etree.ElementTree as ET
import re
import os
from datetime import datetime
import random

SOURCES = [
    ("Digi24", "https://www.digi24.ro/rss"),
    ("Mediafax", "https://www.mediafax.ro/feed"),
    ("Europa FM", "https://www.europafm.ro/feed/"),
    ("Libertatea", "https://www.libertatea.ro/rss"),
    ("Adevarul", "https://adevarul.ro/rss"),
]

def fetch_news(source_name, url):
    """Fetch news from RSS feed"""
    news = []
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
    
    try:
        r = requests.get(url, headers=headers, timeout=15)
        if r.status_code != 200:
            print(f"  ⚠ {source_name}: HTTP {r.status_code}")
            return news
            
        root = ET.fromstring(r.text)
        
        for item in root.findall('.//item')[:10]:
            title_elem = item.find('title')
            link_elem = item.find('link')
            pubdate_elem = item.find('pubDate')
            enclosure = item.find('enclosure')
            
            image_url = ""
            if enclosure is not None:
                image_url = enclosure.get('url', '')
            
            # Also try media:content
            if not image_url:
                media_content = item.find('.//{http://search.yahoo.com/mrss/}content')
                if media_content is not None:
                    image_url = media_content.get('url', '')
            
            if title_elem is not None and link_elem is not None:
                title = (title_elem.text or "").strip()
                link = (link_elem.text or "").strip()
                
                # Skip empty or very short titles
                if len(title) < 15:
                    continue
                
                # Clean title
                title = re.sub(r'<[^>]+>', '', title)
                
                # Parse time from pubDate
                time_str = ""
                if pubdate_elem is not None and pubdate_elem.text:
                    try:
                        pubdate = pubdate_elem.text
                        # Extract time from RFC 2822 format: "Fri, 13 Mar 2026 15:34:11 +0200"
                        time_match = re.search(r'(\d{1,2}:\d{2})', pubdate)
                        if time_match:
                            time_str = time_match.group(1)
                    except:
                        pass
                
                news.append({
                    "source": source_name,
                    "url": link,
                    "title": title[:150],
                    "image": image_url,
                    "time": time_str
                })
                
    except Exception as e:
        print(f"  ⚠ {source_name}: {e}")
    
    return news

def update_index_html(all_news):
    """Update index.html with new news"""
    # Build news array for JavaScript
    news_js = "const news = [\n"
    for item in all_news:
        title_escaped = item['title'].replace('\\', '\\\\').replace('"', '\\"').replace('\n', ' ')
        image = item.get('image', '')
        time_str = item.get('time', '')
        
        news_item = f"    {{ source: '{item['source']}', url: '{item['url']}', title: \"{title_escaped}\""
        if image:
            news_item += f', image: "{image}"'
        if time_str:
            news_item += f', time: "{time_str}"'
        news_item += " },\n"
        news_js += news_item
    news_js = news_js.rstrip(',\n') + "\n];"
    
    # Read current index.html
    with open('index.html', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Replace existing news array
    pattern = r'const news = \[.*?\];'
    new_content = re.sub(pattern, news_js, content, flags=re.DOTALL)
    
    # Update timestamp
    new_content = new_content.replace(
        'Ultimele știri din România',
        f'Ultimele știri din România • {datetime.now().strftime("%d %b %H:%M")}'
    )
    
    with open('index.html', 'w', encoding='utf-8') as f:
        f.write(new_content)
    
    print(f"✅ Actualizat cu {len(all_news)} știri")

def main():
    print(f"[{datetime.now().strftime('%H:%M')}] Actualizare știri...")
    
    all_news = []
    for name, url in SOURCES:
        print(f"Preia {name}...")
        news = fetch_news(name, url)
        print(f"  -> {len(news)} știri")
        all_news.extend(news)
    
    # Amestecă știrile
    random.shuffle(all_news)
    
    if all_news:
        update_index_html(all_news)
    else:
        print("⚠ Nu s-au găsit știri!")

if __name__ == "__main__":
    main()