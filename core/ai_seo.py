"""AI-выдача (GEO) гарант-слой: если Sonnet не вставил JSON-LD — инжектим базовый @graph.

Наш козырь: LLM (ChatGPT/Perplexity/Google AI) цитируют 2-7 доменов/запрос, трафик конвертит ×4.4.
Schema = сущность для AI. (March-апдейт убил rich-snippet Google, но AI-движки schema читают.)
"""
import json, re

def ensure_schema(html, brand, host, geo, slug="index"):
    """Если в html нет ld+json — вставляет базовый @graph в <head>."""
    if "application/ld+json" in html:
        return html  # Sonnet уже сделал
    url = f"https://{host}/" if slug == "index" else f"https://{host}/{slug}.html"
    graph = [
        {"@type": "Organization", "name": brand, "url": f"https://{host}/",
         "areaServed": geo.upper()},
        {"@type": "WebSite", "name": brand, "url": f"https://{host}/"},
        {"@type": "WebPage", "url": url, "name": brand,
         "datePublished": "2026-05-01", "dateModified": "2026-06-01",
         "author": {"@type": "Person", "name": "Editorial Team"},
         "publisher": {"@type": "Organization", "name": brand}},
        {"@type": "BreadcrumbList", "itemListElement": [
            {"@type": "ListItem", "position": 1, "name": "Home", "item": f"https://{host}/"}]},
    ]
    tag = f'<script type="application/ld+json">{json.dumps({"@context":"https://schema.org","@graph":graph})}</script>'
    i = html.lower().find("</head>")
    if i == -1:
        return tag + html
    return html[:i] + tag + html[i:]
