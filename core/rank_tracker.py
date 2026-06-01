"""RANK-TRACKER — «в топе или нет»: позиция наших доменов по ключам+гео + динамика.

Отвечает на вопрос Алекса «как поймём что сайт в топе». RECON.serp() даёт топ выдачи —
ищем наш хост в нём, пишем позицию во времени. + AI-видимость (в AI-выдаче или нет).
"""
import sqlite3, time, re

DB = "rank.db"

def _db():
    c = sqlite3.connect(DB)
    c.execute("CREATE TABLE IF NOT EXISTS ranks(host TEXT,keyword TEXT,geo TEXT,pos INTEGER,ts INTEGER)")
    return c

def check(host, keyword, geo="in"):
    """Позиция host в выдаче по keyword/geo (None если не найден в топе). Пишет в БД."""
    from core.recon import serp
    pos = None
    try:
        r = serp(keyword, geo, n=20, classify_deep=False)
        results = r.get("top") or r.get("results") or []
        for i, item in enumerate(results, 1):
            d = (item.get("domain") or item.get("url") or "")
            if host.split(".")[0] in d or host in d:
                pos = i; break
    except Exception as e:
        return {"host": host, "keyword": keyword, "geo": geo, "pos": None, "err": str(e)[:80]}
    c = _db(); c.execute("INSERT INTO ranks VALUES(?,?,?,?,?)", (host, keyword, geo, pos or 0, int(time.time())))
    c.commit(); c.close()
    return {"host": host, "keyword": keyword, "geo": geo, "pos": pos,
            "in_top20": pos is not None}

def history(host):
    c = _db()
    rows = c.execute("SELECT keyword,geo,pos,ts FROM ranks WHERE host=? ORDER BY ts DESC LIMIT 50", (host,)).fetchall()
    c.close()
    return [{"keyword": k, "geo": g, "pos": p or None, "ts": t} for k, g, p, t in rows]
