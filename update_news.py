#!/usr/bin/env python3
"""AziNews: preia știrile din RSS și le salvează ca fișiere JSON mici.

Structura datelor (tot ce citește site-ul):
  data/latest.json            ultimele LATEST_COUNT știri + lista zilelor din arhivă
  data/archive/YYYY-MM-DD.json  toate știrile unei zile (cele mai noi primele)
  data/search/YYYY-MM.json    index compact pentru căutare: [titlu, sursă, url, zi, oră]

Ziua unei știri = data (ora României) la care a fost preluată.
"""

import html
import json
import os
import random
import re
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime
from zoneinfo import ZoneInfo

import requests

SOURCES = [
    ("Digi24", "https://www.digi24.ro/rss"),
    ("Mediafax", "https://www.mediafax.ro/feed"),
    ("Europa FM", "https://www.europafm.ro/feed/"),
    ("Libertatea", "https://www.libertatea.ro/rss"),
    ("Adevarul", "https://adevarul.ro/rss"),
    ("G4Media", "https://www.g4media.ro/feed"),
]

RO_TZ = ZoneInfo("Europe/Bucharest")
DATA_DIR = "data"
ARCHIVE_DIR = os.path.join(DATA_DIR, "archive")
SEARCH_DIR = os.path.join(DATA_DIR, "search")
LATEST_FILE = os.path.join(DATA_DIR, "latest.json")
LATEST_COUNT = 300
DEDUPE_DAYS = 7  # câte zile în urmă verificăm dacă știrea există deja
ITEMS_PER_FEED = 20

HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; AziNewsBot/2.0; +https://azinews.ro)"}


# ---------- utilitare ----------

def utc_iso(dt):
    return dt.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def day_of(item):
    """Ziua (ora României) în care a fost preluată știrea, ca YYYY-MM-DD."""
    fa = item.get("fetched_at", "")
    try:
        dt = datetime.fromisoformat(fa.replace("Z", "+00:00"))
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(RO_TZ).strftime("%Y-%m-%d")
    except ValueError:
        return datetime.now(RO_TZ).strftime("%Y-%m-%d")


def read_json(path, default):
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return default


def write_json(path, data):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, separators=(",", ":"))
    os.replace(tmp, path)


def archive_path(day):
    return os.path.join(ARCHIVE_DIR, f"{day}.json")


def list_days():
    if not os.path.isdir(ARCHIVE_DIR):
        return []
    return sorted((f[:-5] for f in os.listdir(ARCHIVE_DIR) if f.endswith(".json")), reverse=True)


# resturi pe care unele feed-uri le pun la finalul rezumatului
TRAILING_JUNK = [
    re.compile(r"\s*©\s*[\w.-]+\.ro\.?\s*$", re.I),                    # "© G4Media.ro."
    re.compile(r"\s*The post .{0,300} appeared first on .{0,80}$", re.I),  # WordPress
    re.compile(r"\s*Articolul .{0,300} apare prima dată pe .{0,80}$", re.I),
]


def clean_text(text):
    text = text or ""
    for _ in range(2):  # unele feed-uri codifică de două ori (&amp;#8230;)
        text = html.unescape(text)
    text = re.sub(r"<[^>]+>", "", text)
    text = text.replace("\u00a0", " ")
    text = re.sub(r"\s+", " ", text).strip()
    for rx in TRAILING_JUNK:
        text = rx.sub("", text)
    text = re.sub(r"\s*\[(…|\.\.\.)\]\s*(©.{0,40})?$", "…", text)  # "[…]" (+ © tăiat) de la final -> "…"
    return text.strip()


# ---------- preluare RSS ----------

def fetch_news(source_name, url):
    news = []
    try:
        r = requests.get(url, headers=HEADERS, timeout=15)
        if r.status_code != 200:
            print(f"  ⚠ {source_name}: HTTP {r.status_code}")
            return news
        root = ET.fromstring(r.content)
    except Exception as e:  # rețea sau XML invalid
        print(f"  ⚠ {source_name}: {e}")
        return news

    now = datetime.now(timezone.utc)
    for item in root.findall(".//item")[:ITEMS_PER_FEED]:
        title = clean_text(item.findtext("title"))
        link = (item.findtext("link") or "").strip()
        if len(title) < 15 or not link.startswith("http"):
            continue

        image = ""
        enclosure = item.find("enclosure")
        if enclosure is not None:
            image = enclosure.get("url", "")
        if not image:
            media = item.find(".//{http://search.yahoo.com/mrss/}content")
            if media is not None:
                image = media.get("url", "")

        ts = ""
        time_str = ""
        date_str = ""
        pub = item.findtext("pubDate")
        if pub:
            try:
                pdt = parsedate_to_datetime(pub)
                if pdt.tzinfo is None:
                    pdt = pdt.replace(tzinfo=RO_TZ)
                ts = utc_iso(pdt)
                local = pdt.astimezone(RO_TZ)
                time_str = local.strftime("%H:%M")
                date_str = f"{local.day} {local.strftime('%b')}"
            except (TypeError, ValueError):
                pass

        content = clean_text(item.findtext("description"))
        if len(content) > 500:
            cut = content[:500]
            space = cut.rfind(" ")
            content = (cut[:space] if space > 400 else cut).rstrip(" .,;:…") + "…"

        news.append({
            "source": source_name,
            "url": link,
            "title": title[:200],
            "image": image,
            "time": time_str,
            "date": date_str,
            "ts": ts,
            "content": content,
            "fetched_at": utc_iso(now),
        })
    return news


# ---------- scriere fișiere derivate ----------

def rebuild_latest(days, touched=()):
    items = []
    for day in days:
        items.extend(read_json(archive_path(day), []))
        if len(items) >= LATEST_COUNT:
            break
    # refolosim numărătorile vechi; recitim doar zilele modificate sau necunoscute
    old = {d["d"]: d["n"] for d in read_json(LATEST_FILE, {}).get("days", [])}
    counts = {}
    for day in days:
        if day in touched or day not in old:
            counts[day] = len(read_json(archive_path(day), []))
        else:
            counts[day] = old[day]
    total = sum(counts.values())
    write_json(LATEST_FILE, {
        "updated": utc_iso(datetime.now(timezone.utc)),
        "total": total,
        "days": [{"d": d, "n": counts[d]} for d in days],
        "items": items[:LATEST_COUNT],
    })
    return total


def rebuild_search_month(month, days):
    rows = []
    for day in days:
        if day.startswith(month):
            for n in read_json(archive_path(day), []):
                rows.append([n["title"], n["source"], n["url"], day, n.get("time", "")])
    write_json(os.path.join(SEARCH_DIR, f"{month}.json"), rows)


def main():
    print(f"[{datetime.now(RO_TZ).strftime('%H:%M')}] Actualizare știri...")
    days = list_days()

    seen = set()
    for day in days[:DEDUPE_DAYS]:
        seen.update(n["url"] for n in read_json(archive_path(day), []))

    fresh = []
    for name, url in SOURCES:
        print(f"Preia {name}...")
        items = fetch_news(name, url)
        added = 0
        for n in items:
            if n["url"] not in seen:
                seen.add(n["url"])
                fresh.append(n)
                added += 1
        print(f"  -> {added} știri noi din {len(items)}")

    touched = set()
    if fresh:
        random.shuffle(fresh)  # amestecă sursele în lotul nou
        today = day_of(fresh[0])
        path = archive_path(today)
        write_json(path, fresh + read_json(path, []))
        touched.add(today)
        days = list_days()
        rebuild_search_month(today[:7], days)

    total = rebuild_latest(days, touched)
    print(f"✅ {len(fresh)} știri noi, {total} în arhivă, {len(days)} zile")


if __name__ == "__main__":
    main()
