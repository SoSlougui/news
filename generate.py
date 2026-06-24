#!/usr/bin/env python3
"""
TechFeed — Générateur du site HTML (v3)
Lit articles.js et génère un index.html responsive avec recherche,
bookmarks, panneau latéral et catégories.
"""

import json
import re
import os
from datetime import datetime

# ─────────────────────────────────────────
# CATÉGORIES
# ─────────────────────────────────────────
CAT_LABELS = {
    "all":     "Toutes les actualités",
    "ia":      "IA & Tech",
    "crypto":  "Crypto",
    "gaming":  "Jeux Vidéo",
    "markets": "Marchés",
    "general": "Général",
    "science": "Science",
    "dev":     "Développement",
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
    """Lit articles.js (window.ARTICLES = [...]) et extrait les articles."""
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
        rel_label = "✓ Consensus fort" if vsrc >= 2 else "~ Source unique"
        img = item.get("image", "")

        articles.append({
            "id":              item.get("id", slug(title)),
            "cat":             cat,
            "catLabel":        CAT_LABELS.get(cat, "Général"),
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
.img-fb{width:100%;height:100%;display:flex;align-items:center;justify-content:center;background:linear-gradient(135deg,#e5e7eb,#f0f2f5);color:#9ca3af;font-size:.7rem;font-weight:700;letter-spacing:1px;text-transform:uppercase;text-align:center;padding:8px;line-height:1.2}
.card-body{padding:13px;flex:1;display:flex;flex-direction:column}
.card-top{display:flex;align-items:center;justify-content:space-between;margin-bottom:7px}
.badge-cat{padding:2px 8px;border-radius:99px;font-size:.63rem;font-weight:700;text-transform:uppercase;letter-spacing:.3px}
.cat-ia{background:#eff6ff;color:#1d4ed8}.cat-crypto{background:#fffbeb;color:#b45309}
.cat-gaming{background:#f0fdf4;color:#15803d}.cat-markets{background:#faf5ff;color:#7e22ce}.cat-general{background:#fff1f2;color:#be123c}
.cat-science{background:#ecfeff;color:#0891b2}.cat-dev{background:#f5f3ff;color:#7c3aed}.cat-startups{background:#fefce8;color:#a16207}
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
.wc-section{background:#fff;border-radius:14px;border:1px solid #e5e7eb;padding:16px 20px;margin-bottom:14px}
.wc-section h3{font-size:.82rem;font-weight:700;margin-bottom:10px;color:#111827;display:flex;align-items:center;gap:6px}
.wc-table{width:100%;border-collapse:collapse;font-size:.78rem}
.wc-table th{text-align:left;padding:6px 8px;font-size:.68rem;font-weight:700;text-transform:uppercase;letter-spacing:.5px;color:#9ca3af;border-bottom:1px solid #e5e7eb}
.wc-table td{padding:5px 8px;border-bottom:1px solid #f3f4f6;vertical-align:middle}
.wc-table tr:last-child td{border-bottom:none}
.wc-flag{width:22px;height:16px;display:inline-block;border-radius:2px;vertical-align:middle;margin-right:6px}
.wc-team{font-weight:600;display:flex;align-items:center;gap:5px}
.wc-pts{font-weight:700;color:#2563eb}
.wc-qualified{font-size:.62rem;color:#15803d;background:#f0fdf4;padding:1px 6px;border-radius:99px;font-weight:600}
.wc-eliminated{font-size:.62rem;color:#be123c;background:#fff1f2;padding:1px 6px;border-radius:99px;font-weight:600}
.wc-score{font-weight:700;font-size:.82rem;min-width:32px;text-align:center}
.wc-winner{color:#15803d}.wc-draw{color:#9ca3af}
.wc-time{font-size:.68rem;color:#9ca3af;white-space:nowrap}
.wc-matchup{display:flex;align-items:center;justify-content:space-between;gap:8px;padding:6px 0}
.wc-matchup .teams{display:flex;align-items:center;gap:8px;flex:1}
.wc-matchup .teams .vs{color:#9ca3af;font-size:.7rem;font-weight:600;margin:0 4px}
.wc-poule-title{font-size:.7rem;font-weight:700;text-transform:uppercase;letter-spacing:.5px;color:#6b7280;margin-bottom:8px;padding-bottom:4px;border-bottom:2px solid #e5e7eb}
.wc-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(320px,1fr));gap:12px}
.wc-knockout{font-size:.78rem;line-height:1.6;color:#374151}
.wc-knockout b{color:#111827}
@media(max-width:640px){.wc-grid{grid-template-columns:1fr}}
@media(max-width:1024px){.layout.panel-open .panel-col{width:360px}.grid{grid-template-columns:repeat(auto-fill,minmax(220px,1fr))}}
@media(max-width:768px){.upd{display:none}.layout.panel-open .panel-col{width:100%;position:absolute;inset:0;z-index:10}.layout.panel-open .feed-col{display:none}.hero{grid-template-columns:1fr}.hero-img{height:200px;order:-1}.hero-body{padding:16px}.grid{grid-template-columns:repeat(auto-fill,minmax(200px,1fr));gap:10px}}
@media(max-width:640px){header{padding:10px 14px;height:52px}.logo h1{font-size:1rem}.view-toggle{display:none}.btn-ghost{padding:5px 9px;font-size:.72rem}.tabs{top:52px;padding:0 8px}.tab{padding:9px 11px;font-size:.76rem}.layout{top:96px}.feed-col{padding:10px}.grid{grid-template-columns:1fr;gap:8px}.card{flex-direction:row;height:110px}.card-img{width:120px;height:110px;flex-shrink:0;border-radius:0}.card-body{padding:9px 11px}.card-title{font-size:.82rem;-webkit-line-clamp:2;display:-webkit-box;-webkit-box-orient:vertical;overflow:hidden}.card-excerpt{display:none}.hero{grid-template-columns:1fr;min-height:auto}.hero-img{height:170px;order:-1}.hero-body{padding:13px 14px}.hero-title{font-size:1rem}.hero-excerpt{-webkit-line-clamp:2}.bm-btn{font-size:1.1rem;padding:4px 6px}.panel-body{padding:14px 16px 32px}.art-title{font-size:1rem}.art-hero-img img{max-height:200px}.list .card{flex-direction:column;height:auto}.list .card-img{width:100%;height:130px}}
"""

JS = r"""
const ARTICLES = __ARTICLES__;
const CAT_LABELS = {all:'Toutes les actualites',ia:'IA & Tech',crypto:'Crypto',gaming:'Jeux Video',markets:'Marches',general:'General',science:'Science',dev:'Developpement',startups:'Startups',bookmarks:'Sauvegardes',search:'Recherche',worldcup:'Coupe du Monde 2026'};
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
  if(cat==='worldcup'){renderWorldCup(fc);return;}
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
};;

// Résultats des matchs déjà joués (24 juin inclus)
const WC_MATCHES_DONE = [
  // Groupe A
  {g:'A',d:'11 juin',t1:'Mexique',t2:'Afrique du Sud',s1:2,s2:0},
  {g:'A',d:'11 juin',t1:'Coree du Sud',t2:'Republique Tcheque',s1:2,s2:1},
  {g:'A',d:'18 juin',t1:'Republique Tcheque',t2:'Afrique du Sud',s1:1,s2:1},
  {g:'A',d:'18 juin',t1:'Mexique',t2:'Coree du Sud',s1:1,s2:0},
  // Groupe B
  {g:'B',d:'12 juin',t1:'Canada',t2:'Bosnie-Herzegovine',s1:1,s2:1},
  {g:'B',d:'13 juin',t1:'Qatar',t2:'Suisse',s1:1,s2:1},
  {g:'B',d:'18 juin',t1:'Suisse',t2:'Bosnie-Herzegovine',s1:4,s2:1},
  {g:'B',d:'18 juin',t1:'Canada',t2:'Qatar',s1:6,s2:0},
  // Groupe C
  {g:'C',d:'13 juin',t1:'Bresil',t2:'Maroc',s1:1,s2:1},
  {g:'C',d:'13 juin',t1:'Haiti',t2:'Ecosse',s1:0,s2:1},
  {g:'C',d:'19 juin',t1:'Ecosse',t2:'Maroc',s1:0,s2:1},
  {g:'C',d:'19 juin',t1:'Bresil',t2:'Haiti',s1:3,s2:0},
  // Groupe D
  {g:'D',d:'12 juin',t1:'Etats-Unis',t2:'Paraguay',s1:4,s2:1},
  {g:'D',d:'13 juin',t1:'Australie',t2:'Turkiye',s1:2,s2:0},
  {g:'D',d:'19 juin',t1:'Etats-Unis',t2:'Australie',s1:2,s2:0},
  {g:'D',d:'19 juin',t1:'Turkiye',t2:'Paraguay',s1:0,s2:1},
  // Groupe E
  {g:'E',d:'14 juin',t1:'Allemagne',t2:'Curacao',s1:7,s2:1},
  {g:'E',d:'14 juin',t1:'Cote d\'Ivoire',t2:'Equateur',s1:1,s2:0},
  {g:'E',d:'20 juin',t1:'Allemagne',t2:'Cote d\'Ivoire',s1:2,s2:1},
  {g:'E',d:'20 juin',t1:'Equateur',t2:'Curacao',s1:0,s2:0},
  // Groupe F
  {g:'F',d:'14 juin',t1:'Pays-Bas',t2:'Japon',s1:2,s2:2},
  {g:'F',d:'14 juin',t1:'Suede',t2:'Tunisie',s1:5,s2:1},
  {g:'F',d:'20 juin',t1:'Pays-Bas',t2:'Suede',s1:5,s2:1},
  {g:'F',d:'20 juin',t1:'Tunisie',t2:'Japon',s1:0,s2:4},
  // Groupe G
  {g:'G',d:'15 juin',t1:'Belgique',t2:'Egypte',s1:1,s2:1},
  {g:'G',d:'15 juin',t1:'Iran',t2:'Nouvelle-Zelande',s1:2,s2:2},
  {g:'G',d:'21 juin',t1:'Belgique',t2:'Iran',s1:0,s2:0},
  {g:'G',d:'21 juin',t1:'Nouvelle-Zelande',t2:'Egypte',s1:1,s2:3},
  // Groupe H
  {g:'H',d:'15 juin',t1:'Espagne',t2:'Cap-Vert',s1:0,s2:0},
  {g:'H',d:'15 juin',t1:'Arabie Saoudite',t2:'Uruguay',s1:1,s2:1},
  {g:'H',d:'21 juin',t1:'Espagne',t2:'Arabie Saoudite',s1:4,s2:0},
  {g:'H',d:'21 juin',t1:'Uruguay',t2:'Cap-Vert',s1:2,s2:2},
  // Groupe I
  {g:'I',d:'16 juin',t1:'France',t2:'Senegal',s1:3,s2:1},
  {g:'I',d:'16 juin',t1:'Irak',t2:'Norvege',s1:1,s2:4},
  {g:'I',d:'22 juin',t1:'France',t2:'Irak',s1:3,s2:0},
  {g:'I',d:'22 juin',t1:'Norvege',t2:'Senegal',s1:3,s2:2},
  // Groupe J
  {g:'J',d:'16 juin',t1:'Argentine',t2:'Algerie',s1:3,s2:0},
  {g:'J',d:'16 juin',t1:'Autriche',t2:'Jordanie',s1:3,s2:1},
  {g:'J',d:'22 juin',t1:'Argentine',t2:'Autriche',s1:2,s2:0},
  {g:'J',d:'22 juin',t1:'Jordanie',t2:'Algerie',s1:1,s2:2},
  // Groupe K
  {g:'K',d:'17 juin',t1:'Portugal',t2:'RD Congo',s1:1,s2:1},
  {g:'K',d:'17 juin',t1:'Ouzbekistan',t2:'Colombie',s1:1,s2:3},
  {g:'K',d:'23 juin',t1:'Portugal',t2:'Ouzbekistan',s1:5,s2:0},
  {g:'K',d:'23 juin',t1:'Colombie',t2:'RD Congo',s1:1,s2:0},
  // Groupe L
  {g:'L',d:'17 juin',t1:'Angleterre',t2:'Croatie',s1:4,s2:2},
  {g:'L',d:'17 juin',t1:'Ghana',t2:'Panama',s1:1,s2:0},
  {g:'L',d:'23 juin',t1:'Angleterre',t2:'Ghana',s1:0,s2:0},
  {g:'L',d:'23 juin',t1:'Panama',t2:'Croatie',s1:0,s2:1}
];;

// Matchs à venir (25 juin - 27 juin)
const WC_MATCHES_UPCOMING = [
  // Matchs du 24 juin (programmes aujourd'hui)
  {g:'A',d:'24 juin',t1:'Republique Tcheque',t2:'Mexique',h:'21:00'},
  {g:'A',d:'24 juin',t1:'Afrique du Sud',t2:'Coree du Sud',h:'21:00'},
  {g:'B',d:'24 juin',t1:'Suisse',t2:'Canada',h:'15:00'},
  {g:'B',d:'24 juin',t1:'Bosnie-Herzegovine',t2:'Qatar',h:'15:00'},
  {g:'C',d:'24 juin',t1:'Ecosse',t2:'Bresil',h:'18:00'},
  {g:'C',d:'24 juin',t1:'Maroc',t2:'Haiti',h:'18:00'},
  // Matchs du 25 juin
  {g:'E',d:'25 juin',t1:'Equateur',t2:'Allemagne',h:'16:00'},
  {g:'E',d:'25 juin',t1:'Curacao',t2:'Cote d\'Ivoire',h:'16:00'},
  {g:'F',d:'25 juin',t1:'Japon',t2:'Suede',h:'19:00'},
  {g:'F',d:'25 juin',t1:'Tunisie',t2:'Pays-Bas',h:'19:00'},
  {g:'D',d:'25 juin',t1:'Turkiye',t2:'Etats-Unis',h:'22:00'},
  {g:'D',d:'25 juin',t1:'Paraguay',t2:'Australie',h:'22:00'},
  // Matchs du 26 juin
  {g:'I',d:'26 juin',t1:'Norvege',t2:'France',h:'15:00'},
  {g:'I',d:'26 juin',t1:'Senegal',t2:'Irak',h:'15:00'},
  {g:'H',d:'26 juin',t1:'Cap-Vert',t2:'Arabie Saoudite',h:'20:00'},
  {g:'H',d:'26 juin',t1:'Uruguay',t2:'Espagne',h:'20:00'},
  {g:'G',d:'26 juin',t1:'Egypte',t2:'Iran',h:'23:00'},
  {g:'G',d:'26 juin',t1:'Nouvelle-Zelande',t2:'Belgique',h:'23:00'},
  // Matchs du 27 juin
  {g:'L',d:'27 juin',t1:'Panama',t2:'Angleterre',h:'17:00'},
  {g:'L',d:'27 juin',t1:'Croatie',t2:'Ghana',h:'17:00'},
  {g:'K',d:'27 juin',t1:'Colombie',t2:'Portugal',h:'19:30'},
  {g:'K',d:'27 juin',t1:'RD Congo',t2:'Ouzbekistan',h:'19:30'},
  {g:'J',d:'27 juin',t1:'Algerie',t2:'Autriche',h:'22:00'},
  {g:'J',d:'27 juin',t1:'Jordanie',t2:'Argentine',h:'22:00'}
];;

function renderWorldCup(fc){
  // Auto-suppression après le 22 juillet 2026
  const now = new Date();
  const deadline = new Date('2026-07-23T00:00:00');
  if(now >= deadline){
    fc.innerHTML='<div class="bm-empty">&#9917;<br><br>La section Coupe du Monde 2026 a ete archivee.</div>';
    return;
  }

  // ── Groupes ──
  let out = '<div class="sec-label">Coupe du Monde 2026 &mdash; Phases de Groupes</div><div class="wc-grid">';
  for(const [gk, g] of Object.entries(WC_GROUPS)){
    out += `<div class="wc-section"><div class="wc-poule-title">${g.name}</div><table class="wc-table"><thead><tr><th>Equipe</th><th style="text-align:center;width:30px">J</th><th style="text-align:center;width:30px">V</th><th style="text-align:center;width:30px">N</th><th style="text-align:center;width:30px">D</th><th style="text-align:center;width:40px">BP</th><th style="text-align:center;width:40px">BC</th><th style="text-align:center;width:30px">+/-</th><th style="text-align:center;width:30px">Pts</th></tr></thead><tbody>`;
    const sorted = [...g.teams].sort((a,b)=>b.p-a.p || (b.gf-b.ga)-(a.gf-a.ga));
    for(const t of sorted){
      const gd = t.gf - t.ga;
const status = t.q ? '<span class="wc-qualified">Qualifie</span>' : t.e ? '<span class="wc-eliminated">Elimine</span>' : '';
      const gp = t.pl || 3;
      out += `<tr><td><span class="wc-team">${t.flag} ${t.team} ${status}</span></td><td style="text-align:center">${gp}</td><td style="text-align:center">${Math.floor(t.p/3)}</td><td style="text-align:center">${t.p%3!==0?1:0}</td><td style="text-align:center">${gp-Math.floor(t.p/3)-(t.p%3!==0?1:0)}</td><td style="text-align:center">${t.gf}</td><td style="text-align:center">${t.ga}</td><td style="text-align:center">${gd>0?'+':''}${gd}</td><td style="text-align:center" class="wc-pts">${t.p}</td></tr>`;
    }
    out += '</tbody></table></div>';
  }
  out += '</div>';

  // ── Phase finale (équipes qualifiées) ──
  out += '<div class="sec-label">Coupe du Monde 2026 &mdash; Phase Finale</div><div class="wc-section">';
  out += '<h3>&#127942; 32es de finale</h3>';
  out += '<div class="wc-knockout">';
  out += `<i>Les 32es de finale debutent le 29 juin. Les 12 premiers de groupe, les 12 deuxiemes et les 8 meilleurs troisiemes composeront le tableau. Les derniers matchs de groupes se jouent du 24 au 27 juin.</i>`;
  out += '</div></div>';

  // ── Résultats des matchs ──
  out += '<div class="sec-label">Matchs Joues</div><div class="wc-grid">';
  const byGroupD = {};
  for(const m of WC_MATCHES_DONE){
    if(!byGroupD[m.g]) byGroupD[m.g] = [];
    byGroupD[m.g].push(m);
  }
  for(const [gk, matches] of Object.entries(byGroupD)){
    const gname = WC_GROUPS[gk] ? WC_GROUPS[gk].name : 'Groupe '+gk;
    out += `<div class="wc-section"><div class="wc-poule-title">${gname}</div>`;
    for(const m of matches){
      const cls1 = m.s1 > m.s2 ? 'wc-winner' : m.s1 === m.s2 ? 'wc-draw' : '';
      const cls2 = m.s2 > m.s1 ? 'wc-winner' : m.s2 === m.s1 ? 'wc-draw' : '';
      out += `<div class="wc-matchup"><div class="teams"><span class="${cls1}">${m.flag1||''} ${m.t1}</span><span class="vs">vs</span><span class="${cls2}">${m.flag2||''} ${m.t2}</span></div><div style="display:flex;align-items:center;gap:6px"><span class="wc-score ${cls1}">${m.s1}</span><span style="color:#9ca3af;font-size:.7rem">-</span><span class="wc-score ${cls2}">${m.s2}</span><span class="wc-time">${m.d}</span></div></div>`;
    }
    out += '</div>';
  }
  out += '</div>';

  // ── Programme des matchs à venir ──
  out += '<div class="sec-label">Matchs a Venir</div><div class="wc-grid">';
  const byGroupU = {};
  for(const m of WC_MATCHES_UPCOMING){
    if(!byGroupU[m.g]) byGroupU[m.g] = [];
    byGroupU[m.g].push(m);
  }
  for(const [gk, matches] of Object.entries(byGroupU)){
    const gname = WC_GROUPS[gk] ? WC_GROUPS[gk].name : 'Groupe '+gk;
    out += `<div class="wc-section"><div class="wc-poule-title">${gname}</div>`;
    for(const m of matches){
      out += `<div class="wc-matchup"><div class="teams"><span>${m.t1}</span><span class="vs">vs</span><span>${m.t2}</span></div><span class="wc-time" style="font-weight:600">${m.d} &middot; ${m.h}</span></div>`;
    }
    out += '</div>';
  }
  out += '</div>';

  out += '<div class="wc-section" style="text-align:center;color:#9ca3af;font-size:.72rem">Derniere mise a jour : 24 juin 2026 &middot; Les qualifications sont mises a jour au fil des matchs</div>';

  fc.innerHTML = out;
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
    print("TechFeed v3 - Generation du site...")
    
    # Lecture des articles (cron job Kimi)
    articles = load_articles_js()
    print(f"  -> {len(articles)} articles (articles.js)")
    
    # Generation HTML
    last_update = datetime.now().strftime("%d %B %Y - %H:%M")
    content = generate_html(articles, last_update)
    with open("index.html", "w", encoding="utf-8") as f:
        f.write(content)
    open(".nojekyll", "w").close()
    
    print(f"OK - {len(articles)} articles, {len(content)//1024}KB")


if __name__ == "__main__":
    main()
