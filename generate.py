#!/usr/bin/env python3
"""
TechFeed — Générateur automatique de news (v2)
- Récupère les flux RSS via requests + feedparser
- Traduit les titres/résumés en français via MyMemory (avec retry)
- Ne traduit PAS les sources francophones (Le Monde, France Info, BFM, Les Echos)
- Extraction d'images : RSS → og:image → Pollinations.ai (fallback thématique)
- Ingestion des articles premium depuis new_articles.json (body HTML complet)
- Génère un site HTML avec design responsive, bookmarks, panneau latéral
"""

import feedparser
import json
import html
import re
import hashlib
import urllib.parse
import time
import calendar
import os
import requests
from datetime import datetime, timezone
import sys
sys.stdout.reconfigure(encoding='utf-8')
from collections import defaultdict

# ─────────────────────────────────────────
# CACHE TRADUCTION
# ─────────────────────────────────────────
TRANSLATION_CACHE = {}
TRANSLATION_CACHE_PATH = "translation_cache.json"

def load_translation_cache():
    global TRANSLATION_CACHE
    if os.path.exists(TRANSLATION_CACHE_PATH):
        try:
            with open(TRANSLATION_CACHE_PATH, "r", encoding="utf-8") as f:
                TRANSLATION_CACHE = json.load(f)
        except Exception:
            TRANSLATION_CACHE = {}

def save_translation_cache():
    try:
        with open(TRANSLATION_CACHE_PATH, "w", encoding="utf-8") as f:
            json.dump(TRANSLATION_CACHE, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"  (!) Erreur sauvegarde cache traduction: {e}")


# ─────────────────────────────────────────
# SOURCES RSS PAR CATÉGORIE
# ─────────────────────────────────────────
FEEDS = {
    "ia": [
        ("ZDNet France",       "https://www.zdnet.fr/actualites/"),
        ("01net",              "https://www.01net.com/actualites/"),
        ("Numerama",           "https://www.numerama.com/feed/"),
    ],
    "crypto": [
        ("Le Journal du Coin", "https://journalducoin.com/feed/"),
        ("Cryptoast",          "https://cryptoast.fr/feed/"),
    ],
    "gaming": [
        ("JeuxVideo.com",      "https://www.jeuxvideo.com/rss/rss.xml"),
        ("Gamekult",           "https://www.gamekult.com/feed.xml"),
    ],
    "markets": [
        ("Boursorama",         "https://www.boursorama.com/rss/actualites/"),
        ("Investing.com",      "https://fr.investing.com/rss/news.rss"),
    ],
    "general": [
        ("Le Monde",           "https://www.lemonde.fr/rss/une.xml"),
        ("France Info",        "https://www.francetvinfo.fr/titres.rss"),
        ("Le Figaro",          "https://www.lefigaro.fr/rss/figaro_actualites.xml"),
    ],
    "science": [
        ("Futura-Sciences",    "https://www.futura-sciences.com/rss/actualites.xml"),
        ("Sciences et Avenir", "https://www.sciencesetavenir.fr/rss.xml"),
    ],
    "dev": [
        ("Developpez.com",     "https://www.developpez.com/rss/"),
    ],
    "startups": [
        ("FrenchWeb",          "https://www.frenchweb.fr/feed/"),
    ],
}

CAT_LABELS = {
    "ia":      "IA & Tech",
    "crypto":  "Crypto",
    "gaming":  "Jeux Vidéo",
    "markets": "Marchés",
    "general": "Général",
    "science": "Science",
    "dev":     "Développement",
    "startups":"Startups",
}

CAT_COLORS = {
    "ia":      ("#eff6ff", "#1d4ed8"),
    "crypto":  ("#fffbeb", "#b45309"),
    "gaming":  ("#f0fdf4", "#15803d"),
    "markets": ("#faf5ff", "#7e22ce"),
    "general": ("#fff1f2", "#be123c"),
    "science": ("#ecfeff", "#0891b2"),
    "dev":     ("#f5f3ff", "#7c3aed"),
    "startups":("#fefce8", "#a16207"),
}

CAT_KEYWORDS = {
    "ia":      "artificial intelligence technology",
    "crypto":  "cryptocurrency blockchain finance",
    "gaming":  "video game gaming controller",
    "markets": "stock market finance economy",
    "general": "world news current events",
    "science": "science space research discovery",
    "dev":     "programming developer code software",
    "startups":"startup entrepreneur business venture",
}

STOP_WORDS = {
    'the','a','an','is','are','was','were','be','been','being','have','has','had',
    'do','does','did','will','would','could','should','may','might','can',
    'to','for','in','on','at','by','with','about','as','of','and','or','but',
    'not','no','from','up','out','that','this','these','those','how','why',
    'what','when','where','who','which','its','it','into','their','new','first',
    'last','more','most','some','such','than','very','just','after','before',
    'over','under','then','there','here','now','also','only','even',
    'back','still','way','since','both','each','few','between',
}

FR_WORDS = {'le','la','les','un','une','des','est','sont','dans','pour','avec',
            'sur','par','qui','que','plus','mais','aussi','tout','bien','cette',
            'comme','même','très','après','avant','entre','selon','vers','lors',
            'leur','leurs','elles','ils','nous','vous','être','avoir','faire'}

# Sources déjà en français → pas de traduction
FR_SOURCES = {"Le Monde", "France Info", "Le Figaro", "JeuxVideo.com", "Futura-Sciences", "Gamekult", "Boursorama", "Investing.com", "Sciences et Avenir", "Developpez.com", "FrenchWeb", "Le Journal du Coin", "Cryptoast", "ZDNet France", "01net", "Numerama"}

# ─────────────────────────────────────────
# TRADUCTION
# ─────────────────────────────────────────
def is_french(text):
    words = set(re.findall(r'\b\w+\b', text.lower()))
    return len(words & FR_WORDS) >= 2


def _translate_chunk(text, retries=2):
    """Traduit un chunk de max 450 caractères via MyMemory. Retourne None si échec."""
    if not text or len(text.strip()) < 3:
        return None
    text = text[:450]
    cache_key = hashlib.md5(text.encode()).hexdigest()[:16]
    if cache_key in TRANSLATION_CACHE:
        cached = TRANSLATION_CACHE[cache_key]
        return cached if cached != text else None
    for attempt in range(retries):
        try:
            url = ("https://api.mymemory.translated.net/get?q="
                   + urllib.parse.quote(text)
                   + "&langpair=en|fr&de=techfeed@news.fr")
            resp = requests.get(url, headers={"User-Agent": "TechFeed/1.0"}, timeout=6)
            data = resp.json()
            translated = data.get("responseData", {}).get("translatedText", "")
            if translated and "MYMEMORY WARNING" in translated:
                print("    (!) Quota MyMemory atteint.")
                return None
            if translated and len(translated) > 5 and translated.lower() != text.lower():
                TRANSLATION_CACHE[cache_key] = translated
                return translated
        except Exception as e:
            print(f"    (!) Traduction echouee (tentative {attempt+1}): {e}")
            time.sleep(1)
    return None


def translate_to_french(text, retries=2):
    if not text or len(text.strip()) < 5 or is_french(text):
        return text if is_french(text) else None
    if len(text) <= 450:
        return _translate_chunk(text, retries)
    sentences = re.split(r'(?<=[.!?])\s+', text)
    chunks, current = [], ""
    for s in sentences:
        if len(current) + len(s) + 1 <= 440:
            current = (current + " " + s).strip()
        else:
            if current:
                chunks.append(current)
            current = s[:440]
    if current:
        chunks.append(current)
    parts = []
    for chunk in chunks:
        t = _translate_chunk(chunk, retries)
        if t is None:
            return None
        parts.append(t)
        time.sleep(0.2)
    return " ".join(parts)


# ─────────────────────────────────────────
# IMAGES
# ─────────────────────────────────────────
def extract_rss_image(entry):
    """Tente d'extraire une image depuis les éléments media du flux RSS."""
    for attr in ("media_thumbnail", "media_content"):
        items = getattr(entry, attr, [])
        if items:
            url = items[0].get("url", "") if isinstance(items[0], dict) else ""
            if url and url.startswith("http"):
                return url
    for enc in getattr(entry, "enclosures", []):
        url = enc.get("href", enc.get("url", ""))
        mime = enc.get("type", "")
        if "image" in mime and url.startswith("http"):
            return url
    summary = getattr(entry, "summary", "") or ""
    m = re.search(r'<img[^>]+src=["\']([^"\']+)["\']', summary)
    if m and m.group(1).startswith("http"):
        return m.group(1)
    return ""


def fetch_og_image(article_url, timeout=4):
    """Récupère l'og:image depuis la page de l'article via requests."""
    try:
        with requests.get(
            article_url,
            headers={"User-Agent": "Mozilla/5.0 TechFeed/1.0", "Accept": "text/html"},
            timeout=timeout,
            stream=True,
        ) as resp:
            chunk = resp.raw.read(8192).decode("utf-8", errors="ignore")
        m = re.search(r'<meta[^>]+property=["\']og:image["\'][^>]+content=["\']([^"\']+)["\']', chunk)
        if not m:
            m = re.search(r'<meta[^>]+content=["\']([^"\']+)["\'][^>]+property=["\']og:image["\']', chunk)
        if m:
            url = m.group(1)
            if url.startswith("http"):
                return url
    except Exception:
        pass
    return ""


def pollinations_url(title, cat, w=640, h=360):
    """Génère une URL Pollinations.ai thématique basée sur le titre et la catégorie."""
    seed = hashlib.md5(title.encode()).hexdigest()[:10]
    cat_kw = {
        "ia":      "artificial intelligence technology futuristic",
        "crypto":  "cryptocurrency blockchain bitcoin digital",
        "gaming":  "video game gaming controller screenshot",
        "markets": "stock market finance economy charts",
        "general": "world news journalism newspaper",
    }
    prompt = f"{title}, {cat_kw.get(cat, 'news')}, professional editorial photography"
    encoded = urllib.parse.quote(prompt)
    return f"https://image.pollinations.ai/prompt/{encoded}?width={w}&height={h}&seed={seed}&nologo=true"


def verify_image_url(url, timeout=5):
    """Vérifie qu'une URL d'image est accessible (retourne vrai si 200 et content-type image)."""
    try:
        r = requests.head(url, timeout=timeout, allow_redirects=True, headers={"User-Agent": "Mozilla/5.0"})
        if r.status_code == 200:
            ct = r.headers.get("Content-Type", "")
            return "image" in ct or url.endswith((".jpg", ".jpeg", ".png", ".webp", ".gif"))
    except Exception:
        pass
    return False


def fetch_full_text(article_url, timeout=10):
    """Récupère le texte complet d'un article via r.jina.ai et nettoie le bruit."""
    try:
        r = requests.get(f"https://r.jina.ai/http://{article_url}", timeout=timeout, headers={"User-Agent": "Mozilla/5.0"})
        if r.status_code == 200:
            text = r.text.strip()
            return clean_jina_content(text, article_url)
    except Exception as e:
        print(f"    (!) Extraction jina.ai échouée: {e}")
    return ""


# Patterns de navigation / footer à supprimer
NOISE_PATTERNS = [
    r'^\*+$',                                    # Lignes d'astérisques
    r'^\*\s+\[',                                # Listes de liens
    r'^\[.*?\]\(.*?\)\s*$',                    # Lignes qui sont juste un lien
    r'^\[.*?\]\(.*?\)\s+\[',                  # Multiple liens
    r'^\d+-\s+(Services|Guides|Suppléments)',   # Services Le Monde etc.
    r'^(Services|Guides|Suppléments|Menu|Fermer)\b',
    r'^Retour\b',
    r'^Voir\s+plus',
    r'^Tous\s+(nos|les)',
    r'^Article\s+(réservé|réservés)',
    r'^Publié\s+(aujourd|hier|le)',
    r'^\d{2}:\d{2}\s+\[',                      # Horodatage + lien
    r'^Copyright\s+©',
    r'^Tous\s+droits\s+réservés',
    r'^Politique\s+de\s+(confidentialité|cookies)',
    r'^C\.G\.U\.|^C\.G\.V\.|^Mentions\s+légales',
    r'^Gérer\s+Utiq|^Préférences\s+cookies',
    r'^Newsletter|^RSS|^Jobs$|^Contact$',
    r'^Nous\s+suivre|^Téléchargez|^INFORMATIONS',
    r'^OK$|^Menu$|^Menu\s+Menu$',
    r'^CONNEXION$|^Se\s+connecter|^S\'abonner',
    r'^Votre\s+compte|^Sélections|^Notifications',
    r'^Le\s+journal\s+numérique',
    r'^En\s+ce\s+moment',
    r'^Exprimez\s+vos\s+choix',
    r'^En\s+savoir\s+plus|^Refuser|^Accepter',
    r'^\d+\s+partenaires',
    r'^Aide$|^FAQ$',
    r'^Gestion\s+des\s+cookies',
    r'^Mettre\s+à\s+jour\s+ma\s+CB',
    r'^Régler\s+l\'impayé',
    r'^Autres\s+offres',
    r'^Partager\s+votre\s+abonnement',
    r'^Lire\s+le\s+journal\s+numérique',
    r'^Édition\s+du\s+jour',
    r'^Daté\s+du',
    r'^Cet\s+article\s+vous\s+est\s+offert',
    r'^Pour\s+lire\s+gratuitement',
    r'^Vous\s+n\'êtes\s+pas\s+inscrit',
    r'^Inscrivez-vous',
    r'^Découvrir$|^Tester$',
    r'^Cours\s+du\s+soir',
    r'^Testez\s+votre\s+culture',
    r'^\d+\s+min\s+de\s+lecture',
    r'^\[Image\s+\d+\]',
    r'^blob:',
    r'^[A-Z][A-Z\s]+/\s*(REUTERS|AFP|AP|GETTY|EPA|ANSA|DPA|AFP)\s*$',  # Signatures photo
]


def clean_jina_content(text, article_url):
    """Nettoie le contenu jina.ai : supprime menus, footers, liens, signatures."""
    lines = text.split('\n')
    
    # Étape 1 : trouver le début du contenu principal
    # Chercher après "Markdown Content:"
    content_started = False
    content_lines = []
    for line in lines:
        if line.startswith('Markdown Content:'):
            content_started = True
            continue
        if not content_started:
            continue
        content_lines.append(line)
    
    # Étape 2 : filtrer les lignes de bruit
    filtered = []
    for line in content_lines:
        stripped = line.strip()
        if not stripped:
            continue
        # Supprimer les liens markdown
        line_no_links = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', stripped)
        # Supprimer les images markdown
        line_no_links = re.sub(r'!\[([^\]]*)\]\([^)]+\)', '', line_no_links)
        # Supprimer les headings markdown
        line_no_links = re.sub(r'^#{1,4}\s+', '', line_no_links)
        line_no_links = line_no_links.strip()
        if not line_no_links:
            continue
        # Vérifier si la ligne est du bruit
        is_noise = False
        for pattern in NOISE_PATTERNS:
            if re.search(pattern, line_no_links, re.IGNORECASE):
                is_noise = True
                break
        # Supprimer aussi les lignes très courtes qui sont probablement des nav links
        if len(line_no_links) < 25 and ('.' not in line_no_links and '!' not in line_no_links and '?' not in line_no_links):
            # Si c'est une phrase courte sans ponctuation, c'est probablement un menu
            if not line_no_links.startswith(('Le', 'La', 'Les', 'Un', 'Une', 'En', 'Dans', 'Sur', 'À', 'A ', 'C\'est', 'Il', 'Elle')):
                is_noise = True
        if not is_noise:
            filtered.append(line_no_links)
    
    # Étape 3 : chercher le vrai contenu de l'article
    # Le contenu principal commence généralement après une série de lignes courtes (menus)
    # et se caractérise par des paragraphes plus longs
    # On va chercher le premier "paragraphe substantiel" (au moins 80 mots)
    # et garder tout ce qui suit
    
    result = []
    found_content = False
    for i, line in enumerate(filtered):
        word_count = len(line.split())
        if word_count >= 80:
            found_content = True
        if found_content:
            # S'arrêter si on retrouve des patterns de footer
            if re.search(r'^(Copyright|©|Tous droits|Politique de|C\.G\.U|Gérer|Contact|Newsletter|RSS|Jobs|Nous suivre|INFORMATIONS)', line, re.IGNORECASE):
                break
            # S'arrêter si on retrouve des liens de services
            if re.search(r'^(\d+-\s|Services|Guides|Suppléments|Boutique|Ateliers|Newsletters|Jeux|Mots croisés|Sudoku)', line, re.IGNORECASE):
                break
            result.append(line)
    
    full_text = ' '.join(result).strip()
    # Vérifier qu'on a assez de contenu
    if len(full_text.split()) >= 100:
        return full_text
    return ""


def translate_long_text(text, retries=1):
    """Traduit un texte long (jusqu'à 5000 mots) en français, chunk par chunk."""
    if not text or len(text.strip()) < 5:
        return None
    if is_french(text):
        return text
    
    # Découper en chunks de ~400 caractères (par phrases)
    sentences = re.split(r'(?<=[.!?])\s+', text)
    chunks, current = [], ""
    for s in sentences:
        if len(current) + len(s) + 1 <= 400:
            current = (current + " " + s).strip()
        else:
            if current:
                chunks.append(current)
            current = s[:400]
    if current:
        chunks.append(current)
    
    translated_parts = []
    for i, chunk in enumerate(chunks):
        t = _translate_chunk(chunk, retries)
        if t is None:
            print(f"    (!) Traduction chunk {i+1}/{len(chunks)} échouée, skip article")
            return None
        translated_parts.append(t)
        time.sleep(0.1)
    return " ".join(translated_parts)


def get_article_image(entry, title, article_url, cat):
    """Stratégie en cascade : RSS → og:image → Pollinations thématique (vérifiée)."""
    # 1. RSS media
    img = extract_rss_image(entry)
    if img:
        return img, "rss"
    # 2. og:image de la page
    img = fetch_og_image(article_url)
    if img:
        return img, "og"
    # 3. Pollinations — vérifier qu'elle est accessible
    purl = pollinations_url(title, cat)
    if verify_image_url(purl):
        return purl, "pollinations"
    # 4. Fallback : data-URL invalide qui force onerror → affiche le label de catégorie
    return "data:image/gif;base64,invalid", "fallback"


# ─────────────────────────────────────────
# FETCH & DÉDUPLICATION
# ─────────────────────────────────────────
def fetch_articles(cat, feeds, max_per_feed=4):
    all_articles = []
    titles_seen = set()

    for source_name, url in feeds:
        try:
            resp = requests.get(
                url,
                headers={"User-Agent": "Mozilla/5.0 TechFeed/1.0"},
                timeout=10,
            )
            resp.raise_for_status()
            feed = feedparser.parse(resp.content)
        except Exception as e:
            print(f"  (!) Erreur flux {source_name}: {e}")
            continue

        count = 0
        for entry in feed.entries:
            if count >= max_per_feed:
                break
            title_raw = (entry.get("title") or "").strip()
            if not title_raw:
                continue
            key = re.sub(r'\W+', '', title_raw.lower())[:60]
            if key in titles_seen:
                continue
            titles_seen.add(key)

            link = entry.get("link", "#")
            if not link or link == "#":
                continue

            # Récupérer le contenu COMPLET de l'article (pas seulement le résumé RSS)
            full_text = fetch_full_text(link)
            if not full_text:
                # Fallback sur le résumé RSS si jina.ai échoue
                desc_raw = ""
                if hasattr(entry, "summary"):
                    desc_raw = entry.summary
                elif hasattr(entry, "content") and entry.content:
                    desc_raw = entry.content[0].get("value", "")
                desc_raw = strip_html(desc_raw)[:8000]
                if not desc_raw or len(desc_raw.strip()) < 30:
                    print(f"      -> SKIP: pas de contenu: {title_raw[:50]}...")
                    continue
                full_text = desc_raw
            else:
                # Vérifier que le contenu complet fait au moins 300 mots
                word_count = len(full_text.split())
                if word_count < 300:
                    print(f"      -> SKIP: contenu trop court ({word_count} mots): {title_raw[:50]}...")
                    continue
                print(f"      -> Contenu complet: {word_count} mots")

            # Date de publication (timestamp Unix pour tri)
            pub_ts = 0
            pub_label = ""
            if hasattr(entry, "published_parsed") and entry.published_parsed:
                try:
                    pub_ts = calendar.timegm(entry.published_parsed)
                    dt = datetime.fromtimestamp(pub_ts, tz=timezone.utc)
                    # Format français manuel
                    mois_fr = {1:'janv',2:'févr',3:'mars',4:'avr',5:'mai',6:'juin',
                               7:'juil',8:'août',9:'sept',10:'oct',11:'nov',12:'déc'}
                    pub_label = f"{dt.day} {mois_fr.get(dt.month, dt.strftime('%b'))} {dt.year}, {dt.strftime('%H:%M')}"
                except Exception:
                    pass
            if not pub_label:
                now = datetime.now()
                mois_fr = {1:'janv',2:'févr',3:'mars',4:'avr',5:'mai',6:'juin',
                           7:'juil',8:'août',9:'sept',10:'oct',11:'nov',12:'déc'}
                pub_label = f"{now.day} {mois_fr.get(now.month, now.strftime('%b'))} {now.year}, {now.strftime('%H:%M')}"

            # Image
            img_url, img_src = get_article_image(entry, title_raw, link, cat)

            # Traduction (skip si source francophone)
            if source_name in FR_SOURCES:
                title_fr = title_raw
                desc_fr = full_text
                print(f"      -> Source FR: {title_raw[:50]}...")
            else:
                print(f"      -> Traduction titre: {title_raw[:50]}...")
                title_fr = translate_to_french(title_raw)
                if title_fr is None:
                    print(f"      -> SKIP: traduction titre impossible: {title_raw[:50]}...")
                    continue
                # Traduction du contenu complet (chunk par chunk)
                print(f"      -> Traduction contenu ({len(full_text.split())} mots)...")
                desc_fr = translate_long_text(full_text)
                if desc_fr is None:
                    print(f"      -> SKIP: traduction contenu impossible: {title_raw[:50]}...")
                    continue
                time.sleep(0.3)

            all_articles.append({
                "title":    title_fr,
                "desc":     desc_fr,
                "url":      link,
                "source":   source_name,
                "cat":      cat,
                "catLabel": CAT_LABELS[cat],
                "image":    img_url,
                "imgSrc":   img_src,
                "pubTs":    pub_ts,
                "pubLabel": pub_label,
            })
            count += 1

    return all_articles


def fetch_articles_light(cat, feeds, max_per_feed=2):
    """Version allégée qui récupère le contenu complet pour chaque article."""
    return fetch_articles(cat, feeds, max_per_feed=max_per_feed)


def strip_html(text):
    text = re.sub(r"<[^>]+>", " ", text)
    text = html.unescape(text)
    return re.sub(r"\s+", " ", text).strip()


def cross_verify(articles):
    by_cat = defaultdict(list)
    for a in articles:
        by_cat[a["cat"]].append(a)

    verified = []
    for cat, items in by_cat.items():
        kw_index = defaultdict(list)
        for a in items:
            for w in set(re.findall(r"\b\w{5,}\b", a["title"].lower())):
                kw_index[w].append(a)

        for a in items:
            words = set(re.findall(r"\b\w{5,}\b", a["title"].lower()))
            overlap = {o["source"] for w in words for o in kw_index[w] if o["source"] != a["source"]}
            a["verifiedSources"] = len(overlap) + 1
            a["reliability"]      = "strong" if overlap else "moderate"
            a["reliabilityLabel"] = "✓ Consensus fort" if overlap else "~ Source unique"
            verified.append(a)

    return verified


# ─────────────────────────────────────────
# ARTICLES PREMIUM (new_articles.json)
# ─────────────────────────────────────────
def load_articles_js(path="articles.js"):
    """Lit articles.js (window.ARTICLES = [...]) et extrait les articles premium."""
    if not os.path.exists(path):
        return []
    try:
        content = open(path, "r", encoding="utf-8").read()
        m = re.search(r"window\.ARTICLES\s*=\s*(\[.*?\]);?\s*$", content, re.DOTALL)
        if not m:
            return []
        data = json.loads(m.group(1))
    except Exception as e:
        print(f"  (!) Impossible de lire {path}: {e}")
        return []

    premium = []
    for item in data:
        if not isinstance(item, dict):
            continue
        cat = item.get("cat", "general")
        title = item.get("title", "").strip()
        if not title:
            continue
        body = item.get("body", "")
        excerpt = item.get("excerpt", "")
        text = strip_html(body) if body else strip_html(excerpt)
        read_time = str(max(2, len(text.split()) // 50 + 1)) + " min"
        vsrc = item.get("verifiedSources", 1)
        rel = "strong" if vsrc >= 2 else "moderate"
        rel_label = "✓ Consensus fort" if vsrc >= 2 else "~ Source unique"
        img = item.get("image", "")
        if not img:
            img = pollinations_url(title, cat)
            img_src = "pollinations"
        else:
            img_src = "premium"

        premium.append({
            "id":              item.get("id", slug(title)),
            "cat":             cat,
            "catLabel":        CAT_LABELS.get(cat, "Général"),
            "title":           title,
            "desc":            excerpt,
            "body":            body,
            "image":           img,
            "imgSrc":          img_src,
            "url":             item.get("url", "#"),
            "source":          item.get("source", "Inconnu"),
            "pubTs":           item.get("pubTs", int(datetime.now().timestamp())),
            "pubLabel":        item.get("date", datetime.now().strftime("%d %b %Y")),
            "readTime":        read_time,
            "reliability":     rel,
            "reliabilityLabel": rel_label,
            "verifiedSources": vsrc,
        })
    return premium


def merge_articles(rss_articles, premium_articles):
    """Fusionne les articles RSS et premium (dédoublonnage par URL, premium prime)."""
    by_url = {}
    for a in premium_articles:
        by_url[a["url"]] = a
    for a in rss_articles:
        url = a.get("url", "#")
        if url in by_url:
            continue
        # Génère un ID unique basé sur le titre, avec suffixe si collision
        base_id = slug(a["title"])
        existing_ids = {x.get("id", slug(x["title"])) for x in by_url.values()}
        if base_id in existing_ids:
            suffix = hashlib.md5(url.encode()).hexdigest()[:6]
            a["id"] = f"{base_id}-{suffix}"
        else:
            a["id"] = base_id
        by_url[url] = a
    return list(by_url.values())


# ─────────────────────────────────────────
# GÉNÉRATION HTML
# ─────────────────────────────────────────
def slug(text):
    return re.sub(r'[^a-z0-9]+', '-', text.lower())[:48].strip('-')


def build_articles_json(articles):
    sorted_articles = sorted(articles, key=lambda a: a.get("pubTs", 0), reverse=True)
    items = []
    for a in sorted_articles:
        items.append({
            "id":              a.get("id", slug(a["title"])),
            "cat":             a["cat"],
            "catLabel":        a.get("catLabel", CAT_LABELS.get(a["cat"], "")),
            "title":           a["title"],
            "excerpt":         a.get("desc", ""),
            "body":            a.get("body", ""),
            "image":           a["image"],
            "url":             a["url"],
            "source":          a["source"],
            "date":            a.get("pubLabel", datetime.now().strftime("%d %b %Y")),
            "pubTs":           a.get("pubTs", 0),
            "readTime":        a.get("readTime", str(max(2, len(a.get("desc", "").split()) // 50 + 1)) + " min"),
            "reliability":     a.get("reliability", "moderate"),
            "reliabilityLabel": a.get("reliabilityLabel", "~ Source unique"),
            "verifiedSources": a.get("verifiedSources", 1),
        })
    raw = json.dumps(items, ensure_ascii=True)
    raw = raw.replace('</script>', '<\\/script>').replace('<!--', '<\\!--')
    return raw


CSS = """
:root{color-scheme:light}*{box-sizing:border-box;margin:0;padding:0}
body{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;background:#f0f2f5;color:#1a1a1a;overflow:hidden}
header{background:#fff;border-bottom:1px solid #e5e7eb;padding:12px 24px;display:flex;align-items:center;justify-content:space-between;height:56px;position:fixed;top:0;left:0;right:0;z-index:20}
.logo{display:flex;align-items:center;gap:10px}
.logo h1{font-size:1.2rem;font-weight:800;background:linear-gradient(135deg,#2563eb,#7c3aed);-webkit-background-clip:text;-webkit-text-fill-color:transparent}
.badge{font-size:.6rem;background:#2563eb;color:#fff;padding:2px 7px;border-radius:99px;font-weight:700;-webkit-text-fill-color:#fff}
.hright{display:flex;align-items:center;gap:8px}
.upd{font-size:.7rem;color:#9ca3af}
.view-toggle{display:flex;align-items:center;gap:3px;background:#f3f4f6;border-radius:8px;padding:3px}
.vbtn{background:none;border:none;cursor:pointer;padding:4px 10px;border-radius:5px;font-size:.75rem;color:#6b7280;font-weight:500;transition:all .15s}
.vbtn.active{background:#fff;color:#111827;box-shadow:0 1px 2px rgba(0,0,0,.12)}
.btn-ghost{background:transparent;border:1px solid #e5e7eb;color:#6b7280;border-radius:8px;padding:6px 12px;font-size:.78rem;font-weight:500;cursor:pointer}
.btn-ghost:hover{background:#f0f2f5}
.tabs{background:#fff;border-bottom:1px solid #e5e7eb;padding:0 16px;display:flex;overflow-x:auto;scrollbar-width:none;position:fixed;top:56px;left:0;right:0;z-index:19}
.tabs::-webkit-scrollbar{display:none}
.tab{padding:11px 15px;font-size:.82rem;font-weight:500;color:#6b7280;cursor:pointer;border-bottom:2px solid transparent;white-space:nowrap}
.tab.active{color:#2563eb;border-bottom-color:#2563eb;font-weight:600}
.layout{display:flex;position:fixed;top:104px;left:0;right:0;bottom:0}
.feed-col{flex:1;overflow-y:auto;padding:16px;min-width:0;transition:flex .3s}
.panel-col{width:0;overflow:hidden;background:#fff;border-right:2px solid #e5e7eb;transition:width .3s;display:flex;flex-direction:column;flex-shrink:0;order:-1}
.layout.panel-open .panel-col{width:480px}
.sec-label{font-size:.7rem;font-weight:700;text-transform:uppercase;letter-spacing:1px;color:#9ca3af;margin-bottom:14px}
.hero{background:#fff;border-radius:14px;border:1px solid #e5e7eb;display:grid;grid-template-columns:1fr 280px;overflow:hidden;cursor:pointer;transition:all .15s;margin-bottom:14px;min-height:200px}
.hero:hover{box-shadow:0 6px 20px rgba(0,0,0,.09)}
.hero.active-card{border-color:#2563eb;box-shadow:0 0 0 2px rgba(37,99,235,.18)}
.hero-body{padding:20px 24px;display:flex;flex-direction:column;justify-content:space-between}
.hero-kicker{font-size:.65rem;font-weight:800;text-transform:uppercase;letter-spacing:1px;color:#2563eb;margin-bottom:8px;display:flex;align-items:center;gap:5px}
.hero-kicker::before{content:'';width:5px;height:5px;border-radius:50%;background:#2563eb;display:inline-block;animation:pulse 1.5s ease-in-out infinite}
@keyframes pulse{0%,100%{opacity:1}50%{opacity:.4}}
.hero-title{font-size:1.15rem;font-weight:800;line-height:1.35;color:#111827;margin-bottom:8px}
.hero-excerpt{font-size:.82rem;color:#6b7280;line-height:1.6;flex:1;margin-bottom:14px;display:-webkit-box;-webkit-line-clamp:3;-webkit-box-orient:vertical;overflow:hidden}
.hero-foot{display:flex;align-items:center;justify-content:space-between}
.hero-img{overflow:hidden}.hero-img img{width:100%;height:100%;object-fit:cover}
.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(260px,1fr));gap:12px}
.layout.panel-open .grid{grid-template-columns:repeat(auto-fill,minmax(200px,1fr))}
.card{background:#fff;border-radius:12px;border:1px solid #e5e7eb;overflow:hidden;cursor:pointer;transition:all .15s;display:flex;flex-direction:column}
.card:hover{box-shadow:0 4px 16px rgba(0,0,0,.08)}
.card.active-card{border-color:#2563eb;box-shadow:0 0 0 2px rgba(37,99,235,.15)}
.card-img{height:148px;overflow:hidden;flex-shrink:0;background:#f8faff}
.card-img img{width:100%;height:100%;object-fit:cover;transition:transform .3s}
.card:hover .card-img img{transform:scale(1.03)}
.card-body{padding:13px;flex:1;display:flex;flex-direction:column}
.card-top{display:flex;align-items:center;justify-content:space-between;margin-bottom:7px}
.badge-cat{padding:2px 8px;border-radius:99px;font-size:.63rem;font-weight:700;text-transform:uppercase;letter-spacing:.3px}
.cat-ia{background:#eff6ff;color:#1d4ed8}.cat-crypto{background:#fffbeb;color:#b45309}
.cat-gaming{background:#f0fdf4;color:#15803d}.cat-markets{background:#faf5ff;color:#7e22ce}.cat-general{background:#fff1f2;color:#be123c}
.cat-science{background:#ecfeff;color:#0891b2}.cat-dev{background:#f5f3ff;color:#7c3aed}.cat-startups{background:#fefce8;color:#a16207}
.img-fb{width:100%;height:100%;display:flex;align-items:center;justify-content:center;background:linear-gradient(135deg,#e5e7eb,#f0f2f5);color:#9ca3af;font-size:.7rem;font-weight:700;letter-spacing:1px;text-transform:uppercase;text-align:center;padding:8px;line-height:1.2}
.date-group{font-size:.75rem;font-weight:700;color:#6b7280;margin:18px 0 10px;padding-bottom:6px;border-bottom:1px solid #e5e7eb;text-transform:uppercase;letter-spacing:.5px}
.search-wrap{display:flex;align-items:center;gap:6px;flex:1;max-width:320px;margin:0 12px}
.search-wrap input{width:100%;border:1px solid #e5e7eb;border-radius:8px;padding:6px 10px;font-size:.78rem;outline:none}
.search-wrap input:focus{border-color:#2563eb}
.search-clear{background:none;border:none;color:#9ca3af;font-size:.85rem;cursor:pointer;padding:2px 5px;border-radius:4px;display:none}
.search-clear.on{display:inline-block}
.bm-btn{background:none;border:none;cursor:pointer;font-size:.95rem;padding:2px 4px;border-radius:4px;color:#d1d5db;line-height:1}
.bm-btn.on{color:#f59e0b}
.card-title{font-size:.86rem;font-weight:600;line-height:1.4;color:#111827;margin-bottom:5px;flex:1}
.card-excerpt{font-size:.75rem;color:#6b7280;line-height:1.5;margin-bottom:9px;display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;overflow:hidden}
.card-foot{display:flex;align-items:center;justify-content:space-between;margin-top:auto}
.rel.strong{font-size:.65rem;font-weight:600;color:#15803d}.rel.moderate{font-size:.65rem;font-weight:600;color:#b45309}
.card-cta{font-size:.7rem;color:#2563eb;font-weight:500}
.date-badge{font-size:.63rem;color:#9ca3af;margin-top:3px}
.list .grid{display:flex;flex-direction:column;gap:8px}
.list .card{flex-direction:row;height:100px}
.list .card-img{width:140px;height:100px;flex-shrink:0;border-radius:0}
.list .card-body{padding:10px 13px}
.list .card-excerpt{-webkit-line-clamp:1}
.list .hero{grid-template-columns:1fr 200px;min-height:140px}
.panel-topbar{display:flex;align-items:center;justify-content:space-between;padding:12px 18px;border-bottom:1px solid #e5e7eb;flex-shrink:0;background:#fff;position:sticky;top:0;z-index:2}
.panel-topbar-l{display:flex;align-items:center;gap:7px;flex-wrap:wrap;min-width:0;flex:1}
.panel-actions{display:flex;gap:6px;align-items:center;flex-shrink:0}
.panel-close{background:none;border:none;font-size:1rem;cursor:pointer;color:#9ca3af;padding:5px 7px;border-radius:6px;line-height:1}
.panel-close:hover{background:#f0f2f5;color:#111}
.panel-bm{background:none;border:1px solid #e5e7eb;border-radius:7px;padding:4px 11px;font-size:.75rem;cursor:pointer;color:#6b7280;white-space:nowrap}
.panel-bm.on{background:#fffbeb;border-color:#fde68a;color:#b45309}
.panel-body{flex:1;overflow-y:auto;padding:18px 22px 40px}
.art-hero-img{border-radius:10px;overflow:hidden;margin-bottom:18px;background:#f8faff}
.art-hero-img img{width:100%;max-height:260px;object-fit:cover;display:block}
.art-title{font-size:1.15rem;font-weight:800;line-height:1.3;color:#111827;margin-bottom:8px}
.art-meta{font-size:.7rem;color:#9ca3af;margin-bottom:16px;display:flex;align-items:center;gap:8px;flex-wrap:wrap}
.rel-tag{padding:3px 8px;border-radius:6px;font-size:.68rem;font-weight:700}
.rel-tag.strong{background:#f0fdf4;color:#15803d}.rel-tag.moderate{background:#fffbeb;color:#b45309}
.art-content{font-size:.86rem;line-height:1.82;color:#374151}
.art-content p{margin-bottom:13px}
.read-more{display:inline-flex;align-items:center;gap:6px;background:#2563eb;color:#fff;border:none;padding:9px 16px;border-radius:8px;font-size:.8rem;font-weight:500;cursor:pointer;text-decoration:none;margin-top:6px}
.annexes{margin-top:22px;padding-top:18px;border-top:1px solid #e5e7eb}
.annexes h3{font-size:.68rem;font-weight:700;text-transform:uppercase;letter-spacing:.8px;color:#9ca3af;margin-bottom:10px}
.src-item{display:flex;align-items:flex-start;gap:8px;margin-bottom:7px}
.src-num{font-size:.66rem;font-weight:700;color:#2563eb;background:#eff6ff;padding:2px 6px;border-radius:4px;flex-shrink:0;margin-top:2px}
.src-name{font-size:.78rem;font-weight:600;color:#6b7280;display:block}
.src-url{font-size:.7rem;color:#2563eb;text-decoration:none;word-break:break-all}
.src-url:hover{text-decoration:underline}
.vfoot{display:flex;align-items:center;gap:5px;margin-top:10px;font-size:.68rem;color:#15803d;background:#f0fdf4;padding:7px 11px;border-radius:7px}
.bm-empty{text-align:center;padding:48px;color:#9ca3af}
@media(max-width:1024px){.layout.panel-open .panel-col{width:360px}.grid{grid-template-columns:repeat(auto-fill,minmax(220px,1fr))}}
@media(max-width:768px){.upd{display:none}.layout.panel-open .panel-col{width:100%;position:absolute;inset:0;z-index:10}.layout.panel-open .feed-col{display:none}.hero{grid-template-columns:1fr}.hero-img{height:200px;order:-1}.hero-body{padding:16px}.grid{grid-template-columns:repeat(auto-fill,minmax(200px,1fr));gap:10px}}
@media(max-width:640px){header{padding:10px 14px;height:52px}.logo h1{font-size:1rem}.view-toggle{display:none}.btn-ghost{padding:5px 9px;font-size:.72rem}.tabs{top:52px;padding:0 8px}.tab{padding:9px 11px;font-size:.76rem}.layout{top:96px}.feed-col{padding:10px}.grid{grid-template-columns:1fr;gap:8px}.card{flex-direction:row;height:110px}.card-img{width:120px;height:110px;flex-shrink:0;border-radius:0}.card-body{padding:9px 11px}.card-title{font-size:.82rem;-webkit-line-clamp:2;display:-webkit-box;-webkit-box-orient:vertical;overflow:hidden}.card-excerpt{display:none}.hero{grid-template-columns:1fr;min-height:auto}.hero-img{height:170px;order:-1}.hero-body{padding:13px 14px}.hero-title{font-size:1rem}.hero-excerpt{-webkit-line-clamp:2}.bm-btn{font-size:1.1rem;padding:4px 6px}.panel-body{padding:14px 16px 32px}.art-title{font-size:1rem}.art-hero-img img{max-height:200px}.list .card{flex-direction:column;height:auto}.list .card-img{width:100%;height:130px}}
"""

JS = r"""
const ARTICLES = __ARTICLES__;
const CAT_LABELS = {all:'Toutes les actualites',ia:'IA & Tech',crypto:'Crypto',gaming:'Jeux Video',markets:'Marches',general:'General',science:'Science',dev:'Developpement',startups:'Startups',bookmarks:'Sauvegardes',search:'Recherche'};
let cat='all', curId=null, viewMode='grid', searchTerm='';
let bm=[];
try{bm=JSON.parse(localStorage.getItem('tf_bm')||'[]')}catch(e){}
try{viewMode=localStorage.getItem('tf_view')||'grid'}catch(e){}
const saveBm=()=>{try{localStorage.setItem('tf_bm',JSON.stringify(bm))}catch(e){}};
const isBm=id=>bm.includes(id);
const esc=s=>(s||'').replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');

function setView(v){
  viewMode=v;
  try{localStorage.setItem('tf_view',v)}catch(e){}
  document.querySelectorAll('.vbtn').forEach(b=>b.classList.toggle('active',b.dataset.v===v));
  const fc=document.getElementById('feed');
  if(fc) fc.className='feed-col'+(v==='list'?' list':'');
}

function toggleBm(id,e){
  if(e)e.stopPropagation();
  isBm(id)?bm=bm.filter(x=>x!==id):bm.push(id);
  saveBm();
  document.querySelectorAll(`[data-bmid="${id}"]`).forEach(b=>b.classList.toggle('on',isBm(id)));
  if(curId===id){
    const pb=document.getElementById('panelBm');
    if(pb){pb.classList.toggle('on',isBm(id));pb.textContent=isBm(id)?'Sauvegarde':'Sauvegarder';}
  }
}

function showTab(c,el){
  cat=c; searchTerm='';
  const si=document.getElementById('searchInput'); if(si) si.value='';
  const sc=document.getElementById('searchClear'); if(sc) sc.classList.remove('on');
  document.querySelectorAll('.tab').forEach(t=>t.classList.remove('active'));
  if(el)el.classList.add('active');
  else{const bt=document.getElementById('bmTab');if(bt)bt.classList.add('active');}
  closePanel();render();
}

function searchArticles(q){
  searchTerm=q.trim().toLowerCase();
  const sc=document.getElementById('searchClear'); if(sc) sc.classList.toggle('on',searchTerm.length>0);
  if(searchTerm.length>0){
    cat='search';
    document.querySelectorAll('.tab').forEach(t=>t.classList.remove('active'));
    closePanel(); render();
  } else if(cat==='search'){
    cat='all';
    document.querySelectorAll('.tab').forEach(t=>t.classList.remove('active'));
    document.querySelector('.tab').classList.add('active');
    closePanel(); render();
  }
}

function dateLabel(ts){
  if(!ts) return 'Plus ancien';
  const now = new Date();
  const d = new Date(ts * 1000);
  const diffDays = Math.floor((now - d) / (1000 * 60 * 60 * 24));
  if(diffDays === 0) return 'Aujourd\'hui';
  if(diffDays === 1) return 'Hier';
  if(diffDays < 7) return 'Cette semaine';
  return d.toLocaleDateString('fr-FR', {day:'numeric', month:'long'});
}

function groupByDate(list){
  const groups = {};
  for(const a of list){
    const label = dateLabel(a.pubTs);
    if(!groups[label]) groups[label] = [];
    groups[label].push(a);
  }
  return groups;
}

function render(){
  const fc=document.getElementById('feed');if(!fc)return;
  if(cat==='bookmarks'){renderBm(fc);return;}
  if(cat==='search'){renderSearch(fc);return;}
  const list=(cat==='all'?ARTICLES:ARTICLES.filter(a=>a.cat===cat)).slice().sort((a,b)=>(b.pubTs||0)-(a.pubTs||0));
  const feat=cat==='all'&&viewMode==='grid'?list[0]:null;
  const rest=feat?list.slice(1):list;
  let out=`<div class="sec-label">${CAT_LABELS[cat]} &mdash; ${list.length} article${list.length!==1?'s':''}</div>`;
  if(feat) out+=heroHTML(feat);
  if(rest.length){
    const groups = groupByDate(rest);
    for(const [label, items] of Object.entries(groups)){
      out += `<div class="date-group">${label} &mdash; ${items.length} article${items.length!==1?'s':''}</div>`;
      out += `<div class="grid">${items.map(cardHTML).join('')}</div>`;
    }
  }
  fc.innerHTML=out;
}

function renderSearch(fc){
  const found=ARTICLES.filter(a=>{
    const t=(a.title+' '+a.excerpt+' '+a.source+' '+a.catLabel).toLowerCase();
    return t.includes(searchTerm);
  }).slice().sort((a,b)=>(b.pubTs||0)-(a.pubTs||0));
  let out=`<div class="sec-label">Recherche &mdash; ${found.length} resultat${found.length!==1?'s':''} pour "${esc(searchTerm)}"</div>`;
  if(found.length){
    const groups = groupByDate(found);
    for(const [label, items] of Object.entries(groups)){
      out += `<div class="date-group">${label} &mdash; ${items.length} article${items.length!==1?'s':''}</div>`;
      out += `<div class="grid">${items.map(cardHTML).join('')}</div>`;
    }
  }else{
    out+=`<div class="bm-empty">Aucun article ne correspond a votre recherche.</div>`;
  }
  fc.innerHTML=out;
}

function heroHTML(a){
  const active=curId===a.id?' active-card':'';
  const bmc=isBm(a.id)?'bm-btn on':'bm-btn';
  return `<div class="hero${active}" onclick="openPanel('${a.id}')">
    <div class="hero-body">
      <div class="hero-kicker">A la une</div>
      <div class="hero-title">${esc(a.title)}</div>
      <div class="hero-excerpt">${esc(a.excerpt)}</div>
      <div class="hero-foot">
        <div style="display:flex;align-items:center;gap:7px">
          <span class="badge-cat cat-${a.cat}">${a.catLabel}</span>
          <span class="rel ${a.reliability}">${a.reliabilityLabel}</span>
        </div>
        <div style="display:flex;align-items:center;gap:8px">
          <button class="${bmc}" data-bmid="${a.id}" onclick="toggleBm('${a.id}',event)">&#128204;</button>
          <span class="card-cta">Lire &rarr;</span>
        </div>
      </div>
    </div>
    <div class="hero-img"><img src="${esc(a.image)}" alt="" loading="lazy" onerror="this.style.display='none';this.nextElementSibling.style.display='flex'"><div class="img-fb" style="display:none">${esc(a.catLabel)}</div></div>
  </div>`;
}

function cardHTML(a){
  const active=curId===a.id?' active-card':'';
  const bmc=isBm(a.id)?'bm-btn on':'bm-btn';
  return `<div class="card${active}" onclick="openPanel('${a.id}')">
    <div class="card-img"><img src="${esc(a.image)}" alt="" loading="lazy" onerror="this.style.display='none';this.nextElementSibling.style.display='flex'">
    <div class="img-fb" style="display:none">${esc(a.catLabel)}</div></div>
    <div class="card-body">
      <div class="card-top">
        <span class="badge-cat cat-${a.cat}">${a.catLabel}</span>
        <button class="${bmc}" data-bmid="${a.id}" onclick="toggleBm('${a.id}',event)">&#128204;</button>
      </div>
      <div class="card-title">${esc(a.title)}</div>
      <div class="card-excerpt">${esc(a.excerpt)}</div>
      <div class="card-foot"><span class="rel ${a.reliability}">${a.reliabilityLabel}</span><span class="card-cta">Lire &rarr;</span></div>
      <div class="date-badge">${a.date}</div>
    </div>
  </div>`;
}

function renderBm(fc){
  const saved=ARTICLES.filter(a=>isBm(a.id));
  if(saved.length){
    fc.innerHTML=`<div class="sec-label">Sauvegardes &mdash; ${saved.length}</div><div class="grid">${saved.map(cardHTML).join('')}</div>`;
  }else{
    fc.innerHTML='<div class="sec-label">Sauvegardes &mdash; 0</div><div class="bm-empty">&#128204;<br><br>Aucun article sauvegarde.</div>';
  }
}

function openPanel(id){
  const a=ARTICLES.find(x=>x.id===id);if(!a)return;
  curId=id;
  document.querySelectorAll('.active-card').forEach(el=>el.classList.remove('active-card'));
  document.querySelectorAll(`[onclick="openPanel('${id}')"]`).forEach(el=>el.classList.add('active-card'));
  const panel=document.getElementById('panel');
  const layout=document.getElementById('layout');
  if(!panel||!layout)return;
  const content = a.body ? a.body : formatContent(a.excerpt);
  panel.innerHTML=`
    <div class="panel-topbar">
      <div class="panel-topbar-l">
        <span class="badge-cat cat-${a.cat}">${a.catLabel}</span>
        <span class="rel-tag ${a.reliability}">${a.reliabilityLabel} &mdash; ${a.verifiedSources} source${a.verifiedSources>1?'s':''}</span>
      </div>
      <div class="panel-actions">
        <button class="panel-bm${isBm(id)?' on':''}" id="panelBm" onclick="toggleBm('${id}',null)">${isBm(id)?'Sauvegarde':'Sauvegarder'}</button>
        <button class="panel-close" onclick="closePanel()">&#x2715;</button>
      </div>
    </div>
    <div class="panel-body">
      <div class="art-hero-img"><img src="${esc(a.image)}" alt="" loading="lazy" onerror="this.style.display='none'"></div>
      <h1 class="art-title">${esc(a.title)}</h1>
      <div class="art-meta">
        <span>${a.date}</span><span>&middot;</span>
        <span>${a.readTime} de lecture</span><span>&middot;</span>
        <span>${esc(a.source)}</span>
      </div>
      <div class="art-content">${content}</div>
      <a class="read-more" href="${esc(a.url)}" target="_blank" rel="noopener">Lire l&#39;article complet &rarr;</a>
      <div class="annexes">
        <h3>Source originale</h3>
        <div class="src-item">
          <span class="src-num">[1]</span>
          <div>
            <span class="src-name">${esc(a.source)}</span>
            <a class="src-url" href="${esc(a.url)}" target="_blank" rel="noopener">${esc(a.url)}</a>
          </div>
        </div>
        <div class="vfoot">&#10003; Croise sur ${a.verifiedSources} source${a.verifiedSources>1?'s':''} avant publication</div>
      </div>
    </div>`;
  layout.classList.add('panel-open');
}

function formatContent(text){
  if(!text)return '';
  const sentences=text.split(/(?<=[.!?])\s+/);
  const paras=[];let cur='';
  for(const s of sentences){
    cur=cur?cur+' '+s:s;
    if(cur.length>280){paras.push(cur);cur='';}
  }
  if(cur)paras.push(cur);
  return (paras.length?paras:[text]).map(p=>`<p>${esc(p)}</p>`).join('');
}

function closePanel(){
  curId=null;
  document.getElementById('layout').classList.remove('panel-open');
  document.getElementById('panel').innerHTML='';
  document.querySelectorAll('.active-card').forEach(el=>el.classList.remove('active-card'));
}

document.addEventListener('keydown',e=>{if(e.key==='Escape')closePanel();});
document.querySelectorAll('.vbtn').forEach(b=>b.classList.toggle('active',b.dataset.v===viewMode));
if(viewMode==='list'){const fc=document.getElementById('feed');if(fc)fc.className='feed-col list';}
try{render();}catch(e){
  console.error(e);
  const fc=document.getElementById('feed');
  if(fc)fc.innerHTML=`<div style="padding:40px;text-align:center;color:#ef4444">Erreur: ${e.message}</div>`;
}
"""


def generate_html(articles, last_update):
    articles_json = build_articles_json(articles)
    js = JS.replace("__ARTICLES__", articles_json)

    return f"""<!DOCTYPE html>
<html lang="fr">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>TechFeed</title>
<style>{CSS}</style>
</head>
<body>
<header>
  <div class="logo">
    <h1>&#128240; TechFeed</h1>
    <span class="badge">AUTO</span>
  </div>
  <div class="search-wrap">
    <input id="searchInput" type="text" placeholder="Rechercher..." oninput="searchArticles(this.value)">
    <button id="searchClear" class="search-clear" onclick="document.getElementById('searchInput').value='';searchArticles('')">&#x2715;</button>
  </div>
  <div class="hright">
    <span class="upd">Mis a jour le {last_update}</span>
    <div class="view-toggle">
      <button class="vbtn" data-v="grid" onclick="setView('grid');render()">&#8862; Grille</button>
      <button class="vbtn" data-v="list" onclick="setView('list');render()">&#9776; Liste</button>
    </div>
    <button class="btn-ghost" onclick="showTab('bookmarks',null)">&#128204; Sauvegardes</button>
  </div>
</header>
<div class="tabs">
  <div class="tab active" onclick="showTab('all',this)">&#128240; Tout</div>
  <div class="tab" onclick="showTab('ia',this)">&#129302; IA &amp; Tech</div>
  <div class="tab" onclick="showTab('crypto',this)">&#8383; Crypto</div>
  <div class="tab" onclick="showTab('gaming',this)">&#127918; Jeux</div>
  <div class="tab" onclick="showTab('markets',this)">&#128200; Marches</div>
  <div class="tab" onclick="showTab('general',this)">&#127758; General</div>
  <div class="tab" onclick="showTab('science',this)">&#128300; Science</div>
  <div class="tab" onclick="showTab('dev',this)">&#128187; Dev</div>
  <div class="tab" onclick="showTab('startups',this)">&#128640; Startups</div>
  <div class="tab" id="bmTab" onclick="showTab('bookmarks',this)">&#128204; Sauvegardes</div>
</div>
<div class="layout" id="layout">
  <div class="feed-col" id="feed"></div>
  <div class="panel-col" id="panel"></div>
</div>
<script>{js}</script>
</body>
</html>"""


def main():
    print("TechFeed v2 - Demarrage...")
    load_translation_cache()
    # 1. Articles RSS
    rss_articles = []
    for cat, feeds in FEEDS.items():
        print(f"  {CAT_LABELS[cat]}")
        articles = fetch_articles(cat, feeds, max_per_feed=2)
        print(f"    -> {len(articles)} articles RSS")
        rss_articles.extend(articles)

    # 2. Verification croisee (uniquement RSS)
    print(f"Verification croisee ({len(rss_articles)} articles RSS)...")
    rss_articles = cross_verify(rss_articles)

    # 3. Articles premium (articles.js)
    premium = load_articles_js()
    print(f"  -> {len(premium)} articles premium (articles.js)")

    # 4. Fusion
    all_articles = merge_articles(rss_articles, premium)
    print(f"Total fusionne : {len(all_articles)} articles")

    # 5. Generation HTML
    last_update = datetime.now().strftime("%d %B %Y - %H:%M")
    content = generate_html(all_articles, last_update)
    with open("index.html", "w", encoding="utf-8") as f:
        f.write(content)
    open(".nojekyll", "w").close()
    save_translation_cache()
    print(f"OK - {len(all_articles)} articles, {len(content)//1024}KB")


if __name__ == "__main__":
    main()
