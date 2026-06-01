"""BRAND-RADAR — ловит СВЕЖИЕ гембл-бренды раньше конкурентов (вход брендоджека).

Источник: Certificate Transparency (crt.sh) — все новые TLS-сертификаты. Новый бренд = новый
сертификат на brand-casino.com и т.п. Кто первый засёк→купил домен→сделал сайт→проиндексил —
перехватывает брендовую выдачу. Это машина денег (модель Димы: гонка времени на новых брендах).
"""
import json, urllib.request, re, time

PATTERNS = ["casino", "bet", "win", "spin", "slots", "aviator", "jackpot", "gaming", "play"]
_GENERIC = {"casino", "bet", "win", "spins", "spin", "slots", "online", "best", "top", "the",
            "game", "games", "gaming", "play", "app", "live", "club", "vip", "bonus", "free",
            "real", "money", "new", "site", "review", "official", "www"}

def _crt(pattern, timeout=25):
    url = f"https://crt.sh/?q=%25{pattern}%25&output=json"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        return json.loads(urllib.request.urlopen(req, timeout=timeout).read())
    except Exception:
        return []

def fresh_brands(patterns=None, limit=20, since_days=14):
    """Свежие бренд-кандидаты: {brand, domain, first_seen}. Дедуп, без generic-мусора."""
    patterns = patterns or PATTERNS[:4]
    seen, out = set(), []
    for p in patterns:
        for row in _crt(p):
            name = (row.get("name_value") or "").lower()
            for dom in name.split("\n"):
                dom = dom.strip().lstrip("*.")
                if not dom or dom.count(".") < 1 or " " in dom:
                    continue
                # отсев мусора: хостинг-платформы, парковки, не-гембл
                if any(h in dom for h in ("hosted.app", "web.app", "pages.dev", "vercel.app",
                        "netlify", "github", "wingforum", "kosmetik", "sunglasses", "ray-ban", "amazonaws")):
                    continue
                sld = dom.split(".")[0]
                if sld in seen or len(sld) < 4 or sld in _GENERIC:
                    continue
                if sld.count("-") > 1 or re.search(r"\d{3,}", sld):  # авто-сген домены
                    continue
                # бренд = SLD содержит гембл-паттерн но не чисто generic
                if not any(pt in sld for pt in PATTERNS):
                    continue
                seen.add(sld)
                # извлекаем «имя бренда» = SLD без gambling-суффиксов
                brand = re.sub(r"(casino|bet|win|spin|slots|官方|gaming|play|app|vip|club)", "", sld).strip("-_")
                brand = (brand or sld).replace("-", " ").title()
                out.append({"brand": brand or sld.title(), "domain": dom,
                            "first_seen": row.get("not_before", "")[:10]})
                if len(out) >= limit:
                    return out
    return out
