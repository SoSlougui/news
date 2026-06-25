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
.panel-col{display:none}
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
.panel-close{width:32px;height:32px;border-radius:50%;background:rgba(0,0,0,.04);border:none;cursor:pointer;font-size:1rem;display:flex;align-items:center;justify-content:center;color:#1d1d1f}
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

/* Desktop improvements */
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
.layout{display:flex;height:calc(100vh - 48px)}
.feed-col{flex:1;min-width:0;overflow-y:auto}
.panel-col{width:0;overflow:hidden;background:#fff;transition:width .35s;order:-1}
.panel-head{top:0}
.layout.panel-open .feed-col{display:block}
.layout.panel-open .panel-col{width:540px;display:block;overflow-y:auto}
}
"""

JS = r"""const ARTICLES = __ARTICLES__;
const CAT_LABELS = {all:'Toutes les actualites',ia:'IA & Tech',crypto:'Crypto',gaming:'Jeux Video',markets:'Marches',general:'General',science:'Science',dev:'Developpement',startups:'Startups',bookmarks:'Sauvegardes',search:'Recherche',worldcup:'Coupe du Monde 2026'};
// Theme
(function(){if(localStorage.theme==='dark'){document.body.classList.add('dark');setTimeout(function(){var t=document.getElementById('themeBtn');if(t)t.textContent='☾'},50)}})();
function toggleTheme(){
  document.body.classList.toggle('dark');
  localStorage.theme=document.body.classList.contains('dark')?'dark':'light';
  var t=document.getElementById('themeBtn');
  if(t)t.textContent=document.body.classList.contains('dark')?'☾':'☀';
}
let cat='all', curId=null, searchTerm='';
let bm=[];
try{bm=JSON.parse(localStorage.getItem('tf_bm')||'[]')}catch(e){}
const saveBm=()=>{try{localStorage.setItem('tf_bm',JSON.stringify(bm))}catch(e){}};
const isBm=id=>bm.includes(id);
const esc=s=>(s||'').replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');

// Initialisation sans render() — le HTML est pré-rendu côté serveur
var tb=document.getElementById('themeBtn');
if(tb&&localStorage.theme==='dark'){document.body.classList.add('dark');tb.textContent='\\u263e';}
try{bm=JSON.parse(localStorage.getItem('tf_bm')||'[]')}catch(e){}
// Appliquer les bookmarks sur les étoiles existantes
document.querySelectorAll('[data-bmid]').forEach(function(el){
  if(bm.includes(el.getAttribute('data-bmid')))el.classList.add('on');
});

function toggleTheme(){
  document.body.classList.toggle('dark');
  localStorage.theme=document.body.classList.contains('dark')?'dark':'light';
  const tb=document.getElementById('themeBtn');
  if(tb)tb.textContent=document.body.classList.contains('dark')?'\u263e':'\u2600';
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
    {team:'Mexique',flag:'🇲🇽',p:4,gf:3,ga:0,pl:2},
    {team:'Coree du Sud',flag:'🇰🇷',p:3,gf:2,ga:2,pl:2},
    {team:'Republique Tcheque',flag:'🇨🇿',p:1,gf:2,ga:3,pl:2},
    {team:'Afrique du Sud',flag:'🇿🇦',p:1,gf:1,ga:3,pl:2}
  ]},
  B:{name:'Groupe B',teams:[
    {team:'Canada',flag:'🇨🇦',p:4,gf:7,ga:1,pl:2},
    {team:'Suisse',flag:'🇨🇭',p:4,gf:5,ga:2,pl:2},
    {team:'Bosnie-Herzegovine',flag:'🇧🇦',p:1,gf:2,ga:5,pl:2},
    {team:'Qatar',flag:'🇶🇦',p:1,gf:1,ga:7,pl:2}
  ]},
  C:{name:'Groupe C',teams:[
    {team:'Bresil',flag:'🇧🇷',p:4,gf:4,ga:1,pl:2},
    {team:'Maroc',flag:'🇲🇦',p:4,gf:2,ga:1,pl:2},
    {team:'Ecosse',flag:'🏴󠁧󠁢󠁳󠁣󠁴󠁿',p:3,gf:1,ga:1,pl:2},
    {team:'Haiti',flag:'🇭🇹',p:0,gf:0,ga:4,pl:2}
  ]},
  D:{name:'Groupe D',teams:[
    {team:'Etats-Unis',flag:'🇺🇸',p:6,gf:6,ga:1,pl:2},
    {team:'Australie',flag:'🇦🇺',p:3,gf:2,ga:2,pl:2},
    {team:'Paraguay',flag:'🇵🇾',p:3,gf:2,ga:4,pl:2},
    {team:'Turkiye',flag:'🇹🇷',p:0,gf:0,ga:3,pl:2}
  ]},
  E:{name:'Groupe E',teams:[
    {team:'Allemagne',flag:'🇩🇪',p:6,gf:9,ga:2,pl:2},
    {team:'Cote d\'Ivoire',flag:'🇨🇮',p:3,gf:2,ga:2,pl:2},
    {team:'Equateur',flag:'🇪🇨',p:1,gf:0,ga:1,pl:2},
    {team:'Curacao',flag:'🇨🇼',p:1,gf:1,ga:7,pl:2}
  ]},
  F:{name:'Groupe F',teams:[
    {team:'Pays-Bas',flag:'🇳🇱',p:4,gf:7,ga:3,pl:2},
    {team:'Japon',flag:'🇯🇵',p:4,gf:6,ga:2,pl:2},
    {team:'Suede',flag:'🇸🇪',p:3,gf:6,ga:6,pl:2},
    {team:'Tunisie',flag:'🇹🇳',p:0,gf:1,ga:9,pl:2}
  ]},
  G:{name:'Groupe G',teams:[
    {team:'Egypte',flag:'🇪🇬',p:4,gf:4,ga:2,pl:2},
    {team:'Iran',flag:'🇮🇷',p:2,gf:2,ga:2,pl:2},
    {team:'Belgique',flag:'🇧🇪',p:2,gf:1,ga:1,pl:2},
    {team:'Nouvelle-Zelande',flag:'🇳🇿',p:1,gf:3,ga:5,pl:2}
  ]},
  H:{name:'Groupe H',teams:[
    {team:'Espagne',flag:'🇪🇸',p:4,gf:4,ga:0,pl:2},
    {team:'Uruguay',flag:'🇺🇾',p:2,gf:3,ga:3,pl:2},
    {team:'Cap-Vert',flag:'🇨🇻',p:2,gf:2,ga:2,pl:2},
    {team:'Arabie Saoudite',flag:'🇸🇦',p:1,gf:1,ga:5,pl:2}
  ]},
  I:{name:'Groupe I',teams:[
    {team:'France',flag:'🇫🇷',p:6,gf:6,ga:1,pl:2},
    {team:'Norvege',flag:'🇳🇴',p:3,gf:6,ga:5,pl:2},
    {team:'Senegal',flag:'🇸🇳',p:0,gf:3,ga:6,pl:2},
    {team:'Irak',flag:'🇮🇶',p:0,gf:1,ga:7,pl:2}
  ]},
  J:{name:'Groupe J',teams:[
    {team:'Argentine',flag:'🇦🇷',p:6,gf:5,ga:1,pl:2},
    {team:'Autriche',flag:'🇦🇹',p:3,gf:4,ga:5,pl:2},
    {team:'Algerie',flag:'🇩🇿',p:3,gf:2,ga:4,pl:2},
    {team:'Jordanie',flag:'🇯🇴',p:0,gf:2,ga:5,pl:2}
  ]},
  K:{name:'Groupe K',teams:[
    {team:'Colombie',flag:'🇨🇴',p:6,gf:4,ga:1,pl:2},
    {team:'Portugal',flag:'🇵🇹',p:4,gf:6,ga:1,pl:2},
    {team:'RD Congo',flag:'🇨🇩',p:1,gf:1,ga:2,pl:2},
    {team:'Ouzbekistan',flag:'🇺🇿',p:0,gf:1,ga:8,pl:2}
  ]},
  L:{name:'Groupe L',teams:[
    {team:'Angleterre',flag:'🏴󠁧󠁢󠁥󠁮󠁧󠁿',p:4,gf:4,ga:2,pl:2},
    {team:'Ghana',flag:'🇬🇭',p:4,gf:1,ga:0,pl:2},
    {team:'Croatie',flag:'🇭🇷',p:3,gf:3,ga:4,pl:2},
    {team:'Panama',flag:'🇵🇦',p:0,gf:0,ga:2,pl:2}
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
  {g:'L',d:'23 juin',t1:'Panama',t2:'Croatie',s1:0,s2:1}
];

const WC_MATCHES_UPCOMING = [
  {g:'A',d:'24 juin',t1:'Republique Tcheque',t2:'Mexique',h:'21:00'},
  {g:'A',d:'24 juin',t1:'Afrique du Sud',t2:'Coree du Sud',h:'21:00'},
  {g:'B',d:'24 juin',t1:'Suisse',t2:'Canada',h:'15:00'},
  {g:'B',d:'24 juin',t1:'Bosnie-Herzegovine',t2:'Qatar',h:'15:00'},
  {g:'C',d:'24 juin',t1:'Ecosse',t2:'Bresil',h:'18:00'},
  {g:'C',d:'24 juin',t1:'Maroc',t2:'Haiti',h:'18:00'},
  {g:'E',d:'25 juin',t1:'Equateur',t2:'Allemagne',h:'16:00'},
  {g:'E',d:'25 juin',t1:'Curacao',t2:'Cote d\'Ivoire',h:'16:00'},
  {g:'F',d:'25 juin',t1:'Japon',t2:'Suede',h:'19:00'},
  {g:'F',d:'25 juin',t1:'Tunisie',t2:'Pays-Bas',h:'19:00'},
  {g:'D',d:'25 juin',t1:'Turkiye',t2:'Etats-Unis',h:'22:00'},
  {g:'D',d:'25 juin',t1:'Paraguay',t2:'Australie',h:'22:00'},
  {g:'I',d:'26 juin',t1:'Norvege',t2:'France',h:'15:00'},
  {g:'I',d:'26 juin',t1:'Senegal',t2:'Irak',h:'15:00'},
  {g:'H',d:'26 juin',t1:'Cap-Vert',t2:'Arabie Saoudite',h:'20:00'},
  {g:'H',d:'26 juin',t1:'Uruguay',t2:'Espagne',h:'20:00'},
  {g:'G',d:'26 juin',t1:'Egypte',t2:'Iran',h:'23:00'},
  {g:'G',d:'26 juin',t1:'Nouvelle-Zelande',t2:'Belgique',h:'23:00'},
  {g:'L',d:'27 juin',t1:'Panama',t2:'Angleterre',h:'17:00'},
  {g:'L',d:'27 juin',t1:'Croatie',t2:'Ghana',h:'17:00'},
  {g:'K',d:'27 juin',t1:'Colombie',t2:'Portugal',h:'19:30'},
  {g:'K',d:'27 juin',t1:'RD Congo',t2:'Ouzbekistan',h:'19:30'},
  {g:'J',d:'27 juin',t1:'Algerie',t2:'Autriche',h:'22:00'},
  {g:'J',d:'27 juin',t1:'Jordanie',t2:'Argentine',h:'22:00'}
];

function renderWorldCup(fc){
  var n=new Date();if(n>=new Date('2026-07-23T00:00:00')){fc.innerHTML='<div class="bm-empty"><h3>⚽</h3><p>Section archivée.</p></div>';return}
  var h='',dk=false;

  // Groupes
  h+='<section class="light"><div class="container"><div class="sec-head"><h3>Phases de Groupes</h3><div class="count">12 groupes · 3e journée</div></div></div>';
  h+='<div style="max-width:960px;margin:0 auto;padding:0 28px;display:grid;grid-template-columns:repeat(auto-fill,minmax(310px,1fr));gap:18px">';
  for(var gk in WC_GROUPS){var g=WC_GROUPS[gk];
    h+='<div style="background:#fff;border-radius:16px;padding:24px 26px;box-shadow:rgba(0,0,0,.05)0 1px 4px">';
    h+='<div class="cat">'+g.name+'</div>';
    h+='<table style="width:100%;border-collapse:collapse;font-size:.76rem;margin-top:12px">';
    h+='<tr style="color:rgba(0,0,0,.3);font-size:.6rem;text-transform:uppercase;letter-spacing:1px"><th style="text-align:left;padding:6px 6px;font-weight:500">Équipe</th><th style="text-align:center;padding:6px 3px;font-weight:500">J</th><th style="text-align:center;padding:6px 3px;font-weight:500">V</th><th style="text-align:center;padding:6px 3px;font-weight:500">N</th><th style="text-align:center;padding:6px 3px;font-weight:500">D</th><th style="text-align:center;padding:6px 3px;font-weight:500">+/-</th><th style="text-align:center;padding:6px 3px;font-weight:500;color:#0071e3">Pts</th></tr>';
    var s=[].concat(g.teams).sort(function(a,b){return b.p-a.p||(b.gf-b.ga)-(a.gf-a.ga)});
    for(var i=0;i<s.length;i++){var t=s[i],gp=t.pl||2,gd=t.gf-t.ga,st=t.q?'<span style="font-size:.55rem;color:#059669;margin-left:3px">Q</span>':t.e?'<span style="font-size:.55rem;color:#dc2626;margin-left:3px">E</span>':'';
      h+='<tr style="border-bottom:1px solid rgba(0,0,0,.04)"><td style="padding:7px 6px;font-weight:600;font-size:.74rem">'+t.flag+' '+t.team+st+'</td><td style="text-align:center;padding:7px 3px;font-size:.72rem">'+gp+'</td><td style="text-align:center;padding:7px 3px;font-size:.72rem">'+Math.floor(t.p/3)+'</td><td style="text-align:center;padding:7px 3px;font-size:.72rem">'+(t.p%3!==0?1:0)+'</td><td style="text-align:center;padding:7px 3px;font-size:.72rem">'+(gp-Math.floor(t.p/3)-(t.p%3!==0?1:0))+'</td><td style="text-align:center;padding:7px 3px;font-size:.72rem">'+(gd>0?'+':'')+gd+'</td><td style="text-align:center;padding:7px 3px;font-weight:700;color:#0071e3;font-size:.76rem">'+t.p+'</td></tr>';
    }
    h+='</table></div>';
  }
  h+='</div></section>';

  // Phase Finale
  h+='<section class="white"><div class="container"><div class="sec-head"><h3>Phase Finale</h3><div class="count">16es de finale · 29 juin</div></div></div>';
  h+='<div style="max-width:960px;margin:0 auto;padding:0 28px"><p style="color:rgba(0,0,0,.45);line-height:1.7;font-size:.88rem;text-align:center;max-width:600px;margin:0 auto">Les 12 premiers de groupe, les 12 deuxièmes et les 8 meilleurs troisièmes composeront le tableau des 16es de finale.</p></div></section>';

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

  h+='<div style="text-align:center;padding:40px;color:rgba(0,0,0,.3);font-size:.68rem">Dernière mise à jour : 24 juin 2026</div>';
  fc.innerHTML=h;
}
function openPanel(id){
  const a=ARTICLES.find(x=>x.id===id);if(!a)return;curId=id;
  const panel=document.getElementById('panel'),layout=document.getElementById('layout');
  if(!panel||!layout)return;
  panel.innerHTML='<div class="panel-head">'
    +'<div class="cat" style="margin:0;font-size:.62rem">'+esc(a.catLabel)+'</div>'
    +'<button class="panel-close" onclick="closePanel()">\u2715</button></div>'
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
  document.getElementById('layout').classList.remove('panel-open');
  document.getElementById('panel').innerHTML='';
  document.querySelectorAll('.active-card').forEach(el=>el.classList.remove('active-card'));
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
