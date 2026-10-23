#!/usr/bin/env python3
"""Cursul valutar pentru AziNews -> data/fx.json

Sursa principală: cursul oficial BNR (ultimele 10 zile, ca să avem și variația față de ziua anterioară).
Rezervă: cursul de referință BCE (frankfurter.dev), dacă BNR nu răspunde.

Format: {"source": "BNR", "date": "2026-10-22", "rates": {"EUR": {"v": 5.345, "prev": 5.3365}, ...}}
Valoarea e în lei pentru o unitate (HUF: pentru 100 de forinți, ca la BNR).
"""

import json
import os
import xml.etree.ElementTree as ET
from datetime import date, timedelta

import requests

OUT = os.path.join("data", "fx.json")
CURRENCIES = ["EUR", "USD", "GBP", "CHF", "HUF", "PLN", "CZK", "TRY", "MDL"]
PER_100 = {"HUF"}
HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; AziNewsBot/2.0; +https://azinews.ro)"}


def from_bnr():
    r = requests.get("https://www.bnr.ro/nbrfxrates10days.xml", headers=HEADERS, timeout=20)
    r.raise_for_status()
    root = ET.fromstring(r.content)
    ns = {"b": "http://www.bnr.ro/xsd"}
    days = []
    for cube in root.findall(".//b:Cube", ns):
        rates = {}
        for rate in cube.findall("b:Rate", ns):
            cur = rate.get("currency")
            mult = int(rate.get("multiplier", "1"))
            value = float(rate.text) / mult
            rates[cur] = value * (100 if cur in PER_100 else 1)
        days.append((cube.get("date"), rates))
    days.sort()
    if len(days) < 2:
        raise ValueError("BNR: prea puține zile")
    return "BNR", days


def from_ecb():
    start = (date.today() - timedelta(days=12)).isoformat()
    syms = ",".join(c for c in CURRENCIES if c != "EUR" and c != "MDL") + ",RON"
    r = requests.get(f"https://api.frankfurter.dev/v1/{start}..?base=EUR&symbols={syms}", timeout=20)
    r.raise_for_status()
    days = []
    for d, rates in sorted(r.json()["rates"].items()):
        ron = rates["RON"]
        out = {"EUR": ron}
        for cur, v in rates.items():
            if cur != "RON":
                out[cur] = ron / v * (100 if cur in PER_100 else 1)
        days.append((d, out))
    return "BCE", days


def main():
    for fetch in (from_bnr, from_ecb):
        try:
            source, days = fetch()
            break
        except Exception as e:  # rețea, blocare, format schimbat
            print(f"  ⚠ {fetch.__name__}: {e}")
    else:
        print("Curs valutar indisponibil; păstrez fișierul vechi.")
        return

    (last_date, last), (_, prev) = days[-1], days[-2]
    data = {
        "source": source,
        "date": last_date,
        "rates": {c: {"v": round(last[c], 4), "prev": round(prev.get(c, last[c]), 4)}
                  for c in CURRENCIES if c in last},
        "history": {c: [round(r[c], 4) for _, r in days[-7:] if c in r] for c in ("EUR", "USD")},
    }
    os.makedirs("data", exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(data, f, separators=(",", ":"))
    eur = data["rates"]["EUR"]
    print(f"✅ Curs {source} {last_date}: EUR {eur['v']} (ieri {eur['prev']})")


if __name__ == "__main__":
    main()
