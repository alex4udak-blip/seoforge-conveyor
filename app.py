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

@app.get("/sites")
def sites(): return {"sites":_site_slugs()}

@app.get("/", response_class=HTMLResponse)
def dashboard():
    net=_load_net(); slugs=_site_slugs()
    cards=""
    for s in slugs:
        m=net.get(s,{}); score=m.get("audit_score","—"); geo=m.get("geo","?"); brand=m.get("brand",s)
        color="#00e5a0" if isinstance(score,(int,float)) and score>=70 else ("#f5b73d" if isinstance(score,(int,float)) and score>=50 else "#888")
        cards+=f'''<div class="card"><div class="ch"><b>{brand}</b><span class="geo">{geo.upper()}</span></div>
        <a class="vis" href="/site/{s}/index.html" target="_blank">открыть сайт →</a>
        <div class="score" style="color:{color}">vision: {score}</div></div>'''
    return f"""<!doctype html><html><head><meta charset=utf-8><title>SEOForge — панель сети</title>
<style>body{{font-family:system-ui;background:#0a0e1a;color:#eaf0ff;margin:0;padding:30px}}
h1{{color:#00e5a0}}.grid{{display:grid;grid-template-columns:repeat(auto-fill,minmax(240px,1fr));gap:14px;margin-top:20px}}
.card{{background:#121829;border:1px solid #ffffff14;border-radius:14px;padding:16px}}.ch{{display:flex;justify-content:space-between;align-items:center}}
.geo{{background:#00e5a022;color:#00e5a0;padding:2px 8px;border-radius:6px;font-size:12px}}.vis{{color:#22d3ee;font-size:13px;text-decoration:none}}
.score{{margin-top:8px;font-weight:700}}code{{background:#1a2030;padding:2px 6px;border-radius:4px}}.ep{{opacity:.7;font-size:13px;line-height:1.8}}</style></head>
<body><h1>🔥 SEOForge — панель управления сетью</h1>
<p>Генератор + vision-оценка + деплой + метрики. Сеть гембл-SEO сайтов на Hetzner/Saturn.</p>
<div class="ep">API: <code>POST /generate</code> · <code>POST /audit</code> · <code>GET /network</code> · <code>GET /sites</code> · <code>GET /health</code></div>
<h2>Сеть сайтов ({len(slugs)})</h2><div class="grid">{cards or '<p>пока пусто — POST /generate</p>'}</div>
</body></html>"""

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

@app.post("/generate")
def generate(req: GenReq):
    try:
        if not os.path.exists(f"output/assets/{req.geo}/hero.jpg"):
            try:
                from build_assets import build as build_assets; build_assets(req.geo)
            except Exception as e: print("assets warn:", e)
        from site_builder import build_site
        outdir,n=build_site(req.domain, req.brand, req.geo, req.mode)
        slug=os.path.basename(outdir)
        net=_load_net(); net[slug]={**net.get(slug,{}),"brand":req.brand,"geo":req.geo,"domain":req.domain,"pages":n}; _save_net(net)
        return {"ok":True,"pages":n,"slug":slug,"url":f"/site/{slug}/index.html"}
    except Exception as e:
        return JSONResponse(status_code=500, content={"ok":False,"error":str(e)})

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
