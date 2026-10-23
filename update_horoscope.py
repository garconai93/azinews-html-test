#!/usr/bin/env python3
"""
AziNews Horoscop Generator
Generează horoscop zilnic diferit pentru fiecare zodie
"""
import json
import random
import sys
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

RO_TZ = ZoneInfo("Europe/Bucharest")
OUT = Path(__file__).parent / "data" / "horoscope.json"

# Mesaje pentru fiecare zodie (vor fi amestecate zilnic)
HOROSCOPE_MESSAGES = {
    "Berbec": [
        "Zi perfectă pentru inițiative noi",
        "Energie maximă, profită de ea",
        "Momente favorabile în relații",
        "Succes în proiectele personale",
        "Oportunități profesionale"
    ],
    "Taur": [
        "Stabilitate financiară",
        "Zi de relaxare și reflecție",
        "Conexiuni emoționale puternice",
        "Progrese în carieră",
        "Armonie în familie"
    ],
    "Gemeni": [
        "Zi dinamică și interesantă",
        "Comunicare excelentă",
        "Inspirație creativă",
        "Noi cunoștințe valoroase",
        "Flexibilitate și adaptabilitate"
    ],
    "Rac": [
        "Timp prețios cu familia",
        "Intuiție puternică",
        "Emoții profunde",
        "Protecție și siguranță",
        "Sentimente reciproce"
    ],
    "Leu": [
        "Strălucești în orice situație",
        "Atenție din partea celorlalți",
        "Creativitate debordantă",
        "Leadership natural",
        "Succes în afaceri"
    ],
    "Fecioară": [
        "Sănătate și bunăstare",
        "Atenție la detalii",
        "Organizare impecabilă",
        "Analiză profundă",
        "Perfecțiune în lucruri"
    ],
    "Balanță": [
        "Echilibru în toate",
        "Relații armonioase",
        "Justiție și fair-play",
        "Frumusețe și artă",
        "Diplomație excelentă"
    ],
    "Scorpion": [
        "Putere și determinare",
        "Transformări pozitive",
        "Mister și charisma",
        "Intensitate emoțională",
        "Descoperiri importante"
    ],
    "Săgetător": [
        "Aventură și explorare",
        "Optimism exploziv",
        "Călătorii benefice",
        "Filozofie de viață",
        "Libertate personală"
    ],
    "Capricorn": [
        "Responsabilitate și disciplină",
        "Obiective clare",
        "Țintește sus",
        "Disciplină de fier",
        "Succes garantat"
    ],
    "Vărsător": [
        "Inovație și originalitate",
        "Gândire unică",
        "Schimbări benefice",
        "Comunitate și prietenie",
        "Viitor luminos"
    ],
    "Pești": [
        "Creativitate artistică",
        "Intuiție spirituală",
        "Visatori romantici",
        "Compasiune profundă",
        "Lume interioară bogată"
    ]
}

def get_daily_horoscope():
    """Generează horoscop zilnic bazat pe ziua lunii"""
    today = datetime.now(RO_TZ)
    day_of_month = today.day
    month = today.month
    
    # Seed pentru random bazat pe ziua lunii
    seed = day_of_month * 100 + month
    random.seed(seed)
    
    horoscope = []
    signs = list(HOROSCOPE_MESSAGES.keys())
    random.shuffle(signs)
    
    for i, sign in enumerate(signs):
        messages = HOROSCOPE_MESSAGES[sign]
        # Alege un mesaj diferit în fiecare zi
        msg_index = (day_of_month + i) % len(messages)
        horoscope.append({
            "sign": sign,
            "msg": messages[msg_index]
        })
    
    # Resetează random seed-ul
    random.seed()
    
    return horoscope

def update_json(horoscope):
    """Scrie horoscopul în data/horoscope.json (citit de index.html)"""
    OUT.parent.mkdir(exist_ok=True)
    OUT.write_text(json.dumps({"date": datetime.now(RO_TZ).strftime('%Y-%m-%d'), "items": horoscope},
                              ensure_ascii=False, indent=1), encoding='utf-8')
    print(f"Horoscop actualizat pentru {datetime.now(RO_TZ).strftime('%d-%m-%Y')}")


def main():
    # --if-new-day: rulează doar dacă horoscopul nu e deja de azi (folosit de actualizarea orară)
    if "--if-new-day" in sys.argv:
        try:
            if json.loads(OUT.read_text(encoding="utf-8")).get("date") == datetime.now(RO_TZ).strftime('%Y-%m-%d'):
                print("Horoscopul e deja de azi.")
                return
        except (OSError, ValueError):
            pass
    print(f"Horoscop Generator - {datetime.now(RO_TZ)}")
    horoscope = get_daily_horoscope()
    
    print("\nHoroscop zilnic:")
    for h in horoscope:
        print(f"  {h['sign']}: {h['msg']}")
    
    update_json(horoscope)
    print("\nGata!")

if __name__ == "__main__":
    main()
