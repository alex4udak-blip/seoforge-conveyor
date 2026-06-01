"""АГЕНТ-FULLSITE — Sonnet пишет ВЕСЬ HTML+CSS казино-сайта (не мой каркас).

Корень "голой колонки": вёрстку держал мой программистский скелет. Решение: дизайнер
пишет полную страницу как настоящий веб-дизайнер. Я даю данные (контент/картинки/бренд) + рамки.
Контракт: build_fullsite(brand,keyword,geo,domain,plan,content,images) -> html.
Защита: vision-приёмка снаружи + если HTML битый/короткий → fallback на agent_builder.
"""
import os, json, re, urllib.request, html as _html
from core.keyword_taxonomy import GEO_FLAVOR
from core.footprint import mutate

KEY = os.environ.get("ANTHROPIC_API_KEY", "")
MODEL = "claude-sonnet-4-5"

def build_fullsite(brand, keyword, geo, domain, plan, content, images=None):
    fl = GEO_FLAVOR.get(geo, {})
    cur = fl.get("cur", "$"); maxbonus = fl.get("bonus", "5,000")
    pays = fl.get("pay", ["UPI", "Visa"])[:4]
    hot = fl.get("hot", ["Aviator", "Slots"])[:4]
    images = images or {}
    hero = images.get("hero", "")
    games_imgs = images.get("games", {})  # {game: url}
    pay_logos = images.get("pays", {})     # {pay: logo_url}
    casinos = images.get("casinos", [])    # [{name, logo, bonus}]
    # контент блоков сериализуем для агента
    blocks_data = [{"id": b, "h2": content.get(b, {}).get("h2", b),
                    "lead": content.get(b, {}).get("lead", ""),
                    "body": content.get(b, {}).get("body", "")} for b in plan.get("blocks", [])]
    if not KEY:
        return None  # без ключа — пусть caller использует agent_builder

    payload = {
        "brand": brand, "keyword": keyword, "geo": geo.upper(), "currency": cur,
        "max_bonus": maxbonus, "payments": pays, "popular_games": hot,
        "hero_image": hero, "game_images": games_imgs, "payment_logos": pay_logos,
        "top_casinos": casinos, "blocks": blocks_data,
    }
    prompt = f"""You are a world-class web designer+developer. Build a COMPLETE, modern, professional
online casino landing page in ONE self-contained HTML file (inline <style>, mobile-first).

DATA (use ALL of it):
{json.dumps(payload, ensure_ascii=False)[:6000]}

REQUIREMENTS — make it look like a REAL top-tier 2026 casino site (better than WordPress competitors):
- Sticky HEADER with brand logo-text + nav.
- HERO IS CRITICAL: the hero_image URL MUST be visibly rendered as a full-bleed background of the hero
  section (e.g. <section class="hero" style="background-image:linear-gradient(rgba(0,0,0,.55),rgba(0,0,0,.75)),url('HERO_IMAGE_URL');background-size:cover;background-position:center">).
  A plain dark hero with NO image = FAILURE. The image must show through behind the H1. Add a dark
  gradient overlay so white text stays readable. Use the EXACT hero_image URL from the data.
- Big H1, bonus badge, prominent CTA in the hero. Full width, real layout — NOT a narrow centered column.
- GAMES grid above-the-fold-ish: render each game_images URL as a real <img> card with the game name.
  These visuals MUST appear — a text-only page = FAILURE.
- TOPLIST of top_casinos with their logos, bonuses, ratings, Claim buttons (cards/table, styled). Skip if empty.
- PAYMENTS row using payment_logos (real <img> logos) + trust badges (licensed, SSL, 18+).
- Content blocks (use h2+lead+body) with good typography, spacing, sections that alternate bg.
- Sticky mobile CTA at bottom: a SHORT "Join Now"/"Sign Up" button ONLY — do NOT repeat the bonus
  amount there (it already appears in the hero; repeating it looks broken).
- Footer.
- Micro-animations (count-up, hover lift, shimmer on bonus) — write your own CSS @keyframes.
- RICH palette: a primary brand color + a SECONDARY accent + gradients — NOT one single accent on black
  everywhere (monotone = amateur). Dark premium base but with visual variety. Good fonts (Google Fonts link).
- MOBILE-FIRST: must look great on 390px AND desktop. Use grid/flex, responsive.
Output ONLY the full HTML from <!doctype html> to </html>. No explanation, no markdown fences."""
    def _gen(extra=""):
        body = json.dumps({"model": MODEL, "max_tokens": 16000,
                           "messages": [{"role": "user", "content": prompt + extra}]}).encode()
        req = urllib.request.Request("https://api.anthropic.com/v1/messages", data=body,
            headers={"x-api-key": KEY, "anthropic-version": "2023-06-01", "content-type": "application/json"})
        r = json.loads(urllib.request.urlopen(req, timeout=180).read())
        txt = r["content"][0]["text"]
        txt = re.sub(r"^```(?:html)?\s*|\s*```$", "", txt.strip())
        i = txt.lower().find("<!doctype")
        if i == -1: i = txt.lower().find("<html")
        if i == -1: return None
        html = txt[i:]
        if len(html) < 3000 or "</html>" not in html.lower() or html.count("<") < 50:
            return None
        return html
    try:
        html = _gen()
        # hero-картинка ОБЯЗАНА присутствовать (vision ловил "no hero image, plain dark bg")
        if html and hero and hero not in html:
            retry = _gen(f"\n\nCRITICAL: your previous output omitted the hero image. The hero section "
                         f"MUST contain this exact URL as a CSS background-image: {hero}")
            if retry and hero in retry:
                html = retry
        if not html:
            return None
        return mutate(html, domain)   # анти-footprint
    except Exception:
        return None
