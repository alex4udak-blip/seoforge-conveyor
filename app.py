"""SEOForge — конвейер 24/7: генератор сайтов v2 + vision-оценщик + панель сети.
FastAPI. Деплой на Saturn (Hetzner) из git. Единый интерфейс управления сетью SEO-сайтов."""
import os, glob, json, time
from fastapi import FastAPI
from fastapi.responses import HTMLResponse, JSONResponse, FileResponse, PlainTextResponse
from pydantic import BaseModel

app = FastAPI(title="SEOForge", description="Gambling SEO network: generate + vision + deploy + metrics")

NET_DB = "output/network.json"   # реестр сайтов сети (slug -> brand/geo/audit/deploy)

def _load_net():
    try: return json.load(open(NET_DB))
    except Exception: return {}
def _save_net(d):
    os.makedirs("output", exist_ok=True); json.dump(d, open(NET_DB,"w"), ensure_ascii=False, indent=1)

def _site_slugs():
    return [os.path.basename(d) for d in glob.glob("output/*") if os.path.isdir(d) and os.path.basename(d)!="assets"]

class GenReq(BaseModel):
    domain: str; brand: str; geo: str="in"; mode: str="brand"

class AuditReq(BaseModel):
    slug: str; geo: str="in"; keyword: str="online casino"; competitors: list=[]

@app.get("/health")
def health(): return {"status":"ok","service":"SEOForge"}

@app.get("/recon")
def recon_serp(keyword: str, geo: str="in", n: int=10):
    """Разведка конкурентов: топ органики по ключу+гео + классификация footprint (наша разработка)."""
    try:
        from core.recon import serp
        return serp(keyword, geo, n)
    except Exception as e:
        return JSONResponse(status_code=500, content={"error":str(e)[:200]})

@app.get("/debug")
def debug():
    """Ground-truth из контейнера: какой python, есть ли playwright, стартует ли chromium."""
    import sys, subprocess, shutil
    info={"executable":sys.executable,"version":sys.version.split()[0]}
    try:
        import playwright; info["playwright_import"]="OK "+getattr(playwright,"__version__","?")
    except Exception as e: info["playwright_import"]="FAIL: "+str(e)[:120]
    # запуск через тот же python что и _shot
    code="from playwright.sync_api import sync_playwright\nwith sync_playwright() as p:\n b=p.chromium.launch(args=['--no-sandbox']); b.close(); print('LAUNCH_OK')"
    try:
        r=subprocess.run([sys.executable,"-c",code],capture_output=True,text=True,timeout=60)
        info["chromium_launch"]=(r.stdout.strip() or "")+" | err:"+(r.stderr or "")[:200]
    except Exception as e: info["chromium_launch"]="EXC: "+str(e)[:150]
    info["chromium_bin"]=shutil.which("chromium") or shutil.which("chromium-browser") or "not-in-PATH"
    return info

@app.get("/sites")
def sites(): return {"sites":_site_slugs()}

@app.get("/", response_class=HTMLResponse)
def dashboard():
    """Полноценный продукт — русский UI с вкладками: Обзор / Создать / Метрики / Разведка."""
    try:
        return HTMLResponse(open(os.path.join(os.path.dirname(__file__),"ui.html"),encoding="utf-8").read())
    except Exception as e:
        return HTMLResponse(f"<h1>SEOForge</h1><p>ui.html не найден: {e}</p>")

@app.get("/network")
def network():
    """Реестр всей сети: каждый сайт + его метрики (vision-балл, гео, статус)."""
    net=_load_net()
    out=[]
    for s in _site_slugs():
        m=net.get(s,{})
        out.append({"slug":s,"brand":m.get("brand"),"geo":m.get("geo"),
                    "audit_score":m.get("audit_score"),"audit_at":m.get("audit_at"),
                    "url":f"/site/{s}/index.html"})
    return {"count":len(out),"network":out}

@app.get("/metrics/{slug}")
def site_metrics(slug: str):
    """Проваливание вглубь по 1 сайту: страницы, vision-разбор+фиксы, история, заглушки SERP/Keitaro."""
    import os as _os
    d=f"output/{slug}"
    if not _os.path.isdir(d): return JSONResponse(status_code=404, content={"error":"site not found"})
    m=_load_net().get(slug,{})
    pages=[]
    for f in sorted(_os.listdir(d)):
        if f.endswith(".html"):
            pages.append({"page":f,"bytes":_os.path.getsize(_os.path.join(d,f))})
    return {
        "slug":slug,"brand":m.get("brand"),"geo":m.get("geo"),"domain":m.get("domain"),
        "pages_count":len(pages),"pages":pages,
        "vision":{"score":m.get("audit_score"),"breakdown":m.get("audit_scores"),"fixes":m.get("audit_fixes")},
        "history":m.get("history",[]),
        "uptime":{"status":"live","pages_served":len(pages),"total_bytes":sum(p["bytes"] for p in pages)},
        "serp":{"status":"not_wired","note":"подключить SERP-сканер (позиции по ключам)"},
        "keitaro":{"status":"not_wired","note":"подключить Keitaro API (депы/клики/EPC)"},
        "indexation":{"status":"not_wired","note":"GSC/Bing API"},
    }

@app.get("/dash/{slug}", response_class=HTMLResponse)
def site_dashboard(slug: str):
    """HTML страница глубокого анализа одного сайта сети."""
    import os as _os
    d=f"output/{slug}"
    if not _os.path.isdir(d): return HTMLResponse("<h1>404 — сайта нет в сети</h1>", status_code=404)
    m=_load_net().get(slug,{})
    bd=m.get("audit_scores") or {}
    rows=""
    for k,v in bd.items():
        sc=v.get("score") if isinstance(v,dict) else v
        why=v.get("why","") if isinstance(v,dict) else ""
        col="#00e5a0" if isinstance(sc,(int,float)) and sc>=70 else ("#f5b73d" if isinstance(sc,(int,float)) and sc>=50 else "#ff6b6b")
        rows+=f'<tr><td>{k}</td><td style="color:{col};font-weight:700">{sc}</td><td style="opacity:.7">{why}</td></tr>'
    pg=""
    for f in sorted(_os.listdir(d)):
        if f.endswith(".html"): pg+=f'<li><a href="/site/{slug}/{f}" target="_blank">{f}</a></li>'
    fixes="".join(f"<li>{x}</li>" for x in (m.get("audit_fixes") or []))
    return f"""<!doctype html><html><head><meta charset=utf-8><title>{slug} — анализ</title>
<style>body{{font-family:system-ui;background:#0a0e1a;color:#eaf0ff;margin:0;padding:30px;max-width:900px;margin:auto}}
a{{color:#22d3ee}}h1{{color:#00e5a0}}table{{width:100%;border-collapse:collapse;margin:14px 0}}td{{padding:8px;border-bottom:1px solid #ffffff14}}
.box{{background:#121829;border:1px solid #ffffff14;border-radius:12px;padding:18px;margin:14px 0}}.big{{font-size:40px;font-weight:800;color:#00e5a0}}</style></head>
<body><a href="/">← сеть</a><h1>{m.get('brand',slug)} <span style="opacity:.5">/{m.get('geo','?')}</span></h1>
<div class="box"><div>vision-балл</div><div class="big">{m.get('audit_score','—')}</div></div>
<div class="box"><h3>Разбор по критериям</h3><table>{rows or '<tr><td>нет аудита — POST /audit</td></tr>'}</table></div>
<div class="box"><h3>Что чинить (приоритет)</h3><ol>{fixes or '<li>—</li>'}</ol></div>
<div class="box"><h3>Страницы ({pg.count('<li>')})</h3><ul>{pg}</ul></div>
<div class="box" style="opacity:.6"><h3>Метрики (в работе)</h3>SERP-позиции · Keitaro депы/EPC · индексация GSC — подключаются</div>
</body></html>"""

def _set_stage(slug, stage, pct, **extra):
    net=_load_net(); cur=net.get(slug,{})
    net[slug]={**cur,"build":"building","stage":stage,"progress":pct,**extra}; _save_net(net)

def _build_job(req: "GenReq", slug: str):
    """Фоновая сборка сайта со стадиями прогресса (для realtime-UI)."""
    try:
        _set_stage(slug,"Подготовка изображений",15,brand=req.brand,geo=req.geo,domain=req.domain)
        if not os.path.exists(f"output/assets/{req.geo}/hero.jpg"):
            try:
                from build_assets import build as build_assets; build_assets(req.geo)
            except Exception as e: print("assets warn:", e)
        _set_stage(slug,"Генерация контента и страниц",55,brand=req.brand,geo=req.geo,domain=req.domain)
        from site_builder import build_site
        outdir,n=build_site(req.domain, req.brand, req.geo, req.mode)
        _set_stage(slug,"Финализация (sitemap, schema)",90,brand=req.brand,geo=req.geo,domain=req.domain,pages=n)
        net=_load_net(); net[slug]={**net.get(slug,{}),"brand":req.brand,"geo":req.geo,"domain":req.domain,"pages":n,"build":"done","stage":"Готово","progress":100}; _save_net(net)
    except Exception as e:
        net=_load_net(); net[slug]={**net.get(slug,{}),"build":"error","stage":"Ошибка: "+str(e)[:100],"progress":0}; _save_net(net)

@app.get("/status")
def status():
    """Лёгкий поллинг всей сети для realtime-UI: статус сборки + балл каждого сайта."""
    net=_load_net(); out=[]
    for s in _site_slugs():
        m=net.get(s,{})
        out.append({"slug":s,"brand":m.get("brand"),"geo":m.get("geo"),
                    "build":m.get("build","done"),"stage":m.get("stage"),"progress":m.get("progress"),
                    "audit_score":m.get("audit_score")})
    # плюс сайты ещё в сборке (папки может не быть)
    seen={o["slug"] for o in out}
    for s,m in net.items():
        if s not in seen and m.get("build")=="building":
            out.append({"slug":s,"brand":m.get("brand"),"geo":m.get("geo"),
                        "build":"building","stage":m.get("stage"),"progress":m.get("progress"),"audit_score":None})
    sc=[o["audit_score"] for o in out if o.get("audit_score")]
    return {"count":len(out),"avg":round(sum(sc)/len(sc),1) if sc else None,"sites":out}

@app.post("/generate")
def generate(req: GenReq, sync: bool=False):
    """sync=false (дефолт): мгновенный ответ + фоновая сборка (нет CF 524). sync=true: ждать (для локалки)."""
    slug=req.domain.replace(".","_")
    if sync:
        _build_job(req, slug)
        m=_load_net().get(slug,{})
        return {"ok":True,"pages":m.get("pages"),"slug":slug,"build":m.get("build"),"url":f"/site/{slug}/index.html"}
    import threading
    net=_load_net(); net[slug]={**net.get(slug,{}),"brand":req.brand,"geo":req.geo,"domain":req.domain,"build":"building"}; _save_net(net)
    threading.Thread(target=_build_job, args=(req, slug), daemon=True).start()
    return {"ok":True,"slug":slug,"build":"building","url":f"/site/{slug}/index.html","note":"сборка в фоне, проверь через ~60-90с"}

@app.post("/audit")
def audit_site(req: AuditReq):
    """Умная vision-оценка по рубрике + запись балла в реестр сети."""
    try:
        from core.vision_audit import audit, weighted
        base=os.environ.get("SELF_URL","http://localhost:8000")
        res=audit(f"{base}/site/{req.slug}/index.html", req.competitors, req.geo, req.keyword)
        if "scores" in res:
            res["weighted_recomputed"]=weighted(res["scores"])
            net=_load_net()
            net[req.slug]={**net.get(req.slug,{}),"audit_score":res.get("weighted_total"),
                           "audit_scores":res.get("scores"),"audit_fixes":res.get("top_fixes")}
            _save_net(net)
        return res
    except Exception as e:
        return JSONResponse(status_code=500, content={"ok":False,"error":str(e)})

class ScoreReq(BaseModel):
    slug: str; brand: str=""; geo: str=""; weighted_total: float=0
    scores: dict={}; fixes: list=[]

@app.post("/score")
def write_score(req: ScoreReq):
    """Записать готовый vision-балл в реестр сети (vision гоняется внешне — локальный playwright vs живой прод-URL,
    т.к. Saturn не пересобирает образ с playwright). Так панель сети наполняется реальными оценками."""
    net=_load_net()
    cur=net.get(req.slug,{})
    hist=cur.get("history",[])
    if cur.get("audit_score") is not None:
        hist=hist+[{"score":cur.get("audit_score")}]
    net[req.slug]={**cur,
        "brand":req.brand or cur.get("brand"),"geo":req.geo or cur.get("geo"),
        "audit_score":req.weighted_total,"audit_scores":req.scores,"audit_fixes":req.fixes,
        "history":hist[-20:]}
    _save_net(net)
    return {"ok":True,"slug":req.slug,"score":req.weighted_total}

@app.get("/site/{slug}")
@app.get("/site/{slug}/{path:path}")
def serve_site(slug: str, path: str="index.html"):
    base=os.path.abspath("output")
    fp=os.path.abspath(os.path.join(base, slug, path or "index.html"))
    if not fp.startswith(base) or not os.path.isfile(fp):
        return PlainTextResponse("404", status_code=404)
    return FileResponse(fp)

if __name__=="__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT","8000")))
