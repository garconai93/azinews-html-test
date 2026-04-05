#!/usr/bin/env python3
"""Update AziNews HTML with news from RSS feeds - WITH HISTORICAL PERSISTENCE"""

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
    ("G4Media", "https://www.g4media.ro/feed"),
]

NEWS_JSON_FILE = "all_news.json"
# MAX_DISPLAY_NEWS = None  # Afișăm TOATE știrile (Varianta A)

def load_existing_news():
    """Load existing news from all_news.json if it exists"""
    if os.path.exists(NEWS_JSON_FILE):
        try:
            with open(NEWS_JSON_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
                if isinstance(data, list):
                    print(f"  📂 Încarc {len(data)} știri existente din JSON")
                    return data
        except Exception as e:
            print(f"  ⚠ Nu am putut încărca {NEWS_JSON_FILE}: {e}")
    return []

def save_all_news(news_list):
    """Save all news to all_news.json"""
    try:
        with open(NEWS_JSON_FILE, 'w', encoding='utf-8') as f:
            json.dump(news_list, f, ensure_ascii=False, indent=2)
        print(f"  💾 Salvate {len(news_list)} știri în {NEWS_JSON_FILE}")
    except Exception as e:
        print(f"  ⚠ Nu am putut salva {NEWS_JSON_FILE}: {e}")

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
                date_str = ""
                if pubdate_elem is not None and pubdate_elem.text:
                    try:
                        pubdate = pubdate_elem.text
                        # Extract time from RFC 2822 format: "Fri, 13 Mar 2026 15:34:11 +0200"
                        time_match = re.search(r'(\d{1,2}:\d{2})', pubdate)
                        if time_match:
                            time_str = time_match.group(1)
                        # Extract date
                        date_match = re.search(r'(\d{1,2})\s+(\w+)\s+(\d{4})', pubdate)
                        if date_match:
                            date_str = f"{date_match.group(1)} {date_match.group(2)}"
                    except:
                        pass
                
                # Get description/content - stop at word boundary, not mid-word
                content_str = ""
                if desc_elem is not None and desc_elem.text:
                    cleaned = re.sub(r'<[^>]+>', '', desc_elem.text).strip()
                    if len(cleaned) > 500:
                        # Find last space before 500 chars
                        cut = cleaned[:500]
                        last_space = cut.rfind(' ')
                        if last_space > 400:
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
                    "date": date_str,
                    "content": content_str,
                    "fetched_at": datetime.now().isoformat()  # Când a fost adăugată
                })
                
    except Exception as e:
        print(f"  ⚠ {source_name}: {e}")
    
    return news

def update_index_html(all_news):
    """Update index.html with mixed news: old in order, new shuffled"""
    from datetime import datetime, timedelta
    
    # Split: old (over 2 hours) vs new (last 2 hours)
    now = datetime.now()
    cutoff = now - timedelta(hours=2)
    
    old_news = []
    new_news = []
    
    for item in all_news:
        try:
            fetched = datetime.fromisoformat(item.get('fetched_at', ''))
            if fetched < cutoff:
                old_news.append(item)
            else:
                new_news.append(item)
        except:
            old_news.append(item)  # If no fetched_at, treat as old
    
    # Old news stay in order, new news get shuffled
    random.shuffle(new_news)
    
    # Combine: old first, then new shuffled
    display_news = old_news + new_news
    
    # Build news array for JavaScript
    news_js = "const news = [\n"
    for item in display_news:
        title_escaped = item['title'].replace('\\', '\\\\').replace('"', '\\"').replace('\n', ' ')
        content_escaped = item.get('content', '').replace('\\', '\\\\').replace('"', '\\"').replace('\n', ' ')
        image = item.get('image', '')
        time_str = item.get('time', '')
        date_str = item.get('date', '')
        
        news_item = f"    {{ source: '{item['source']}', url: '{item['url']}', title: \"{title_escaped}\""
        if image:
            news_item += f', image: "{image}"'
        if time_str:
            news_item += f', time: "{time_str}"'
        if date_str:
            news_item += f', date: "{date_str}"'
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
    
    # Update timestamp and show total count
    total = len(all_news)
    new_content = new_content.replace(
        'Ultimele știri din România',
        f'Ultimele știri din România • {datetime.now().strftime("%d %b %H:%M")} ({total} știri)'
    )
    
    with open('index.html', 'w', encoding='utf-8') as f:
        f.write(new_content)
    
    print(f"✅ Actualizat cu {total} știri în site")

def main():
    print(f"[{datetime.now().strftime('%H:%M')}] Actualizare știri...")
    
    # Load existing news from JSON
    all_news = load_existing_news()
    
    # Fetch new news from RSS feeds
    new_news_by_source = {}
    for name, url in SOURCES:
        print(f"Preia {name}...")
        news = fetch_news(name, url)
        print(f"  -> {len(news)} știri noi")
        new_news_by_source[name] = news
    
    # Add new news to the beginning of the list (most recent first)
    # Build set of existing URLs to avoid duplicates
    existing_urls = set(n['url'] for n in all_news)
    
    # Collect all new news first, then shuffle them before inserting
    new_news_list = []
    
    for name, url in SOURCES:
        if new_news_by_source[name]:
            # Add only news that aren't already in the list
            for news_item in new_news_by_source[name]:
                if news_item['url'] not in existing_urls:
                    new_news_list.append(news_item)
                    existing_urls.add(news_item['url'])
    
    # Shuffle new news so they get mixed from different sources
    random.shuffle(new_news_list)
    
    # Insert shuffled new news at the beginning
    for news_item in new_news_list:
        all_news.insert(0, news_item)
    
    # Report total
    total = len(all_news)
    if total > 0:
        print(f"📰 Total {total} știri în arhivă")
    
    # Save all news to JSON (persistent storage)
    save_all_news(all_news)
    
    # Update index.html with recent news
    if all_news:
        update_index_html(all_news)
    else:
        print("⚠ Nu există știri de afișat!")

if __name__ == "__main__":
    main()
