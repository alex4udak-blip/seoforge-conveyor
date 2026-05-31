#!/usr/bin/env python3
"""Vision-чекер: скрин сайта → Claude-vision судит как человек (современно/устарело, что не так).
Решает боль 'проверять визуально без ручного просмотра'.
Usage: python3 vision_checker.py <url>"""
import sys, base64, json, urllib.request, subprocess, os
KEY=os.environ.get("ANTHROPIC_API_KEY","")

def shot(url, path="/tmp/vc.png"):
    code=f"""
from playwright.sync_api import sync_playwright
with sync_playwright() as p:
    b=p.chromium.launch(); pg=b.new_page(viewport={{'width':1200,'height':1400}})
    pg.goto('{url}',wait_until='networkidle',timeout=30000)
    pg.screenshot(path='{path}',full_page=True); b.close()
"""
    subprocess.run(["/Users/marsatim/Projects/SEO-Scanner-Pro/venv/bin/python","-c",code],timeout=60)
    return path

def judge(path):
    img=base64.b64encode(open(path,"rb").read()).decode()
    prompt="""Ты — жёсткий арт-директор. Перед тобой скриншот gambling/casino affiliate-сайта.
Оцени ЧЕСТНО как профи 2026:
1. Уровень дизайна 1-10 (10=топ-конкурент типа casino.org, 1=шаблон 2010).
2. Выглядит современно или устарело? Почему конкретно.
3. ТОП-5 что улучшить визуально (конкретно: картинки, отступы, иерархия, цвета, элементы).
4. Чего не хватает vs реальный казино-сайт (картинки игр? баннеры? и т.д.).
Кратко, по делу, JSON: {"score":N,"verdict":"...","fix":["..."],"missing":["..."]}"""
    body=json.dumps({"model":"claude-haiku-4-5","max_tokens":900,"messages":[{"role":"user","content":[
        {"type":"image","source":{"type":"base64","media_type":"image/png","data":img}},
        {"type":"text","text":prompt}]}]}).encode()
    req=urllib.request.Request("https://api.anthropic.com/v1/messages",data=body,
        headers={"x-api-key":KEY,"anthropic-version":"2023-06-01","content-type":"application/json"})
    r=json.loads(urllib.request.urlopen(req,timeout=60).read())
    return r["content"][0]["text"]

if __name__=="__main__":
    url=sys.argv[1] if len(sys.argv)>1 else "http://localhost:8090/78win01_host/index.html"
    p=shot(url); print("=== VISION QA ===\n", judge(p))
