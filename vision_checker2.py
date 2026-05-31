#!/usr/bin/env python3
"""Vision-2.0: скринит ТОП-7 реальных сайтов выдачи + наш сайт, Claude сравнивает.
Эталон = кто реально в топе. Вердикт против РЕАЛЬНЫХ лидеров, не абстракции.
Usage: python3 vision_checker2.py"""
import base64,json,urllib.request,subprocess,os
KEY=os.environ.get("ANTHROPIC_API_KEY")
VENV="/Users/marsatim/Projects/SEO-Scanner-Pro/venv/bin/python"

# топ-7 сеошников выдачи 'best online casino india' (собрано браузером, отфильтрованы официалы)
TOP=["https://gameshub.com/online-casino/","https://gambling.com/in","https://gamerules.com/in/casino/"]
OUR="http://localhost:8090/78win01_host/index.html"

def shot(url,path):
    code=f"""
from playwright.sync_api import sync_playwright
with sync_playwright() as p:
    b=p.chromium.launch(); pg=b.new_page(viewport={{'width':1200,'height':1000}})
    try: pg.goto('{url}',wait_until='domcontentloaded',timeout=30000); pg.wait_for_timeout(3000)
    except Exception as e: print('warn',e)
    pg.screenshot(path='{path}'); b.close()
"""
    try: subprocess.run([VENV,"-c",code],timeout=55); return os.path.exists(path)
    except Exception: return False

def b64(p): return base64.b64encode(open(p,"rb").read()).decode()

def compare():
    imgs=[]
    # наш
    shot(OUR,"/tmp/our.png"); imgs.append(("НАШ САЙТ","/tmp/our.png"))
    for i,u in enumerate(TOP):
        p=f"/tmp/top{i}.png"
        if shot(u,p): imgs.append((f"ТОП-{i+1} {u.split('/')[2]}",p))
    content=[]
    for label,p in imgs:
        if os.path.exists(p):
            content.append({"type":"text","text":label})
            content.append({"type":"image","source":{"type":"base64","media_type":"image/png","data":b64(p)}})
    content.append({"type":"text","text":"""Ты SEO/CRO эксперт по gambling. Первый скрин — НАШ сайт, остальные — РЕАЛЬНЫЕ конкуренты из ТОП Google по 'best online casino india'.
Сравни НАШ с реальными лидерами. Что у НИХ есть, чего у нас нет (структура, хуки, trust, контент, маркетинг)? Что делает их топовыми?
Не абстрактно 'красиво' — конкретно vs эти конкуренты. JSON: {"our_score_vs_them":N(1-10),"they_have_we_dont":["..."],"our_advantages":["..."],"priority_fixes":["..."]}"""})
    body=json.dumps({"model":"claude-haiku-4-5","max_tokens":1200,"messages":[{"role":"user","content":content}]}).encode()
    req=urllib.request.Request("https://api.anthropic.com/v1/messages",data=body,headers={"x-api-key":KEY,"anthropic-version":"2023-06-01","content-type":"application/json"})
    r=json.loads(urllib.request.urlopen(req,timeout=90).read())
    return r["content"][0]["text"], [l for l,_ in imgs]

if __name__=="__main__":
    v,labels=compare()
    print("Сравнивались:",labels); print("\n=== VISION 2.0 (vs реальные топы) ===\n",v)
