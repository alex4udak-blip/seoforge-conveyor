"""АГЕНТ-АРХИТЕКТОР (генератор v2, агентная модель Димы).

Ключевой сдвиг от v1: НЕ фикс-шаблон, а LLM решает структуру КАЖДОГО сайта заново
из живых RECON-данных. Два сайта = два независимых плана → footprint падает в корне
(не вариации одного скелета, а разные скелеты).

Вход: keyword, geo, recon (топ/типы/семантика). Выход: structure-plan (JSON):
  блоки, порядок, H2 под query fan-out, тип каждой страницы.
Контракт: run(job)->job совместим.

Без ключа Claude — детерминированный fallback (хеш-комбинаторика на расширенном пуле),
который всё равно даёт больше энтропии чем v1 (берём из БОЛЬШОГО пула блоков+layout'ов).
"""
import os, json, hashlib, urllib.request

KEY = os.environ.get("ANTHROPIC_API_KEY", "")
MODEL = "claude-haiku-4-5"

# расширенный пул блоков (24 типа vs 9 в v1) — больше комбинаторики даже в fallback
BLOCK_POOL = [
    "intro_passage", "toplist_cards", "toplist_table", "comparison_grid", "why_trust",
    "payout_speed", "games_showcase", "live_casino", "crash_games", "bonuses_breakdown",
    "payment_methods", "how_to_register", "how_to_deposit", "mobile_app", "responsible_gaming",
    "licensing_info", "faq_accordion", "expert_review", "pros_cons", "user_reviews",
    "strategy_tips", "vs_comparison", "news_updates", "geo_legal",
]
# layout-архетипы (разный общий каркас, не один hero)
LAYOUTS = ["review-first", "toplist-first", "guide-first", "comparison-first", "qa-first", "magazine"]

def _h(seed, key):
    return int(hashlib.sha256(f"{seed}:{key}".encode()).hexdigest(), 16)

def _fallback_plan(keyword, geo, seed):
    """Детерминированный план без LLM — но из БОЛЬШОГО пула → высокая энтропия между доменами."""
    layout = LAYOUTS[_h(seed, "layout") % len(LAYOUTS)]
    n = 6 + _h(seed, "n") % 5  # 6-10 блоков
    pool = BLOCK_POOL[:]
    blocks = []
    for i in range(n):
        if not pool:
            break
        idx = _h(seed, f"b{i}") % len(pool)
        blocks.append(pool.pop(idx))
    # обязательные якоря под интент, но позиция варьируется
    if "intro_passage" not in blocks:
        blocks.insert(_h(seed, "intropos") % max(1, len(blocks)), "intro_passage")
    if "faq_accordion" not in blocks:
        blocks.append("faq_accordion")
    return {
        "layout": layout, "blocks": blocks, "source": "fallback",
        "h2_plan": [f"{b.replace('_',' ').title()}" for b in blocks],
    }

def plan_structure(keyword, geo, recon=None, seed=None):
    """Генерит структуру сайта. С ключом — Claude по RECON; без — fallback с энтропией."""
    seed = seed or keyword
    if not KEY:
        return _fallback_plan(keyword, geo, seed)
    # промпт агенту: спланируй УНИКАЛЬНУЮ структуру под этот ключ+гео+конкурентов
    comp = ""
    if recon and recon.get("results"):
        types = [r.get("type", "?") for r in recon["results"][:6]]
        comp = f"Конкуренты в топе (типы): {', '.join(types)}. Сделай ИНАЧЕ/лучше."
    rel = ", ".join((recon or {}).get("related", [])[:8])
    from core.agent_copywriter import GEO_LANG
    lang = GEO_LANG.get(geo, "English")
    prompt = f"""You are a gambling-SEO site architect. Keyword: {keyword}, geo: {geo.upper()}. {comp}
Semantic cluster (query fan-out): {rel}
Plan a UNIQUE structure (not a template). Pick a layout archetype and 6-10 blocks from:
{', '.join(BLOCK_POOL)}
Each H2 = a sub-query from the semantics (AI search loves fan-out).
CRITICAL: write every h2_plan title in {lang} (the language local users of {geo.upper()} actually read). Never Russian unless {lang} is Russian.
Return STRICT JSON only:
{{"layout":"<one of {LAYOUTS}>","blocks":["..."],"h2_plan":["one H2 per block, in {lang}"]}}"""
    try:
        body = json.dumps({"model": MODEL, "max_tokens": 800,
                           "messages": [{"role": "user", "content": prompt}]}).encode()
        req = urllib.request.Request("https://api.anthropic.com/v1/messages", data=body,
            headers={"x-api-key": KEY, "anthropic-version": "2023-06-01", "content-type": "application/json"})
        r = json.loads(urllib.request.urlopen(req, timeout=60).read())
        txt = r["content"][0]["text"]
        s = txt.find("{"); e = txt.rfind("}") + 1
        plan = json.loads(txt[s:e]); plan["source"] = "claude"
        return plan
    except Exception as ex:
        fb = _fallback_plan(keyword, geo, seed); fb["llm_error"] = str(ex)[:80]
        return fb
