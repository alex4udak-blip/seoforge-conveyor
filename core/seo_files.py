"""SEO-файлы сайта: robots.txt (allow AI-боты!), sitemap.xml, llms.txt.

Без robots/sitemap Google/AI-боты не понимают сайт. AI-боты (GPTBot/PerplexityBot/OAI-SearchBot/
ClaudeBot) НЕ рендерят JS и смотрят robots — обязательно allow. llms.txt краулит OpenAI (стоимость 0).
"""
AI_BOTS = ["GPTBot", "OAI-SearchBot", "ChatGPT-User", "PerplexityBot", "Perplexity-User",
           "Google-Extended", "ClaudeBot", "anthropic-ai", "Applebot-Extended", "Bingbot", "Googlebot"]

def robots_txt(domain):
    lines = ["User-agent: *", "Allow: /", ""]
    for b in AI_BOTS:
        lines += [f"User-agent: {b}", "Allow: /", ""]
    lines += [f"Sitemap: https://{domain}/sitemap.xml", ""]
    return "\n".join(lines)

def sitemap_xml(domain, slugs, lastmod="2026-06-01"):
    urls = []
    for s in slugs:
        loc = f"https://{domain}/" if s == "index" else f"https://{domain}/{s}.html"
        pr = "1.0" if s == "index" else "0.8"
        urls.append(f"  <url><loc>{loc}</loc><lastmod>{lastmod}</lastmod>"
                    f"<changefreq>weekly</changefreq><priority>{pr}</priority></url>")
    return ('<?xml version="1.0" encoding="UTF-8"?>\n'
            '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
            + "\n".join(urls) + "\n</urlset>\n")

def llms_txt(brand, domain, geo, summary="", pages=None):
    """llms.txt под РЕАЛЬНЫЕ страницы сайта (pages={slug:title} или список slug)."""
    head = (f"# {brand}\n\n"
            f"> {brand} — online casino guide for {geo.upper()} players in 2026. {summary}\n\n## Pages\n")
    lines = []
    items = pages.items() if isinstance(pages, dict) else [(s, s.replace("-", " ").title()) for s in (pages or ["index"])]
    for slug, title in items:
        loc = f"https://{domain}/" if slug == "index" else f"https://{domain}/{slug}.html"
        lines.append(f"- [{title}]({loc})")
    return head + "\n".join(lines) + "\n"
