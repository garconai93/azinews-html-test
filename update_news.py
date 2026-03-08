#!/usr/bin/env python3
"""
AziNews Auto-Updater
Extrage știri de pe Digi24, Mediafax, Europa FM, Libertatea, Adevărul
"""
import json
import re
import os
from datetime import datetime, timedelta
from pathlib import Path
from email.utils import parsedate_to_datetime

HTML_FILE = Path(__file__).parent / "index.html"

def parse_rss_time(pub_date_str):
    """Parsează data din RSS și o convertește în format 'acum X'"""
    if not pub_date_str:
        return "Acum"
    
    try:
        # Încearcă să parsezi data RSS
        pub_date = parsedate_to_datetime(pub_date_str)
        now = datetime.now(pub_date.tzinfo) if pub_date.tzinfo else datetime.now()
        
        diff = now - pub_date
        minutes = diff.total_seconds() / 60
        hours = minutes / 60
        days = hours / 24
        
        if minutes < 1:
            return "Acum"
        elif minutes < 60:
            mins = int(minutes)
            return f"acum {mins} min"
        elif hours < 24:
            hrs = int(hours)
            return f"acum {hrs} oră" if hrs == 1 else f"acum {hrs} ore"
        elif days < 7:
            zile = int(days)
            return f"acum {zile} zi" if zile == 1 else f"acum {zile} zile"
        else:
            return pub_date.strftime("%d %b")
    except Exception:
        return "Acum"

def fetch_digi24_news():
    """Preia știri de pe Digi24 RSS"""
    news = []
    try:
        import urllib.request
        url = "https://www.digi24.ro/rss"
        with urllib.request.urlopen(url, timeout=15) as response:
            content = response.read().decode('utf-8')
        
        items = re.findall(r'<item>(.*?)</item>', content, re.DOTALL)
        for item in items[:8]:
            title_match = re.search(r'<title><!\[CDATA\[(.*?)\]\]></title>', item)
            if not title_match:
                title_match = re.search(r'<title>(.*?)</title>', item)
            
            link_match = re.search(r'<link>(.*?)</link>', item)
            desc_match = re.search(r'<description><!\[CDATA\[(.*?)\]\]></description>', item)
            if not desc_match:
                desc_match = re.search(r'<description>(.*?)</description>', item)
            
            img_match = re.search(r'<media:content[^>]*url="([^"]+)"', item)
            if not img_match:
                img_match = re.search(r'<enclosure[^>]*url="([^"]+)"', item)
            
            # Extrage data publicării
            pubdate_match = re.search(r'<pubDate>(.*?)</pubDate>', item)
            pubdate = pubdate_match.group(1).strip() if pubdate_match else ""
            news_time = parse_rss_time(pubdate)
            
            if title_match and link_match:
                title = title_match.group(1).strip()
                link = link_match.group(1).strip()
                desc = desc_match.group(1).strip() if desc_match else ""
                desc = re.sub(r'<[^>]+>', '', desc)[:200]
                img = img_match.group(1) if img_match else ""
                
                news.append({
                    "source": "Digi24",
                    "url": link,
                    "title": title,
                    "image": img,
                    "content": desc,
                    "time": news_time
                })
    except Exception as e:
        print(f"Eroare Digi24: {e}")
    return news

def fetch_mediafax_news():
    """Preia știri de pe Mediafax RSS"""
    news = []
    try:
        import urllib.request
        url = "https://www.mediafax.ro/rss"
        
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=15) as response:
            content = response.read().decode('utf-8')
        
        items = re.findall(r'<item>(.*?)</item>', content, re.DOTALL)
        for item in items[:8]:
            title_match = re.search(r'<title><!\[CDATA\[(.*?)\]\]></title>', item)
            if not title_match:
                title_match = re.search(r'<title>(.*?)</title>', item)
            
            link_match = re.search(r'<link>(.*?)</link>', item)
            desc_match = re.search(r'<description><!\[CDATA\[(.*?)\]\]></description>', item)
            if not desc_match:
                desc_match = re.search(r'<description>(.*?)</description>', item)
            
            img_match = re.search(r'<media:content[^>]*url="([^"]+)"', item)
            if not img_match:
                img_match = re.search(r'<enclosure[^>]*url="([^"]+)"', item)
            
            # Extrage data publicării
            pubdate_match = re.search(r'<pubDate>(.*?)</pubDate>', item)
            pubdate = pubdate_match.group(1).strip() if pubdate_match else ""
            news_time = parse_rss_time(pubdate)
            
            if title_match and link_match:
                title = title_match.group(1).strip()
                link = link_match.group(1).strip()
                desc = desc_match.group(1).strip() if desc_match else ""
                desc = re.sub(r'<[^>]+>', '', desc)[:200]
                img = img_match.group(1) if img_match else ""
                
                news.append({
                    "source": "Mediafax",
                    "url": link,
                    "title": title,
                    "image": img,
                    "content": desc,
                    "time": news_time
                })
    except Exception as e:
        print(f"Eroare Mediafax: {e}")
    return news

def fetch_europafm_news():
    """Preia știri de pe Europa FM RSS"""
    news = []
    try:
        import urllib.request
        url = "https://www.europafm.ro/feed/"
        
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=15) as response:
            content = response.read().decode('utf-8')
        
        items = re.findall(r'<item>(.*?)</item>', content, re.DOTALL)
        for item in items[:8]:
            title_match = re.search(r'<title><!\[CDATA\[(.*?)\]\]></title>', item)
            if not title_match:
                title_match = re.search(r'<title>(.*?)</title>', item)
            
            link_match = re.search(r'<link>(.*?)</link>', item)
            desc_match = re.search(r'<description><!\[CDATA\[(.*?)\]\]></description>', item)
            if not desc_match:
                desc_match = re.search(r'<description>(.*?)</description>', item)
            
            img_match = re.search(r'<media:content[^>]*url="([^"]+)"', item)
            if not img_match:
                img_match = re.search(r'<enclosure[^>]*url="([^"]+)"', item)
            
            # Extrage data publicării
            pubdate_match = re.search(r'<pubDate>(.*?)</pubDate>', item)
            pubdate = pubdate_match.group(1).strip() if pubdate_match else ""
            news_time = parse_rss_time(pubdate)
            
            if title_match and link_match:
                title = title_match.group(1).strip()
                link = link_match.group(1).strip()
                desc = desc_match.group(1).strip() if desc_match else ""
                desc = re.sub(r'<[^>]+>', '', desc)[:200]
                img = img_match.group(1) if img_match else ""
                
                news.append({
                    "source": "Europa FM",
                    "url": link,
                    "title": title,
                    "image": img,
                    "content": desc,
                    "time": news_time
                })
    except Exception as e:
        print(f"Eroare Europa FM: {e}")
    return news

def fetch_libertatea_news():
    """Preia știri de pe Libertatea RSS"""
    news = []
    try:
        import urllib.request
        url = "https://www.libertatea.ro/rss"
        
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=15) as response:
            content = response.read().decode('utf-8')
        
        items = re.findall(r'<item>(.*?)</item>', content, re.DOTALL)
        for item in items[:8]:
            title_match = re.search(r'<title><!\[CDATA\[(.*?)\]\]></title>', item)
            if not title_match:
                title_match = re.search(r'<title>(.*?)</title>', item)
            
            link_match = re.search(r'<link>(.*?)</link>', item)
            desc_match = re.search(r'<description><!\[CDATA\[(.*?)\]\]></description>', item)
            if not desc_match:
                desc_match = re.search(r'<description>(.*?)</description>', item)
            
            img_match = re.search(r'<enclosure[^>]*url="([^"]+)"', item)
            
            # Extrage data publicării
            pubdate_match = re.search(r'<pubDate>(.*?)</pubDate>', item)
            pubdate = pubdate_match.group(1).strip() if pubdate_match else ""
            news_time = parse_rss_time(pubdate)
            
            if title_match and link_match:
                title = title_match.group(1).strip()
                link = link_match.group(1).strip()
                desc = desc_match.group(1).strip() if desc_match else ""
                desc = re.sub(r'<[^>]+>', '', desc)[:200]
                img = img_match.group(1) if img_match else ""
                
                news.append({
                    "source": "Libertatea",
                    "url": link,
                    "title": title,
                    "image": img,
                    "content": desc,
                    "time": news_time
                })
    except Exception as e:
        print(f"Eroare Libertatea: {e}")
    return news

def fetch_adevarul_news():
    """Preia știri de pe Adevărul RSS"""
    news = []
    try:
        import urllib.request
        url = "https://www.adevarul.ro/rss"
        
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=15) as response:
            content = response.read().decode('utf-8')
        
        items = re.findall(r'<item>(.*?)</item>', content, re.DOTALL)
        for item in items[:8]:
            title_match = re.search(r'<title><!\[CDATA\[(.*?)\]\]></title>', item)
            if not title_match:
                title_match = re.search(r'<title>(.*?)</title>', item)
            
            link_match = re.search(r'<link>(.*?)</link>', item)
            desc_match = re.search(r'<description><!\[CDATA\[(.*?)\]\]></description>', item)
            if not desc_match:
                desc_match = re.search(r'<description>(.*?)</description>', item)
            
            img_match = re.search(r'<enclosure[^>]*url="([^"]+)"', item)
            
            # Extrage data publicării
            pubdate_match = re.search(r'<pubDate>(.*?)</pubDate>', item)
            pubdate = pubdate_match.group(1).strip() if pubdate_match else ""
            news_time = parse_rss_time(pubdate)
            
            if title_match and link_match:
                title = title_match.group(1).strip()
                link = link_match.group(1).strip()
                desc = desc_match.group(1).strip() if desc_match else ""
                desc = re.sub(r'<[^>]+>', '', desc)[:200]
                img = img_match.group(1) if img_match else ""
                
                news.append({
                    "source": "Adevărul",
                    "url": link,
                    "title": title,
                    "image": img,
                    "content": desc,
                    "time": news_time
                })
    except Exception as e:
        print(f"Eroare Adevărul: {e}")
    return news

def update_html(news_list):
    """Actualizează index.html cu noile știri"""
    if not HTML_FILE.exists():
        print("Nu am găsit index.html!")
        return False
    
    html_content = HTML_FILE.read_text(encoding='utf-8')
    
    news_js = "const news = [\n"
    for n in news_list:
        img = n.get('image', '') or ''
        title = n['title'].replace('\\', '\\\\').replace('"', '\\"').replace('\n', ' ')
        content = n.get('content', '').replace('\\', '\\\\').replace('"', '\\"').replace('\n', ' ')
        news_js += f'''    {{ source: '{n["source"]}', url: '{n["url"]}', title: "{title}", image: '{img}', content: "{content}", time: '{n["time"]}' }},\n'''
    news_js += "];"
    
    pattern = r'const news = \[.*?\];'
    html_content = re.sub(pattern, news_js, html_content, flags=re.DOTALL)
    
    HTML_FILE.write_text(html_content, encoding='utf-8')
    print(f"Actualizat cu {len(news_list)} știri!")
    return True

def git_push():
    """Face commit și push la GitHub"""
    import subprocess
    try:
        subprocess.run(["git", "config", "--global", "credential.helper", "!gh auth git-credential"], check=False)
        
        subprocess.run(["git", "add", "index.html"], check=True)
        subprocess.run(["git", "commit", "-m", f"Auto-update: {datetime.now().strftime('%Y-%m-%d %H:%M')}"], check=True)
        subprocess.run(["git", "push"], check=True)
        print("Push la GitHub făcut!")
        
        cloudflare_purge("azinews.ro")
        
        return True
    except Exception as e:
        print(f"Eroare git: {e}")
        return False

def cloudflare_purge(domain):
    """Purge cache Cloudflare"""
    import urllib.request
    import json
    import os
    
    cf_email = os.environ.get('CF_EMAIL', '')
    cf_api_key = os.environ.get('CF_API_KEY', '')
    
    zone_ids = {
        'azinews.ro': os.environ.get('CF_ZONE_ID_azinews', ''),
        'flacarafood.ro': os.environ.get('CF_ZONE_ID_flacarafood', '')
    }
    
    if not cf_api_key or not cf_email:
        print("⚠️ Cloudflare API keys not set. Skipping cache purge.")
        return
    
    zone_id = zone_ids.get(domain)
    if not zone_id:
        print(f"Nu am găsit Zone ID pentru {domain}")
        return
    
    url = f"https://api.cloudflare.com/client/v4/zones/{zone_id}/purge_cache"
    data = json.dumps({"purge_everything": True}).encode('utf-8')
    
    req = urllib.request.Request(url, data=data, method='POST')
    req.add_header('X-Auth-Email', cf_email)
    req.add_header('X-Auth-Key', cf_api_key)
    req.add_header('Content-Type', 'application/json')
    
    try:
        with urllib.request.urlopen(req, timeout=10) as response:
            result = json.loads(response.read().decode())
            if result.get('success'):
                print(f"✓ Cache purjat pentru {domain}")
            else:
                print(f"Eroare Cloudflare: {result}")
    except Exception as e:
        print(f"Eroare la purge cache: {e}")

def main():
    print(f"AziNews Updater - {datetime.now()}")
    
    print("Preiau știri de pe Digi24...")
    digi_news = fetch_digi24_news()
    print(f"  -> {len(digi_news)} știri Digi24")
    
    print("Preiau știri de pe Mediafax...")
    mediafax_news = fetch_mediafax_news()
    print(f"  -> {len(mediafax_news)} știri Mediafax")
    
    print("Preiau știri de pe Europa FM...")
    europafm_news = fetch_europafm_news()
    print(f"  -> {len(europafm_news)} știri Europa FM")
    
    print("Preiau știri de pe Libertatea...")
    libertatea_news = fetch_libertatea_news()
    print(f"  -> {len(libertatea_news)} știri Libertatea")
    
    print("Preiau știri de pe Adevărul...")
    adevarul_news = fetch_adevarul_news()
    print(f"  -> {len(adevarul_news)} știri Adevărul")
    
    # Combină (5 surse x 8 = 40 total)
    all_news = (digi_news[:8] + mediafax_news[:8] + europafm_news[:8] + libertatea_news[:8] + adevarul_news[:8])[:40]
    
    import random
    random.shuffle(all_news)
    
    if all_news:
        print(f"Total: {len(all_news)} știri")
        update_html(all_news)
        git_push()
    else:
        print("Nu am putut prelua știri!")

if __name__ == "__main__":
    main()
