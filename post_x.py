#!/usr/bin/env python3
"""
AziNews X Poster - Extrage știri și le formatează pentru X/Twitter
"""
import os
import re
import sys

NEWS_FILE = "/home/elitedesk/.openclaw/workspace/AziNews-HTML/index.html"

def extract_news():
    """Citește ultimele știri din data/latest.json"""
    import json
    path = os.path.join(os.path.dirname(NEWS_FILE), "data", "latest.json")
    try:
        with open(path, 'r', encoding='utf-8') as f:
            items = json.load(f).get('items', [])
    except (OSError, ValueError):
        return []
    return [{'title': n['title'], 'source': n['source'], 'url': n['url']} for n in items]

def format_for_x(news_item, max_length=280):
    """Formatează știrea pentru X"""
    title = news_item['title']
    source = news_item['source']
    url = news_item['url']
    
    # Scurtează titlul dacă e prea lung
    if len(title) > 180:
        title = title[:177] + "..."
    
    post = f"{title}\n\n📰 Sursa: {source}\n🔗 {url}\n\n🌐 azinews.ro"
    
    # Verifică lungimea
    if len(post) > max_length:
        # Reduce și mai mult
        while len(post) > max_length and len(title) > 100:
            title = title[:-10] + "..."
            post = f"{title}\n\n📰 Sursa: {source}\n🔗 {url}\n\n🌐 azinews.ro"
    
    return post

def main():
    news_items = extract_news()
    
    if not news_items:
        print("❌ Nu s-au găsit știri!")
        sys.exit(1)
    
    print(f"✅ Găsite {len(news_items)} știri")
    
    # Alege prima (cea mai recentă)
    news_item = news_items[0]
    
    post = format_for_x(news_item)
    
    print("=" * 50)
    print("🦞 AZINEWS X POST DRAFT")
    print("=" * 50)
    print()
    print(post)
    print()
    print("=" * 50)
    print(f"Caractere: {len(post)}/{280}")
    print("=" * 50)
    
    # Salvează într-un fișier pentru posting
    with open("/home/elitedesk/.openclaw/workspace/AziNews-HTML/x_post.txt", "w", encoding='utf-8') as f:
        f.write(post)
    
    print("\n✅ Draft salvat în x_post.txt")

if __name__ == "__main__":
    main()
