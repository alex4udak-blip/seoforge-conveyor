"""VISION-ПРИЁМКА — vision смотрит СКРИН готового сайта глазами перед выдачей.

Корень проблемы: я выдавал сайты НЕ ГЛЯДЯ → мерседес/HERO/говно-дизайн доходили до Алекса.
Решение: после сборки делаем скриншот, Claude vision оценивает: профессионально? mobile ок?
картинки норм (не мусор/не текст на фото)? балл < порога → пометка "переделать".
Использует тот же playwright-скрин что vision_audit (локально, venv).
"""
import os, json, base64, subprocess, sys, urllib.request

KEY = os.environ.get("ANTHROPIC_API_KEY", "")
MODEL = "claude-sonnet-4-5"  # оценка дизайна — сильная модель

def _shot(url, path):
    code = f"""
from playwright.sync_api import sync_playwright
with sync_playwright() as p:
    b=p.chromium.launch(args=['--no-sandbox','--disable-dev-shm-usage'])
    pg=b.new_page(viewport={{'width':390,'height':844}})  # MOBILE viewport — проверяем моб!
    try: pg.goto('{url}',wait_until='networkidle',timeout=30000); pg.wait_for_timeout(2500)
    except Exception as e: print('warn',e)
    pg.screenshot(path='{path}',full_page=False); b.close()
"""
    venv = "/Users/marsatim/Projects/SEO-Scanner-Pro/venv/bin/python"
    py = venv if os.path.exists(venv) else sys.executable
    try:
        subprocess.run([py, "-c", code], timeout=90, capture_output=True)
        return os.path.exists(path)
    except Exception:
        return False

def accept(url, brand=""):
    """Скрин (mobile) → vision оценка пригодности сайта. Возвращает {score, pass, issues, fixes}."""
    path = "/tmp/accept_shot.png"
    if not _shot(url, path):
        return {"error": "screenshot failed", "score": None}
    img = base64.b64encode(open(path, "rb").read()).decode()
    prompt = f"""You are a strict design reviewer. This is a MOBILE screenshot of a gambling site "{brand}".
Rate it as a real user would. Check:
1. Looks professional (not amateur/empty)?
2. Mobile layout OK (not broken, not desktop squeezed)?
3. Hero image relevant (real casino, NOT random car/object, NO text-on-image artifacts like letters)?
4. Visual hierarchy, spacing, modern feel?
5. Clear CTA, marketing hooks visible?
Return STRICT JSON: {{"score":0-100,"pass":true/false,"issues":["concrete problems you SEE"],"fixes":["what to change"]}}
pass=true only if it looks like a real professional casino site (score>=70)."""
    content = [{"type": "image", "source": {"type": "base64", "media_type": "image/png", "data": img}},
               {"type": "text", "text": prompt}]
    try:
        body = json.dumps({"model": MODEL, "max_tokens": 800,
                           "messages": [{"role": "user", "content": content}]}).encode()
        req = urllib.request.Request("https://api.anthropic.com/v1/messages", data=body,
            headers={"x-api-key": KEY, "anthropic-version": "2023-06-01", "content-type": "application/json"})
        r = json.loads(urllib.request.urlopen(req, timeout=90).read())
        txt = r["content"][0]["text"]
        import re
        txt = re.sub(r"^```(?:json)?\s*|\s*```$", "", txt.strip())
        s = txt.find("{"); e = txt.rfind("}") + 1
        return json.loads(txt[s:e])
    except Exception as ex:
        return {"error": str(ex)[:120], "score": None}
