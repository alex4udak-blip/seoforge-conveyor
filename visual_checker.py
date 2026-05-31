#!/usr/bin/env python3
"""Visual QA чекер: проверяет сгенерированный сайт автоматически (без ручного просмотра).
Картинки не битые, контент есть, нет placeholder, sticky/nav/schema работают.
Usage: python3 visual_checker.py <site_dir> [base_url]
"""
import sys, glob, os, json
sys.path.insert(0,"/Users/marsatim/Projects/SEO-Scanner-Pro/venv/lib/python3.9/site-packages")
from playwright.sync_api import sync_playwright

def check_site(site_dir, base="http://localhost:8090"):
    rel=site_dir.split("output/")[-1]
    pages=[os.path.basename(f) for f in glob.glob(f"{site_dir}/*.html")]
    report=[]
    with sync_playwright() as p:
        b=p.chromium.launch(); pg=b.new_page(viewport={"width":390,"height":844})
        for page in sorted(pages):
            url=f"{base}/{rel}/{page}"
            try: pg.goto(url,wait_until="networkidle",timeout=25000)
            except Exception as e: report.append({"page":page,"FAIL":f"load:{str(e)[:40]}"}); continue
            r=pg.evaluate("""()=>{
              const imgs=[...document.querySelectorAll('img')];
              const broken=imgs.filter(i=>!i.complete||i.naturalWidth===0).map(i=>i.src.slice(0,40));
              const txt=document.body.innerText;
              return {
                imgs:imgs.length, broken_imgs:broken,
                placeholders:(txt.match(/placeholder|content-agent|\\bcontent for\\b/gi)||[]).length,
                ai_markers:(txt.match(/in conclusion|moreover|seamless|unlock the|delve/gi)||[]).length,
                sticky:!!document.querySelector('.sticky-cta'),
                nav_links:document.querySelectorAll('.navlinks a').length,
                schema:[...document.querySelectorAll('script[type=\"application/ld+json\"]')].length,
                text_len:txt.length, h2:document.querySelectorAll('section h2').length
              }
            }""")
            issues=[]
            if r["broken_imgs"]: issues.append(f"битых картинок:{len(r['broken_imgs'])}")
            if r["placeholders"]: issues.append(f"placeholder:{r['placeholders']}")
            if r["ai_markers"]: issues.append(f"AI-маркеры:{r['ai_markers']}")
            if not r["sticky"]: issues.append("нет sticky-CTA")
            if r["nav_links"]<3: issues.append("нет навигации")
            if r["text_len"]<400: issues.append(f"мало текста:{r['text_len']}")
            report.append({"page":page,"status":"✅ PASS" if not issues else "❌ "+", ".join(issues),
                           "imgs":r["imgs"],"broken":len(r["broken_imgs"]),"schema":r["schema"]})
        b.close()
    return report

if __name__=="__main__":
    d=sys.argv[1] if len(sys.argv)>1 else "/Users/marsatim/Projects/generator-v2/output/78win01_host"
    rep=check_site(d)
    print(f"\n=== VISUAL QA: {os.path.basename(d)} ({len(rep)} страниц) ===")
    passed=sum(1 for r in rep if "PASS" in r.get("status",""))
    for r in rep: print(f"{r['page']:<20} {r['status']:<45} img:{r.get('imgs',0)} битых:{r.get('broken',0)} schema:{r.get('schema',0)}")
    print(f"\nИТОГ: {passed}/{len(rep)} страниц PASS")
