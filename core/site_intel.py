"""ЕДИНАЯ КАРТОЧКА САЙТА — всё по одному домену в одном месте (то что просил Алекс):
индекс (Google), позиция Google + Bing, AI-видимость, http-статус, клики/просмотры (наша аналитика).
"""
import sqlite3, hashlib

def intel(host, keyword=None, geo="in"):
    keyword = keyword or host.split(".")[0]
    out = {"host": host, "keyword": keyword, "geo": geo}
    # http + индекс
    try:
        from core.monitor import http_status, indexed_count
        out["http"] = http_status(f"https://{host}/")
        out["indexed_pages"] = indexed_count(host)
    except Exception as e:
        out["monitor_err"] = str(e)[:60]
    # позиции Google + Bing
    try:
        from core.rank_tracker import check
        out["google_pos"] = check(host, keyword, geo).get("pos")
    except Exception:
        out["google_pos"] = None
    try:
        from core.recon import bing_position
        out["bing_pos"] = bing_position(host, keyword)
    except Exception:
        out["bing_pos"] = None
    # AI-видимость
    try:
        from core.recon import ai_visibility
        av = ai_visibility(keyword, geo, our_domain=host)
        out["ai_visible"] = av.get("we_in_serp") if isinstance(av, dict) else None
    except Exception:
        out["ai_visible"] = None
    # наша аналитика (beacon /px)
    try:
        sid = hashlib.sha256(host.encode()).hexdigest()[:12]
        c = sqlite3.connect("analytics.db")
        c.execute("CREATE TABLE IF NOT EXISTS hits(site TEXT,event TEXT,extra TEXT,ref TEXT,path TEXT,ip TEXT,ts INTEGER)")
        rows = c.execute("SELECT event,COUNT(*) FROM hits WHERE site=? GROUP BY event", (sid,)).fetchall()
        c.close()
        d = {e: n for e, n in rows}
        out["views"] = d.get("view", 0); out["cta_clicks"] = d.get("cta", 0)
        out["ctr_to_offer"] = round(d.get("cta", 0) / d["view"], 3) if d.get("view") else 0
    except Exception:
        out["views"] = out["cta_clicks"] = 0
    # сводный вердикт
    g, b = out.get("google_pos"), out.get("bing_pos")
    out["verdict"] = ("в топ-5 Google" if g and g <= 5 else "в топ-20 Google" if g else
                      "в Bing" if b else "не в выдаче (ждём индекс)")
    return out
