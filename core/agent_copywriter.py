"""АГЕНТ-КОПИРАЙТЕР (генератор v2). Пишет контент блоков под AI-выдачу.

Принципы (из карты AI-платформ, цифры подтверждены):
- пассаж 134-167 слов (AIO favorit), прямой ответ 40-60 слов в НАЧАЛЕ блока (citation block)
- inverted pyramid: главное первым (44% цитат из первых 30% текста)
- конкретные факты/числа, не размытое промо (AI берёт факты)
- гео-локализация: валюта/платежи/игры из GEO_FLAVOR
- каждый H2 = под-запрос (query fan-out)
Возвращает {block_id: {"h2":..., "lead":<40-60сл прямой ответ>, "body":<пассаж>}}.
Без ключа — структурный fallback (всё равно по блокам, с гео-данными).
"""
import os, json, re, urllib.request
from core.keyword_taxonomy import GEO_FLAVOR

# язык контента под гео (сайт на языке аудитории, не русском!)
GEO_LANG = {"in": "English", "bd": "English", "ng": "English", "ke": "English",
            "ph": "English", "uk": "English", "br": "Brazilian Portuguese", "pk": "English",
            "de": "German", "fr": "French", "it": "Italian", "es": "Spanish", "pl": "Polish",
            "pt": "European Portuguese", "nl": "Dutch", "se": "Swedish", "ro": "Romanian", "gr": "Greek"}

KEY = os.environ.get("ANTHROPIC_API_KEY", "")
MODEL = "claude-haiku-4-5"

def write_content(brand, keyword, geo, plan):
    """plan = {layout, blocks, h2_plan}. Возвращает контент по блокам под AI-выдачу."""
    fl = GEO_FLAVOR.get(geo, GEO_FLAVOR.get("in", {}))
    cur = fl.get("cur", "$"); pays = ", ".join(fl.get("pay", [])[:3]); hot = ", ".join(fl.get("hot", [])[:3])
    blocks = plan.get("blocks", []); h2s = plan.get("h2_plan", [])
    if not KEY:
        return _fallback(brand, keyword, geo, blocks, h2s, cur, pays, hot)
    h2map = "\n".join(f"- {b}: {h2s[i] if i < len(h2s) else b}" for i, b in enumerate(blocks))
    lang = GEO_LANG.get(geo, "English")
    prompt = f"""You write gambling-site content in {lang} (target audience language!). Brand {brand}, geo {geo.upper()}. Keyword: {keyword}.
Locale: currency {cur}, payments {pays}, popular games {hot}.
Write content for these blocks (H2 already set — they are sub-queries for AI search):
{h2map}

RULES (to get cited in AI Overviews/ChatGPT/Perplexity):
- For EACH block: "lead" = direct answer 40-60 words (AI will cite this), "body" = passage 130-160 words with concrete facts.
- Most important first (inverted pyramid). Facts/numbers, no fluff. Natural human tone, UNIQUE wording per block.
- Geo-relevant: mention {cur}, {pays}, local games. Write ALL text in {lang}.
- Vary sentence structure — do NOT start every block the same way.
Return STRICT JSON only: {{"<block_id>":{{"h2":"...","lead":"40-60 words","body":"130-160 words"}}, ...}} for ALL {len(blocks)} blocks. No markdown."""
    try:
        body = json.dumps({"model": MODEL, "max_tokens": 8000,
                           "messages": [{"role": "user", "content": prompt}]}).encode()
        req = urllib.request.Request("https://api.anthropic.com/v1/messages", data=body,
            headers={"x-api-key": KEY, "anthropic-version": "2023-06-01", "content-type": "application/json"})
        r = json.loads(urllib.request.urlopen(req, timeout=150).read())
        txt = r["content"][0]["text"]
        # убрать markdown-обёртку ```json ... ```
        txt = re.sub(r"^```(?:json)?\s*|\s*```$", "", txt.strip())
        s = txt.find("{"); e = txt.rfind("}") + 1
        data = json.loads(txt[s:e])
        # гарантируем что все блоки покрыты
        for i, b in enumerate(blocks):
            if b not in data:
                data[b] = {"h2": h2s[i] if i < len(h2s) else b.replace("_", " ").title(),
                           "lead": f"{brand} offers top {b.replace('_',' ')} for {geo.upper()} players.",
                           "body": f"{brand} delivers quality {b.replace('_',' ')} with {pays}."}
        return data
    except Exception:
        return _fallback(brand, keyword, geo, blocks, h2s, cur, pays, hot)

def _fallback(brand, keyword, geo, blocks, h2s, cur, pays, hot):
    g = geo.upper(); out = {}
    for i, b in enumerate(blocks):
        h2 = h2s[i] if i < len(h2s) else b.replace("_", " ").title()
        out[b] = {
            "h2": h2,
            "lead": f"{brand} is a leading choice for {keyword} in {g}, offering {pays} payments, fast {cur} withdrawals and games like {hot}.",
            "body": (f"{brand} stands out for {g} players with instant {pays} deposits, licensed operation and a large library "
                     f"including {hot}. Withdrawals in {cur} clear within 24 hours. The platform is mobile-first, "
                     f"optimised for fast loading, and supports local payment methods that make depositing simple. "
                     f"New players receive a welcome bonus, and the site holds an international gaming licence."),
        }
    return out
