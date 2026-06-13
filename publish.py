#!/usr/bin/env python3
"""
publish.py — Fusionne de nouveaux articles dans articles.js (site TechFeed).
La tâche planifiée rédige les articles (recherche + vérif multi-sources + corps
300-500 mots) et les fournit en JSON minimal ; ce script gère tout le formatage
déterministe : slug id, catLabel, reliability, readTime, image de repli, date,
dédoublonnage (par id et url) et cumul sans limite (nouveaux en tête).

Usage: python3 publish.py new_articles.json
Champs par objet: cat, title, excerpt, body (HTML), url, source, verifiedSources
(requis) ; image, sources (optionnels).
"""
import sys, json, re, hashlib, unicodedata, os
from datetime import datetime, timezone
try:
    from zoneinfo import ZoneInfo
except ImportError:
    from backports.zoneinfo import ZoneInfo

ARTICLES_JS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "articles.js")
CAT_LABELS = {"ia":"IA & Tech","crypto":"Crypto","gaming":"Jeux Vidéo","markets":"Marchés","general":"Général"}

def slugify(title):
    t = unicodedata.normalize("NFKD", title).encode("ascii","ignore").decode("ascii").lower()
    t = re.sub(r"[^a-z0-9]+","-",t).strip("-")
    return t[:60].rstrip("-") or hashlib.md5(title.encode()).hexdigest()[:10]

def reliability_for(n):
    return ("strong","✓ Consensus fort") if n>=2 else ("moderate","~ Source unique")

def read_time(body):
    w = len(re.sub(r"<[^>]+>"," ",body or "").split())
    return f"{max(1,round(w/200))} min"

def picsum(title):
    return f"https://picsum.photos/seed/{hashlib.md5(title.encode()).hexdigest()[:10]}/640/360"

def load_existing():
    if not os.path.exists(ARTICLES_JS): return []
    m = re.search(r"window\.ARTICLES\s*=\s*(\[.*\]);?\s*$", open(ARTICLES_JS,encoding="utf-8").read(), re.S)
    return json.loads(m.group(1)) if m else []

def main():
    if len(sys.argv)<2:
        print("usage: publish.py new_articles.json",file=sys.stderr); sys.exit(1)
    new_raw = json.load(open(sys.argv[1],encoding="utf-8"))
    existing = load_existing()
    seen_ids = {a.get("id") for a in existing}
    seen_urls = {a.get("url") for a in existing}
    now = datetime.now(ZoneInfo("Europe/Paris"))
    date_str = now.strftime("%d %b %Y, %H:%M"); pub_ts = int(now.timestamp())
    built = []
    for raw in new_raw:
        title = raw["title"].strip(); url = raw.get("url","").strip(); aid = slugify(title)
        if aid in seen_ids or (url and url in seen_urls): continue
        seen_ids.add(aid); seen_urls.add(url)
        n = int(raw.get("verifiedSources",1)); rel,rel_label = reliability_for(n)
        built.append({
            "id":aid,"cat":raw["cat"],"catLabel":CAT_LABELS.get(raw["cat"],"Général"),
            "title":title,"excerpt":raw["excerpt"].strip(),"body":raw["body"].strip(),
            "image":raw.get("image") or picsum(title),"url":url,"source":raw.get("source","").strip(),
            "date":date_str,"pubTs":pub_ts,"readTime":read_time(raw["body"]),
            "reliability":rel,"reliabilityLabel":rel_label,"verifiedSources":n,
            "sources":raw.get("sources",[]),
        })
    merged = built + existing
    with open(ARTICLES_JS,"w",encoding="utf-8") as f:
        f.write("// Données des articles — régénéré automatiquement par la tâche planifiée Cowork.\n")
        f.write("// Chaque article contient un champ \"body\" (HTML, vrai article 300-500 mots).\n")
        f.write("window.ARTICLES = "+json.dumps(merged,ensure_ascii=False)+";\n")
    print(f"Ajoutés: {len(built)} | total: {len(merged)}")

if __name__ == "__main__":
    main()
