"""Vision-аудит: логичная оценка сгенерированного сайта по ЧЁТКИМ критериям + сравнение с реальными топами.
Не «нравится/не нравится», а взвешенный балл по рубрике. Используется конвейером авто после генерации."""
import os, json, base64, urllib.request, subprocess, tempfile

KEY=os.environ.get("ANTHROPIC_API_KEY","")
MODEL="claude-haiku-4-5"

# РУБРИКА ОЦЕНКИ (веса = что реально важно: маркетинг+SEO важнее красоты — приоритет Алекса)
RUBRIC = {
 "marketing_hooks": 25,   # promo/urgency, бонус крупно, CTA, trust-badges, winners, sticky
 "seo_structure":   25,   # H1/H2 иерархия, schema, мета, инфо-слой, hub-and-spoke, robots/sitemap
 "trust_signals":   15,   # лицензии, payout-speed, отзывы, безопасность
 "conversion_ux":   15,   # toplist-карточки, сравнит.таблица, путь к депозиту, гео-платёжки
 "visual_design":   12,   # современность, картинки, типографика, воздух
 "geo_relevance":   8,    # локальные игры/платёжки/язык/спорт под гео
}

def _shot(url, path):
    code=f"""
from playwright.sync_api import sync_playwright
with sync_playwright() as p:
    b=p.chromium.launch(); pg=b.new_page(viewport={{'width':1280,'height':1400}})
    try: pg.goto('{url}',wait_until='networkidle',timeout=30000); pg.wait_for_timeout(2500)
    except Exception as e: print('warn',e)
    pg.screenshot(path='{path}',full_page=True); b.close()
"""
    venv="/Users/marsatim/Projects/SEO-Scanner-Pro/venv/bin/python"
    py=venv if os.path.exists(venv) else "python3"
    try: subprocess.run([py,"-c",code],timeout=60); return os.path.exists(path)
    except Exception: return False

def _b64(p): return base64.b64encode(open(p,"rb").read()).decode()

def audit(our_url, competitor_urls=None, geo="in", keyword="online casino"):
    """Скринит наш сайт (+конкурентов если заданы) → Claude оценивает по рубрике. Возвращает dict с баллами+обоснованием."""
    imgs=[]
    if _shot(our_url, "/tmp/audit_our.png"): imgs.append(("OUR","/tmp/audit_our.png"))
    for i,u in enumerate(competitor_urls or []):
        p=f"/tmp/audit_comp{i}.png"
        if _shot(u,p): imgs.append((f"COMPETITOR-{i+1} ({u.split('/')[2]})",p))
    if not imgs: return {"error":"screenshot failed"}

    rubric_txt="\n".join(f"- {k} (вес {v}): " for k,v in RUBRIC.items())
    content=[]
    for label,p in imgs:
        content.append({"type":"text","text":label})
        content.append({"type":"image","source":{"type":"base64","media_type":"image/png","data":_b64(p)}})
    has_comp=len(imgs)>1
    cmp_line=("Сравни OUR с реальными конкурентами из ТОП выдачи (они в топе = эталон)." if has_comp
              else "Оцени OUR по абсолютной шкале gambling-affiliate 2026.")
    prompt=f"""Ты — строгий аудитор gambling-SEO сайтов. Гео: {geo}, ключ: {keyword}. {cmp_line}
Оцени КАЖДЫЙ критерий рубрики по шкале 0-100 (насколько хорошо реализован), приоритет маркетинг+SEO важнее красоты:
{rubric_txt}
Для каждого критерия — балл + 1 фраза ПОЧЕМУ (что конкретно на скрине). Затем посчитай weighted_total (сумма балл*вес/100).
Верни СТРОГО JSON: {{"scores":{{"marketing_hooks":{{"score":N,"why":"..."}},"seo_structure":{{...}},"trust_signals":{{...}},"conversion_ux":{{...}},"visual_design":{{...}},"geo_relevance":{{...}}}},"weighted_total":N,"verdict":"одна фраза","top_fixes":["3 конкретных улучшения по приоритету"]}}"""
    content.append({"type":"text","text":prompt})
    body=json.dumps({"model":MODEL,"max_tokens":1500,"messages":[{"role":"user","content":content}]}).encode()
    req=urllib.request.Request("https://api.anthropic.com/v1/messages",data=body,
        headers={"x-api-key":KEY,"anthropic-version":"2023-06-01","content-type":"application/json"})
    r=json.loads(urllib.request.urlopen(req,timeout=90).read())
    txt=r["content"][0]["text"]
    s=txt.find("{"); e=txt.rfind("}")+1
    try: return json.loads(txt[s:e])
    except Exception: return {"raw":txt[:800]}

def weighted(scores):
    """Пересчёт weighted_total из scores по рубрике (контроль, не доверяем модели на арифметике)."""
    tot=0
    for k,w in RUBRIC.items():
        sc=scores.get(k,{})
        v=sc.get("score",0) if isinstance(sc,dict) else (sc or 0)
        tot+=v*w/100
    return round(tot,1)
