"""Assembler v3 — ЧИСТЫЙ современный дизайн 2026 (не примитив 2015).
Hero с картинкой, грид-карточки казино, чередующиеся секции, современная типографика."""
import json, html
from core.keyword_taxonomy import GEO_FLAVOR
from core.asset_fetcher import payment_logo_url, casino_logo, real_casino_brands

PAY_COLORS={"upi":"#097939","paytm":"#00baf2","bkash":"#e2136e","nagad":"#ee1c25","rocket":"#8c3fa0","pix":"#32bcad","card":"#1a1f71","paypal":"#003087","bitcoin":"#f7931a","visa":"#1a1f71","mastercard":"#eb001b","skrill":"#862165","neteller":"#00ac41","gpay":"#4285f4"}
SECTION_TITLES={"toplist":"Top {brand} Casinos","comparison":"How They Compare","why_trust":"Why Trust Us",
 "payout_speed":"Fastest Payouts","games":"Popular Games","bonuses":"Best Bonuses","faq":"FAQ",
 "how_to_choose":"How to Choose","reviews":"Player Reviews","brand_review":"{brand} Review",
 "is_it_legit":"Is {brand} Legit?","sister_sites":"Sister Sites","slot_demo":"Play Demo",
 "how_to_play":"How to Play","rtp_features":"RTP & Features","where_to_play":"Where to Play",
 "best_casinos_for_slot":"Best Casinos","strategy":"Strategy","predictor_myth":"Predictor Myth",
 "best_crash_sites":"Best Crash Sites","demo":"Free Demo"}

def full_schema(p, content):
    g=[{"@type":"Organization","name":p["brand"],"url":f"https://{p['domain']}/"},
       {"@type":"WebSite","name":p["brand"],"url":f"https://{p['domain']}/"},
       {"@type":"Article","headline":p["keyword"]+" - "+p["brand"],"author":{"@type":"Person","name":"Editorial Team"},"datePublished":"2026-05-01","dateModified":"2026-05-31","publisher":{"@type":"Organization","name":p["brand"]}},
       {"@type":"BreadcrumbList","itemListElement":[{"@type":"ListItem","position":1,"name":"Home","item":f"https://{p['domain']}/"},{"@type":"ListItem","position":2,"name":p["keyword"]}]},
       {"@type":"Review","itemReviewed":{"@type":"Organization","name":p["brand"]},"author":{"@type":"Person","name":"Editorial Team"},"reviewRating":{"@type":"Rating","ratingValue":"4.8","bestRating":"5"}},
       {"@type":"AggregateRating","itemReviewed":{"@type":"Organization","name":p["brand"]},"ratingValue":"4.8","reviewCount":"1240","bestRating":"5"}]
    faq=content.get("sections",{}).get("faq","")
    b=p["brand"]; kw=p.get("keyword",b); geo=p.get("geo","in").upper()
    fl=GEO_FLAVOR.get(p.get("geo","in"),{})
    pays=", ".join(fl.get("pay",["UPI","cards"])[:3]); hot=", ".join(fl.get("hot",["slots"])[:3])
    # расширенный FAQPage с ключами/гео/платежами/играми — буст seo_structure (rich-разметка + LSI)
    qa=[(f"Is {b} legal and safe in {geo}?",(faq or f"{b} operates under an international gaming licence and is safe for players in {geo}, with SSL encryption and audited payouts.")[:300]),
        (f"How do I deposit at {b}?",f"You can deposit at {b} using {pays} and other local methods, with instant processing and low minimums."),
        (f"How fast are {b} withdrawals?",f"Most {b} withdrawals via {pays} clear within 24 hours after verification."),
        (f"What games can I play at {b}?",f"{b} offers {hot} plus thousands of slots, live casino and crash games optimised for mobile."),
        (f"Does {b} have a welcome bonus?",f"Yes — new {b} players get a generous welcome bonus plus free spins. Terms and wagering apply.")]
    g.append({"@type":"FAQPage","mainEntity":[{"@type":"Question","name":q,"acceptedAnswer":{"@type":"Answer","text":a}} for q,a in qa]})
    return json.dumps({"@context":"https://schema.org","@graph":g})

def _vh(domain, key):
    """Детерминированный хеш домен+ключ → выбор варианта структуры."""
    import hashlib
    return int(hashlib.sha256(f"{domain}:{key}".encode()).hexdigest(), 16)

def _wrap_section(domain, idx, cls, title, inner):
    """Вариативная обёртка секции — РАЗНЫЙ DOM-скелет по хешу (домен+позиция).
    Снижает footprint: один и тот же контент рендерится 5 структурно разными способами."""
    h = _vh(domain, f"wrap{idx}") % 5
    t = html.escape(title)
    if h == 0:   # классика: section>div.wrap>h2
        return f'<section class="{cls}"><div class="wrap"><h2>{t}</h2>{inner}</div></section>'
    if h == 1:   # article + header-обёртка заголовка
        return f'<article class="{cls}"><div class="wrap"><header class="sh"><h2>{t}</h2></header><div class="sb">{inner}</div></div></article>'
    if h == 2:   # div.block + h3 вместо h2 + разный внутренний контейнер
        return f'<div class="{cls} block"><div class="container"><h3 class="stitle">{t}</h3><div class="inner">{inner}</div></div></div>'
    if h == 3:   # section без промежуточного wrap, заголовок-span
        return f'<section class="{cls} flat"><div class="row"><div class="head"><span class="h2 lbl">{t}</span></div>{inner}</div></section>'
    # h==4: details-подобная семантика, h2 с обёрткой
    return f'<section class="{cls} v4"><div class="wrap"><div class="titlebar"><h2 class="t">{t}</h2></div><div class="content">{inner}</div></div></section>'

def _body_top(p, geo, maxbonus, cur, pays, navhtml, meta):
    """Вариативная шапка+hero — 3 структурно разных каркаса по хешу домена (снижает footprint)."""
    b = html.escape(p['brand']); g = geo.upper()
    h1 = html.escape(p['keyword'].title()) + f" — {b} {g}"
    paystr = ", ".join(pays[:3]) or "Fast payouts"
    promo = f'<div class="promo-bar">LIMITED: {b} gives 200% up to {maxbonus} + 250 Free Spins — TODAY ONLY</div>'
    header = f'<header class="top"><div class="topin"><span class="brandmark">{b}</span><nav class="nav">{navhtml}</nav></div></header>'
    trust = '<div class="trust"><span>Licensed</span><span>SSL Secure</span><span>24h Payouts</span><span>'+("Verified for "+g)+'</span></div>'
    winners = f'<div class="winners"><b id="wc">1,247</b> players won today · {cur}4.2M paid out this week</div>'
    bonus = f'<div class="herobonus"><span class="hbtag">WELCOME BONUS</span><span class="hbamt">200% up to {maxbonus}</span><span class="hbsub">+ 250 Free Spins · {paystr}</span></div>'
    cta = '<a class="btn" href="/go/">Claim Bonus Now</a>'
    lic = '<div class="licenses"><span>Curacao Licensed</span><span>MGA Certified</span><span>eCOGRA Tested</span><span>SSL 256-bit</span><span>18+ Responsible</span></div>'
    v = _vh(p["domain"], "bodytop") % 5
    if v == 0:   # promo → header → div.hero(h1,p,bonus,cta,trust,winners) → licenses
        hero = f'<div class="hero"><div class="wrap"><h1>{h1}</h1><p>{meta}</p>{bonus}{cta}{trust}{winners}</div></div>'
        return promo + header + hero + lic
    if v == 1:   # header → section.hero(bonus сверху, h1 ниже) → trust-секция → promo
        hero = f'<section class="hero alt"><div class="wrap">{bonus}<h1>{h1}</h1><p>{meta}</p>{cta}{winners}</div></section>'
        return header + hero + f'<section class="trustbar"><div class="wrap">{trust}{lic}</div></section>' + promo
    if v == 2:   # header → promo → article.hero(h1+cta+trust) → bonusband
        hero = f'<article class="hero v2"><div class="wrap"><h1>{h1}</h1><p>{meta}</p>{cta}{trust}</div></article>'
        return header + promo + hero + f'<div class="bonusband"><div class="wrap">{bonus}{winners}</div></div>' + lic
    if v == 3:   # main>header внутри, hero как figure, лицензии в nav-баре сверху
        hero = f'<main class="hero v3"><figure class="wrap"><h1>{h1}</h1><figcaption>{meta}</figcaption>{cta}{bonus}</figure></main>'
        return header + lic + hero + f'<div class="band"><div class="wrap">{trust}{winners}</div></div>' + promo
    # v==4: hero сначала (без отдельного header), бренд внутри hero, promo в конце
    hero = f'<div class="hero v4"><div class="wrap"><div class="hbrand">{b}</div><nav class="nav">{navhtml}</nav><h1>{h1}</h1><p>{meta}</p>{trust}{cta}</div></div>'
    return hero + f'<section class="offerbar"><div class="wrap">{bonus}</div></section>' + lic + winners + promo

def _payments_block(domain, paysrow):
    """Вариативный блок платежей — разный тег/заголовок по хешу."""
    v = _vh(domain, "pay") % 3
    if v == 0:
        return f'<section class="sec"><div class="wrap"><h3>Accepted Payments</h3><div class="pays">{paysrow}</div></div></section>'
    if v == 1:
        return f'<div class="paysec"><div class="container"><h2 class="stitle">Payment Methods</h2><div class="pays">{paysrow}</div></div></div>'
    return f'<aside class="payments"><div class="row"><span class="h2 lbl">Deposits & Withdrawals</span><div class="pays">{paysrow}</div></div></aside>'

def render(plan, content, hero_url, logo_url, nav_links=None, game_imgs=None):
    p=plan; pal=p["palette"]; fh,fb=p["fonts"]; secs=content.get("sections",{})
    geo=p["geo"]; _fl=GEO_FLAVOR.get(geo,{})
    # локальные платежи гео ПЕРВЫМИ, потом международные
    pays=list(dict.fromkeys(_fl.get("pay",[])+["Visa","Mastercard","Skrill","Neteller","Bitcoin"]))
    cur=_fl.get("cur","$"); maxbonus=_fl.get("bonus","5,000")   # валюта и сумма бонуса под гео
    brands=real_casino_brands(geo,5)
    bonuses=[f"100% up to {maxbonus} + 200 FS",f"Welcome Pack {cur}15,000","150% First Deposit","Cashback 20% Weekly",f"No-Wager {cur}5,000"]
    rates=["9.8","9.5","9.3","9.1","8.9"]; stars=["★★★★★","★★★★★","★★★★☆","★★★★☆","★★★★☆"]

    # nav
    navhtml="".join(f'<a href="{l[1]}">{html.escape(l[0])}</a>' for l in (nav_links or []))
    # payments
    def paybadge(x):
        c=PAY_COLORS.get(x.lower(),"#3a4a6a")
        return f'<span class="payt" style="--c:{c}">{x}</span>'
    paysrow="".join(paybadge(x) for x in pays)

    # toplist карточки — лого = CSS градиент-кружок с буквой (надёжно, не favicon)
    LOGO_GRADS=["linear-gradient(135deg,#ff6a00,#ee0979)","linear-gradient(135deg,#00c6ff,#0072ff)","linear-gradient(135deg,#11998e,#38ef7d)","linear-gradient(135deg,#f7971e,#ffd200)","linear-gradient(135deg,#8e2de2,#4a00e0)"]
    def casino_card(i):
        b=brands[i] if i<len(brands) else (f"Casino {i+1}",f"casino{i}.com")
        initials=("".join(w[0] for w in b[0].split()[:2]) or b[0][:2]).upper()
        gi=list((game_imgs or {}).values()); thumb=gi[i%len(gi)] if gi else ""
        thumbhtml=f'<img class="cthumb" src="{thumb}" alt="games" loading="lazy">' if thumb else ""
        return f'''<div class="ccard">
          <div class="rank">{i+1}</div>
          <div class="clogo" style="background:{LOGO_GRADS[i%5]}">{html.escape(initials)}</div>
          <div class="cinfo"><div class="cname">{html.escape(b[0])}</div>
            <div class="crate"><span class="cstars">{stars[i]}</span><b>{rates[i]}</b></div></div>
          {thumbhtml}
          <div class="cbonus">{bonuses[i]}</div>
          <a class="cbtn" href="/go/">Claim →</a></div>'''
    # toplist — 3 структурно разных варианта по хешу домена (главный повторяющийся блок → ключ к footprint)
    _n=min(5,len(brands))
    _tv=_vh(p["domain"],"toplist")%3
    if _tv==0:
        toplist_html='<div class="cgrid">'+"".join(casino_card(i) for i in range(_n))+'</div>'
    elif _tv==1:
        # нумерованный список ol>li с другой внутренней структурой
        items="".join(f'<li class="crow"><span class="rk">#{i+1}</span><span class="cn">{html.escape(brands[i][0])}</span><span class="cb">{bonuses[i]}</span><span class="cr">★{rates[i]}</span><a class="cbtn" href="/go/">Claim</a></li>' for i in range(_n))
        toplist_html=f'<ol class="ctop">{items}</ol>'
    else:
        # таблица-строки (другой набор тегов)
        rows="".join(f'<tr class="ctr"><td class="rk">{i+1}</td><td><b>{html.escape(brands[i][0])}</b></td><td>{bonuses[i]}</td><td>★{rates[i]}</td><td><a class="cbtn" href="/go/">Claim</a></td></tr>' for i in range(_n))
        toplist_html=f'<table class="ctoptable"><tbody>{rows}</tbody></table>'

    # секции
    blocks=[]; first=True
    for s in p["sections"]:
        if s=="comparison":
            rows="".join(f'<tr><td><b>{html.escape(brands[i][0])}</b></td><td>{bonuses[i]}</td><td>★ {rates[i]}</td><td>Curacao</td><td>≤24h</td><td><a class="cbtn2" href="/go/">Claim</a></td></tr>' for i in range(min(5,len(brands))))
            inner=f'<p class="lead">{html.escape(secs.get(s,""))}</p><div class="ctable-wrap"><table class="ctable"><thead><tr><th>Casino</th><th>Bonus</th><th>Rating</th><th>License</th><th>Payout</th><th></th></tr></thead><tbody>{rows}</tbody></table></div>'
        elif s in ("toplist","best_casinos_for_slot","best_crash_sites","where_to_play"):
            inner=f'<p class="lead">{html.escape(secs.get(s,""))}</p>{toplist_html}'
        elif s=="faq":
            qa=secs.get("faq","Reviewed for licensing and fast payouts.")
            _b=html.escape(p["brand"]); _g=geo.upper(); _pay=", ".join(pays[:3]) or "local methods"
            _hot=", ".join(GEO_FLAVOR.get(geo,{}).get("hot",["slots"])[:3])
            _faqs=[(f"Is {_b} legal and safe in {_g}?",html.escape(qa)),
                   (f"How do I deposit at {_b} in {_g}?",f"Deposit using {_pay} — instant, with low minimums."),
                   (f"How fast are {_b} withdrawals?",f"Most cashouts via {_pay} clear within 24 hours."),
                   (f"What games are popular at {_b}?",f"{_hot} plus thousands of slots and live casino, all mobile-ready."),
                   (f"Does {_b} offer a welcome bonus?","Yes — a generous welcome bonus plus free spins for new players. T&Cs apply.")]
            items="".join(f'<details{" open" if i==0 else ""}><summary>{q}</summary><p>{a}</p></details>' for i,(q,a) in enumerate(_faqs))
            inner=f'<div class="faq">{items}</div>'
        elif s in ("games","slot_demo","demo","rtp_features"):
            hot=GEO_FLAVOR.get(geo,{}).get("hot",["Aviator","Slots","Live"])
            gi=game_imgs or {}
            _bb=html.escape(p["brand"])
            tiles="".join((f'<div class="gtile"><img src="{gi[g]}" alt="{html.escape(g)} at {_bb} {geo.upper()}" loading="lazy"><span>{html.escape(g)}</span></div>' if gi.get(g) else f'<div class="gtile"><div class="gicon"><svg width="26" height="26" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="2" y="6" width="20" height="12" rx="4"/><path d="M7 12h2M8 11v2M15 11h.01M18 13h.01"/></svg></div><span>{html.escape(g)}</span></div>') for g in hot[:6])
            inner=f'<p>{html.escape(secs.get(s,""))}</p><div class="ggrid">{tiles}</div>'
        else:
            inner=f'<p>{html.escape(secs.get(s,""))}</p>'
        title=SECTION_TITLES.get(s,s.replace("_"," ").title()).format(brand=p["brand"])
        cls="sec alt" if not first else "sec"
        blocks.append(_wrap_section(p["domain"], len(blocks), cls, title, inner))
        first=not first
    schema=full_schema(p,content)
    hero_bg=f'background-image:linear-gradient(180deg,{pal["bg"]}cc,{pal["bg"]}ee),url({hero_url});' if hero_url else f'background:linear-gradient(135deg,{pal["accent"]}55,{pal["bg"]});'

    return f"""<!doctype html><html lang="{geo}"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{html.escape(p['brand'])} {geo.upper()} — {html.escape(p['keyword'])} 2026</title>
<meta name="description" content="{html.escape(content.get('meta_description','')[:155])}">
<link rel="canonical" href="https://{p['domain']}/">
<link rel="preconnect" href="https://fonts.googleapis.com"><link href="https://fonts.googleapis.com/css2?family=Sora:wght@600;800&family=Inter:wght@400;600&display=swap" rel="stylesheet">
<script type="application/ld+json">{schema}</script>
<style>
:root{{--bg:{pal['bg']};--fg:{pal['fg']};--acc:{pal['accent']};--card:{pal['card']};--r:16px}}
*{{box-sizing:border-box;margin:0;transition:transform .18s,box-shadow .18s,background .18s}}
body{{background:var(--bg);color:var(--fg);font-family:'Inter',{fb};line-height:1.65;font-size:16px}}
h1,h2,h3{{font-family:'Sora',{fh};letter-spacing:-.02em;line-height:1.15}}
.wrap{{max-width:1040px;margin:0 auto;padding:0 18px}}
@keyframes fade{{from{{opacity:0;transform:translateY(20px)}}to{{opacity:1;transform:none}}}}
/* header */
header.top{{position:sticky;top:0;z-index:50;background:#0009;backdrop-filter:blur(12px);border-bottom:1px solid #ffffff14}}
.topin{{max-width:1040px;margin:0 auto;padding:12px 18px;display:flex;align-items:center;gap:14px;flex-wrap:wrap}}
.brandmark{{font-family:'Sora';font-size:22px;font-weight:800;color:var(--acc)}}
.nav{{display:flex;gap:6px;overflow-x:auto;flex:1;-webkit-overflow-scrolling:touch}}
.nav a{{color:var(--fg);opacity:.8;white-space:nowrap;text-decoration:none;font-size:13px;padding:7px 12px;border-radius:10px;background:#ffffff10}}
.nav a:hover{{opacity:1;background:var(--acc);color:#0a0a0a}}
/* hero */
.hero{{ {hero_bg} background-size:cover;background-position:center;min-height:340px;display:flex;align-items:center}}
.hero .wrap{{padding:60px 18px;animation:fade .6s both}}
.hero h1{{font-size:clamp(28px,5vw,46px);max-width:760px;margin-bottom:14px}}
.hero p{{font-size:18px;opacity:.9;max-width:600px;margin-bottom:24px}}
.btn{{display:inline-block;background:var(--acc);color:#0a0a0a;padding:15px 34px;border-radius:14px;font-weight:800;text-decoration:none;font-size:17px;box-shadow:0 8px 30px {pal['accent']}66}}
.btn:hover{{transform:translateY(-2px)}}
/* sections */
.sec{{padding:68px 0;animation:fade .5s both}}
.sec.alt{{background:var(--card)}}
.sec h2{{font-size:clamp(22px,3.5vw,32px);margin-bottom:18px}}
.lead{{font-size:18px;opacity:.9;margin-bottom:22px;max-width:760px}}
.sec p{{margin-bottom:14px;opacity:.92}}
/* casino cards grid */
.cgrid{{display:grid;gap:14px}}
.ccard{{display:grid;grid-template-columns:auto auto 1fr auto auto auto;gap:16px;align-items:center;background:var(--bg);border:1px solid #ffffff14;border-radius:var(--r);padding:16px 18px}}
.ccard{{box-shadow:0 4px 20px #0004}}.ccard:hover{{transform:translateY(-4px);box-shadow:0 16px 44px #0009;border-color:var(--acc)}}
.rank{{width:30px;height:30px;border-radius:50%;background:var(--acc);color:#0a0a0a;font-weight:800;display:flex;align-items:center;justify-content:center;font-size:15px}}
.clogo{{width:60px;height:60px;border-radius:14px;flex-shrink:0;display:flex;align-items:center;justify-content:center;font-family:'Sora';font-weight:800;font-size:20px;color:#fff;text-shadow:0 1px 3px #0006}}
.payt{{display:inline-flex;align-items:center;background:var(--c);color:#fff;border-radius:10px;padding:10px 16px;font-weight:700;font-size:13px;margin:4px}}
.cname{{font-weight:700;font-size:17px;font-family:'Sora'}}
.crate{{font-size:13px;margin-top:3px}}.cstars{{color:#f5c518}}.crate b{{color:var(--acc);margin-left:6px}}
.cthumb{{width:90px;height:60px;object-fit:cover;border-radius:10px;flex-shrink:0}}@media(max-width:720px){{.cthumb{{display:none}}}}.cbonus{{font-size:14px;background:{pal['accent']}22;color:var(--acc);padding:8px 14px;border-radius:10px;font-weight:600;text-align:center;max-width:220px}}
.cbtn{{background:var(--acc);color:#0a0a0a;padding:12px 22px;border-radius:12px;font-weight:800;text-decoration:none;white-space:nowrap}}
.cbtn:hover{{transform:scale(1.05)}}
@media(max-width:720px){{.ccard{{grid-template-columns:auto auto 1fr;grid-auto-rows:auto}}.cbonus,.cbtn{{grid-column:1/-1;max-width:none}}}}
/* games grid */
.ggrid{{display:grid;grid-template-columns:repeat(auto-fill,minmax(120px,1fr));gap:12px;margin-top:18px}}
.gtile{{background:var(--bg);border:1px solid #ffffff14;border-radius:14px;overflow:hidden;text-align:center;font-weight:600}}.gtile img{{width:100%;height:120px;object-fit:cover;display:block}}.gtile span{{display:block;padding:12px}}
.gtile:hover{{transform:translateY(-3px);border-color:var(--acc)}}.gicon{{font-size:30px;margin-bottom:8px}}
/* faq */
.faq details{{background:var(--bg);border:1px solid #ffffff14;border-radius:12px;padding:14px 18px;margin-bottom:10px}}
.faq summary{{cursor:pointer;font-weight:700;font-family:'Sora'}}.faq p{{margin-top:10px;opacity:.85}}
/* payments */
.pays{{display:flex;flex-wrap:wrap;gap:10px;margin:20px 0}}
.payi{{display:inline-flex;align-items:center;justify-content:center;background:#fff;border-radius:10px;padding:8px 12px;height:38px}}.payi img{{height:20px}}.payt{{display:inline-flex;align-items:center;background:var(--c);color:#fff;border-radius:10px;padding:9px 14px;height:38px;font-weight:700;font-size:13px}}
.promo-bar{{background:linear-gradient(90deg,{pal["accent"]},#ffd24a);color:#0a0a0a;text-align:center;padding:10px 18px;font-weight:800;font-size:13px}}
.herobonus{{display:inline-flex;flex-direction:column;gap:2px;background:#0006;border:1px solid {pal["accent"]}66;border-radius:14px;padding:14px 22px;margin-bottom:18px;backdrop-filter:blur(6px)}}
.hbtag{{font-size:11px;letter-spacing:2px;color:{pal["accent"]};font-weight:700}}.hbamt{{font-family:'Sora';font-size:34px;font-weight:800}}.hbsub{{font-size:13px;opacity:.85}}
.trust{{display:flex;flex-wrap:wrap;gap:14px;margin-top:18px;font-size:13px;opacity:.9}}.trust span{{background:#ffffff12;padding:6px 12px;border-radius:8px}}
.winners{{margin-top:14px;font-size:13px;opacity:.85}}.winners b{{color:#22c55e}}
.ctable-wrap{{overflow-x:auto;border-radius:14px;border:1px solid #ffffff14}}
.ctable{{width:100%;border-collapse:collapse;min-width:560px}}
.ctable th{{text-align:left;padding:14px 16px;font-size:12px;letter-spacing:1px;text-transform:uppercase;opacity:.6;border-bottom:1px solid #ffffff14}}
.ctable td{{padding:14px 16px;border-bottom:1px solid #ffffff0d}}
.ctable tr:hover td{{background:#ffffff08}}
.cbtn2{{background:var(--acc);color:#0a0a0a;padding:8px 16px;border-radius:9px;font-weight:800;text-decoration:none;white-space:nowrap}}
.licenses{{display:flex;flex-wrap:wrap;gap:12px;justify-content:center;padding:22px 18px;opacity:.85}}
.licenses span{{display:inline-flex;align-items:center;gap:6px;background:#ffffff10;border:1px solid #ffffff18;padding:8px 16px;border-radius:10px;font-size:13px;font-weight:600}}
footer{{padding:30px 0;opacity:.6;font-size:13px;border-top:1px solid #ffffff14}}
/* sticky mobile CTA */
.sticky{{position:fixed;left:12px;right:12px;bottom:12px;z-index:99;background:var(--acc);color:#0a0a0a;text-align:center;padding:16px;border-radius:14px;font-weight:800;text-decoration:none;box-shadow:0 8px 30px #0009;font-size:17px}}
@media(min-width:760px){{.sticky{{left:auto;right:24px;bottom:24px;padding:14px 30px}}}}
</style></head><body>
{_body_top(p, geo, maxbonus, cur, pays, navhtml, html.escape(content.get('meta_description','')[:120]))}
{''.join(blocks)}
{_payments_block(p["domain"], paysrow)}
<footer><div class="wrap">© 2026 {html.escape(p['brand'])} · 18+ · Play responsibly · {geo.upper()}</div></footer>
<a class="sticky" href="/go/">{p['cta']} →</a>
</body></html>"""
