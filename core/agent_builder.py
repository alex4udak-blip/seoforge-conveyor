"""АГЕНТ-ВЕРСТАЛЬЩИК (генератор v2). Собирает УНИКАЛЬНЫЙ сайт из плана+контента.

НЕ один шаблон: рендер зависит от layout-архетипа (6 разных каркасов) + блоки рендерятся
вариативно + мутатор. Каждый блок несёт lead+body (под AI-выдачу) + FAQPage/Article schema.
Контракт: build(brand,keyword,geo,domain,plan,content,assets) -> html.
"""
import json, hashlib, os, html as _html
from core.keyword_taxonomy import GEO_FLAVOR
from core.footprint import mutate
from core.asset_fetcher import payment_logo_url, casino_logo, real_casino_brands

def _payments_html(geo):
    """Реальные лого платёжек (simpleicons CDN) + цветной бейдж если лого нет."""
    pays = GEO_FLAVOR.get(geo, {}).get("pay", []) + ["Visa", "Mastercard", "Skrill", "Bitcoin"]
    out = []
    for p in list(dict.fromkeys(pays))[:8]:
        url = payment_logo_url(p)
        if url:
            out.append(f'<span class="pay"><img src="{url}" alt="{_html.escape(p)}" loading="lazy" height="22">{_html.escape(p)}</span>')
        else:
            out.append(f'<span class="pay badge">{_html.escape(p)}</span>')
    return '<div class="pays">' + "".join(out) + '</div>'

# маппинг игр на фото-теги для реальных фото (LoremFlickr — настоящие фотографии Flickr)
GAME_PHOTO_TAG = {
    "aviator": "airplane,sky", "jetx": "airplane", "spaceman": "astronaut",
    "teen patti": "playing-cards", "andar bahar": "playing-cards", "crazy time": "casino-wheel",
    "fortune tiger": "tiger", "slots": "slot-machine", "live": "casino-dealer",
    "book of dead": "egypt,pyramid", "starburst": "neon", "color game": "colorful",
}
def _photo(tags, domain, key, w=600, h=400):
    """Реальное фото по теме (LoremFlickr Flickr). seed по домену+ключу — стабильно, но у каждого своё."""
    seed = _h(domain, key) % 100000
    return f"https://loremflickr.com/{w}/{h}/{tags}?lock={seed}"

def _games_html(geo, domain):
    """РЕАЛЬНЫЕ фото игр (LoremFlickr по теме игры) — настоящие фотографии, не ИИ/заглушки."""
    hot = GEO_FLAVOR.get(geo, {}).get("hot", ["Aviator", "Slots", "Live"])[:6]
    out = []
    for g in hot:
        tag = GAME_PHOTO_TAG.get(g.lower(), "casino,gambling")
        url = _photo(tag, domain, f"game_{g}", 400, 260)
        out.append(f'<figure class="gt"><img src="{url}" alt="{_html.escape(g)}" loading="lazy"><figcaption>{_html.escape(g)}</figcaption></figure>')
    return '<div class="games">' + "".join(out) + '</div>'

def _toplist_html(geo, cur, maxbonus):
    """Toplist реальных казино-брендов с favicon-лого."""
    brands = real_casino_brands(geo, 5)
    bonuses = [maxbonus, f"{cur}15,000", "150% Match", "20% Cashback", f"{cur}5,000 Free"]
    rates = ["9.8", "9.5", "9.3", "9.1", "8.9"]
    rows = []
    for i, b in enumerate(brands[:5]):
        name, dom = b if isinstance(b, (list, tuple)) else (b, f"casino{i}.com")
        logo = casino_logo(dom)
        rows.append(f'<div class="cc"><span class="rk">{i+1}</span>'
                    f'<img class="clogo" src="{logo}" alt="{_html.escape(name)}" loading="lazy" width="32" height="32">'
                    f'<span class="cn">{_html.escape(name)}</span><span class="cb">{bonuses[i]}</span>'
                    f'<span class="cr">★{rates[i]}</span><a class="cta sm" href="/go/">Claim</a></div>')
    return '<div class="toplist">' + "".join(rows) + '</div>'

def _h(seed, k): return int(hashlib.sha256(f"{seed}:{k}".encode()).hexdigest(), 16)

# вариативные фирменные фразы — у каждого домена свои (анти текст-футпринт)
def phrase(domain, kind, **kw):
    i = _h(domain, kind)
    if kind == "bonus":
        forms = [
            "200% up to {bonus} + 250 Free Spins",
            "Welcome package: {bonus} across first 3 deposits",
            "Get {bonus} bonus plus 200 spins on signup",
            "Double your first deposit up to {bonus}",
            "{bonus} welcome offer + free spins bundle",
            "New players: claim {bonus} + spin rewards",
        ]
        return forms[i % len(forms)].format(**kw)
    if kind == "winners":
        forms = [
            "{wc} players won today · {cur}{amt} paid this week",
            "{cur}{amt} in winnings paid out · {wc} winners this week",
            "Join {wc}+ winners — {cur}{amt} cashed out recently",
            "This week: {cur}{amt} paid to {wc} lucky players",
            "{wc} recent wins · fast {cur} payouts every day",
        ]
        wc = 1000 + (i % 900); amt = f"{1 + i % 9}.{i % 9}M"
        return forms[i % len(forms)].format(wc=wc, cur=kw.get("cur", "$"), amt=amt)
    return ""

def _schema(brand, keyword, domain, geo, content):
    g = [
        {"@type": "Organization", "name": brand, "url": f"https://{domain}/"},
        {"@type": "WebSite", "name": brand, "url": f"https://{domain}/"},
        {"@type": "Article", "headline": f"{keyword} - {brand}",
         "author": {"@type": "Person", "name": "Editorial Team"},
         "datePublished": "2026-05-01", "dateModified": "2026-06-01",
         "publisher": {"@type": "Organization", "name": brand}},
    ]
    # FAQPage из блоков-вопросов (lead = ответ — это под цитирование)
    faqs = [{"@type": "Question", "name": c.get("h2", ""),
             "acceptedAnswer": {"@type": "Answer", "text": c.get("lead", "")[:300]}}
            for c in list(content.values())[:6] if c.get("lead")]
    if faqs:
        g.append({"@type": "FAQPage", "mainEntity": faqs})
    g.append({"@type": "AggregateRating", "itemReviewed": {"@type": "Organization", "name": brand},
              "ratingValue": "4.7", "reviewCount": "1180", "bestRating": "5"})
    return json.dumps({"@context": "https://schema.org", "@graph": g})

def _inner_render(domain, idx, block_id, lead, body):
    """Внутренний рендер пассажа — 6 структурно разных форм (бьёт footprint глубже обёрток)."""
    v = _h(domain, f"inner{idx}") % 6
    # разбиваем body на предложения для вариантов-списков
    sents = [s.strip() for s in body.replace("!", ".").split(".") if len(s.strip()) > 15]
    if v == 0:   # классика: lead + абзац
        return f'<p class="lead">{lead}</p><p>{body}</p>'
    if v == 1 and len(sents) >= 3:   # lead + маркированный список фактов
        li = "".join(f"<li>{s}.</li>" for s in sents[:4])
        return f'<p class="lead">{lead}</p><ul>{li}</ul>'
    if v == 2 and len(sents) >= 3:   # blockquote-lead + нумерованный
        li = "".join(f"<li>{s}.</li>" for s in sents[:4])
        return f'<blockquote class="lead">{lead}</blockquote><ol>{li}</ol>'
    if v == 3:   # таблица «вопрос-факт» (под AI-цитирование Q&A)
        rows = "".join(f"<tr><td>{s.split(' ')[0:3] and ' '.join(s.split(' ')[:3])}</td><td>{s}.</td></tr>" for s in sents[:3])
        return f'<p class="lead">{lead}</p><table class="facts"><tbody>{rows}</tbody></table>'
    if v == 4:   # details/summary (Perplexity Q&A любит)
        return f'<details open><summary class="lead">{lead}</summary><p>{body}</p></details>'
    # v5: dl-список (definition)
    return f'<p class="lead">{lead}</p><dl><dt>Key facts</dt><dd>{body}</dd></dl>'

def _block_html(domain, idx, block_id, c, geo="in", cur="$", maxbonus="5,000"):
    """Рендер блока: H2 + текст-пассаж + ВИЗУАЛ по типу блока (картинки/лого) + вариативная обёртка."""
    h2 = _html.escape(c.get("h2", block_id.replace("_", " ").title()))
    lead = _html.escape(c.get("lead", ""))
    body = _html.escape(c.get("body", ""))
    inner = _inner_render(domain, idx, block_id, lead, body)
    # ВИЗУАЛ: по ключевым словам в имени блока (надёжнее — Claude может назвать блок не из пула)
    bl = block_id.lower()
    if any(w in bl for w in ("toplist", "comparison", "review", "rating", "best", "top", "rank", "vs")):
        inner += _toplist_html(geo, cur, maxbonus)
    elif any(w in bl for w in ("game", "slot", "live", "crash", "showcase")):
        inner += _games_html(geo, domain)
    elif any(w in bl for w in ("payment", "deposit", "withdraw", "banking")):
        inner += _payments_html(geo)
    v = _h(domain, f"blk{idx}") % 4
    if v == 0:
        return f'<section class="b"><div class="wrap"><h2>{h2}</h2>{inner}</div></section>'
    if v == 1:
        return f'<article class="b"><div class="wrap"><header><h2>{h2}</h2></header><div class="bd">{inner}</div></div></article>'
    if v == 2:
        return f'<div class="b block"><div class="container"><h3 class="t">{h2}</h3>{inner}</div></div>'
    return f'<section class="b flat"><div class="row"><div class="head"><span class="h2 lbl">{h2}</span></div>{inner}</div></section>'

LAYOUT_CSS = {
    "review-first": "--accent:#3ddc97", "toplist-first": "--accent:#22d3ee",
    "guide-first": "--accent:#a78bfa", "comparison-first": "--accent:#f5b73d",
    "qa-first": "--accent:#ff8fab", "magazine": "--accent:#5eead4",
}

def build(brand, keyword, geo, domain, plan, content, assets=None):
    fl = GEO_FLAVOR.get(geo, {})
    cur = fl.get("cur", "$"); maxbonus = fl.get("bonus", "5,000")
    pays = ", ".join(fl.get("pay", ["UPI"])[:3])
    layout = plan.get("layout", "toplist-first")
    accent = LAYOUT_CSS.get(layout, "--accent:#3ddc97")
    blocks = plan.get("blocks", [])
    g = geo.upper()
    # H1 из первого блока или ключа
    first = list(content.values())[0] if content else {}
    h1 = _html.escape(first.get("h2", f"{keyword.title()} — {brand} {g}"))
    blocks_html = "".join(_block_html(domain, i, b, content.get(b, {}), geo, cur, maxbonus) for i, b in enumerate(blocks))
    schema = _schema(brand, keyword, domain, geo, content)
    # hero зависит от layout — разный первый экран
    # hero — РЕАЛЬНОЕ фото казино (LoremFlickr), тема варьируется по домену
    _hero_tags = ["casino,luxury", "casino,neon", "las-vegas,casino", "poker,casino", "slot-machine,casino"]
    _ht = _hero_tags[_h(domain, "herophoto") % len(_hero_tags)]
    hero_img = f'<img class="hbg" src="{_photo(_ht, domain, "hero", 1000, 360)}" alt="{_html.escape(brand)}" loading="eager">'
    hero = _hero(layout, brand, h1, maxbonus, cur, pays, g, _html.escape(first.get("lead", "")), domain, hero_img)
    html = f"""<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{_html.escape(brand)} — {_html.escape(keyword.title())} {g}</title>
<meta name="description" content="{_html.escape(first.get('lead','')[:155])}">
<style>:root{{{accent};--bg:#0b1018;--tx:#eaf0ff}}
body{{margin:0;font-family:system-ui,Segoe UI,Roboto;background:var(--bg);color:var(--tx);line-height:1.6}}
.wrap,.container,.row{{max-width:920px;margin:0 auto;padding:22px}}
h1{{font-size:30px}}h2,.h2{{color:var(--accent);font-size:21px;margin-top:8px}}h3{{color:var(--accent)}}
.lead{{font-size:17px;font-weight:600}}.b{{border-bottom:1px solid #ffffff10}}
.hero{{background:linear-gradient(135deg,var(--accent)33,var(--bg));padding:40px 0}}
.cta{{display:inline-block;background:var(--accent);color:#04140d;padding:13px 26px;border-radius:10px;font-weight:700;text-decoration:none;margin-top:14px}}.cta.sm{{padding:7px 14px;font-size:13px;margin:0}}
.sticky{{position:fixed;left:12px;right:12px;bottom:12px;background:var(--accent);color:#04140d;text-align:center;padding:15px;border-radius:12px;font-weight:800;text-decoration:none;z-index:50}}
@media(min-width:760px){{.sticky{{left:auto;right:24px}}}}
.hero img.hbg{{width:100%;max-height:280px;object-fit:cover;border-radius:14px;margin-top:14px}}
.pays{{display:flex;flex-wrap:wrap;gap:10px;margin-top:14px}}
.pay{{display:inline-flex;align-items:center;gap:7px;background:#ffffff10;border:1px solid #ffffff18;border-radius:9px;padding:8px 13px;font-size:13px;font-weight:600}}
.pay img{{display:block}}.pay.badge{{background:var(--accent)22;color:var(--accent)}}
.games{{display:grid;grid-template-columns:repeat(auto-fill,minmax(140px,1fr));gap:12px;margin-top:14px}}
.gt{{margin:0;border-radius:12px;overflow:hidden;background:#ffffff08}}.gt img{{width:100%;height:100px;object-fit:cover;display:block}}
.gt figcaption{{padding:8px;font-size:13px;font-weight:600}}.gt.no{{display:grid;place-items:center;min-height:120px;border:1px dashed #ffffff22}}
.toplist{{margin-top:14px;display:flex;flex-direction:column;gap:8px}}
.cc{{display:flex;align-items:center;gap:12px;background:#ffffff08;border:1px solid #ffffff14;border-radius:12px;padding:12px 14px}}
.cc .rk{{font-weight:800;color:var(--accent);font-size:18px;width:22px}}.cc .clogo{{border-radius:7px;background:#fff}}
.cc .cn{{font-weight:700;flex:1}}.cc .cb{{font-size:13px;opacity:.85}}.cc .cr{{color:var(--accent);font-weight:700}}
@media(max-width:600px){{.cc .cb{{display:none}}}}</style>
<script type="application/ld+json">{schema}</script></head><body>
{hero}
{blocks_html}
<footer><div class="wrap">© 2026 {_html.escape(brand)} · 18+ · Play responsibly · {g}</div></footer>
<a class="sticky" href="/go/">Claim Bonus — {brand}</a>
</body></html>"""
    return mutate(html, domain)   # анти-footprint пост-процессор

def _hero(layout, brand, h1, maxbonus, cur, pays, g, lead, domain="", hero_img=""):
    b = _html.escape(brand)
    bonus = f'<div class="hb">{phrase(domain or brand, "bonus", bonus=maxbonus)} · {pays}</div>'
    cta = '<a class="cta" href="/go/">Claim Bonus Now</a>'
    if layout == "review-first":
        return f'<header class="hero"><div class="wrap"><span>Expert Review</span><h1>{h1}</h1><p class="lead">{lead}</p>{cta}{bonus}{hero_img}</div></header>'
    if layout == "guide-first":
        return f'<main class="hero"><div class="wrap"><h1>{h1}</h1>{hero_img}<p class="lead">{lead}</p>{cta}</div></main>'
    if layout == "comparison-first":
        return f'<section class="hero"><div class="wrap"><h1>{h1}</h1>{bonus}<p class="lead">{lead}</p>{cta}{hero_img}</div></section>'
    if layout == "qa-first":
        return f'<div class="hero"><div class="wrap"><h1>{h1}</h1><details open><summary>{lead}</summary></details>{cta}{hero_img}</div></div>'
    # toplist-first / magazine
    return f'<div class="hero"><div class="wrap"><h1>{h1}</h1>{hero_img}{bonus}{cta}<p class="lead">{lead}</p></div></div>'
