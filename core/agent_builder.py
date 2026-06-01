"""АГЕНТ-ВЕРСТАЛЬЩИК (генератор v2). Собирает УНИКАЛЬНЫЙ сайт из плана+контента.

НЕ один шаблон: рендер зависит от layout-архетипа (6 разных каркасов) + блоки рендерятся
вариативно + мутатор. Каждый блок несёт lead+body (под AI-выдачу) + FAQPage/Article schema.
Контракт: build(brand,keyword,geo,domain,plan,content,assets) -> html.
"""
import json, hashlib, html as _html
from core.keyword_taxonomy import GEO_FLAVOR
from core.footprint import mutate

def _h(seed, k): return int(hashlib.sha256(f"{seed}:{k}".encode()).hexdigest(), 16)

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

def _block_html(domain, idx, block_id, c):
    """Рендер блока: H2 + вариативный внутренний рендер + вариативная обёртка."""
    h2 = _html.escape(c.get("h2", block_id.replace("_", " ").title()))
    lead = _html.escape(c.get("lead", ""))
    body = _html.escape(c.get("body", ""))
    inner = _inner_render(domain, idx, block_id, lead, body)
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
    blocks_html = "".join(_block_html(domain, i, b, content.get(b, {})) for i, b in enumerate(blocks))
    schema = _schema(brand, keyword, domain, geo, content)
    # hero зависит от layout — разный первый экран
    hero = _hero(layout, brand, h1, maxbonus, cur, pays, g, _html.escape(first.get("lead", "")))
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
.cta{{display:inline-block;background:var(--accent);color:#04140d;padding:13px 26px;border-radius:10px;font-weight:700;text-decoration:none;margin-top:14px}}
.sticky{{position:fixed;left:12px;right:12px;bottom:12px;background:var(--accent);color:#04140d;text-align:center;padding:15px;border-radius:12px;font-weight:800;text-decoration:none}}
@media(min-width:760px){{.sticky{{left:auto;right:24px}}}}</style>
<script type="application/ld+json">{schema}</script></head><body>
{hero}
{blocks_html}
<footer><div class="wrap">© 2026 {_html.escape(brand)} · 18+ · Play responsibly · {g}</div></footer>
<a class="sticky" href="/go/">Claim Bonus — {brand}</a>
</body></html>"""
    return mutate(html, domain)   # анти-footprint пост-процессор

def _hero(layout, brand, h1, maxbonus, cur, pays, g, lead):
    b = _html.escape(brand)
    bonus = f'<div class="hb">200% up to {maxbonus} + 250 Free Spins · {pays}</div>'
    cta = '<a class="cta" href="/go/">Claim Bonus Now</a>'
    if layout == "review-first":
        return f'<header class="hero"><div class="wrap"><span>Expert Review</span><h1>{h1}</h1><p class="lead">{lead}</p>{cta}{bonus}</div></header>'
    if layout == "guide-first":
        return f'<main class="hero"><div class="wrap"><h1>{h1}</h1><p class="lead">{lead}</p>{cta}</div></main>'
    if layout == "comparison-first":
        return f'<section class="hero"><div class="wrap"><h1>{h1}</h1>{bonus}<p class="lead">{lead}</p>{cta}</div></section>'
    if layout == "qa-first":
        return f'<div class="hero"><div class="wrap"><h1>{h1}</h1><details open><summary>{lead}</summary></details>{cta}</div></div>'
    # toplist-first / magazine
    return f'<div class="hero"><div class="wrap"><h1>{h1}</h1>{bonus}{cta}<p class="lead">{lead}</p></div></div>'
