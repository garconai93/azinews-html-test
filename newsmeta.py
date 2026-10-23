"""Categorii și gruparea pe subiecte pentru AziNews.

- category_from_url(): categoria din adresa articolului (Digi24, Adevărul, Mediafax, Libertatea)
- Classifier: Naive Bayes pe cuvintele din titlu, antrenat pe știrile care au categorie din URL;
  îl folosim pentru sursele fără categorie în adresă (G4Media, Europa FM, Libertatea /stiri/)
- cluster(): grupează titlurile despre același eveniment din surse diferite
"""

import math
import re
import unicodedata
from collections import Counter, defaultdict
from urllib.parse import urlparse

CATEGORIES = ["politica", "romania", "externe", "economie", "sport", "sanatate", "lifestyle"]

# prefix de cale -> categorie (primul prefix care se potrivește câștigă)
URL_RULES = {
    "Digi24": [
        ("stiri/actualitate/politica", "politica"),
        ("stiri/actualitate/sanatate", "sanatate"),
        ("stiri/actualitate", "romania"),
        ("stiri/externe", "externe"),
        ("stiri/economie", "economie"),
        ("stiri/sport", "sport"),
        ("stiri/sci-tech", "sanatate"),
        ("magazin", "lifestyle"),
    ],
    "Adevarul": [
        ("politica", "politica"),
        ("stiri-externe", "externe"),
        ("stiri-interne", "romania"),
        ("stiri-locale", "romania"),
        ("adevarul-juridic", "romania"),
        ("economie", "economie"),
        ("sport", "sport"),
        ("stil-de-viata/sanatate", "sanatate"),
        ("stil-de-viata", "lifestyle"),
        ("showbiz", "lifestyle"),
        ("dezvoltare-personala", "lifestyle"),
    ],
    "Mediafax": [
        ("politic", "politica"),
        ("externe", "externe"),
        ("social", "romania"),
        ("stirile-zilei", "romania"),
        ("economic", "economie"),
        ("sport", "sport"),
        ("stiinta-sanatate", "sanatate"),
        ("sanatate", "sanatate"),
        ("life-", "lifestyle"),
        ("cultura-media", "lifestyle"),
        ("horoscop", "lifestyle"),
    ],
    "Libertatea": [
        ("lifestyle", "lifestyle"),
        ("entertainment", "lifestyle"),
        ("sport", "sport"),
        ("educatie", "romania"),
    ],
}

STOP = set("""
a ai al ale alea am ar are as asa au azi ca cai care ce cei cel cea cele cine cu cum da de dar daca din
dintre doar dupa e ea ei el este fara fi fie fost iar ii il in inca intr intre isi la le li lui mai mult nu
o or ori pe pentru peste prin s sa sai se si sunt sub ta tot toti un una unei unui unor va vor vrea fata
acum noi nou noua nici doi doua trei ani an anul zi zile ora ore foarte despre spune spus explica cand
unde iata cat cate mare video foto audio live update ultima breaking oficial
""".split())


def norm(text):
    return unicodedata.normalize("NFD", text or "").encode("ascii", "ignore").decode().lower()


def tokens(text):
    """Cuvinte semnificative, trunchiate la 7 litere (rădăcină aproximativă)."""
    return {w[:7] for w in re.findall(r"[a-z0-9]+", norm(text)) if len(w) > 2 and w not in STOP}


def category_from_url(source, url):
    path = urlparse(url).path.strip("/")
    for prefix, cat in URL_RULES.get(source, []):
        if path.startswith(prefix):
            return cat
    return None


class Classifier:
    """Naive Bayes multinomial pe tokenii din titlu + rezumat."""

    def __init__(self):
        self.word = defaultdict(Counter)
        self.docs = Counter()
        self.vocab = set()

    def train(self, items):
        for n in items:
            cat = category_from_url(n["source"], n["url"])
            if not cat:
                continue
            toks = tokens(n["title"] + " " + n.get("content", "")[:200])
            self.docs[cat] += 1
            self.word[cat].update(toks)
            self.vocab |= toks
        return self

    def predict(self, text):
        if not self.docs:
            return "romania"
        toks = tokens(text)
        total = sum(self.docs.values())
        v = len(self.vocab) + 1
        best, best_score = "romania", -math.inf
        for cat, nd in self.docs.items():
            wc = self.word[cat]
            denom = sum(wc.values()) + v
            score = math.log(nd / total) + sum(math.log((wc[t] + 1) / denom) for t in toks)
            if score > best_score:
                best, best_score = cat, score
        return best


def categorize(item, clf):
    return category_from_url(item["source"], item["url"]) or clf.predict(item["title"] + " " + item.get("content", "")[:200])


def cluster(items, min_shared=3, threshold=0.4):
    """Grupează știrile (cele mai noi primele) după cuvintele comune din titlu.

    Două titluri sunt despre același subiect dacă au cel puțin `min_shared` cuvinte
    semnificative comune și acestea reprezintă cel puțin `threshold` din titlul mai scurt.
    """
    groups = []
    for n in items:
        tk = tokens(n["title"])
        if len(tk) < 3:
            groups.append({"tk": tk, "items": [n]})
            continue
        best, best_score = None, 0.0
        for g in groups:
            shared = len(tk & g["tk"])
            if shared < min_shared:
                continue
            score = shared / min(len(tk), len(g["tk"]))
            if score > best_score:
                best, best_score = g, score
        if best is not None and best_score >= threshold:
            best["items"].append(n)
        else:
            groups.append({"tk": tk, "items": [n]})
    return [g["items"] for g in groups]
