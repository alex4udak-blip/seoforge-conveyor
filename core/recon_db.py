"""История выдачи в SQLite — данные = золото (Дима). Каждый скан с timestamp →
динамика позиций (мясорубка vs статика), детект новых/выпавших доменов во времени."""
import sqlite3, os, json, time

DB = "output/recon.db"

def _conn():
    os.makedirs("output", exist_ok=True)
    c = sqlite3.connect(DB)
    c.execute("""CREATE TABLE IF NOT EXISTS serp_snapshots(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        ts INTEGER, geo TEXT, keyword TEXT, domain TEXT, pos INTEGER, type TEXT)""")
    c.execute("CREATE INDEX IF NOT EXISTS idx_kw ON serp_snapshots(geo,keyword,ts)")
    return c

def save_scan(geo, keyword, results, ts):
    """Сохранить срез выдачи. ts передаётся снаружи (в скриптах Date.now недоступен)."""
    c=_conn()
    for r in results:
        c.execute("INSERT INTO serp_snapshots(ts,geo,keyword,domain,pos,type) VALUES(?,?,?,?,?,?)",
                  (ts, geo, keyword.lower(), r["domain"], r.get("pos"), r.get("type")))
    c.commit(); c.close()

def dynamics(geo, keyword):
    """Динамика выдачи: сколько срезов, движение позиций, новые/выпавшие домены между последними двумя."""
    c=_conn()
    rows=c.execute("SELECT DISTINCT ts FROM serp_snapshots WHERE geo=? AND keyword=? ORDER BY ts DESC LIMIT 2",
                   (geo, keyword.lower())).fetchall()
    if len(rows)<2:
        c.close(); return {"scans":len(rows),"note":"нужно ≥2 скана для динамики"}
    t_new,t_old=rows[0][0],rows[1][0]
    def snap(t): return {d:p for d,p in c.execute(
        "SELECT domain,pos FROM serp_snapshots WHERE geo=? AND keyword=? AND ts=?",(geo,keyword.lower(),t)).fetchall()}
    new,old=snap(t_new),snap(t_old)
    entered=[d for d in new if d not in old]
    dropped=[d for d in old if d not in new]
    moved=[{"domain":d,"from":old[d],"to":new[d]} for d in new if d in old and old[d]!=new[d]]
    total=c.execute("SELECT COUNT(DISTINCT ts) FROM serp_snapshots WHERE geo=? AND keyword=?",(geo,keyword.lower())).fetchone()[0]
    c.close()
    churn=len(entered)+len(dropped)
    return {"scans":total,"entered":entered,"dropped":dropped,"moved":moved,
            "churn":churn,
            "verdict":("ДИНАМИЧНАЯ выдача (мясорубка) — легко заскочить" if churn>=2
                       else "стабильная выдача — трудно сдвинуть" if churn==0
                       else "умеренная динамика")}
