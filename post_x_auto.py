#!/usr/bin/env python3
"""
AziNews X Poster - Nu posta aceeasi stire de doua ori
"""
import re
import json
import os

NEWS_FILE = "/home/elitedesk/.openclaw/workspace/AziNews-HTML/index.html"
HISTORY_FILE = "/home/elitedesk/.openclaw/workspace/AziNews-HTML/x_posted.json"

def load_history():
    """Încarcă istoricul postărilor"""
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, 'r') as f:
            return json.load(f)
    return []

def save_history(posted_urls):
    """Salvează istoricul postărilor"""
    with open(HISTORY_FILE, 'w') as f:
        json.dump(posted_urls, f)

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

def get_new_news(news_items, history):
    """Returnează știri care nu au fost postate încă"""
    posted_urls = set(history)
    available = [n for n in news_items if n['url'] not in posted_urls]
    return available

def format_for_x(news_item, max_length=280):
    """Formatează știrea pentru X"""
    title = news_item['title']
    source = news_item['source']
    url = news_item['url']
    
    if len(title) > 180:
        title = title[:177] + "..."
    
    post = f"{title}\n\n📰 Sursa: {source}\n🔗 {url}\n\n🌐 azinews.ro"
    
    if len(post) > max_length:
        while len(post) > max_length and len(title) > 100:
            title = title[:-10] + "..."
            post = f"{title}\n\n📰 Sursa: {source}\n🔗 {url}\n\n🌐 azinews.ro"
    
    return post

def main():
    news_items = extract_news()
    history = load_history()
    
    available = get_new_news(news_items, history)
    
    if not available:
        print("❌ Toate știrile au fost postate! Resetez istoricul...")
        history = []
        available = news_items[:5]
    
    # Alege random una din cele disponibile
    import random
    news_item = random.choice(available[:5])
    
    post = format_for_x(news_item)
    
    print("=" * 50)
    print("🦞 AZINEWS X AUTO POST")
    print("=" * 50)
    print()
    print(post)
    print()
    print("=" * 50)
    print(f"Caractere: {len(post)}/{280}")
    print("=" * 50)
    
    # Salvează postarea
    with open("/home/elitedesk/.openclaw/workspace/AziNews-HTML/x_post.txt", "w", encoding='utf-8') as f:
        f.write(post)
    
    # Adaugă la istoric
    history.append(news_item['url'])
    save_history(history[-50:])  # Păstrează ultimele 50
    
    print(f"\n✅ Salvat în x_post.txt")
    print(f"📜 Istoric: {len(history)} știri postate")

if __name__ == "__main__":
    main()
