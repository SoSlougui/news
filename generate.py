#!/usr/bin/env python3
"""
TechFeed — Generateur du site HTML (v4 — Magazine)
Lit articles.js et genere un index.html responsive avec theme clair/sombre,
bookmarks, panneau lateral, categories, et Coupe du Monde.
"""

import json
import re
import os
from datetime import datetime

# ─────────────────────────────────────────
# CATEGORIES
# ─────────────────────────────────────────
CAT_LABELS = {
    "all":     "Toutes les actualites",
    "ia":      "IA & Tech",
    "crypto":  "Crypto",
    "gaming":  "Jeux Video",
    "markets": "Marches",
    "general": "General",
    "science": "Science",
    "dev":     "Developpement",
    "startups":"Startups",
    "bookmarks":"Sauvegardes",
    "search":  "Recherche",
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


# ─────────────────────────────────────────
# LECTURE DES ARTICLES
# ─────────────────────────────────────────
def load_articles_js(path="articles.js"):
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

    articles = []
    for item in data:
        if not isinstance(item, dict):
            continue
        cat = item.get("cat", "general")
        title = item.get("title", "").strip()
        if not title:
            continue
        body = item.get("body", "")
        excerpt = item.get("excerpt", "")
        text = body or excerpt
        read_time = str(max(2, len(text.split()) // 50 + 1)) + " min"
        vsrc = item.get("verifiedSources", 1)
        rel = "strong" if vsrc >= 2 else "moderate"
        rel_label = "Consensus fort" if vsrc >= 2 else "Source unique"
        img = item.get("image", "")

        articles.append({
            "id":              item.get("id", slug(title)),
            "cat":             cat,
            "catLabel":        CAT_LABELS.get(cat, "General"),
            "title":           title,
            "desc":            excerpt,
            "body":            body,
            "image":           img,
            "url":             item.get("url", "#"),
            "source":          item.get("source", "Inconnu"),
            "pubTs":           item.get("pubTs", int(datetime.now().timestamp())),
            "pubLabel":        item.get("date", datetime.now().strftime("%d %b %Y")),
            "readTime":        read_time,
            "reliability":     rel,
            "reliabilityLabel": rel_label,
            "verifiedSources": vsrc,
        })
    return articles


# ─────────────────────────────────────────
# GENERATION HTML
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
            "image":           a["image"],
            "url":             a["url"],
            "source":          a["source"],
            "date":            a.get("pubLabel", datetime.now().strftime("%d %b %Y")),
            "pubTs":           a.get("pubTs", 0),
            "readTime":        a.get("readTime", str(max(2, len(a.get("desc", "").split()) // 50 + 1)) + " min"),
            "reliability":     a.get("reliability", "moderate"),
            "reliabilityLabel": a.get("reliabilityLabel", "Source unique"),
            "verifiedSources": a.get("verifiedSources", 1),
        })
    raw = json.dumps(items, ensure_ascii=True)
    raw = raw.replace('</script>', '<\\/script>').replace('<!--', '<\\!--')
    return raw


def build_bodies_json(articles):
    """Articles bodies, loaded separately to keep main JS light."""
    bodies = {}
    for a in articles:
        bid = a.get("id", slug(a["title"]))
        body = a.get("body", "")
        if body:
            bodies[bid] = body
    raw = json.dumps(bodies, ensure_ascii=True)
    raw = raw.replace('</script>', '<\\/script>').replace('<!--', '<\\!--')
    return raw


def build_feed_html(articles, is_home=True):
    """Pre-render the all-articles feed HTML so content is visible without JS.
    Mirrors the JS render() function logic."""
    if not articles:
        return '<div class="bm-empty"><h3>Aucun article</h3></div>'

    if not is_home:
        cat_articles = [a for a in articles if a.get("cat") == is_home]
    else:
        cat_articles = articles

    cat_articles.sort(key=lambda a: a.get("pubTs", 0), reverse=True)
    hero = cat_articles[0]
    rest = cat_articles[1:]

    from datetime import datetime as dt
    now = dt.now()

    def date_label(ts):
        if not ts:
            return "Plus ancien"
        d = dt.fromtimestamp(ts)
        diff = (now - d).days
        if diff == 0:
            return "Aujourd'hui"
        if diff == 1:
            return "Hier"
        if diff < 7:
            return "Cette semaine"
        return d.strftime("%d %B")

    groups = {}
    for a in rest:
        lbl = date_label(a.get("pubTs", 0))
        groups.setdefault(lbl, []).append(a)

    def esc(s):
        return str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

    h = ""
    h += '<div class="hero">'
    h += '<img src="' + esc(hero.get("image", "")) + '" alt="" onerror="this.style.display=\'none\'">'
    h += '<div class="hero-overlay">'
    h += '<div class="hero-cat">' + esc(hero.get("catLabel", "")) + '</div>'
    h += '<div class="hero-title">' + esc(hero.get("title", "")) + '</div>'
    h += '<div class="hero-desc">' + esc(hero.get("excerpt", "")) + '</div>'
    h += '</div></div>'

    is_dark = False
    for lbl, items in groups.items():
        bg = "white" if is_dark else "light"
        is_dark = not is_dark
        h += '<section class="' + bg + '"><div class="container"><div class="sec-head"><h3>' + lbl + '</h3><div class="count">' + str(len(items)) + ' article' + ('s' if len(items) > 1 else '') + '</div></div></div><div class="articles">'
        for i, a in enumerate(items):
            aid = a.get("id", "")
            if i == 0 and lbl == "Aujourd'hui":
                h += '<div class="feat" onclick="openPanel(\'' + aid + '\')">'
                h += '<img src="' + esc(a.get("image", "")) + '" alt="" onerror="this.style.display=\'none\'">'
                h += '<div class="feat-body">'
                h += '<div class="cat">' + esc(a.get("catLabel", "")) + '</div>'
                h += '<h4>' + esc(a.get("title", "")) + '</h4>'
                h += '<div class="excerpt">' + esc(a.get("excerpt", "")) + '</div>'
                h += '<div class="meta">' + esc(a.get("source", "")) + ' · ' + a.get("date", "") + '</div>'
                h += '</div></div>'
            else:
                h += '<div class="art-row" onclick="openPanel(\'' + aid + '\')">'
                h += '<div class="art-img"><img src="' + esc(a.get("image", "")) + '" alt="" onerror="this.style.display=\'none\'"></div>'
                h += '<div class="art-body">'
                h += '<div class="cat">' + esc(a.get("catLabel", "")) + '</div>'
                h += '<h4>' + esc(a.get("title", "")) + '</h4>'
                h += '<div class="excerpt">' + esc(a.get("excerpt", "")) + '</div>'
                h += '<div class="meta">' + esc(a.get("source", "")) + ' · ' + a.get("date", "") + '</div>'
                h += '</div></div>'
        h += '</div></section>'

    return h


CSS = """/* Simple flowing layout */
*{box-sizing:border-box;margin:0;padding:0}
body{font-family:system-ui,-apple-system,'Segoe UI',Roboto,sans-serif;background:#f5f5f7;color:#1d1d1f}

/* Sticky header — like test page */
header{position:sticky;top:0;z-index:100;background:rgba(245,245,247,.95);display:flex;align-items:center;justify-content:space-between;padding:0 12px;height:48px;border-bottom:1px solid rgba(0,0,0,.08)}
.logo{font-size:.82rem;font-weight:700;display:flex;align-items:center;gap:5px}
.logo em{font-style:normal;font-size:.46rem;background:#0071e3;color:#fff;padding:2px 7px;border-radius:99px;font-weight:600}
.hright{display:flex;align-items:center;gap:3px;overflow-x:auto;scrollbar-width:none}
.hright::-webkit-scrollbar{display:none}
.hright a,.hright button{width:34px;height:34px;display:flex;align-items:center;justify-content:center;border-radius:50%;text-decoration:none;font-size:.88rem;opacity:.6;flex-shrink:0;color:#1d1d1f}
.search-wrap{flex-shrink:0}
.search-wrap input{border:none;background:rgba(0,0,0,.04);border-radius:8px;padding:5px 10px;font-size:.72rem;width:120px}
.upd{font-size:.7rem;opacity:.5;margin-right:6px;white-space:nowrap}

/* Layout — simple block flow */
.layout{width:100%}
.feed-col{width:100%}
.panel-col{display:none;background:#fff}
.layout.panel-open .feed-col{display:none}
.layout.panel-open .panel-col{display:block;width:100%}

/* Hero */
.hero{background:#000;color:#fff;padding:0 0 36px}
.hero img{width:100%;height:320px;object-fit:cover;opacity:.7;display:block}
.hero-cat{font-size:.6rem;text-transform:uppercase;letter-spacing:2px;opacity:.55;padding:12px 16px 4px}
.hero-title{font-size:1.4rem;font-weight:700;line-height:1.1;padding:0 16px 6px}
.hero-desc{font-size:.85rem;opacity:.75;padding:0 16px;max-width:500px}

/* Sections */
section{padding:32px 0}
section.light{background:#f5f5f7}
.container,.articles{max-width:960px;margin:0 auto;padding:0 16px}
.sec-head{text-align:center;margin-bottom:24px}
.sec-head h3{font-size:1.5rem;font-weight:600}
.sec-head .count{font-size:.88rem;opacity:.5}

/* Articles */
.art-row{padding:18px 0;border-bottom:1px solid rgba(0,0,0,.06);cursor:pointer}
.art-img{margin-bottom:10px}
.art-img img{width:100%;height:160px;object-fit:cover;border-radius:10px;display:block}
.art-body .cat{font-size:.58rem;text-transform:uppercase;letter-spacing:1.5px;color:#0071e3;font-weight:600;margin-bottom:4px}
.art-body h4{font-size:1.05rem;font-weight:700;line-height:1.15;margin-bottom:4px}
.art-body .excerpt{font-size:.8rem;line-height:1.45;opacity:.55}
.art-body .meta{font-size:.7rem;opacity:.36;margin-top:4px}

/* Featured card */
.feat{background:#fff;border-radius:16px;overflow:hidden;margin-bottom:28px;cursor:pointer}
.feat img{width:100%;height:200px;object-fit:cover;display:block}
.feat-body{padding:16px}
.feat-body .cat{font-size:.58rem;text-transform:uppercase;letter-spacing:1.5px;color:#0071e3;font-weight:600}
.feat-body h4{font-size:1.1rem;font-weight:700;line-height:1.15;margin-bottom:4px}
.art-body .meta{font-size:.7rem;opacity:.36;margin-top:4px}

/* Panel — Apple style */
.panel-head{position:sticky;top:48px;z-index:10;background:rgba(255,255,255,.92);backdrop-filter:saturate(180%)blur(20px);display:flex;align-items:center;justify-content:space-between;padding:12px 20px;border-bottom:1px solid rgba(0,0,0,.06);min-height:48px}
.panel-close{width:32px;height:32px;border-radius:50%;background:rgba(0,0,0,.04);border:none;cursor:pointer;font-size:1rem;display:flex;align-items:center;justify-content:center;color:#1d1d1f;transition:background .2s}
.panel-close:hover{background:rgba(0,0,0,.08)}

/* Backdrop overlay — desktop only */
.backdrop{display:none}
@media(min-width:1024px){
.backdrop{display:none;position:fixed;top:48px;left:0;right:0;bottom:0;background:rgba(0,0,0,.35);z-index:40;opacity:0;transition:opacity .4s cubic-bezier(.4,0,.2,1);-webkit-backdrop-filter:blur(2px);backdrop-filter:blur(2px)}
.layout.panel-overlay.panel-open .backdrop{display:block;opacity:1}
}

/* Smooth transitions */
.feed-col{transition:filter .35s cubic-bezier(.4,0,.2,1)}
.hright a{transition:opacity .2s,color .2s,background .2s}
.art-row{transition:opacity .2s}
.art-row:hover{opacity:.7}
.panel-body{padding:20px}
.panel-body img{width:100%;border-radius:12px;margin-bottom:20px;display:block}
.panel-body h2{font-size:1.4rem;font-weight:700;line-height:1.15;color:#1d1d1f;margin-bottom:8px}
.panel-body .meta{font-size:.78rem;color:rgba(0,0,0,.44);margin-bottom:20px}
.panel-body .body{font-size:.95rem;line-height:1.6;color:rgba(0,0,0,.78)}
.panel-body .body p{margin-bottom:14px}
.panel-body .read{display:inline-flex;align-items:center;gap:6px;background:#0071e3;color:#fff;padding:10px 20px;border-radius:980px;font-size:.82rem;font-weight:500;text-decoration:none;margin-top:16px}
.src-section{margin-top:20px;padding-top:14px;border-top:1px solid rgba(0,0,0,.06)}
.src-section h3{font-size:.65rem;font-weight:600;color:rgba(0,0,0,.4);text-transform:uppercase;letter-spacing:1px;margin-bottom:8px}
.src-item{display:flex;align-items:flex-start;gap:8px;margin-bottom:6px;font-size:.8rem}
.src-num{font-weight:700;color:#0071e3;width:20px;height:20px;border-radius:50%;background:rgba(0,113,227,.08);display:flex;align-items:center;justify-content:center;flex-shrink:0;font-size:.65rem}
.src-name{font-weight:600;color:rgba(0,0,0,.55)}
.src-url{color:#0071e3;text-decoration:none;font-size:.68rem;word-break:break-all;display:block;margin-top:2px}

@media(min-width:768px){
header{padding:0 22px}
.hero img{height:380px}
.hero-cat,.hero-title,.hero-desc{padding-left:0;padding-right:0;text-align:center}
.hero-title{font-size:2rem;max-width:700px;margin:0 auto}
.hero-desc{margin:0 auto;text-align:center}
.container,.articles{padding:0 28px}
.art-row{display:flex;gap:20px;align-items:center;padding:24px 0}
.art-img{flex:0 0 240px;margin-bottom:0}
.art-img img{height:160px}
.art-body{flex:1;min-width:0}
.feat{display:flex;align-items:center}
.feat img{width:45%;height:240px}
.feat-body{flex:1}
section{padding:48px 0}
.sec-head h3{font-size:1.7rem}
}
@media(min-width:1024px){
/* Layout */
.layout{display:flex;height:calc(100vh - 48px)}
.feed-col{flex:1;min-width:0;overflow-y:auto;transition:filter .35s cubic-bezier(.4,0,.2,1)}
.panel-head{top:0}

/* Panel latéral (défaut) */
.panel-col{overflow:hidden;background:#fff;transition:width .35s cubic-bezier(.4,0,.2,1);order:-1}
.layout.panel-open .panel-col{width:540px;overflow-y:auto}
.layout.panel-open .feed-col{display:block}

/* Panel overlay (optionnel — via .panel-overlay) */
.layout.panel-overlay .panel-col{position:fixed;top:48px;left:0;right:0;bottom:0;width:90%;max-width:1200px;margin:0 auto;z-index:50;overflow:hidden;border-radius:16px 16px 0 0;box-shadow:0 20px 80px rgba(0,0,0,.25);transform:translateY(24px) scale(.97);opacity:0;transition:transform .4s cubic-bezier(.4,0,.2,1),opacity .4s cubic-bezier(.4,0,.2,1);pointer-events:none}
.layout.panel-overlay.panel-open .panel-col{transform:translateY(0) scale(1);opacity:1;overflow-y:auto;pointer-events:auto}
.layout.panel-overlay.panel-open .feed-col{filter:blur(5px);pointer-events:none;user-select:none}

/* Panel body */
.panel-body{overflow-y:auto;padding:24px 28px 48px}
}

/* ═══════════════════════════════════════════ */
/* Bracket Phase Finale — 2 moitiés           */
/* ═══════════════════════════════════════════ */
.bwrap{display:flex;gap:8px;justify-content:center;overflow-x:auto;padding:12px 4px;margin:0 auto;max-width:1200px}
.bhalf{display:flex;flex-direction:column;align-items:center;min-width:380px;flex:1}
.bhlbl{font-size:11px;font-weight:700;color:#0071e3;margin-bottom:12px;text-align:center}
.brow{display:flex;align-items:center;gap:4px;margin-bottom:8px}
.bcol16{display:flex;flex-direction:column;gap:3px;min-width:130px}
.bcol8{display:flex;flex-direction:column;gap:3px;min-width:105px}
.bcolQ{display:flex;flex-direction:column;justify-content:center;gap:3px;min-width:95px}
.bcolD{display:flex;flex-direction:column;justify-content:center;gap:3px;min-width:95px}
.barr{min-width:16px;text-align:center;font-size:14px;color:rgba(0,0,0,.12);display:flex;align-items:center;justify-content:center}
.bcenter{display:flex;flex-direction:column;align-items:center;justify-content:center;flex-shrink:0;min-width:120px}
.bcolQ .kobox{margin:8px 0}
.bcolD .kobox{margin:10px 0}
.kobox{margin-bottom:3px}
.kodate{font-size:8px;color:#86868b;margin-bottom:1px}
.komatch{background:#fff;border-radius:5px;overflow:hidden;border:1px solid rgba(0,0,0,.08);box-shadow:0 1px 2px rgba(0,0,0,.03)}
.koteam{padding:4px 6px;font-size:10px;font-weight:500;color:#1d1d1f;white-space:nowrap}
.kotop{border-bottom:1px solid rgba(0,0,0,.06);font-weight:700}
.koidle{background:rgba(0,0,0,.015);padding:7px 6px;text-align:center}
.koidletext{font-size:8px;color:rgba(0,0,0,.25);font-style:italic}
.kofinal{max-width:260px;margin:0 auto;text-align:center;padding:8px}
.kofstars{font-size:8px;letter-spacing:2px;color:#f5a623;margin-bottom:1px}
.koftitle{font-size:11px;font-weight:700;color:#1d1d1f}
.kofvs{font-size:11px;font-weight:700;color:#1d1d1f;margin:2px 0}
.kofvenue{font-size:8px;color:#86868b}
.kothird{background:#fff;border-radius:8px;padding:8px 16px;border:1px solid rgba(0,0,0,.06);text-align:center;max-width:280px;margin:12px auto 0}
.kothirdlbl{font-size:8px;color:#0071e3;font-weight:600;text-transform:uppercase;letter-spacing:1px}
.kothirdvs{font-size:10px;font-weight:600;margin-top:2px;color:rgba(0,0,0,.5)}

@media(max-width:700px){
  .bhalf{min-width:260px}
  .bcol16{min-width:100px}
  .bcol8{min-width:80px}
  .bcolQ,.bcolD{min-width:72px}
  .bcenter{min-width:80px}
  .koteam{font-size:8px;padding:3px 4px}
  .kobox{margin-bottom:1px}
}

/* Dark mode */
body.dark{background:#1c1c1e;color:#e8e8ec}
body.dark header{background:rgba(28,28,30,.95);border-color:rgba(255,255,255,.06)}
body.dark .hright a,body.dark .hright button{color:#e8e8ec}
body.dark section.white,body.dark .feat,body.dark .art-row,body.dark .panel-col,body.dark .panel-head{background:#1c1c1e}
body.dark section.light{background:#232326}
body.dark .art-row{border-color:rgba(255,255,255,.04)}
body.dark .art-body h4,body.dark .art-body .excerpt,body.dark .art-body .meta,body.dark .sec-head h3{color:rgba(255,255,255,.8)}
body.dark .sec-head .count{color:rgba(255,255,255,.35)}
body.dark .hero{background:#0a0a0a}
body.dark .panel-head{background:rgba(28,28,30,.92);border-color:rgba(255,255,255,.06)}
body.dark .panel-body h2{color:#e8e8ec}
body.dark .panel-body .body{color:rgba(255,255,255,.78)}
body.dark .src-section{border-color:rgba(255,255,255,.06)}
body.dark .src-section h3{color:rgba(255,255,255,.35)}
body.dark .src-name{color:rgba(255,255,255,.55)}
/* Bracket dark */
body.dark .komatch{background:#232326;border-color:rgba(255,255,255,.06)}
body.dark .koteam{color:#e8e8ec}
body.dark .kotop{border-color:rgba(255,255,255,.06)}
body.dark .koidle{background:rgba(255,255,255,.03)}
body.dark .koidletext{color:rgba(255,255,255,.2)}
body.dark .bhlbl{color:#5e9eff}
body.dark .barr{color:rgba(255,255,255,.1)}
body.dark .bcenter .kofinal{}
body.dark .kofvs{color:#e8e8ec}
body.dark .koftitle{color:#e8e8ec}
body.dark .kothird{background:#232326;border-color:rgba(255,255,255,.06)}
body.dark .kothirdvs{color:rgba(255,255,255,.45)}
/* WC tables dark */
body.dark table,body.dark td,body.dark th{border-color:rgba(255,255,255,.04)}
body.dark td{color:#e8e8ec}
body.dark .cat{color:rgba(255,255,255,.5)}
"""

JS = r"""const ARTICLES = __ARTICLES__;
const CAT_LABELS = {all:'Toutes les actualites',ia:'IA & Tech',crypto:'Crypto',gaming:'Jeux Video',markets:'Marches',general:'General',science:'Science',dev:'Developpement',startups:'Startups',bookmarks:'Sauvegardes',search:'Recherche',worldcup:'Coupe du Monde 2026'};
// Theme
(function(){if(localStorage.theme==='dark'){document.body.classList.add('dark');var t=document.getElementById('themeBtn');if(t)t.textContent='☾'}})();
function toggleTheme(){
  document.body.classList.toggle('dark');
  localStorage.theme=document.body.classList.contains('dark')?'dark':'light';
  var t=document.getElementById('themeBtn');
  if(t)t.textContent=document.body.classList.contains('dark')?'☾':'☀';
}

function toggleBm(id,e){
  if(e)e.stopPropagation();
  isBm(id)?bm=bm.filter(x=>x!==id):bm.push(id);
  saveBm();
  document.querySelectorAll('[data-bmid="'+id+'"]').forEach(b=>b.classList.toggle('on',isBm(id)));
  if(curId===id){
    const pb=document.getElementById('panelBm');
    if(pb){pb.classList.toggle('on',isBm(id));pb.textContent=isBm(id)?'Sauvegarde':'Sauvegarder';}
  }
}

function showTab(c,el){
  cat=c;searchTerm='';
  const si=document.getElementById('searchInput');if(si)si.value='';
  document.querySelectorAll('.hright a').forEach(a=>a.classList.remove('active'));
  if(c==='bookmarks'){const bl=document.getElementById('bmLink');if(bl)bl.classList.add('active')}
  else if(c==='all'){document.querySelector('.hright a')?.classList.add('active')}
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
  if(diffDays === 0) return 'Aujourd\u2019hui';
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
  if(cat==='worldcup'){renderWorldCup(fc);return;}
  const list=(cat==='all'?ARTICLES:ARTICLES.filter(a=>a.cat===cat)).slice().sort((a,b)=>(b.pubTs||0)-(a.pubTs||0));
  if(!list.length){fc.innerHTML='<div class="bm-empty"><h3>Aucun article</h3></div>';return}
  const hero=list[0],rest=list.slice(1);
  const groups={};rest.forEach(a=>{const l=dateLabel(a.pubTs);if(!groups[l])groups[l]=[];groups[l].push(a)});
  let h='',isDark=false;
  // Hero
  h+='<div class="hero">'
    +'<img src="'+esc(hero.image)+'" alt="" onerror="this.style.display=\'none\'">'
    +'<div class="hero-overlay">'
      +'<div class="hero-cat">'+esc(hero.catLabel)+'</div>'
      +'<div class="hero-title">'+esc(hero.title)+'</div>'
      +'<div class="hero-desc">'+esc(hero.excerpt)+'</div>'
    +'</div></div>';
  // Sections
  for(const[l,items]of Object.entries(groups)){
    const bg=isDark?'white':'light';isDark=!isDark;
    h+='<section class="'+bg+'"><div class="container"><div class="sec-head"><h3>'+l+'</h3><div class="count">'+items.length+' article'+(items.length>1?'s':'')+'</div></div></div><div class="articles">';
    items.forEach((a,i)=>{
      const bc=isBm(a.id)?'bm-star on':'bm-star';
      if(i===0&&l==='Aujourd\'hui'){
        h+='<div class="feat" onclick="openPanel(\''+a.id+'\')">'
          +'<img src="'+esc(a.image)+'" alt="" onerror="this.style.display=\'none\'">'
          +'<div class="feat-body">'
            +'<div class="cat">'+esc(a.catLabel)+'</div>'
            +'<h4>'+esc(a.title)+'</h4>'
            +'<div class="excerpt">'+esc(a.excerpt)+'</div>'
            +'<div class="meta">'+esc(a.source)+' \u00b7 '+a.date+' <button class="'+bc+'" data-bmid="'+a.id+'" onclick="toggleBm(\''+a.id+'\',event)">\u2606</button></div>'
          +'</div></div>';
      }else{
        h+='<div class="art-row" onclick="openPanel(\''+a.id+'\')">'
          +'<div class="art-img"><img src="'+esc(a.image)+'" alt="" onerror="this.style.display=\'none\'"></div>'
          +'<div class="art-body">'
            +'<div class="cat">'+esc(a.catLabel)+'</div>'
            +'<h4>'+esc(a.title)+'</h4>'
            +'<div class="excerpt">'+esc(a.excerpt)+'</div>'
            +'<div class="meta">'+esc(a.source)+' \u00b7 '+a.date+' <button class="'+bc+'" data-bmid="'+a.id+'" onclick="toggleBm(\''+a.id+'\',event)">\u2606</button></div>'
          +'</div></div>';
      }
    });
    h+='</div></section>';
  }
  fc.innerHTML=h;
}

function onSearch(q){
  searchTerm=q.trim().toLowerCase();cat=searchTerm?'search':'all';closePanel();render();
}
function renderSearch(fc){
  const found=ARTICLES.filter(a=>((a.title||'')+' '+(a.excerpt||'')+' '+a.catLabel).toLowerCase().includes(searchTerm)).sort((a,b)=>(b.pubTs||0)-(a.pubTs||0));
  if(!found.length){fc.innerHTML='<div class="bm-empty"><h3>Aucun resultat</h3><p>pour "'+esc(searchTerm)+'"</p></div>';return}
  let h='',isDark=false;const g={};found.forEach(a=>{const l=dateLabel(a.pubTs);if(!g[l])g[l]=[];g[l].push(a)});
  for(const[l,items]of Object.entries(g)){
    const bg=isDark?'white':'light';isDark=!isDark;
    h+='<section class="'+bg+'"><div class="container"><div class="sec-head"><h3>'+l+'</h3><div class="count">'+items.length+' resultat'+(items.length>1?'s':'')+'</div></div></div><div class="articles">';
    items.forEach(a=>{
      h+='<div class="art-row" onclick="openPanel(\''+a.id+'\')">'
        +'<div class="art-img"><img src="'+esc(a.image)+'" alt="" onerror="this.style.display=\'none\'"></div>'
        +'<div class="art-body"><div class="cat">'+esc(a.catLabel)+'</div><h4>'+esc(a.title)+'</h4><div class="excerpt">'+esc(a.excerpt)+'</div><div class="meta">'+esc(a.source)+' \u00b7 '+a.date+'</div></div></div>';
    });
    h+='</div></section>';
  }
  fc.innerHTML=h;
}

function renderBm(fc){
  const saved=ARTICLES.filter(a=>isBm(a.id));
  if(!saved.length){fc.innerHTML='<div class="bm-empty"><h3>\u2606</h3><p>Aucun article sauvegarde.</p></div>';return}
  let h='<section class="light"><div class="container"><div class="sec-head"><h3>Sauvegardes</h3><div class="count">'+saved.length+' article'+(saved.length>1?'s':'')+'</div></div></div><div class="articles">';
  saved.forEach(a=>{
    const bc=isBm(a.id)?'bm-star on':'bm-star';
    h+='<div class="art-row" onclick="openPanel(\''+a.id+'\')">'
      +'<div class="art-img"><img src="'+esc(a.image)+'" alt="" onerror="this.style.display=\'none\'"></div>'
      +'<div class="art-body"><div class="cat">'+esc(a.catLabel)+'</div><h4>'+esc(a.title)+'</h4><div class="excerpt">'+esc(a.excerpt)+'</div><div class="meta">'+esc(a.source)+' \u00b7 '+a.date+'</div></div></div>';
  });
  fc.innerHTML=h+'</div></section>';
}
// ───── Coupe du Monde 2026 ─────
const WC_GROUPS = {
  A:{name:'Groupe A',teams:[
    {team:'Mexique',flag:'🇲🇽',p:7,gf:6,ga:0,pl:3,q:true},
    {team:'Afrique du Sud',flag:'🇿🇦',p:4,gf:2,ga:3,pl:3,q:true},
    {team:'Coree du Sud',flag:'🇰🇷',p:3,gf:2,ga:3,pl:3,e:true},
    {team:'Republique Tcheque',flag:'🇨🇿',p:1,gf:2,ga:6,pl:3,e:true}
  ]},
  B:{name:'Groupe B',teams:[
    {team:'Suisse',flag:'🇨🇭',p:7,gf:7,ga:3,pl:3,q:true},
    {team:'Canada',flag:'🇨🇦',p:4,gf:8,ga:3,pl:3,q:true},
    {team:'Bosnie-Herzegovine',flag:'🇧🇦',p:4,gf:5,ga:6,pl:3},
    {team:'Qatar',flag:'🇶🇦',p:1,gf:2,ga:10,pl:3,e:true}
  ]},
  C:{name:'Groupe C',teams:[
    {team:'Bresil',flag:'🇧🇷',p:7,gf:7,ga:1,pl:3,q:true},
    {team:'Maroc',flag:'🇲🇦',p:7,gf:6,ga:3,pl:3,q:true},
    {team:'Ecosse',flag:'🏴󠁧󠁢󠁳󠁣󠁴󠁿',p:3,gf:1,ga:4,pl:3,e:true},
    {team:'Haiti',flag:'🇭🇹',p:0,gf:2,ga:8,pl:3,e:true}
  ]},
  D:{name:'Groupe D',teams:[
    {team:'Etats-Unis',flag:'🇺🇸',p:6,gf:8,ga:4,pl:3,q:true},
    {team:'Australie',flag:'🇦🇺',p:4,gf:2,ga:2,pl:3,q:true},
    {team:'Paraguay',flag:'🇵🇾',p:4,gf:2,ga:4,pl:3},
    {team:'Turkiye',flag:'🇹🇷',p:3,gf:3,ga:5,pl:3,e:true}
  ]},
  E:{name:'Groupe E',teams:[
    {team:'Cote d\'Ivoire',flag:'🇨🇮',p:6,gf:4,ga:2,pl:3,q:true},
    {team:'Allemagne',flag:'🇩🇪',p:6,gf:10,ga:4,pl:3,q:true},
    {team:'Equateur',flag:'🇪🇨',p:4,gf:2,ga:2,pl:3},
    {team:'Curacao',flag:'🇨🇼',p:1,gf:1,ga:9,pl:3,e:true}
  ]},
  F:{name:'Groupe F',teams:[
    {team:'Pays-Bas',flag:'🇳🇱',p:7,gf:10,ga:4,pl:3,q:true},
    {team:'Japon',flag:'🇯🇵',p:5,gf:7,ga:3,pl:3,q:true},
    {team:'Suede',flag:'🇸🇪',p:4,gf:7,ga:7,pl:3},
    {team:'Tunisie',flag:'🇹🇳',p:0,gf:2,ga:12,pl:3,e:true}
  ]},
  G:{name:'Groupe G',teams:[
    {team:'Belgique',flag:'🇧🇪',p:5,gf:6,ga:2,pl:3,q:true},
    {team:'Egypte',flag:'🇪🇬',p:5,gf:5,ga:3,pl:3,q:true},
    {team:'Iran',flag:'🇮🇷',p:3,gf:3,ga:3,pl:3,e:true},
    {team:'Nouvelle-Zelande',flag:'🇳🇿',p:1,gf:4,ga:10,pl:3,e:true}
  ]},
  H:{name:'Groupe H',teams:[
    {team:'Espagne',flag:'🇪🇸',p:7,gf:5,ga:0,pl:3,q:true},
    {team:'Cap-Vert',flag:'🇨🇻',p:3,gf:2,ga:2,pl:3,q:true},
    {team:'Uruguay',flag:'🇺🇾',p:2,gf:3,ga:4,pl:3,e:true},
    {team:'Arabie Saoudite',flag:'🇸🇦',p:2,gf:1,ga:5,pl:3,e:true}
  ]},
  I:{name:'Groupe I',teams:[
    {team:'France',flag:'🇫🇷',p:9,gf:10,ga:2,pl:3,q:true},
    {team:'Norvege',flag:'🇳🇴',p:6,gf:8,ga:7,pl:3,q:true},
    {team:'Senegal',flag:'🇸🇳',p:3,gf:8,ga:6,pl:3},
    {team:'Irak',flag:'🇮🇶',p:0,gf:1,ga:12,pl:3,e:true}
  ]},
  J:{name:'Groupe J',teams:[
    {team:'Argentine',flag:'🇦🇷',p:9,gf:8,ga:1,pl:3,q:true},
    {team:'Autriche',flag:'🇦🇹',p:4,gf:6,ga:6,pl:3,q:true},
    {team:'Algerie',flag:'🇩🇿',p:4,gf:5,ga:7,pl:3},
    {team:'Jordanie',flag:'🇯🇴',p:0,gf:3,ga:8,pl:3,e:true}
  ]},
  K:{name:'Groupe K',teams:[
    {team:'Colombie',flag:'🇨🇴',p:7,gf:4,ga:1,pl:3,q:true},
    {team:'Portugal',flag:'🇵🇹',p:5,gf:6,ga:1,pl:3,q:true},
    {team:'RD Congo',flag:'🇨🇩',p:4,gf:4,ga:3,pl:3},
    {team:'Ouzbekistan',flag:'🇺🇿',p:0,gf:2,ga:11,pl:3,e:true}
  ]},
  L:{name:'Groupe L',teams:[
    {team:'Angleterre',flag:'🏴󠁧󠁢󠁥󠁮󠁧󠁿',p:7,gf:6,ga:2,pl:3,q:true},
    {team:'Croatie',flag:'🇭🇷',p:6,gf:5,ga:5,pl:3,q:true},
    {team:'Ghana',flag:'🇬🇭',p:4,gf:2,ga:2,pl:3},
    {team:'Panama',flag:'🇵🇦',p:0,gf:0,ga:4,pl:3,e:true}
  ]}
};

const WC_MATCHES_DONE = [
  {g:'A',d:'11 juin',t1:'Mexique',t2:'Afrique du Sud',s1:2,s2:0},
  {g:'A',d:'11 juin',t1:'Coree du Sud',t2:'Republique Tcheque',s1:2,s2:1},
  {g:'A',d:'18 juin',t1:'Republique Tcheque',t2:'Afrique du Sud',s1:1,s2:1},
  {g:'A',d:'18 juin',t1:'Mexique',t2:'Coree du Sud',s1:1,s2:0},
  {g:'B',d:'12 juin',t1:'Canada',t2:'Bosnie-Herzegovine',s1:1,s2:1},
  {g:'B',d:'13 juin',t1:'Qatar',t2:'Suisse',s1:1,s2:1},
  {g:'B',d:'18 juin',t1:'Suisse',t2:'Bosnie-Herzegovine',s1:4,s2:1},
  {g:'B',d:'18 juin',t1:'Canada',t2:'Qatar',s1:6,s2:0},
  {g:'C',d:'13 juin',t1:'Bresil',t2:'Maroc',s1:1,s2:1},
  {g:'C',d:'13 juin',t1:'Haiti',t2:'Ecosse',s1:0,s2:1},
  {g:'C',d:'19 juin',t1:'Ecosse',t2:'Maroc',s1:0,s2:1},
  {g:'C',d:'19 juin',t1:'Bresil',t2:'Haiti',s1:3,s2:0},
  {g:'D',d:'12 juin',t1:'Etats-Unis',t2:'Paraguay',s1:4,s2:1},
  {g:'D',d:'13 juin',t1:'Australie',t2:'Turkiye',s1:2,s2:0},
  {g:'D',d:'19 juin',t1:'Etats-Unis',t2:'Australie',s1:2,s2:0},
  {g:'D',d:'19 juin',t1:'Turkiye',t2:'Paraguay',s1:0,s2:1},
  {g:'E',d:'14 juin',t1:'Allemagne',t2:'Curacao',s1:7,s2:1},
  {g:'E',d:'14 juin',t1:'Cote d\'Ivoire',t2:'Equateur',s1:1,s2:0},
  {g:'E',d:'20 juin',t1:'Allemagne',t2:'Cote d\'Ivoire',s1:2,s2:1},
  {g:'E',d:'20 juin',t1:'Equateur',t2:'Curacao',s1:0,s2:0},
  {g:'F',d:'14 juin',t1:'Pays-Bas',t2:'Japon',s1:2,s2:2},
  {g:'F',d:'14 juin',t1:'Suede',t2:'Tunisie',s1:5,s2:1},
  {g:'F',d:'20 juin',t1:'Pays-Bas',t2:'Suede',s1:5,s2:1},
  {g:'F',d:'20 juin',t1:'Tunisie',t2:'Japon',s1:0,s2:4},
  {g:'G',d:'15 juin',t1:'Belgique',t2:'Egypte',s1:1,s2:1},
  {g:'G',d:'15 juin',t1:'Iran',t2:'Nouvelle-Zelande',s1:2,s2:2},
  {g:'G',d:'21 juin',t1:'Belgique',t2:'Iran',s1:0,s2:0},
  {g:'G',d:'21 juin',t1:'Nouvelle-Zelande',t2:'Egypte',s1:1,s2:3},
  {g:'H',d:'15 juin',t1:'Espagne',t2:'Cap-Vert',s1:0,s2:0},
  {g:'H',d:'15 juin',t1:'Arabie Saoudite',t2:'Uruguay',s1:1,s2:1},
  {g:'H',d:'21 juin',t1:'Espagne',t2:'Arabie Saoudite',s1:4,s2:0},
  {g:'H',d:'21 juin',t1:'Uruguay',t2:'Cap-Vert',s1:2,s2:2},
  {g:'I',d:'16 juin',t1:'France',t2:'Senegal',s1:3,s2:1},
  {g:'I',d:'16 juin',t1:'Irak',t2:'Norvege',s1:1,s2:4},
  {g:'I',d:'22 juin',t1:'France',t2:'Irak',s1:3,s2:0},
  {g:'I',d:'22 juin',t1:'Norvege',t2:'Senegal',s1:3,s2:2},
  {g:'J',d:'16 juin',t1:'Argentine',t2:'Algerie',s1:3,s2:0},
  {g:'J',d:'16 juin',t1:'Autriche',t2:'Jordanie',s1:3,s2:1},
  {g:'J',d:'22 juin',t1:'Argentine',t2:'Autriche',s1:2,s2:0},
  {g:'J',d:'22 juin',t1:'Jordanie',t2:'Algerie',s1:1,s2:2},
  {g:'K',d:'17 juin',t1:'Portugal',t2:'RD Congo',s1:1,s2:1},
  {g:'K',d:'17 juin',t1:'Ouzbekistan',t2:'Colombie',s1:1,s2:3},
  {g:'K',d:'23 juin',t1:'Portugal',t2:'Ouzbekistan',s1:5,s2:0},
  {g:'K',d:'23 juin',t1:'Colombie',t2:'RD Congo',s1:1,s2:0},
  {g:'L',d:'17 juin',t1:'Angleterre',t2:'Croatie',s1:4,s2:2},
  {g:'L',d:'17 juin',t1:'Ghana',t2:'Panama',s1:1,s2:0},
  {g:'L',d:'23 juin',t1:'Angleterre',t2:'Ghana',s1:0,s2:0},
  {g:'L',d:'23 juin',t1:'Panama',t2:'Croatie',s1:0,s2:1},
  {g:'A',d:'24 juin',t1:'Republique Tcheque',t2:'Mexique',s1:0,s2:3},
  {g:'A',d:'24 juin',t1:'Afrique du Sud',t2:'Coree du Sud',s1:1,s2:0},
  {g:'B',d:'24 juin',t1:'Suisse',t2:'Canada',s1:2,s2:1},
  {g:'B',d:'24 juin',t1:'Bosnie-Herzegovine',t2:'Qatar',s1:3,s2:1},
  {g:'C',d:'24 juin',t1:'Ecosse',t2:'Bresil',s1:0,s2:3},
  {g:'C',d:'24 juin',t1:'Maroc',t2:'Haiti',s1:4,s2:2},
  {g:'E',d:'25 juin',t1:'Equateur',t2:'Allemagne',s1:2,s2:1},
  {g:'E',d:'25 juin',t1:'Curacao',t2:'Cote d\'Ivoire',s1:0,s2:2},
  {g:'F',d:'25 juin',t1:'Japon',t2:'Suede',s1:1,s2:1},
  {g:'F',d:'25 juin',t1:'Tunisie',t2:'Pays-Bas',s1:1,s2:3},
  {g:'D',d:'25 juin',t1:'Turkiye',t2:'Etats-Unis',s1:3,s2:2},
  {g:'D',d:'25 juin',t1:'Paraguay',t2:'Australie',s1:0,s2:0},
  {g:'I',d:'26 juin',t1:'Norvege',t2:'France',s1:1,s2:4},
  {g:'I',d:'26 juin',t1:'Senegal',t2:'Irak',s1:5,s2:0},
  {g:'H',d:'26 juin',t1:'Cap-Vert',t2:'Arabie Saoudite',s1:0,s2:0},
  {g:'H',d:'26 juin',t1:'Uruguay',t2:'Espagne',s1:0,s2:1},
  {g:'G',d:'26 juin',t1:'Egypte',t2:'Iran',s1:1,s2:1},
  {g:'G',d:'26 juin',t1:'Nouvelle-Zelande',t2:'Belgique',s1:1,s2:5},
  {g:'L',d:'27 juin',t1:'Panama',t2:'Angleterre',s1:0,s2:2},
  {g:'L',d:'27 juin',t1:'Croatie',t2:'Ghana',s1:2,s2:1},
  {g:'K',d:'27 juin',t1:'Colombie',t2:'Portugal',s1:0,s2:0},
  {g:'K',d:'27 juin',t1:'RD Congo',t2:'Ouzbekistan',s1:3,s2:1},
  {g:'J',d:'27 juin',t1:'Algerie',t2:'Autriche',s1:3,s2:3},
  {g:'J',d:'27 juin',t1:'Jordanie',t2:'Argentine',s1:1,s2:3}
];

const WC_MATCHES_UPCOMING = [
  // Fin des phases de groupes — les 16es de finale débutent le 29 juin
];

function renderWorldCup(fc){
  var n=new Date();if(n>=new Date('2026-07-23T00:00:00')){fc.innerHTML='<div class="bm-empty"><h3>⚽</h3><p>Section archivée.</p></div>';return}
  var h='',dk=false;

  // Phase Finale — affichée en premier
  h+='<section class="white"><div class="container"><div class="sec-head"><h3>Phase Finale</h3><div class="count">16es de finale · 29 juin – 19 juillet · Heure de Paris</div></div></div>';
  h+='<p style="text-align:center;color:rgba(0,0,0,.45);font-size:.82rem;margin-bottom:20px">32 qualifiés · Défilez horizontalement pour voir la suite →</p>';
  
  // REAL match data from touteleurope.eu (Paris time)
  // Moitié Haute
  var mh=[[
    ['28 juin','21h00','🇿🇦 Afrique du Sud','🇨🇦 Canada'],
    ['29 juin','19h00','🇧🇷 Brésil','🇯🇵 Japon'],
    ['29 juin','22h30','🇩🇪 Allemagne','🇵🇾 Paraguay'],
    ['30 juin','03h00','🇳🇱 Pays-Bas','🇲🇦 Maroc']
  ],[
    ['30 juin','19h00','🇨🇮 Côte d\'Ivoire','🇳🇴 Norvège'],
    ['30 juin','23h00','🇫🇷 France','🇸🇪 Suède'],
    ['1 juil.','03h00','🇲🇽 Mexique','🇪🇨 Équateur'],
    ['1 juil.','18h00','🏴󠁧󠁢󠁥󠁮󠁧󠁿 Angleterre','🇨🇩 RD Congo']
  ]];
  // Moitié Basse
  var mb2=[[
    ['1 juil.','22h00','🇧🇪 Belgique','🇸🇳 Sénégal'],
    ['2 juil.','02h00','🇺🇸 États-Unis','🇧🇦 Bosnie-Herzégovine'],
    ['2 juil.','21h00','🇪🇸 Espagne','🇦🇹 Autriche'],
    ['3 juil.','01h00','🇵🇹 Portugal','🇭🇷 Croatie']
  ],[
    ['3 juil.','05h00','🇨🇭 Suisse','🇩🇿 Algérie'],
    ['3 juil.','20h00','🇦🇺 Australie','🇪🇬 Égypte'],
    ['4 juil.','00h00','🇦🇷 Argentine','🇨🇻 Cap Vert'],
    ['4 juil.','03h30','🇨🇴 Colombie','🇬🇭 Ghana']
  ]];
  
  function mbx(m){return'<div class="kobox"><div class="kodate">'+m[0]+' · '+m[1]+'</div><div class="komatch"><div class="koteam kotop">'+m[2]+'</div><div class="koteam">'+m[3]+'</div></div></div>';}
  function mw(matchNum,date,hour){return'<div class="kobox"><div class="kodate">'+date+' · '+hour+'</div><div class="komatch koidle"><div class="koidletext">Vainqueur<br>match '+matchNum+'</div></div></div>';}
  
  h+='<div class="bwrap">';
  
  // ═══ MOITIÉ HAUTE (16es à gauche → Demi au centre) ═══
  h+='<div class="bhalf"><div class="bhlbl">🔼 Moitié Haute</div>';
  // Row 0: 16es → 8es → Quart
  h+='<div class="brow">';
  h+='<div class="bcol16">'+mbx(mh[0][0])+mbx(mh[0][1])+mbx(mh[0][2])+mbx(mh[0][3])+'</div>';
  h+='<div class="barr">→</div><div class="bcol8">'+mw(89,'4 juil.','23h00')+mw(90,'4 juil.','19h00')+'</div>';
  h+='<div class="barr">→</div><div class="bcolQ">'+mw(97,'7 juil.','18h00')+'</div>';
  h+='</div>';
  // Demi — alignée avec les Quarts via colonnes invisibles
  h+='<div class="brow">';
  h+='<div class="bcol16" style="visibility:hidden">·</div><div class="barr" style="visibility:hidden">→</div>';
  h+='<div class="bcol8" style="visibility:hidden">·</div><div class="barr" style="visibility:hidden">→</div>';
  h+='<div class="bcolD">'+mw(101,'14 juil.','21h00')+'</div></div>';
  // Row 2: 16es → 8es → Quart
  h+='<div class="brow">';
  h+='<div class="bcol16">'+mbx(mh[1][0])+mbx(mh[1][1])+mbx(mh[1][2])+mbx(mh[1][3])+'</div>';
  h+='<div class="barr">→</div><div class="bcol8">'+mw(91,'6 juil.','21h00')+mw(92,'7 juil.','02h00')+'</div>';
  h+='<div class="barr">→</div><div class="bcolQ">'+mw(98,'7 juil.','22h00')+'</div>';
  h+='</div></div>';
  
  // ═══ CENTRE → FINALE ═══
  h+='<div class="bcenter"><div class="kofinal"><div class="kofstars">★ ★ ★ ★ ★</div><div class="koftitle">🏆 FINALE</div><div class="kofvs">19 juillet · 21h00</div><div class="kofvenue">MetLife Stadium</div></div></div>';
  
  // ═══ MOITIÉ BASSE (16es à droite ← Demi au centre) ═══
  h+='<div class="bhalf"><div class="bhlbl">🔽 Moitié Basse</div>';
  // Row 0: Quart ← 8es ← 16es (sans Demi)
  h+='<div class="brow">';
  h+='<div class="bcolD" style="visibility:hidden">·</div><div class="barr" style="visibility:hidden">←</div>';
  h+='<div class="bcolQ">'+mw(99,'9 juil.','22h00')+'</div>';
  h+='<div class="barr">←</div><div class="bcol8">'+mw(93,'5 juil.','22h00')+mw(94,'6 juil.','02h00')+'</div>';
  h+='<div class="barr">←</div><div class="bcol16">'+mbx(mb2[0][0])+mbx(mb2[0][1])+mbx(mb2[0][2])+mbx(mb2[0][3])+'</div>';
  h+='</div>';
  // Demi — centrée entre les deux rows (comme Haute)
  h+='<div class="brow">';
  h+='<div class="bcolD">'+mw(102,'15 juil.','21h00')+'</div>';
  h+='<div class="barr" style="visibility:hidden">←</div><div class="bcolQ" style="visibility:hidden">·</div>';
  h+='<div class="barr" style="visibility:hidden">←</div><div class="bcol8" style="visibility:hidden">·</div>';
  h+='<div class="barr" style="visibility:hidden">←</div><div class="bcol16" style="visibility:hidden">·</div>';
  h+='</div>';
  // Row 2: Quart ← 8es ← 16es (sans Demi)
  h+='<div class="brow">';
  h+='<div class="bcolD" style="visibility:hidden">·</div><div class="barr" style="visibility:hidden">←</div>';
  h+='<div class="bcolQ">'+mw(100,'12 juil.','03h00')+'</div>';
  h+='<div class="barr">←</div><div class="bcol8">'+mw(95,'10 juil.','21h00')+mw(96,'11 juil.','23h00')+'</div>';
  h+='<div class="barr">←</div><div class="bcol16">'+mbx(mb2[1][0])+mbx(mb2[1][1])+mbx(mb2[1][2])+mbx(mb2[1][3])+'</div>';
  h+='</div></div>';
  
  h+='</div>';
  
  // 3e place
  h+='<div class="kothird"><div class="kothirdlbl">🥉 Match pour la 3<sup>e</sup> place · 18 juillet · 23h00</div>';
  h+='<div class="kothirdvs">Perdant Demi-finale 1 — Perdant Demi-finale 2</div></div>';
  h+='</section>';

  // Groupes — affichés après la Phase Finale
  h+='<section class="light"><div class="container"><div class="sec-head"><h3>Phases de Groupes</h3><div class="count">12 groupes · 3e journée</div></div></div>';
  h+='<div style="max-width:960px;margin:0 auto;padding:0 28px;display:grid;grid-template-columns:repeat(auto-fill,minmax(310px,1fr));gap:18px">';
  for(var gk in WC_GROUPS){var g=WC_GROUPS[gk];
    h+='<div style="background:#fff;border-radius:16px;padding:24px 26px;box-shadow:rgba(0,0,0,.05)0 1px 4px">';
    h+='<div class="cat">'+g.name+'</div>';
    h+='<table style="width:100%;border-collapse:collapse;font-size:.76rem;margin-top:12px">';
    h+='<tr style="color:rgba(0,0,0,.3);font-size:.6rem;text-transform:uppercase;letter-spacing:1px"><th style="text-align:left;padding:6px 6px;font-weight:500">Équipe</th><th style="text-align:center;padding:6px 3px;font-weight:500">J</th><th style="text-align:center;padding:6px 3px;font-weight:500">V</th><th style="text-align:center;padding:6px 3px;font-weight:500">N</th><th style="text-align:center;padding:6px 3px;font-weight:500">D</th><th style="text-align:center;padding:6px 3px;font-weight:500">+/-</th><th style="text-align:center;padding:6px 3px;font-weight:500;color:#0071e3">Pts</th></tr>';
    var s=g.teams;
    for(var i=0;i<s.length;i++){var t=s[i],gp=t.pl||2,gd=t.gf-t.ga,st=t.q?'<span style="font-size:.55rem;color:#059669;margin-left:3px">Q</span>':t.e?'<span style="font-size:.55rem;color:#dc2626;margin-left:3px">E</span>':'';
      h+='<tr style="border-bottom:1px solid rgba(0,0,0,.04)"><td style="padding:7px 6px;font-weight:600;font-size:.74rem">'+t.flag+' '+t.team+st+'</td><td style="text-align:center;padding:7px 3px;font-size:.72rem">'+gp+'</td><td style="text-align:center;padding:7px 3px;font-size:.72rem">'+Math.floor(t.p/3)+'</td><td style="text-align:center;padding:7px 3px;font-size:.72rem">'+(t.p%3!==0?1:0)+'</td><td style="text-align:center;padding:7px 3px;font-size:.72rem">'+(gp-Math.floor(t.p/3)-(t.p%3!==0?1:0))+'</td><td style="text-align:center;padding:7px 3px;font-size:.72rem">'+(gd>0?'+':'')+gd+'</td><td style="text-align:center;padding:7px 3px;font-weight:700;color:#0071e3;font-size:.76rem">'+t.p+'</td></tr>';
    }
    h+='</table></div>';
  }
  h+='</div></section>';

  // Matchs Joués
  h+='<section class="light"><div class="container"><div class="sec-head"><h3>Matchs Joués</h3></div></div>';
  h+='<div style="max-width:960px;margin:0 auto;padding:0 28px;display:grid;grid-template-columns:repeat(auto-fill,minmax(420px,1fr));gap:6px">';
  var bd={};for(var i=0;i<WC_MATCHES_DONE.length;i++){var m=WC_MATCHES_DONE[i];if(!bd[m.g])bd[m.g]=[];bd[m.g].push(m)}
  for(var gk in bd){var matches=bd[gk],gn=WC_GROUPS[gk]?WC_GROUPS[gk].name:'Groupe '+gk;
    h+='<div style="padding:16px 0;border-bottom:1px solid rgba(0,0,0,.05)"><div class="cat" style="margin-bottom:10px">'+gn+'</div>';
    for(var j=0;j<matches.length;j++){var m=matches[j],c1=m.s1>m.s2?'#059669':m.s1===m.s2?'rgba(0,0,0,.4)':'',c2=m.s2>m.s1?'#059669':m.s2===m.s1?'rgba(0,0,0,.4)':'';
    h+='<div style="display:flex;align-items:center;justify-content:space-between;padding:5px 0;font-size:.8rem">'
      +'<span><span style="font-weight:'+(m.s1>m.s2?'700':'400')+';color:'+c1+'">'+m.t1+'</span> <span style="color:rgba(0,0,0,.2);font-size:.68rem">vs</span> <span style="font-weight:'+(m.s2>m.s1?'700':'400')+';color:'+c2+'">'+m.t2+'</span></span>'
      +'<span style="font-size:.78rem;display:flex;align-items:center;gap:4px"><b style="color:'+c1+'">'+m.s1+'</b><span style="color:rgba(0,0,0,.2)">-</span><b style="color:'+c2+'">'+m.s2+'</b><span style="color:rgba(0,0,0,.25);font-size:.66rem;margin-left:6px">'+m.d+'</span></span></div>';
    }
    h+='</div>';
  }
  h+='</div></section>';

  // Matchs à Venir
  h+='<section class="white"><div class="container"><div class="sec-head"><h3>Matchs à Venir</h3></div></div>';
  h+='<div style="max-width:960px;margin:0 auto;padding:0 28px;display:grid;grid-template-columns:repeat(auto-fill,minmax(420px,1fr));gap:6px">';
  var bu={};for(var i=0;i<WC_MATCHES_UPCOMING.length;i++){var m=WC_MATCHES_UPCOMING[i];if(!bu[m.g])bu[m.g]=[];bu[m.g].push(m)}
  for(var gk in bu){var matches=bu[gk],gn=WC_GROUPS[gk]?WC_GROUPS[gk].name:'Groupe '+gk;
    h+='<div style="padding:16px 0;border-bottom:1px solid rgba(0,0,0,.05)"><div class="cat" style="margin-bottom:10px">'+gn+'</div>';
    for(var j=0;j<matches.length;j++){var m=matches[j];
    h+='<div style="display:flex;align-items:center;justify-content:space-between;padding:5px 0;font-size:.8rem">'
      +'<span>'+m.t1+' <span style="color:rgba(0,0,0,.2);font-size:.68rem">vs</span> '+m.t2+'</span>'
      +'<span style="font-weight:600;font-size:.74rem;color:#0071e3">'+m.d+' · '+m.h+'</span></div>';
    }
    h+='</div>';
  }
  h+='</div></section>';

  h+='<div style="text-align:center;padding:40px;color:rgba(0,0,0,.3);font-size:.68rem">Dernière mise à jour : 27 juin 2026</div>';
  fc.innerHTML=h;
}
function openPanel(id){
  const a=ARTICLES.find(x=>x.id===id);if(!a)return;curId=id;
  const panel=document.getElementById('panel'),layout=document.getElementById('layout');
  if(!panel||!layout)return;
  panel.innerHTML='<div class="panel-head">'
    +'<div class="cat" style="margin:0;font-size:.62rem">'+esc(a.catLabel)+'</div>'
    +'<div style="display:flex;gap:6px;align-items:center">'
    +'<button class="panel-close" onclick="toggleOverlay()" title="Plein écran" style="font-size:.85rem">\u26F6</button>'
    +'<button class="panel-close" onclick="closePanel()">\u2715</button></div></div>'
    +'<div class="panel-body">'
      +'<img src="'+esc(a.image)+'" alt="" onerror="this.style.display=\'none\'">'
      +'<h2>'+esc(a.title)+'</h2>'
      +'<div class="meta">'+esc(a.source)+' \u00b7 '+a.date+' \u00b7 '+a.readTime+' de lecture</div>'
      +'<div class="body">'+((BODIES||{})[a.id]||'<p>'+esc(a.excerpt)+'</p>')+'</div>'
      +'<a class="read" href="'+esc(a.url)+'" target="_blank">Lire l\'article complet \u2192</a>'
      +'<div class="src-section"><h3>Source originale</h3>'
        +'<div class="src-item"><span class="src-num">1</span><div><span class="src-name">'+esc(a.source)+'</span><a class="src-url" href="'+esc(a.url)+'">'+esc(a.url)+'</a></div></div>'
      +'</div>'
    +'</div>';
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
  return (paras.length?paras:[text]).map(p=>'<p>'+esc(p)+'</p>').join('');
}

function closePanel(){
  curId=null;
  document.getElementById('layout').classList.remove('panel-open','panel-overlay');
  document.getElementById('panel').innerHTML='';
  document.querySelectorAll('.active-card').forEach(el=>el.classList.remove('active-card'));
}
function toggleOverlay(){
  const lay=document.getElementById('layout');
  lay.classList.toggle('panel-overlay');
  const btn=document.querySelector('.panel-head button[onclick*=\"toggleOverlay\"]');
  if(btn)btn.textContent=lay.classList.contains('panel-overlay')?'\u26F6':'⛶';
}

document.addEventListener('keydown',e=>{if(e.key==='Escape')closePanel();});
"""


def generate_html(articles, last_update):
    articles_json = build_articles_json(articles)
    bodies_json = build_bodies_json(articles)
    feed_html = build_feed_html(articles)
    js_core = JS.replace("__ARTICLES__", articles_json)

    return f"""<!DOCTYPE html>
<html lang="fr">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>TechFeed</title>
<style>{CSS}</style>
</head>
<body>
<header>
  <div class="logo">&#128240; TechFeed <em>NEWS</em></div>
  <div class="hright">
    <span class="upd">{last_update}</span>
    <button id="themeBtn" onclick="toggleTheme()" style="font-size:.85rem;width:36px;height:36px;display:flex;align-items:center;justify-content:center;background:none;border:none;cursor:pointer;color:#1d1d1f;opacity:.6;border-radius:50%" onmouseover="this.style.opacity='1';this.style.background='rgba(0,0,0,.04)'" onmouseout="this.style.opacity='.6';this.style.background='none'">☀</button>
    <div class="search-wrap"><input id="searchInput" type="text" placeholder="Rechercher..." oninput="onSearch(this.value)"></div>
    <a href="#" onclick="showTab('all');return false" title="Accueil">&#127968;</a>
    <a href="#" onclick="showTab('ia');return false" title="IA">&#129302;</a>
    <a href="#" onclick="showTab('crypto');return false" title="Crypto">&#8383;</a>
    <a href="#" onclick="showTab('gaming');return false" title="Jeux">&#127918;</a>
    <a href="#" onclick="showTab('markets');return false" title="Marchés">&#128200;</a>
    <a href="#" onclick="showTab('general');return false" title="Général">&#127758;</a>
    <a href="#" onclick="showTab('worldcup');return false" title="Coupe du Monde">&#9917;</a>
    <a href="#" id="bmLink" onclick="showTab('bookmarks');return false" title="Sauvegardes">&#11088;</a>
  </div>
</header>
<div class="layout" id="layout">
  <div class="feed-col" id="feed">{feed_html}</div>
  <div class="panel-col" id="panel"></div>
  <div class="backdrop" id="backdrop" onclick="closePanel()"></div>
</div>
<script>{js_core}</script>
<script defer>const BODIES = {bodies_json};</script>
</body>
</html>"""


def main():
    print("TechFeed v4 - Generation du site (Magazine)...")
    
    articles = load_articles_js()
    print(f"  -> {len(articles)} articles (articles.js)")
    
    last_update = datetime.now().strftime("%d %B %Y - %H:%M")
    content = generate_html(articles, last_update)
    with open("index.html", "w", encoding="utf-8") as f:
        f.write(content)
    open(".nojekyll", "w").close()
    
    print(f"OK - {len(articles)} articles, {len(content)//1024}KB")


if __name__ == "__main__":
    main()
