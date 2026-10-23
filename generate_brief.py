#!/usr/bin/env python3
"""„Pe scurt”: câte o propoziție „de ce contează” pentru primele subiecte ale zilei.

Rulează pe server (GitHub Actions), cu cheia în variabila de mediu GROQ_API_KEY,
ca să nu mai apară în pagina publică. Fără cheie, scriptul nu face nimic și site-ul
arată subiectele fără rezumat.

Scrie data/brief.json: {"updated": ..., "summaries": {id_subiect: "propoziție"}}
"""

import json
import os
import re
from datetime import datetime, timedelta, timezone

import requests

STORIES_FILE = "data/stories.json"
BRIEF_FILE = "data/brief.json"
TOP = 8
REFRESH_HOURS = 3   # regenerăm cel mult o dată la 3 ore, sau când apar subiecte noi în top
MODEL = "openai/gpt-oss-20b"


def load(path, default):
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return default


def main():
    key = os.environ.get("GROQ_API_KEY", "").strip()
    if not key:
        print("GROQ_API_KEY lipsește: sar peste „Pe scurt”.")
        return

    stories = load(STORIES_FILE, {}).get("stories", [])[:TOP]
    if not stories:
        return
    brief = load(BRIEF_FILE, {"summaries": {}})
    old = brief.get("summaries", {})
    missing = [s for s in stories if s["id"] not in old]
    try:
        age = datetime.now(timezone.utc) - datetime.fromisoformat(brief["updated"].replace("Z", "+00:00"))
    except (KeyError, ValueError):
        age = timedelta(days=1)
    if not missing and age < timedelta(hours=REFRESH_HOURS):
        print("„Pe scurt” e la zi.")
        return

    todo = missing if age < timedelta(hours=REFRESH_HOURS) else stories
    blocks = []
    for s in todo:
        heads = "\n".join(f"  - {i['source']}: {i['title']}" for i in s["items"][:5])
        blocks.append(f"[{s['id']}]\n{heads}\n  Rezumat: {s.get('content', '')[:400]}")
    prompt = (
        "Pentru fiecare subiect de mai jos scrie O SINGURĂ propoziție în limba română (maxim 30 de cuvinte) "
        "care explică de ce contează pentru un cititor din România. Folosește DOAR informațiile date, "
        "fără opinii și fără să inventezi. Răspunde STRICT cu un obiect JSON de forma "
        '{"id": "propoziție", ...}, folosind id-urile dintre paranteze drepte.\n\n' + "\n\n".join(blocks)
    )
    r = requests.post(
        "https://api.groq.com/openai/v1/chat/completions",
        headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
        json={
            "model": MODEL,
            "messages": [
                {"role": "system", "content": "Ești redactor la AziNews.ro. Scrii scurt, clar și neutru, în română."},
                {"role": "user", "content": prompt},
            ],
            "temperature": 0.2,
            "max_tokens": 1800,
            "response_format": {"type": "json_object"},
        },
        timeout=60,
    )
    if r.status_code != 200:
        print(f"Groq: HTTP {r.status_code} {r.text[:200]}")
        return
    text = r.json()["choices"][0]["message"].get("content") or ""
    match = re.search(r"\{.*\}", text, re.S)
    try:
        new = json.loads(match.group(0)) if match else {}
    except ValueError:
        new = {}
    ids = {s["id"] for s in stories}
    summaries = {k: v for k, v in old.items() if k in ids}
    summaries.update({k: str(v).strip() for k, v in new.items() if k in ids and str(v).strip()})
    with open(BRIEF_FILE, "w", encoding="utf-8") as f:
        json.dump({"updated": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"), "summaries": summaries},
                  f, ensure_ascii=False, separators=(",", ":"))
    print(f"„Pe scurt”: {len(new)} rezumate noi, {len(summaries)} în total.")


if __name__ == "__main__":
    main()
