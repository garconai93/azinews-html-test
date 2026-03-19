#!/usr/bin/env python3
"""Update AziNews HTML with news from RSS feeds"""

import requests
import xml.etree.ElementTree as ET
import re
import os
import json
from datetime import datetime
import random

SOURCES = [
    ("Digi24", "https://www.digi24.ro/rss"),
    ("Mediafax", "https://www.mediafax.ro/feed"),
    ("Europa FM", "https://www.europafm.ro/feed/"),
    ("Libertatea", "https://www.libertatea.ro/rss"),
    ("Adevarul", "https://adevarul.ro/rss"),
]

def extract_existing_news():
    """Extract existing news from index.html to use as fallback"""
    existing = {name: [] for name, _ in SOURCES}
    try:
        with open('index.html', 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Find news array
        import re
        match = re.search(r'const news = \[(.*?)\];', content, re.DOTALL)
        if not match:
            return existing
        
        # Simple regex to parse news items - extract all fields
        news_text = match.group(1)
        
        # Match each news item with all fields
        item_pattern = r"\{ source: '([^']+)', url: '([^']+)', title: \"([^\"]+)\"(?:, image: \"([^\"]+)\")?(?:, time: \"([^\"]+)\")?(?:, content: \"([^\"]+)\")? \}"
        for m in re.finditer(item_pattern, news_text):
            source = m.group(1)
            if source in existing:
                news_item = {
                    'source': source,
                    'url': m.group(2),
                    'title': m.group(3)
                }
                # Add optional fields if they exist
                if m.group(4):  # image
                    news_item['image'] = m.group(4)
                if m.group(5):  # time
                    news_item['time'] = m.group(5)
                if m.group(6):  # content
                    news_item['content'] = m.group(6)
                existing[source].append(news_item)
    except Exception as e:
        print(f"  ⚠ Nu am putut extrage știrile existente: {e}")
    
    return existing

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
            desc_elem = item.find('description')
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
                
                # Get description/content - stop at word boundary, not mid-word
                content_str = ""
                if desc_elem is not None and desc_elem.text:
                    cleaned = re.sub(r'<[^>]+>', '', desc_elem.text).strip()
                    if len(cleaned) > 150:
                        # Find last space before 150 chars
                        cut = cleaned[:150]
                        last_space = cut.rfind(' ')
                        if last_space > 100:
                            content_str = cut[:last_space] + "..."
                        else:
                            content_str = cut + "..."
                    else:
                        content_str = cleaned
                
                news.append({
                    "source": source_name,
                    "url": link,
                    "title": title[:150],
                    "image": image_url,
                    "time": time_str,
                    "content": content_str
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
        content_escaped = item.get('content', '').replace('\\', '\\\\').replace('"', '\\"').replace('\n', ' ')
        image = item.get('image', '')
        time_str = item.get('time', '')
        
        news_item = f"    {{ source: '{item['source']}', url: '{item['url']}', title: \"{title_escaped}\""
        if image:
            news_item += f', image: "{image}"'
        if time_str:
            news_item += f', time: "{time_str}"'
        if content_escaped:
            news_item += f', content: "{content_escaped}"'
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
    
    # Extrage știrile existente pentru fallback
    existing_news = extract_existing_news()
    
    all_news = []
    for name, url in SOURCES:
        print(f"Preia {name}...")
        news = fetch_news(name, url)
        print(f"  -> {len(news)} știri")
        
        # Fallback la știrile vechi dacă nu s-au găsit știri noi
        if len(news) == 0 and len(existing_news.get(name, [])) > 0:
            print(f"  ⚠ Folosesc {len(existing_news[name])} știri vechi pentru {name}")
            news = existing_news[name]
        
        all_news.extend(news)
    
    # Amestecă știrile
    random.shuffle(all_news)
    
    if all_news:
        update_index_html(all_news)
    else:
        print("⚠ Nu s-au găsit știri!")

if __name__ == "__main__":
    main()