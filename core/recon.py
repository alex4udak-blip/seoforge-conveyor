"""RECON — разведка выдачи (наша замена DataForSEO, фаза A SEOForge).
По ключу+гео: топ органики + классификация ОФИЦИАЛ/СЕОШНИК (по маркерам Димы, не по домену) +
related + PAA (→ FAQ генератора) + footprint топа. Данные для "куда бить".
Источник выдачи: DuckDuckGo HTML (без API-ключа; позже — резид.агенты из гео)."""
import urllib.request, urllib.parse, re, html as _html

UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120 Safari/537.36"
GEO_KL = {"in":"in-en","bd":"bd-en","br":"br-pt","ng":"ng-en","uk":"uk-en","pk":"pk-en","ke":"ke-en","ph":"ph-en"}

def _fetch(url, data=None, timeout=25):
    r = urllib.request.Request(url, data=data, headers={"User-Agent": UA})
    return urllib.request.urlopen(r, timeout=timeout).read().decode("utf-8", "ignore")

def serp(keyword, geo="in", n=10, classify_deep=True):
    """Топ органики + классификация + related. classify_deep=заходить на сайты (точнее, но медленнее)."""
    kl = GEO_KL.get(geo, "us-en")
    try:
        body = urllib.parse.urlencode({"q": keyword, "kl": kl}).encode()
        h = _fetch("https://html.duckduckgo.com/html/", data=body)
    except Exception as e:
        return {"error": f"serp fetch failed: {str(e)[:100]}"}
    out = []
    for m in re.finditer(r'<a[^>]+class="result__a"[^>]+href="([^"]+)"[^>]*>(.*?)</a>', h, re.S):
        href, title = m.group(1), re.sub(r"<[^>]+>", "", m.group(2)).strip()
        mm = re.search(r"uddg=([^&]+)", href)
        real = urllib.parse.unquote(mm.group(1)) if mm else href
        dom = urllib.parse.urlparse(real).netloc.replace("www.", "")
        if not dom or "duckduckgo.com" in dom or dom in [r["domain"] for r in out]:
            continue
        out.append({"pos": len(out)+1, "domain": dom, "url": real, "title": _html.unescape(title)[:120]})
        if len(out) >= n:
            break
    # related: DDG related + Google autocomplete (long-tail семантика, метод Димы)
    related = []
    for m in re.finditer(r'class="related-searches__link"[^>]*>(.*?)</a>', h, re.S):
        t = re.sub(r"<[^>]+>", "", m.group(1)).strip()
        if t: related.append(_html.unescape(t))
    related += autocomplete(keyword, geo)
    # классификация: глубокая (заход на сайт) или быстрая (по домену/тайтлу)
    if classify_deep:
        for r in out[:min(len(out), 7)]:   # топ-7 заходим, остальные быстро
            r["type"], r["signals"] = _classify_page(r["url"])
        for r in out[7:]:
            r["type"], r["signals"] = _classify_fast(r["domain"], r["title"]), []
    else:
        for r in out:
            r["type"], r["signals"] = _classify_fast(r["domain"], r["title"]), []
    # dedup related
    seen=set(); rel=[]
    for x in related:
        k=x.lower().strip()
        if k and k!=keyword.lower() and k not in seen: seen.add(k); rel.append(x)
    return {"keyword": keyword, "geo": geo, "count": len(out),
            "results": out, "related": rel[:12], "classified": _footprint(out)}

def ai_visibility(keyword, geo="in", our_domain=None):
    """Есть ли мы в AI-выдаче. Замер: какие домены/бренды доминируют в источниках по запросу.
    Прокси без браузера: топ органики = база источников AI (ChatGPT 87% берёт топ Bing, AIO берёт топ Google).
    Возвращает: кого AI вероятно процитирует + есть ли наш домен + через кого заходить."""
    s = serp(keyword, geo, n=10, classify_deep=False)
    if "results" not in s:
        return {"error": s.get("error", "serp failed")}
    domains = [r["domain"] for r in s["results"]]
    # агрегаторы/обзорники = источники, на которые опираются AI (Perplexity/ChatGPT цитируют их)
    sources = [r for r in s["results"] if r.get("type") == "сеошник"]
    our_present = bool(our_domain and any(our_domain in d for d in domains))
    return {
        "keyword": keyword, "geo": geo,
        "we_in_serp": our_present,
        "likely_ai_sources": [r["domain"] for r in sources][:6],  # кого AI цитирует
        "all_top": domains,
        "verdict": (f"наш домен {our_domain} В выдаче-источнике AI" if our_present
                    else f"нас НЕТ в источниках AI — цитируют: {', '.join([r['domain'] for r in sources][:3])}. "
                         f"Чтобы попасть в AI-ответ: (1) встать в топ Bing/Google, (2) попасть в списки этих агрегаторов, (3) FAQ+пассажи под цитирование"),
        "related": s.get("related", [])[:8],  # follow-up интенты для генератора
    }

def domain_age(domain):
    """Возраст домена ПО ДАТАМ через Wayback (первый снапшот в веб-архиве). Без ключа.
    Возвращает {first_seen: 'YYYYMMDD', age_years, age_label}. None если домена нет в архиве (= совсем свежий)."""
    domain = domain.replace("https://","").replace("http://","").split("/")[0].replace("www.","")
    try:
        import json as _j
        u = f"http://archive.org/wayback/available?url={domain}&timestamp=20000101"
        d = _j.loads(_fetch(u, timeout=12))
        snap = d.get("archived_snapshots",{}).get("closest",{})
        ts = snap.get("timestamp")
        if not ts:
            return {"first_seen": None, "age_years": 0, "age_label": "нет в архиве (возможно свежий)"}
        year = int(ts[:4]); mon = int(ts[4:6])
        # текущий год передаём приблизительно — точную дату не вычисляем в проде, год архива достаточен
        return {"first_seen": ts[:8], "first_year": year, "first_month": mon}
    except Exception as e:
        return {"first_seen": None, "error": str(e)[:60]}

def botview(domain):
    """Вскрытие клоаки конкурента: контент через translate.goog (Google IP) vs обычный заход.
    Разница = клоака (сайт показывает Google одно, юзеру другое). Метод Димы/affiliate.fm."""
    domain = domain.replace("https://","").replace("http://","").split("/")[0].replace("www.","")
    tg = domain.replace("-","--").replace(".","-") + ".translate.goog"
    google_view = user_view = ""; err=[]
    try:
        google_view = _fetch(f"https://{tg}/?_x_tr_sl=auto&_x_tr_tl=en&_x_tr_hl=en", timeout=20)
    except Exception as e: err.append("google-view:"+str(e)[:60])
    try:
        user_view = _fetch(f"https://{domain}/", timeout=15)
    except Exception as e: err.append("user-view:"+str(e)[:60])
    def feats(h):
        h=h.lower()
        return {
            "len": len(h),
            "casino_words": len(re.findall(r'\b(casino|bet|bonus|deposit|slot|aviator|jackpot|spin)\b', h)),
            "ref_links": sum(h.count(m) for m in REF_MARKERS),
            "has_gambling": any(w in h for w in ("casino","bonus","deposit","betting","slot")),
        }
    gf, uf = feats(google_view), feats(user_view)
    # детект клоаки: Google видит гембл, юзер — нет (или наоборот), либо сильная разница объёма
    cloaked = False; why=[]
    if gf["has_gambling"] != uf["has_gambling"]:
        cloaked=True; why.append("гембл-контент виден Google, но НЕ юзеру (или наоборот)")
    if gf["casino_words"] and uf["len"] and abs(gf["casino_words"]-uf["casino_words"]) > max(20, gf["casino_words"]*0.5):
        cloaked=True; why.append(f"разное число казино-слов: Google={gf['casino_words']} vs юзер={uf['casino_words']}")
    if uf["len"] and gf["len"] and (max(gf["len"],uf["len"])/max(1,min(gf["len"],uf["len"])) > 3):
        cloaked=True; why.append(f"разный объём страницы: Google={gf['len']}b vs юзер={uf['len']}b")
    return {"domain":domain,"google_view":gf,"user_view":uf,
            "cloaked":cloaked,"why":why or (["клоака не обнаружена — сайт отдаёт одинаково"] if not err else []),
            "errors":err}

def autocomplete(keyword, geo="in"):
    """Google autocomplete = long-tail/PAA-семантика без API-ключа. Для FAQ/страниц генератора."""
    try:
        u = f"https://suggestqueries.google.com/complete/search?client=firefox&hl=en&gl={geo}&q=" + urllib.parse.quote(keyword)
        import json as _j
        d = _j.loads(_fetch(u, timeout=12))
        return d[1] if len(d) > 1 else []
    except Exception:
        return []

# ── классификация ОФИЦИАЛ vs СЕОШНИК (playbook: маркеры, не домен) ──
REF_MARKERS = ("/go/", "/redirect", "/out/", "/click", "clickid", "?ref=", "go.php", "/visit/", "aff_id", "/aff/")
SIGNUP_MARKERS = ("sign up", "register", "create account", "deposit now", "залог", "cadastrar", "registrar")
TOPLIST_MARKERS = ("best casino", "top casino", "casino list", "rating", "vs ", "review", "compare", "toplist", "ranked")

def _fetch_via_translate(url):
    """Заход через translate.goog (Google IP) — обход Cloudflare для unreachable-сайтов."""
    dom = urllib.parse.urlparse(url if "://" in url else "http://"+url).netloc.replace("www.","")
    path = url.split(dom,1)[1] if dom in url else "/"
    tg = dom.replace("-","--").replace(".","-") + ".translate.goog"
    return _fetch(f"https://{tg}{path}?_x_tr_sl=auto&_x_tr_tl=en&_x_tr_hl=en", timeout=18)

def _classify_page(url):
    """Заходим на сайт топа → ОФИЦИАЛ (1 бренд+регистрация) или СЕОШНИК (список+редирект наружу).
    Если Cloudflare блочит прямой заход — пробуем через translate.goog (Google IP)."""
    via=""
    try:
        html = _fetch(url, timeout=12).lower()
    except Exception:
        try:
            html = _fetch_via_translate(url).lower(); via="via-translate"
        except Exception:
            return _classify_fast(urllib.parse.urlparse(url if "://" in url else "http://"+url).netloc, ""), ["unreachable"]
    sig = []
    # внешние реф-редиректы (маркер сеошника)
    ref_links = sum(html.count(m) for m in REF_MARKERS)
    if ref_links: sig.append(f"ref-redirects:{ref_links}")
    # сколько разных казино-брендов упомянуто (список = сеошник)
    casino_mentions = len(re.findall(r'\b(1win|melbet|4rabet|parimatch|22bet|betway|stake|1xbet|mostbet|linebet|dafabet)\b', html))
    if casino_mentions: sig.append(f"casino-brands:{casino_mentions}")
    toplist = sum(1 for m in TOPLIST_MARKERS if m in html)
    if toplist: sig.append(f"toplist-words:{toplist}")
    signup = sum(1 for m in SIGNUP_MARKERS if m in html)
    # решение
    if via: sig.append(via)
    is_seo = (ref_links >= 2) or (casino_mentions >= 3) or (toplist >= 3 and ref_links >= 1)
    if is_seo:
        return "сеошник", sig
    if signup >= 1 and casino_mentions <= 2 and ref_links == 0:
        return "официал", sig + [f"signup:{signup}"]
    return "неясно", sig

def _classify_fast(domain, title):
    d = (domain or "").lower(); t = (title or "").lower()
    if any(w in t for w in ("review","best","top","casino list","rating","vs","compare")) or any(w in d for w in ("review","best","top","guru","compare","casinos")):
        return "сеошник"
    if any(w in d for w in ("casino","bet","win","spin","slot","play","aviator","luck","mega","jet","vegas")):
        return "официал?"
    return "неясно"

def _footprint(results):
    """Footprint топа: кого больше → куда бить."""
    seo = sum(1 for r in results if r.get("type")=="сеошник")
    off = sum(1 for r in results if r.get("type") in ("официал","официал?"))
    unk = sum(1 for r in results if r.get("type") in ("неясно",))
    if seo >= off and seo >= 2:
        verdict = f"СЕОШНИКИ доминируют ({seo} из {len(results)}) — это наши конкуренты за трафик. Бей лучшим контентом/обзором + перехватом."
    elif off > seo:
        verdict = f"ОФИЦИАЛЫ держат топ ({off}) — мало сеошников, щель: зайти обзорником/витриной первым."
    else:
        verdict = "Смешанная выдача — изучить топ-3 вручную (botview), искать динамику."
    return {"сеошники": seo, "официалы": off, "неясно": unk, "verdict": verdict}
