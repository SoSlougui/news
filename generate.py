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


CSS = """/* v5 — Warm editorial */
:root{
--bg:#fff;--bgw:#faf9f7;--card:#fff;--cardh:#fafafa;
--border:rgba(0,0,0,.06);--text:#1a1a1a;--text2:#555;--text3:#999;
--accent:#e04b4b;--accent2:#ff6b6b;--accent-text:#fff;
--radius:12px;--radius-lg:16px;
--shadow:0 1px 3px rgba(0,0,0,.04);--shadowh:0 6px 24px rgba(0,0,0,.08);
}
.dark{
--bg:#161618;--bgw:#1c1c1f;--card:#1e1e22;--cardh:#24242a;
--border:rgba(255,255,255,.06);--text:#e8e8ec;--text2:#999;--text3:#666;
--shadow:none;--shadowh:0 8px 32px rgba(0,0,0,.3);
}
*{box-sizing:border-box;margin:0;padding:0}
body{font-family:'Inter',system-ui,-apple-system,sans-serif;background:var(--bg);color:var(--text);overflow:hidden;transition:background .3s,color .3s}

header{position:fixed;top:0;left:0;right:0;z-index:50;background:var(--bg);padding:0 28px;height:56px;display:flex;align-items:center;justify-content:space-between;border-bottom:1px solid var(--border)}
.logo{display:flex;align-items:center;gap:8px;font-size:1rem;font-weight:800;color:var(--text)}
.logo em{font-style:normal;background:var(--accent);color:var(--accent-text);font-size:.5rem;padding:3px 7px;border-radius:99px;font-weight:700;letter-spacing:.5px}
.hright{display:flex;align-items:center;gap:10px}
.upd{font-size:.68rem;color:var(--text3)}
.search-wrap{display:flex;align-items:center;flex:1;max-width:260px;margin:0 14px}
.search-wrap input{width:100%;border:1px solid var(--border);border-radius:8px;padding:6px 10px;font-size:.74rem;outline:none;background:var(--bgw);color:var(--text);font-family:inherit}
.search-wrap input:focus{border-color:var(--accent)}
.search-wrap input::placeholder{color:var(--text3)}
.search-clear{background:none;border:none;color:var(--text3);font-size:.8rem;cursor:pointer;padding:2px 5px;border-radius:4px;display:none}
.search-clear.on{display:inline-block}
.btn-theme{width:32px;height:32px;display:flex;align-items:center;justify-content:center;background:none;border:1px solid var(--border);border-radius:50%;cursor:pointer;font-size:.9rem;color:var(--text2);transition:all .2s}
.btn-theme:hover{background:var(--bgw);color:var(--text)}
.btn-bookmarks{background:none;border:1px solid var(--border);border-radius:8px;padding:5px 12px;font-size:.72rem;font-weight:600;cursor:pointer;color:var(--text2);transition:all .2s}
.btn-bookmarks:hover{background:var(--bgw);color:var(--text)}

.tabs{position:fixed;top:56px;left:0;right:0;z-index:49;background:var(--bg);border-bottom:1px solid var(--border);padding:0 22px;display:flex;overflow-x:auto;scrollbar-width:none}
.tabs::-webkit-scrollbar{display:none}
.tab{padding:10px 14px;font-size:.73rem;font-weight:500;color:var(--text2);cursor:pointer;border-bottom:2px solid transparent;white-space:nowrap;transition:all .15s}
.tab:hover{color:var(--text)}
.tab.active{color:var(--accent);border-bottom-color:var(--accent);font-weight:600}

.layout{display:flex;position:fixed;top:104px;left:0;right:0;bottom:0}
.feed-col{flex:1;overflow-y:auto;padding:28px 36px;min-width:0}
.panel-col{width:0;overflow:hidden;background:var(--bg);border-right:1px solid var(--border);transition:width .3s;display:flex;flex-direction:column;flex-shrink:0;order:-1}
.layout.panel-open .panel-col{width:500px}

.section-label{font-size:.62rem;text-transform:uppercase;letter-spacing:2px;color:var(--text3);font-weight:600;margin-bottom:16px}

.hero{display:flex;border-radius:var(--radius-lg);overflow:hidden;background:var(--card);border:1px solid var(--border);margin-bottom:36px;cursor:pointer;min-height:280px;transition:all .3s}
.hero:hover{box-shadow:var(--shadowh)}
.hero-img{flex:0 0 54%;overflow:hidden;position:relative}
.hero-img img{width:100%;height:100%;object-fit:cover;position:absolute;top:0;left:0}
.hero-body{flex:1;padding:30px 34px;display:flex;flex-direction:column;justify-content:center}
.hero-cat{font-size:.58rem;text-transform:uppercase;letter-spacing:1.5px;color:var(--accent);font-weight:700;margin-bottom:8px}
.hero-title{font-size:1.35rem;font-weight:700;line-height:1.22;color:var(--text);margin-bottom:8px;font-family:Georgia,'Times New Roman',serif}
.hero-excerpt{font-size:.8rem;color:var(--text2);line-height:1.6;margin-bottom:12px}
.hero-meta{display:flex;align-items:center;gap:8px;font-size:.68rem;color:var(--text3);margin-top:auto;margin-bottom:4px}
.hero-cta{color:var(--accent);font-weight:600;font-size:.72rem;display:flex;align-items:center;gap:4px}

.date-group{margin-bottom:32px}
.date-title{font-size:.76rem;font-weight:700;color:var(--text);margin-bottom:14px;display:flex;align-items:center;gap:10px}
.date-title::after{content:'';flex:1;height:1px;background:var(--border)}
.date-count{font-weight:400;color:var(--text2);font-size:.68rem}

.grid{display:grid;grid-template-columns:repeat(3,1fr);gap:16px}

.card{background:var(--card);border:1px solid var(--border);border-radius:var(--radius);overflow:hidden;cursor:pointer;transition:all .25s;display:flex;flex-direction:column}
.card:hover{box-shadow:var(--shadowh);transform:translateY(-2px)}
.card-img{height:155px;overflow:hidden;flex-shrink:0;background:var(--bgw)}
.card-img img{width:100%;height:100%;object-fit:cover;transition:transform .3s}
.card:hover .card-img img{transform:scale(1.03)}
.img-fb{width:100%;height:100%;display:flex;align-items:center;justify-content:center;background:var(--bgw);color:var(--text3);font-size:.65rem;font-weight:700;letter-spacing:1px;text-transform:uppercase;text-align:center;padding:8px}
.card-body{padding:16px;flex:1;display:flex;flex-direction:column}
.card-top{display:flex;align-items:center;justify-content:space-between;margin-bottom:7px}
.badge-cat{display:inline-block;padding:2px 8px;border-radius:99px;font-size:.56rem;font-weight:700;text-transform:uppercase;letter-spacing:.3px}
.cat-ia{background:rgba(59,130,246,.1);color:#2563eb}.cat-crypto{background:rgba(245,158,11,.1);color:#d97706}
.cat-gaming{background:rgba(16,185,129,.1);color:#059669}.cat-markets{background:rgba(139,92,246,.1);color:#7c3aed}
.cat-general{background:rgba(239,68,68,.1);color:#dc2626}
.cat-science{background:rgba(6,182,212,.1);color:#0891b2}.cat-dev{background:rgba(129,140,248,.1);color:#6366f1}
.cat-startups{background:rgba(251,191,36,.1);color:#d97706}
.card-title{font-size:.84rem;font-weight:700;line-height:1.3;color:var(--text);margin-bottom:4px;flex:1;font-family:Georgia,'Times New Roman',serif;display:-webkit-box;-webkit-line-clamp:3;-webkit-box-orient:vertical;overflow:hidden}
.card-excerpt{font-size:.71rem;color:var(--text2);line-height:1.5;margin-bottom:8px;display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;overflow:hidden}
.card-foot{display:flex;align-items:center;justify-content:space-between;margin-top:auto;font-size:.64rem;color:var(--text3)}
.card-cta{color:var(--accent);font-weight:600}
.bm-btn{background:none;border:none;cursor:pointer;font-size:.9rem;padding:2px 4px;border-radius:4px;color:var(--text3);line-height:1;transition:color .2s}
.bm-btn.on{color:var(--accent)}
.rel-tag{padding:2px 6px;border-radius:4px;font-size:.6rem;font-weight:600}
.rel-tag.strong{background:rgba(16,185,129,.08);color:#059669}.rel-tag.moderate{background:rgba(245,158,11,.08);color:#d97706}

.panel-topbar{display:flex;align-items:center;justify-content:space-between;padding:14px 20px;border-bottom:1px solid var(--border);flex-shrink:0;background:var(--bg);position:sticky;top:0;z-index:2}
.panel-topbar-l{display:flex;align-items:center;gap:6px;flex-wrap:wrap;min-width:0;flex:1}
.panel-actions{display:flex;gap:6px;align-items:center;flex-shrink:0}
.panel-close{background:none;border:none;font-size:1rem;cursor:pointer;color:var(--text3);padding:4px 7px;border-radius:6px;line-height:1}
.panel-close:hover{background:var(--bgw);color:var(--text)}
.panel-bm{background:none;border:1px solid var(--border);border-radius:7px;padding:4px 11px;font-size:.72rem;cursor:pointer;color:var(--text2);white-space:nowrap}
.panel-bm.on{background:rgba(224,75,75,.08);border-color:rgba(224,75,75,.2);color:var(--accent)}
.panel-body{flex:1;overflow-y:auto;padding:20px 24px 40px}
.art-hero-img{border-radius:10px;overflow:hidden;margin-bottom:18px;background:var(--bgw)}
.art-hero-img img{width:100%;max-height:260px;object-fit:cover;display:block}
.art-title{font-size:1.15rem;font-weight:700;line-height:1.25;color:var(--text);margin-bottom:8px;font-family:Georgia,'Times New Roman',serif}
.art-meta{font-size:.68rem;color:var(--text3);margin-bottom:16px;display:flex;align-items:center;gap:8px;flex-wrap:wrap}
.art-content{font-size:.82rem;line-height:1.8;color:var(--text2)}
.art-content p{margin-bottom:13px}
.read-more{display:inline-flex;align-items:center;gap:6px;background:var(--accent);color:var(--accent-text);border:none;padding:8px 16px;border-radius:8px;font-size:.76rem;font-weight:600;cursor:pointer;text-decoration:none;margin-top:8px}
.read-more:hover{opacity:.9}
.annexes{margin-top:22px;padding-top:16px;border-top:1px solid var(--border)}
.annexes h3{font-size:.64rem;font-weight:700;text-transform:uppercase;letter-spacing:.8px;color:var(--text3);margin-bottom:8px}
.src-item{display:flex;align-items:flex-start;gap:8px;margin-bottom:6px}
.src-num{font-size:.6rem;font-weight:700;color:var(--accent);background:rgba(224,75,75,.08);padding:2px 6px;border-radius:4px;flex-shrink:0;margin-top:1px}
.src-name{font-size:.72rem;font-weight:600;color:var(--text2);display:block}
.src-url{font-size:.66rem;color:var(--accent);text-decoration:none;word-break:break-all}
.src-url:hover{text-decoration:underline}
.vfoot{display:flex;align-items:center;gap:5px;margin-top:10px;font-size:.64rem;color:var(--accent);background:rgba(224,75,75,.06);padding:6px 10px;border-radius:6px}
.bm-empty{text-align:center;padding:48px;color:var(--text3)}

@media(max-width:1024px){.layout.panel-open .panel-col{width:380px}.feed-col{padding:22px 28px}.grid{grid-template-columns:repeat(2,1fr)}}
@media(max-width:768px){
.upd{display:none}.search-wrap{max-width:160px}
.layout.panel-open .panel-col{width:100%;position:absolute;inset:0;z-index:10}
.layout.panel-open .feed-col{display:none}
.hero{flex-direction:column;min-height:auto}.hero-img{flex:0 0 200px}.hero-img img{position:absolute;top:0;left:0;width:100%;height:100%}.hero-body{padding:20px 22px}.hero-title{font-size:1.15rem}
.grid{grid-template-columns:repeat(2,1fr);gap:12px}.feed-col{padding:16px}
}
@media(max-width:640px){
header{padding:0 12px;height:52px}.search-wrap{display:none}
.tabs{top:52px;padding:0 8px}.tab{padding:8px 10px;font-size:.68rem}
.layout{top:96px}.feed-col{padding:10px}.grid{grid-template-columns:1fr;gap:10px}
.hero{border-radius:12px;margin-bottom:22px}.hero-img{flex:0 0 170px}.hero-body{padding:14px 16px}
.card{flex-direction:row;height:120px}.card-img{width:120px;height:120px;flex-shrink:0}.card-body{padding:10px 12px}.card-excerpt{display:none}.card-title{font-size:.78rem}
.panel-body{padding:14px 16px 32px}.art-title{font-size:1rem}.art-hero-img img{max-height:200px}
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
  const feat=cat==='all'?list[0]:null;
  const rest=feat?list.slice(1):list;
  let out='<div class="section-label">'+CAT_LABELS[cat]+' &mdash; '+list.length+' article'+(list.length!==1?'s':'')+'</div>';
  if(feat) out+=heroHTML(feat);
  if(rest.length){
    const groups = groupByDate(rest);
    for(const [label, items] of Object.entries(groups)){
      out += '<div class="date-group"><div class="date-title">'+label+' <span class="date-count">&mdash; '+items.length+' article'+(items.length!==1?'s':'')+'</span></div>';
      out += '<div class="grid">'+items.map(cardHTML).join('')+'</div></div>';
    }
  }
  fc.innerHTML=out;
}

function renderSearch(fc){
  const found=ARTICLES.filter(a=>{
    const t=(a.title+' '+a.excerpt+' '+a.source+' '+a.catLabel).toLowerCase();
    return t.includes(searchTerm);
  }).slice().sort((a,b)=>(b.pubTs||0)-(a.pubTs||0));
  let out='<div class="section-label">Recherche &mdash; '+found.length+' resultat'+(found.length!==1?'s':'')+' pour "'+esc(searchTerm)+'"</div>';
  if(found.length){
    const groups = groupByDate(found);
    for(const [label, items] of Object.entries(groups)){
      out += '<div class="date-group"><div class="date-title">'+label+'</div>';
      out += '<div class="grid">'+items.map(cardHTML).join('')+'</div></div>';
    }
  }else{
    out+='<div class="bm-empty">Aucun article ne correspond a votre recherche.</div>';
  }
  fc.innerHTML=out;
}

function heroHTML(a){
  const bmc=isBm(a.id)?'bm-btn on':'bm-btn';
  return '<div class="hero" onclick="openPanel(\''+a.id+'\')">'
    +'<div class="hero-img"><img src="'+esc(a.image)+'" alt="" loading="lazy" onerror="this.style.display=\'none\';this.nextElementSibling.style.display=\'flex\'"><div class="img-fb" style="display:none">'+esc(a.catLabel)+'</div></div>'
    +'<div class="hero-body">'
      +'<div class="hero-cat">'+esc(a.catLabel)+'</div>'
      +'<div class="hero-title">'+esc(a.title)+'</div>'
      +'<div class="hero-excerpt">'+esc(a.excerpt)+'</div>'
      +'<div class="hero-foot">'
        +'<div style="display:flex;align-items:center;gap:8px">'
          +'<span class="badge-cat cat-'+a.cat+'">'+a.catLabel+'</span>'
          +'<span class="rel-tag '+a.reliability+'">'+a.reliabilityLabel+' &middot; '+a.verifiedSources+' source'+(a.verifiedSources>1?'s':'')+'</span>'
        +'</div>'
        +'<div style="display:flex;align-items:center;gap:8px">'
          +'<button class="'+bmc+'" data-bmid="'+a.id+'" onclick="toggleBm(\''+a.id+'\',event)">&#128204;</button>'
          +'<span class="hero-read">Lire &rarr;</span>'
        +'</div>'
      +'</div>'
    +'</div>'
  +'</div>';
}

function cardHTML(a){
  const bmc=isBm(a.id)?'bm-btn on':'bm-btn';
  return '<div class="card" onclick="openPanel(\''+a.id+'\')">'
    +'<div class="card-img"><img src="'+esc(a.image)+'" alt="" loading="lazy" onerror="this.style.display=\'none\';this.nextElementSibling.style.display=\'flex\'">'
    +'<div class="img-fb" style="display:none">'+esc(a.catLabel)+'</div></div>'
    +'<div class="card-body">'
      +'<div class="card-top">'
        +'<span class="badge-cat cat-'+a.cat+'">'+a.catLabel+'</span>'
        +'<button class="'+bmc+'" data-bmid="'+a.id+'" onclick="toggleBm(\''+a.id+'\',event)">&#128204;</button>'
      +'</div>'
      +'<div class="card-title">'+esc(a.title)+'</div>'
      +'<div class="card-excerpt">'+esc(a.excerpt)+'</div>'
      +'<div class="card-foot"><span>'+a.date+'</span><span class="card-cta">Lire &rarr;</span></div>'
    +'</div>'
  +'</div>';
}

function renderBm(fc){
  const saved=ARTICLES.filter(a=>isBm(a.id));
  if(saved.length){
    fc.innerHTML='<div class="section-label">Sauvegardes &mdash; '+saved.length+'</div><div class="grid">'+saved.map(cardHTML).join('')+'</div>';
  }else{
    fc.innerHTML='<div class="section-label">Sauvegardes &mdash; 0</div><div class="bm-empty">&#128204;<br><br>Aucun article sauvegarde.</div>';
  }
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
  const a=ARTICLES.find(x=>x.id===id);if(!a)return;
  curId=id;
  document.querySelectorAll('.active-card').forEach(el=>el.classList.remove('active-card'));
  const panel=document.getElementById('panel');
  const layout=document.getElementById('layout');
  if(!panel||!layout)return;
  const content = a.body ? a.body : formatContent(a.excerpt);
  panel.innerHTML=''
    +'<div class="panel-topbar">'
      +'<div class="panel-topbar-l">'
        +'<span class="badge-cat cat-'+a.cat+'">'+a.catLabel+'</span>'
        +'<span class="rel-tag '+a.reliability+'">'+a.reliabilityLabel+' &mdash; '+a.verifiedSources+' source'+(a.verifiedSources>1?'s':'')+'</span>'
      +'</div>'
      +'<div class="panel-actions">'
        +'<button class="panel-bm'+(isBm(id)?' on':'')+'" id="panelBm" onclick="toggleBm(\''+id+'\',null)">'+(isBm(id)?'Sauvegarde':'Sauvegarder')+'</button>'
        +'<button class="panel-close" onclick="closePanel()">&#x2715;</button>'
      +'</div>'
    +'</div>'
    +'<div class="panel-body">'
      +'<div class="art-hero-img"><img src="'+esc(a.image)+'" alt="" loading="lazy" onerror="this.style.display=\'none\'"></div>'
      +'<h1 class="art-title">'+esc(a.title)+'</h1>'
      +'<div class="art-meta">'
        +'<span>'+a.date+'</span><span>&middot;</span>'
        +'<span>'+a.readTime+' de lecture</span><span>&middot;</span>'
        +'<span>'+esc(a.source)+'</span>'
      +'</div>'
      +'<div class="art-content">'+content+'</div>'
      +'<a class="read-more" href="'+esc(a.url)+'" target="_blank" rel="noopener">Lire l\'article complet &rarr;</a>'
      +'<div class="annexes">'
        +'<h3>Source originale</h3>'
        +'<div class="src-item">'
          +'<span class="src-num">[1]</span>'
          +'<div>'
            +'<span class="src-name">'+esc(a.source)+'</span>'
            +'<a class="src-url" href="'+esc(a.url)+'" target="_blank" rel="noopener">'+esc(a.url)+'</a>'
          +'</div>'
        +'</div>'
        +'<div class="vfoot">&#10003; Croise sur '+a.verifiedSources+' source'+(a.verifiedSources>1?'s':'')+' avant publication</div>'
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
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>TechFeed</title>
<style>{CSS}</style>
</head>
<body>
<header>
  <div class="logo">&#128240; TechFeed <span>MAGAZINE</span></div>
  <div class="search-wrap">
    <input id="searchInput" type="text" placeholder="Rechercher un article..." oninput="searchArticles(this.value)">
    <button id="searchClear" class="search-clear" onclick="document.getElementById('searchInput').value='';searchArticles('')">&#x2715;</button>
  </div>
  <div class="hright">
    <span class="upd">Mis a jour le {last_update}</span>
    <button class="btn-theme" id="themeBtn" onclick="toggleTheme()" title="Theme clair/sombre">&#9728;</button>
    <button class="btn-bookmarks" onclick="showTab('bookmarks',null)">&#128204; Sauvegardes</button>
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
  <div class="tab" onclick="showTab('worldcup',this)">&#9917; Coupe du Monde</div>
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
