"""SEOForge — конвейер 24/7: генератор сайтов v2 + vision-оценщик + разведка.
FastAPI обёртка. Деплой на Saturn из git. Работает постоянно."""
import os, glob
from fastapi import FastAPI, BackgroundTasks
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

app = FastAPI(title="SEOForge", description="Gambling SEO conveyor: generate + vision + recon")

class GenReq(BaseModel):
    domain: str
    brand: str
    geo: str = "in"
    mode: str = "brand"

@app.get("/")
def home():
    sites=[os.path.basename(d) for d in glob.glob("output/*") if os.path.isdir(d) and d.split("/")[-1]!="assets"]
    rows="".join(f'<li><a href="/site/{s}/index.html">{s}</a></li>' for s in sites)
    return HTMLResponse(f"""<html><head><title>SEOForge</title><style>body{{font-family:system-ui;background:#0a0e1a;color:#eaf0ff;max-width:800px;margin:40px auto;padding:20px}}a{{color:#00e5a0}}code{{background:#1a2030;padding:2px 6px;border-radius:4px}}</style></head>
    <body><h1>🔥 SEOForge — конвейер 24/7</h1>
    <p>Генератор гембл-SEO сайтов + vision-оценка + разведка. Работает на Saturn.</p>
    <h2>Endpoints</h2><ul>
    <li><code>POST /generate</code> {{domain,brand,geo,mode}} — собрать сайт</li>
    <li><code>GET /sites</code> — список сгенерированных</li>
    <li><code>GET /health</code></li></ul>
    <h2>Сгенерированные сайты ({len(sites)})</h2><ul>{rows or '<li>пока нет</li>'}</ul>
    </body></html>""")

@app.get("/health")
def health(): return {"status":"ok","service":"SEOForge"}

@app.get("/sites")
def sites():
    return {"sites":[os.path.basename(d) for d in glob.glob("output/*") if os.path.isdir(d) and not d.endswith("assets")]}

@app.post("/generate")
def generate(req: GenReq):
    try:
        from core.keyword_taxonomy import GEO_FLAVOR
        # картинки: пул (если нет — собрать)
        if not os.path.exists(f"output/assets/{req.geo}/hero.jpg"):
            try:
                from build_assets import build as build_assets
                build_assets(req.geo)
            except Exception as e:
                print("assets warn:", e)
        from site_builder import build_site
        outdir, n = build_site(req.domain, req.brand, req.geo, req.mode)
        slug=os.path.basename(outdir)
        return {"ok":True, "pages":n, "url":f"/site/{slug}/index.html", "slug":slug}
    except Exception as e:
        return JSONResponse(status_code=500, content={"ok":False,"error":str(e)})

# отдаём сгенерированные сайты через route (mount не видит папки созданные после старта)
from fastapi.responses import FileResponse, PlainTextResponse
@app.get("/site/{slug}")
@app.get("/site/{slug}/{path:path}")
def serve_site(slug: str, path: str = "index.html"):
    base = os.path.abspath("output")
    fp = os.path.abspath(os.path.join(base, slug, path or "index.html"))
    if not fp.startswith(base) or not os.path.isfile(fp):
        return PlainTextResponse("404", status_code=404)
    return FileResponse(fp)

if __name__=="__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT","8000")))
