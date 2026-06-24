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
            "body":            a.get("body", ""),
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


CSS = """/* Apple-inspired */
*{box-sizing:border-box;margin:0;padding:0}
body{font-family:system-ui,-apple-system,'Segoe UI',Roboto,sans-serif;background:#f5f5f7;color:#1d1d1f;-webkit-font-smoothing:antialiased;overflow:hidden}
header{position:fixed;top:0;left:0;right:0;z-index:100;height:48px;background:rgba(245,245,247,.72);backdrop-filter:saturate(180%)blur(20px);-webkit-backdrop-filter:saturate(180%)blur(20px);display:flex;align-items:center;justify-content:space-between;padding:0 22px;border-bottom:1px solid rgba(0,0,0,.08)}
.logo{font-size:.85rem;font-weight:700;color:#1d1d1f;display:flex;align-items:center;gap:6px}
.logo em{font-style:normal;font-size:.48rem;background:#0071e3;color:#fff;padding:2px 7px;border-radius:99px;font-weight:600;letter-spacing:.5px}
.hright{display:flex;align-items:center;gap:4px}
.hright a,.hright button{display:flex;align-items:center;justify-content:center;width:36px;height:36px;border-radius:50%;text-decoration:none;color:#1d1d1f;font-size:.9rem;opacity:.6;transition:all .2s;border:none;background:none;cursor:pointer}
.hright a:hover,.hright button:hover{opacity:1;background:rgba(0,0,0,.04)}
.hright a.active,.hright button.active{opacity:1;color:#0071e3}
.search-wrap{display:flex;align-items:center;margin:0 8px}
.search-wrap input{border:none;background:rgba(0,0,0,.04);border-radius:8px;padding:5px 10px;font-size:.75rem;color:#1d1d1f;outline:none;width:180px;font-family:inherit}
.search-wrap input:focus{background:rgba(0,0,0,.06)}
.search-wrap input::placeholder{color:rgba(0,0,0,.4)}
.upd{font-size:.7rem;color:rgba(0,0,0,.4);margin-right:8px}

.tabs{display:none}
.layout{display:flex;position:fixed;top:48px;left:0;right:0;bottom:0}
.feed-col{flex:1;overflow-y:auto;min-width:0}
.panel-col{width:0;overflow:hidden;background:#fff;transition:width .35s cubic-bezier(.4,0,.2,1);display:flex;flex-direction:column;flex-shrink:0;order:-1;box-shadow:-20px 0 60px rgba(0,0,0,.15);z-index:200}
.layout.panel-open .panel-col{width:540px}

/* Hero — dark immersive */
.hero{background:#000;color:#fff;position:relative;overflow:hidden}
.hero img{width:100%;height:460px;object-fit:cover;opacity:.72}
.hero-overlay{position:absolute;bottom:0;left:0;right:0;padding:0 0 56px 0;max-width:800px;margin:0 auto;text-align:center}
.hero-cat{font-size:.62rem;text-transform:uppercase;letter-spacing:2px;opacity:.55;margin-bottom:10px}
.hero-title{font-size:2.6rem;font-weight:700;line-height:1.07;letter-spacing:-.28px;margin-bottom:10px}
.hero-desc{font-size:1rem;line-height:1.47;opacity:.75;max-width:560px;margin:0 auto}

/* Sections */
section{padding:72px 0}
section.light{background:#f5f5f7}
section.white{background:#fff}
.container{max-width:960px;margin:0 auto;padding:0 28px}
.sec-head{text-align:center;margin-bottom:40px}
.sec-head h3{font-size:2.2rem;font-weight:600;line-height:1.1;margin-bottom:6px;color:#1d1d1f}
.sec-head .count{font-size:.94rem;color:rgba(0,0,0,.5)}

/* Articles rows */
.articles{max-width:960px;margin:0 auto;padding:0 28px}
.art-row{display:flex;gap:24px;align-items:center;padding:26px 0;border-bottom:1px solid rgba(0,0,0,.06);cursor:pointer;transition:opacity .2s}
.art-row:hover{opacity:.65}
.art-row:last-child{border-bottom:none}
.art-img{flex:0 0 260px;height:170px;border-radius:12px;overflow:hidden;background:#e8e8ed}
.art-img img{width:100%;height:100%;object-fit:cover}
.art-body{flex:1;min-width:0}
.art-body .cat{font-size:.6rem;text-transform:uppercase;letter-spacing:1.5px;color:#0071e3;font-weight:600;margin-bottom:4px}
.art-body h4{font-size:1.35rem;font-weight:700;line-height:1.14;color:#1d1d1f;margin-bottom:4px}
.art-body .excerpt{font-size:.9rem;line-height:1.47;color:rgba(0,0,0,.55);display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;overflow:hidden}
.art-body .meta{font-size:.72rem;color:rgba(0,0,0,.36);margin-top:5px}
.art-body .bm-star{background:none;border:none;cursor:pointer;font-size:1rem;padding:0 2px;color:rgba(0,0,0,.2);vertical-align:middle}
.art-body .bm-star.on{color:#0071e3}

/* Featured card */
.feat{background:#fff;border-radius:18px;overflow:hidden;box-shadow:rgba(0,0,0,.18)3px 5px 28px 0;margin-bottom:44px;cursor:pointer;transition:transform .3s}
.feat:hover{transform:scale(1.01)}
.feat img{width:100%;height:320px;object-fit:cover;display:block}
.feat-body{padding:30px 34px}
.feat-body .cat{font-size:.6rem;text-transform:uppercase;letter-spacing:1.5px;color:#0071e3;font-weight:600;margin-bottom:6px}
.feat-body h4{font-size:1.6rem;font-weight:700;line-height:1.14;color:#1d1d1f;margin-bottom:6px}
.feat-body .excerpt{font-size:.9rem;line-height:1.47;color:rgba(0,0,0,.55)}
.feat-body .meta{font-size:.74rem;color:rgba(0,0,0,.36);margin-top:8px}

/* Panel */
.panel-head{position:sticky;top:0;z-index:10;background:rgba(255,255,255,.72);backdrop-filter:saturate(180%)blur(20px);-webkit-backdrop-filter:saturate(180%)blur(20px);display:flex;align-items:center;justify-content:space-between;padding:14px 26px;border-bottom:1px solid rgba(0,0,0,.06)}
.panel-close{width:32px;height:32px;display:flex;align-items:center;justify-content:center;border-radius:50%;background:rgba(0,0,0,.04);border:none;cursor:pointer;font-size:1rem;color:#1d1d1f}
.panel-close:hover{background:rgba(0,0,0,.08)}
.panel-body{flex:1;overflow-y:auto;padding:26px 30px 64px}
.panel-body img{width:100%;border-radius:12px;margin-bottom:22px}
.panel-body h2{font-size:1.7rem;font-weight:700;line-height:1.1;color:#1d1d1f;margin-bottom:8px}
.panel-body .meta{font-size:.78rem;color:rgba(0,0,0,.44);margin-bottom:22px}
.panel-body .body{font-size:1rem;line-height:1.65;color:rgba(0,0,0,.78)}
.panel-body .body p{margin-bottom:15px}
.panel-body .read{display:inline-flex;align-items:center;gap:6px;background:#0071e3;color:#fff;padding:10px 20px;border-radius:980px;font-size:.85rem;font-weight:500;text-decoration:none;margin-top:18px}
.panel-body .read:hover{background:#0066cc}
.src-section{margin-top:22px;padding-top:16px;border-top:1px solid rgba(0,0,0,.06)}
.src-section h3{font-size:.68rem;font-weight:600;color:rgba(0,0,0,.4);text-transform:uppercase;letter-spacing:1px;margin-bottom:8px}
.src-item{display:flex;align-items:flex-start;gap:8px;margin-bottom:6px;font-size:.8rem}
.src-num{font-weight:700;color:#0071e3;background:rgba(0,113,227,.08);padding:1px 6px;border-radius:4px;flex-shrink:0;font-size:.68rem}
.src-name{font-weight:600;color:rgba(0,0,0,.6)}.src-url{color:#0071e3;text-decoration:none;font-size:.72rem;word-break:break-all}

.bm-empty{text-align:center;padding:100px 24px;color:rgba(0,0,0,.36)}
.bm-empty h3{font-size:1.3rem;font-weight:600;color:rgba(0,0,0,.5);margin-bottom:6px}

@media(max-width:900px){
.hero img{height:320px}.hero-title{font-size:1.8rem}.hero-desc{font-size:.9rem}
.art-row{flex-direction:column;align-items:stretch;gap:14px}.art-img{flex:0 0 auto;height:190px}
.panel-col{width:100%!important}.layout.panel-open .panel-col{width:100%!important}
section{padding:48px 0}.sec-head h3{font-size:1.6rem}
.feat img{height:240px}.feat-body{padding:20px 24px}.feat-body h4{font-size:1.25rem}
}
@media(max-width:600px){
header{padding:0 12px}.upd{display:none}.search-wrap input{width:120px}
.hero img{height:240px}.hero-overlay{padding:0 0 32px 0}.hero-title{font-size:1.3rem}
.art-img{height:150px}.art-body h4{font-size:1.1rem}
.container,.articles{padding:0 16px}
.panel-body{padding:20px 18px 48px}
}
"""

JS = r"""const ARTICLES = __ARTICLES__;
const CAT_LABELS = {all:'Toutes les actualites',ia:'IA & Tech',crypto:'Crypto',gaming:'Jeux Video',markets:'Marches',general:'General',science:'Science',dev:'Developpement',startups:'Startups',bookmarks:'Sauvegardes',search:'Recherche',worldcup:'Coupe du Monde 2026'};
let cat='all', curId=null, searchTerm='';
let bm=[];
try{bm=JSON.parse(localStorage.getItem('tf_bm')||'[]')}catch(e){}
const saveBm=()=>{try{localStorage.setItem('tf_bm',JSON.stringify(bm))}catch(e){}};
const isBm=id=>bm.includes(id);
const esc=s=>(s||'').replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');

// Theme
(function(){
  if(localStorage.theme==='dark') document.body.classList.add('dark');
  const tb=document.getElementById('themeBtn');
  if(tb)tb.textContent=document.body.classList.contains('dark')?'\u263e':'\u2600';
})();

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
  const now = new Date();
  const deadline = new Date('2026-07-23T00:00:00');
  if(now >= deadline){
    fc.innerHTML='<div class="bm-empty">&#9917;<br><br>La section Coupe du Monde 2026 a ete archivee.</div>';
    return;
  }
  let out = '<div class="section-label">Coupe du Monde 2026 &mdash; Phases de Groupes</div><div class="wc-grid">';
  for(const [gk, g] of Object.entries(WC_GROUPS)){
    out += '<div class="wc-section"><div class="wc-poule-title">'+g.name+'</div><table class="wc-table"><thead><tr><th>Equipe</th><th style="text-align:center;width:28px">J</th><th style="text-align:center;width:28px">V</th><th style="text-align:center;width:28px">N</th><th style="text-align:center;width:28px">D</th><th style="text-align:center;width:36px">BP</th><th style="text-align:center;width:36px">BC</th><th style="text-align:center;width:28px">+/-</th><th style="text-align:center;width:28px">Pts</th></tr></thead><tbody>';
    const sorted = [...g.teams].sort((a,b)=>b.p-a.p || (b.gf-b.ga)-(a.gf-a.ga));
    for(const t of sorted){
      const gd = t.gf - t.ga;
      const gp = t.pl || 3;
      const status = t.q ? '<span class="wc-qualified">Qualifie</span>' : t.e ? '<span class="wc-eliminated">Elimine</span>' : '';
      out += '<tr><td><span class="wc-team">'+t.flag+' '+t.team+' '+status+'</span></td><td style="text-align:center">'+gp+'</td><td style="text-align:center">'+Math.floor(t.p/3)+'</td><td style="text-align:center">'+(t.p%3!==0?1:0)+'</td><td style="text-align:center">'+(gp-Math.floor(t.p/3)-(t.p%3!==0?1:0))+'</td><td style="text-align:center">'+t.gf+'</td><td style="text-align:center">'+t.ga+'</td><td style="text-align:center">'+(gd>0?'+':'')+gd+'</td><td style="text-align:center" class="wc-pts">'+t.p+'</td></tr>';
    }
    out += '</tbody></table></div>';
  }
  out += '</div>';

  out += '<div class="section-label">Coupe du Monde 2026 &mdash; Phase Finale</div><div class="wc-section">';
  out += '<h3>&#127942; 16es de finale</h3>';
  out += '<div class="wc-knockout">';
  out += '<i>Les 16es de finale debutent le 29 juin. Les 12 premiers de groupe, les 12 deuxiemes et les 8 meilleurs troisiemes composeront le tableau. Les derniers matchs de groupes se jouent du 24 au 27 juin.</i>';
  out += '</div></div>';

  out += '<div class="section-label">Matchs Joues</div><div class="wc-grid">';
  const byGroupD = {};
  for(const m of WC_MATCHES_DONE){
    if(!byGroupD[m.g]) byGroupD[m.g] = [];
    byGroupD[m.g].push(m);
  }
  for(const [gk, matches] of Object.entries(byGroupD)){
    const gname = WC_GROUPS[gk] ? WC_GROUPS[gk].name : 'Groupe '+gk;
    out += '<div class="wc-section"><div class="wc-poule-title">'+gname+'</div>';
    for(const m of matches){
      const cls1 = m.s1 > m.s2 ? 'wc-winner' : m.s1 === m.s2 ? 'wc-draw' : '';
      const cls2 = m.s2 > m.s1 ? 'wc-winner' : m.s2 === m.s1 ? 'wc-draw' : '';
      out += '<div class="wc-matchup"><div class="teams"><span class="'+cls1+'">'+(m.flag1||'')+' '+m.t1+'</span><span class="vs">vs</span><span class="'+cls2+'">'+(m.flag2||'')+' '+m.t2+'</span></div><div style="display:flex;align-items:center;gap:5px"><span class="wc-score '+cls1+'">'+m.s1+'</span><span style="color:var(--text3);font-size:.68rem">-</span><span class="wc-score '+cls2+'">'+m.s2+'</span><span class="wc-time">'+m.d+'</span></div></div>';
    }
    out += '</div>';
  }
  out += '</div>';

  out += '<div class="section-label">Matchs a Venir</div><div class="wc-grid">';
  const byGroupU = {};
  for(const m of WC_MATCHES_UPCOMING){
    if(!byGroupU[m.g]) byGroupU[m.g] = [];
    byGroupU[m.g].push(m);
  }
  for(const [gk, matches] of Object.entries(byGroupU)){
    const gname = WC_GROUPS[gk] ? WC_GROUPS[gk].name : 'Groupe '+gk;
    out += '<div class="wc-section"><div class="wc-poule-title">'+gname+'</div>';
    for(const m of matches){
      out += '<div class="wc-matchup"><div class="teams"><span>'+m.t1+'</span><span class="vs">vs</span><span>'+m.t2+'</span></div><span class="wc-time" style="font-weight:600">'+m.d+' &middot; '+m.h+'</span></div>';
    }
    out += '</div>';
  }
  out += '</div>';

  out += '<div class="wc-section" style="text-align:center;color:var(--text3);font-size:.7rem">Derniere mise a jour : 24 juin 2026 &middot; Les qualifications sont mises a jour au fil des matchs</div>';

  fc.innerHTML = out;
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
      +'<div class="body">'+(a.body||'<p>'+esc(a.excerpt)+'</p>')+'</div>'
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
try{render();}catch(e){
  console.error(e);
  const fc=document.getElementById('feed');
  if(fc)fc.innerHTML='<div style="padding:40px;text-align:center;color:#ef4444">Erreur: '+e.message+'</div>';
}
"""


def generate_html(articles, last_update):
    articles_json = build_articles_json(articles)
    js = JS.replace("__ARTICLES__", articles_json)

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
  <div class="feed-col" id="feed"></div>
  <div class="panel-col" id="panel"></div>
</div>
<script>{js}</script>
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
