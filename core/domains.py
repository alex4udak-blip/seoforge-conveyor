"""Доменщик: готовая база гембл-трастов (Dynadot marketplace harvest) + верификация возраста Wayback.
Отдаёт домены под задачу: траст-дроп (Tier-1 заход) или дешёвый расходник (Tier-3)."""
import csv, os

BASE = os.path.join(os.path.dirname(__file__), "..", "data_domains.csv")
ENRICHED = os.path.join(os.path.dirname(__file__), "..", "data_domains_enriched.csv")

def _load(path):
    try:
        return list(csv.DictReader(open(path, encoding="utf-8")))
    except Exception:
        return []

def list_domains(sort="backlinks", max_price=None, min_backlinks=0, only_trust=False, limit=60):
    rows = _load(BASE)
    # подтянуть проверенный возраст из enriched
    age = {r["domain"]: r.get("wb_year") for r in _load(ENRICHED)}
    out = []
    for r in rows:
        try:
            price = float(r.get("price") or 0); bl = int(r.get("backlinks") or 0)
        except Exception:
            continue
        wb = age.get(r["domain"])
        is_trust = bool(wb and wb not in ("0", "?", "") and int(wb) <= 2020)
        if max_price and price > max_price: continue
        if bl < min_backlinks: continue
        if only_trust and not is_trust: continue
        out.append({
            "domain": r["domain"], "price": price, "backlinks": bl,
            "wb_year": wb if wb and wb not in ("0","?","") else None,
            "is_trust": is_trust,
            "tier": "Tier-1 траст" if is_trust else ("расходник Tier-3" if price <= 35 else "проверить"),
        })
    keymap = {"backlinks": lambda x: -x["backlinks"], "price": lambda x: x["price"],
              "age": lambda x: (x["wb_year"] or "9999")}
    out.sort(key=keymap.get(sort, keymap["backlinks"]))
    stats = {"total": len(rows), "shown": len(out[:limit]),
             "trusts": sum(1 for o in out if o["is_trust"]),
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
