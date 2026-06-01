"""Собирает МНОГОСТРАНИЧНЫЙ сайт из карты site_planner. content+image+перелинковка+sitemap/robots/llms."""
import os
from core.site_planner import plan_site
from core.structure_planner import plan as page_plan
from core.keyword_taxonomy import KW_TYPES, detect_type
from core.content_agent import generate as gt
from core.image_agent import gen_image
from core.assembler3 import render

def build_site(domain, brand, geo, mode="brand"):
    site=plan_site(brand, geo, mode)
    outdir=f"output/{domain.replace('.','_')}"; os.makedirs(outdir, exist_ok=True)
    nav=[(p["nav"], ("index.html" if p["slug"]=="index" else f"{p['slug'].replace(chr(47),chr(95))}.html")) for p in site["nav"]]
    from core.keyword_taxonomy import GEO_FLAVOR
    import shutil
    # картинки из готового пула (build_assets.py). Копируем в сайт -> локальные пути, надёжно.
    apool=f"output/assets/{geo}"
    sa=f"{outdir}/assets"; os.makedirs(sa, exist_ok=True)
    hero=""
    if os.path.exists(f"{apool}/hero.jpg"):
        shutil.copy(f"{apool}/hero.jpg", f"{sa}/hero.jpg"); hero="assets/hero.jpg"
    game_imgs={}
    for g in GEO_FLAVOR.get(geo,{}).get("hot",[])[:6]:
        slug=g.lower().replace(" ","_"); src=f"{apool}/game_{slug}.jpg"
        if os.path.exists(src):
            shutil.copy(src, f"{sa}/game_{slug}.jpg"); game_imgs[g]=f"assets/game_{slug}.jpg"
        else: game_imgs[g]=""
    urls=[]
    for pg in site["pages"]:
        ktype=detect_type(pg["kw"]); secs=KW_TYPES[ktype]["sections"]
        pl=page_plan(domain+pg["slug"], brand, geo, pg["kw"]); pl["sections"]=secs
        try:
            content,_=gt(brand, geo, pg["kw"], secs)
        except Exception:
            content={"meta_description":pg["title"],"sections":{s:f"{brand} {pg['kw']} information." for s in secs}}
        html=render(pl, content, hero, "", nav, game_imgs)
        try:
            from core.footprint import mutate
            html=mutate(html, domain)   # анти-footprint пост-процессор (структурная мутация per-domain)
        except Exception as e:
            print("footprint mutate warn:", e)
        fn = "index.html" if pg["slug"]=="index" else f"{pg['slug'].replace('/','_')}.html"
        open(f"{outdir}/{fn}","w").write(html)
        urls.append(pg["slug"])
    # sitemap + robots + llms
    sm='<?xml version="1.0"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
    for u in urls: sm+=f'<url><loc>https://{domain}/{"" if u=="index" else u+".html"}</loc></url>\n'
    sm+='</urlset>'; open(f"{outdir}/sitemap.xml","w").write(sm)
    open(f"{outdir}/robots.txt","w").write("User-agent: *\nAllow: /\nUser-agent: GPTBot\nAllow: /\nUser-agent: PerplexityBot\nAllow: /\nUser-agent: ClaudeBot\nAllow: /\nUser-agent: Google-Extended\nAllow: /\nSitemap: https://"+domain+"/sitemap.xml\n")
    open(f"{outdir}/llms.txt","w").write(f"# {brand} {geo.upper()}\n"+ "".join(f"- /{u if u!='index' else ''}\n" for u in urls))
    return outdir, len(urls)

if __name__=="__main__":
    pass  # ANTHROPIC_API_KEY из env
    d,n=build_site("78win01.host","78Win","in","brand")
    print(f"сайт собран: {d} ({n} страниц + sitemap+robots+llms)")
