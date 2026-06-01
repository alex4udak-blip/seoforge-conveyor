"""Доменщик: готовая база гембл-трастов (Dynadot marketplace harvest) + верификация возраста Wayback.
Отдаёт домены под задачу: траст-дроп (Tier-1 заход) или дешёвый расходник (Tier-3)."""
import csv, os, urllib.request, json

BASE = os.path.join(os.path.dirname(__file__), "..", "data_domains.csv")
ENRICHED = os.path.join(os.path.dirname(__file__), "..", "data_domains_enriched.csv")
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120 Safari/537.36"

def wayback_snaps(domain):
    """Число снапшотов в Wayback (по месяцам) + первый год. Живой домен = много снапшотов."""
    try:
        u = f"http://web.archive.org/cdx/search/cdx?url={domain}&output=json&limit=5000&collapse=timestamp:6"
        r = urllib.request.Request(u, headers={"User-Agent": UA})
        data = json.loads(urllib.request.urlopen(r, timeout=18).read().decode())
        rows = data[1:] if len(data) > 1 else []
        snaps = len(rows)
        first_year = int(rows[0][1][:4]) if rows else None  # ts во 2-й колонке CDX
        return snaps, first_year
    except Exception:
        return None, None

OPR_KEY = os.environ.get("OPR_KEY", "")

def openpagerank(domains):
    """Реальный DR (0-10) через OpenPageRank API (база Common Crawl). Батч до 100. Нужен OPR_KEY."""
    if not OPR_KEY or not domains:
        return {}
    out = {}
    # API принимает до 100 доменов за запрос
    for i in range(0, len(domains), 100):
        chunk = domains[i:i+100]
        q = "&".join(f"domains[]={urllib.parse.quote(d)}" for d in chunk)
        try:
            req = urllib.request.Request(
                "https://openpagerank.com/api/v1.0/getPageRank?" + q,
                headers={"API-OPR": OPR_KEY, "User-Agent": UA})
            data = json.loads(urllib.request.urlopen(req, timeout=20).read().decode())
            for row in data.get("response", []):
                out[row.get("domain")] = {
                    "dr": row.get("page_rank_decimal"),   # 0-10
                    "rank": row.get("rank"),
                }
        except Exception as e:
            out["_error"] = str(e)[:80]
    return out

def verdict(price, backlinks, first_year, cur_year=2026, dr=None):
    """ТОЧНЫЙ вывод по возрасту (Wayback) + беки. Ключ: беки физически невозможны без возраста.
    Естественный темп ~ до нескольких тысяч беков/год. Превышение = накрутка."""
    if not first_year:
        # нет в архиве — но беков много = точно накрутка (домен без истории не набирает беки)
        if backlinks > 1000:
            return "СПАМ-беки", f"{backlinks:,} беков, но домена НЕТ в веб-архиве — накрутка/спам-ферма"
        return "свежий домен", f"нет истории, {backlinks} беков — свежак под расходник"
    age = max(cur_year - first_year, 0)
    drtxt = f", DR {dr}" if dr is not None else ""
    # DR от OpenPageRank = НАСТОЯЩИЙ сигнал авторитета (если есть ключ)
    if dr is not None:
        # накрутка = много беков при низком авторитете (реальные беки подняли бы DR)
        if backlinks > 10000 and dr < 3:
            return "СПАМ-беки", f"{backlinks:,} беков, но DR всего {dr}/10 — будь беки реальными, DR был бы выше = накрутка"
        if dr >= 4:
            return "РЕАЛЬНЫЙ ТРАСТ", f"DR {dr}/10 — высокий авторитет (OpenPageRank), {backlinks} беков"
        if dr >= 2.5:
            return "траст рабочий", f"DR {dr}/10, {age}г — нормальный авторитет для гембла"
        if dr < 1.5:
            return "слабый/свежий", f"DR {dr}/10 — низкий авторитет, как расходник"
        return "средний", f"DR {dr}/10, {backlinks} беков, {age}г"
    # fallback по возрасту (без OPR-ключа)
    plausible = max(age, 1) * 3000
    if backlinks > plausible * 3:
        return "СПАМ-беки", f"{backlinks:,} беков за {age}г — невозможно органически (накрутка){drtxt}"
    if age >= 8:
        return "РЕАЛЬНЫЙ ТРАСТ", f"живой {age} лет, {backlinks} беков в норме{drtxt}"
    if age >= 3:
        return "траст средний", f"{age} лет, {backlinks} беков правдоподобно{drtxt}"
    return "честный молодой", f"{age}г, {backlinks} беков без накрутки{drtxt}"

def _load(path):
    try:
        return list(csv.DictReader(open(path, encoding="utf-8")))
    except Exception:
        return []

def list_domains(sort="backlinks", max_price=None, min_backlinks=0, only_trust=False, limit=60):
    rows = _load(BASE)
    enr = {r["domain"]: r for r in _load(ENRICHED)}
    # фильтр-предпросмотр чтобы знать каким доменам тянуть DR
    cand = []
    for r in rows:
        try:
            price = float(r.get("price") or 0); bl = int(r.get("backlinks") or 0)
        except Exception:
            continue
        if max_price and price > max_price: continue
        if bl < min_backlinks: continue
        cand.append((r["domain"], price, bl))
    # батч DR для топ-limit кандидатов (OpenPageRank, если есть ключ)
    dr_map = openpagerank([c[0] for c in cand[:limit]]) if OPR_KEY else {}
    out = []
    for domain, price, bl in cand:
        e = enr.get(domain, {})
        wb = e.get("wb_year")
        fy = int(wb) if wb and str(wb).isdigit() and wb not in ("0",) else None
        dr = (dr_map.get(domain) or {}).get("dr")
        vlabel, vwhy = verdict(price, bl, fy, dr=dr)
        is_trust = "ТРАСТ" in vlabel
        if only_trust and not is_trust: continue
        out.append({
            "domain": domain, "price": price, "backlinks": bl,
            "wb_year": fy, "dr": dr,
            "is_trust": is_trust, "verdict": vlabel, "why": vwhy,
        })
    keymap = {"backlinks": lambda x: -x["backlinks"], "price": lambda x: x["price"],
              "age": lambda x: (x["wb_year"] or 9999)}
    out.sort(key=keymap.get(sort, keymap["backlinks"]))
    stats = {"total": len(rows), "shown": len(out[:limit]),
             "trusts": sum(1 for o in out if o["is_trust"]),
             "spam": sum(1 for o in out if "СПАМ" in o["verdict"]),
             "cheap": sum(1 for o in out if o["price"] <= 35)}
    return {"stats": stats, "domains": out[:limit]}

def check_brand(brand):
    """Проверка домена под НОВЫЙ бренд через Dynadot (доступность+цена). Использует tools/domain_check."""
    import subprocess, sys
    venv = "/Users/marsatim/Projects/SEO-Scanner-Pro/venv/bin/python"
    py = venv if os.path.exists(venv) else sys.executable
    script = "/Users/marsatim/Projects/SEO-Scanner-Pro/tools/domain_check.py"
    if not os.path.exists(script):
        return {"error": "domain_check.py недоступен на этом хосте"}
    try:
        r = subprocess.run([py, script, brand], capture_output=True, text=True, timeout=60)
        out = []
        for line in r.stdout.splitlines():
            if "✅" in line:
                parts = line.split()
                out.append({"domain": parts[0], "available": True,
                            "reg_price": parts[2] if len(parts) > 2 else "?",
                            "renew": parts[3] if len(parts) > 3 else "?"})
        return {"brand": brand, "available": out}
    except Exception as e:
        return {"error": str(e)[:120]}
