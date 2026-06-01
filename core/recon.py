"""Разведка конкурентов: по ключу+гео тянем топ органической выдачи (DuckDuckGo HTML, без API-ключа),
вытаскиваем домены конкурентов, грубо классифицируем тип (бренд-казино / афилейт-обзорник / агрегатор).
Это наша разработка — данные для решения "куда бить" и "какой footprint у топа"."""
import urllib.request, urllib.parse, re, html as _html

UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120 Safari/537.36"

# гео → региональный параметр DuckDuckGo (kl) + язык
GEO_KL = {"in":"in-en","bd":"bd-en","br":"br-pt","ng":"ng-en","uk":"uk-en","pk":"pk-en","ke":"ke-en","ph":"ph-en"}

def _fetch(url, data=None):
    r = urllib.request.Request(url, data=data, headers={"User-Agent": UA})
    return urllib.request.urlopen(r, timeout=25).read().decode("utf-8", "ignore")

def serp(keyword, geo="in", n=10):
    """Топ органики по ключу в гео. Возвращает list[{pos,domain,url,title}]."""
    kl = GEO_KL.get(geo, "us-en")
    q = urllib.parse.urlencode({"q": keyword, "kl": kl})
    try:
        body = urllib.parse.urlencode({"q": keyword, "kl": kl}).encode()
        h = _fetch("https://html.duckduckgo.com/html/", data=body)
    except Exception as e:
        return {"error": f"serp fetch failed: {str(e)[:100]}"}
    out = []
    # ссылки результатов DDG html
    for m in re.finditer(r'<a[^>]+class="result__a"[^>]+href="([^"]+)"[^>]*>(.*?)</a>', h, re.S):
        href, title = m.group(1), re.sub(r"<[^>]+>", "", m.group(2)).strip()
        # ddg редиректит через uddg=
        mm = re.search(r"uddg=([^&]+)", href)
        real = urllib.parse.unquote(mm.group(1)) if mm else href
        dom = urllib.parse.urlparse(real).netloc.replace("www.", "")
        if not dom or "duckduckgo.com" in dom or dom in [r["domain"] for r in out]:
            continue
        out.append({"pos": len(out)+1, "domain": dom, "url": real, "title": _html.unescape(title)[:120]})
        if len(out) >= n:
            break
    return {"keyword": keyword, "geo": geo, "count": len(out), "results": out, "classified": _classify(out)}

CASINO_WORDS = ("casino","bet","win","spin","slot","play","game","aviator","luck","royal","mega","jet","gold","vegas","jackpot")
AFFILIATE_WORDS = ("review","best","top","guide","compare","rating","bonus","sites","list","vs")

def _classify(results):
    """Грубая классификация топа: бренд-казино / афилейт-обзорник / прочее. Footprint топа."""
    brand=aff=other=0
    for r in results:
        d = r["domain"].lower(); t = r["title"].lower()
        if any(w in t for w in AFFILIATE_WORDS) or any(w in d for w in ("review","best","top","guru","compare")):
            aff += 1; r["type"]="affiliate"
        elif any(w in d for w in CASINO_WORDS):
            brand += 1; r["type"]="brand-casino"
        else:
            other += 1; r["type"]="other"
    return {"brand_casino": brand, "affiliate": aff, "other": other,
            "verdict": ("афилейт-обзорники доминируют — бей контентом/обзорами" if aff>=brand
                        else "бренд-казино в топе — нужен сильный бренд+траст")}
