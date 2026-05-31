import json,html
from core.keyword_taxonomy import GEO_FLAVOR
from core.asset_fetcher import payment_logo_url, casino_logo, real_casino_brands
PAY_COLORS={"upi":"#097939","paytm":"#00baf2","bkash":"#e2136e","nagad":"#ee1c25","rocket":"#8c3fa0","pix":"#32bcad","card":"#1a1f71","paypal":"#003087"}
def faq_schema(brand):
    qs=[(f"Is {brand} safe?",f"{brand} is licensed and reviewed for payout speed."),
        (f"How fast are {brand} payouts?","Usually within 24 hours.")]
    return {"@context":"https://schema.org","@type":"FAQPage","mainEntity":[
        {"@type":"Question","name":q,"acceptedAnswer":{"@type":"Answer","text":a}} for q,a in qs]}
def full_schema(p, content):
    import json as _j
    g=[
     {"@type":"Organization","name":p["brand"],"url":f"https://{p['domain']}/"},
     {"@type":"WebSite","name":p["brand"],"url":f"https://{p['domain']}/"},
     {"@type":"Article","headline":p["keyword"]+" - "+p["brand"],"author":{"@type":"Person","name":"Editorial Team"},"datePublished":"2026-05-01","dateModified":"2026-05-30","publisher":{"@type":"Organization","name":p["brand"]}},
     {"@type":"BreadcrumbList","itemListElement":[{"@type":"ListItem","position":1,"name":"Home","item":f"https://{p['domain']}/"},{"@type":"ListItem","position":2,"name":p["keyword"]}]},
     {"@type":"Review","itemReviewed":{"@type":"Organization","name":p["brand"]},"author":{"@type":"Person","name":"Editorial Team"},"reviewRating":{"@type":"Rating","ratingValue":"4.8","bestRating":"5"}},
     {"@type":"AggregateRating","itemReviewed":{"@type":"Organization","name":p["brand"]},"ratingValue":"4.8","reviewCount":"1240","bestRating":"5"},
    ]
    qs=content.get("sections",{}).get("faq","")
    g.append({"@type":"FAQPage","mainEntity":[{"@type":"Question","name":f"Is {p['brand']} safe?","acceptedAnswer":{"@type":"Answer","text":(qs or "Reviewed for licensing and payouts.")[:300]}}]})
    return _j.dumps({"@context":"https://schema.org","@graph":g})

def render(plan,content,hero_url,logo_url,nav_links=None):
    p=plan; pal=p["palette"]; fh,fb=p["fonts"]; secs_txt=content.get("sections",{})
    blocks=[]
    for s in p["sections"]:
        txt=secs_txt.get(s,f"Content about {p['brand']}.")
        if s in ("toplist","comparison"):
            bonuses_pool=["100% up to 10,000","Welcome Pack + 100 FS","150% First Deposit"]
            stars_pool=["★★★★★","★★★★☆","★★★★☆"]; rates=["9.8","9.4","9.1"]
            brands=real_casino_brands(p["geo"],3)
            cards="".join(f'<div class="card"><img class="cardlogo" src="{casino_logo(brands[i][1])}" alt="{brands[i][0]}"><div class="cardmain"><b>{html.escape(brands[i][0])}</b><div class="stars">{stars_pool[i]} <span class="rate">{rates[i]}</span></div><div class="bonus">{bonuses_pool[i]}</div></div><a class="cta" href="/go/">Claim</a></div>' for i in range(min(3,len(brands))))
            body=f'<p>{html.escape(txt)}</p>{cards}'
        elif s=="faq":
            body='<details open><summary>Is it safe?</summary><p>'+html.escape(secs_txt.get("faq",txt))+'</p></details>'
        else:
            body=f'<p>{html.escape(txt)}</p>'
        title=s.replace("_"," ").title()
        blocks.append(f'<section><h2>{title}</h2>{body}</section>')
    css=f"""*{{box-sizing:border-box}}body{{margin:0;background:{pal['bg']};color:{pal['fg']};font-family:{fb};line-height:1.65}}
*{{transition:transform .2s,box-shadow .2s,background .2s}}@keyframes fade{{from{{opacity:0;transform:translateY(16px)}}to{{opacity:1;transform:none}}}}section{{animation:fade .5s ease both}}.card:hover{{transform:translateX(4px)}}.cta:hover{{transform:scale(1.03)}}.sticky-cta:hover{{transform:translateY(-2px)}}.navlinks a:hover{{opacity:1}}h1,h2{{font-family:{fh};letter-spacing:-.02em}}.wrap{{max-width:900px;margin:0 auto;padding:0 16px 40px}}
.nav{{display:flex;align-items:center;gap:12px;padding:14px 0}}.nav img{{height:38px;border-radius:8px}}.nav{{flex-wrap:wrap}}.navlinks{{display:flex;gap:4px;overflow-x:auto;width:100%;margin-top:8px;-webkit-overflow-scrolling:touch;padding-bottom:4px}}.navlinks a{{color:{pal["fg"]};opacity:.75;white-space:nowrap;background:#ffffff14;padding:6px 10px;border-radius:8px;text-decoration:none;font-size:13px;flex-shrink:0}}.brandmark{{font-family:{fh};font-size:22px;font-weight:800;color:{pal["accent"]};letter-spacing:-.03em}}
.hero{{background:linear-gradient(135deg,{pal["accent"]}33,{pal["card"]});position:relative;min-height:220px;border-radius:{p['radius']};overflow:hidden;margin:8px 0 18px}}
.hero img{{width:100%;height:240px;object-fit:cover;display:block;opacity:.55}}
.hero .h{{position:absolute;inset:0;display:flex;flex-direction:column;justify-content:center;padding:24px;text-align:{'center' if p['hero']=='center' else 'left'}}}
.hero h1{{margin:0 0 12px;font-size:30px}}
section{{background:{pal['card']};border-radius:{p['radius']};padding:20px;margin:14px 0;border:1px solid #ffffff14}}
.cta{{display:inline-block;background:{pal['accent']};color:#0a0a0a;padding:11px 20px;border-radius:{p['radius']};text-decoration:none;font-weight:800}}
.card{{display:flex;gap:14px;align-items:center;border-bottom:1px solid #ffffff1a;padding:14px 0}}
.pays-row{{margin:18px 0;color:{pal["fg"]}}}.payimg{{height:16px;vertical-align:middle;margin-right:6px}}.pay{{display:inline-flex;align-items:center;color:#fff;padding:6px 12px;border-radius:8px;font-weight:700;margin-right:8px;font-size:13px}}.sticky-cta{{position:fixed;left:12px;right:12px;bottom:12px;z-index:99;background:{pal["accent"]};color:#0a0a0a;text-align:center;padding:16px;border-radius:{p["radius"]};font-weight:800;text-decoration:none;box-shadow:0 6px 24px #0008;font-size:17px}}@media(min-width:760px){{.sticky-cta{{left:auto;right:24px;bottom:24px;padding:14px 32px}}}}.cardlogo{{width:46px;height:46px;border-radius:12px;flex-shrink:0;background:#fff2;object-fit:contain}}.cardmain{{flex:1}}.stars{{color:#f5c518;font-size:14px;margin:2px 0}}.rate{{color:{pal["accent"]};font-weight:700;margin-left:4px}}.bonus{{font-size:13px;opacity:.85}}.muted{{opacity:.6;font-size:13px}}details summary{{cursor:pointer;font-weight:700}}"""
    schema=full_schema(p,content)
    _heroimg=(f'<img src="{hero_url}" alt="hero">' if hero_url else "")
    hero_block=f'<div class="hero">{_heroimg}<div class="h"><h1>{html.escape(p["keyword"])} — {html.escape(p["brand"])} {p["geo"].upper()}</h1><a class="cta" href="/go/">{p["cta"]}</a></div></div>' 
    pays=GEO_FLAVOR.get(p["geo"],{}).get("pay",[])
    def _pb(x):
        u=payment_logo_url(x)
        if u: return f'<span class="pay" style="background:{PAY_COLORS.get(x.lower(),"#222")}"><img src="{u}" alt="{x}" class="payimg">{x}</span>'
        return f'<span class="pay" style="background:{PAY_COLORS.get(x.lower(),pal["accent"])}">{x}</span>'
    paybadges="".join(_pb(x) for x in pays)
    logo_html=(f'<img src="{logo_url}" alt="logo">' if logo_url else "")
    navhtml="".join(f'<a href="{l[1]}">{html.escape(l[0])}</a>' for l in (nav_links or []))
    return f"""<!doctype html><html lang="{p['geo']}"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{html.escape(p['brand'])} {p['geo'].upper()} — {html.escape(p['keyword'])} Review</title>
<meta name="description" content="{html.escape(content.get('meta_description','')[:155])}">
<link rel="canonical" href="https://{p['domain']}/">
<script type="application/ld+json">{schema}</script><style>{css}</style></head>
<body><div class="wrap">
<div class="nav">{logo_html}<b class="brandmark">{html.escape(p["brand"])}</b><span class="navlinks">{navhtml}</span></div>
{hero_block}
{''.join(blocks)}
<div class="pays-row">Payments: {paybadges}</div><footer class="muted">© {p['brand']} review · {p['geo'].upper()}</footer></div><a class="sticky-cta" href="/go/">{p["cta"]} →</a></body></html>"""
