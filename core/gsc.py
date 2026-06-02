"""Google Search Console — авто-верификация домена через Cloudflare DNS-TXT (наш CF-токен).

Привязка домена к Google-акку (вопрос Алекса): GSC верификация = DNS-TXT запись google-site-verification.
Делаем автоматом если домен в нашей CF-зоне. Сам GSC-API (сабмит/данные) требует OAuth Алекса — отдельно.
NB: токен verification Алекс берёт в GSC (Domain property → DNS TXT), мы лишь ставим запись в CF.
"""
def add_verification_txt(domain, token):
    """Ставит google-site-verification TXT в CF-зону домена (зона = последние 2 лейбла)."""
    import core.provision as p
    parts = domain.split("."); zone = ".".join(parts[-2:])
    r = p._cf_req("GET", f"/zones?name={zone}")
    res = (r or {}).get("result") if isinstance(r, dict) else None
    if not res:
        return {"ok": False, "err": f"zone {zone} not in Cloudflare"}
    zid = res[0]["id"]
    rec = p._cf_req("POST", f"/zones/{zid}/dns_records",
                    {"type": "TXT", "name": zone, "content": f"google-site-verification={token}", "ttl": 1})
    return {"ok": bool(rec.get("success")), "raw": rec if not rec.get("success") else "TXT set"}

# Заметка по индексации (вывод из ресёрча):
# - Google Indexing API НЕ использовать для гембла (деиндексит; только JobPosting/BroadcastEvent легально).
# - Индекс Google: GSC ручной сабмит + sitemap ping + пул аккаунтов (~300 стр/акк).
# - Bing: IndexNow (мгновенно, бесплатно — уже встроено в orchestrator) + Bing Webmaster.
