"""МНОГОСТРАНИЧНЫЙ САЙТ-РАСХОДНИК (модель Димы, Tier-3): 6-9 страниц hub-and-spoke.

Корень претензии Алекса: "почему 1 страница? кнопки не жмутся?". Решение: реальный сайт из
нескольких страниц с РАБОЧЕЙ навигацией (относительные .html ссылки) и CTA на /go/ (редирект на оффер).
Каждую страницу пишет Sonnet (как build_fullsite), но с общей шапкой/футером и своей темой.
Контракт: build_multisite(brand,keyword,geo,domain,plan,content,images) -> {slug: html}.
"""
import os, json, re, urllib.request
from core.keyword_taxonomy import GEO_FLAVOR
from core.footprint import mutate

KEY = os.environ.get("ANTHROPIC_API_KEY", "")
MODEL = "claude-sonnet-4-5"

# страницы расходника (6-9): главная + спутники. role = что на странице.
PAGES = [
    {"slug": "index",       "nav": "Home",      "role": "HOME / toplist landing — hero with the brand, top casinos list, why-trust-us, quick games + payments glimpse"},
    {"slug": "bonuses",     "nav": "Bonuses",   "role": "BONUSES & PROMOTIONS — welcome bonus, free spins, wagering rules table, how to claim step-by-step"},
    {"slug": "games",       "nav": "Games",     "role": "GAMES library — the popular games (cards as grid with images), categories, RTP info"},
    {"slug": "payments",    "nav": "Payments",  "role": "DEPOSITS & WITHDRAWALS — payment methods with logos, min/max, withdrawal times table, step-by-step deposit"},
    {"slug": "review",      "nav": "Review",    "role": "EXPERT REVIEW of the brand — rating stars, pros/cons, verdict, who it's for"},
    {"slug": "app",         "nav": "App",       "role": "MOBILE APP / REGISTRATION — how to download & sign up step-by-step, device support"},
    {"slug": "responsible", "nav": "18+ Safety","role": "RESPONSIBLE GAMING & ABOUT — 18+, licensing, safety, self-exclusion, about us"},
]

def _nav_html(active):
    items = "".join(
        f'<a href="{p["slug"]}.html"{" aria-current=\"page\"" if p["slug"]==active else ""}>{p["nav"]}</a>'
        for p in PAGES)
    return items

def _build_page(page, ctx):
    """Sonnet пишет ОДНУ страницу с общей навигацией + своей темой."""
    nav_links = " | ".join(f'{p["nav"]}=>{p["slug"]}.html' for p in PAGES)
    prompt = f"""You are a world-class web designer+developer building ONE page of a multi-page online casino site.

BRAND: {ctx['brand']} | MARKET: {ctx['geo']} | LANGUAGE: write ALL text in {ctx['lang']} (never Russian unless that is {ctx['lang']}).
CURRENCY: {ctx['cur']} | MAX BONUS: {ctx['maxbonus']} | PAYMENTS: {ctx['pays']} | POPULAR GAMES: {ctx['hot']}

THIS PAGE = "{page['nav']}" — {page['role']}

NAVIGATION (MUST appear in the sticky header on EVERY page, links are relative .html files): {nav_links}
The current page is "{page['nav']}" — mark it active.

ASSETS you MUST use (exact URLs):
- hero/feature image: {ctx['hero']}
- game images: {json.dumps(ctx['games'], ensure_ascii=False)}
- payment logos: {json.dumps(ctx['pays_logos'], ensure_ascii=False)}
- top casinos (logo+bonus): {json.dumps(ctx['casinos'], ensure_ascii=False)}

HARD REQUIREMENTS:
- Sticky HEADER with brand logo-text + the FULL nav above (every nav item is a working <a href="SLUG.html">). The brand logo links to index.html.
- EVERY call-to-action / "Claim"/"Join"/"Sign Up"/"Play" button MUST be <a href="/go/"> (the offer redirect). NEVER href="#". No dead buttons.
- Page-appropriate hero: on index use {ctx['hero']} as a full-bleed CSS background with a LIGHT dark overlay (rgba .30-.55) so the image stays visible. Other pages: a slimmer header band.
- Render the relevant images as real <img> (games grid on Games page, payment logos on Payments page, casino logos in toplist on Home/Review). No garbled/duplicate images.
- ONE primary CTA in the hero (not 4 competing buttons). Secondary CTAs lower on the page are fine.
- Footer with: © {ctx['brand']} · 18+ · Play Responsibly · {ctx['geo']} + the nav links repeated.
- Rich but HARMONIOUS palette (primary + complementary accent, NO clashing teal-on-orange). NO emoji — inline SVG/CSS only.
- MOBILE-FIRST (great at 390px AND desktop), body font-size>=15px line-height>=1.6, own CSS @keyframes micro-animations.
- Real content for THIS page's topic (use the data above), good typography, sections that alternate background.

Output ONLY the full HTML from <!doctype html> to </html>. No markdown fences, no explanation."""
    body = json.dumps({"model": MODEL, "max_tokens": 16000,
                       "messages": [{"role": "user", "content": prompt}]}).encode()
    req = urllib.request.Request("https://api.anthropic.com/v1/messages", data=body,
        headers={"x-api-key": KEY, "anthropic-version": "2023-06-01", "content-type": "application/json"})
    r = json.loads(urllib.request.urlopen(req, timeout=180).read())
    txt = r["content"][0]["text"]
    txt = re.sub(r"^```(?:html)?\s*|\s*```$", "", txt.strip())
    i = txt.lower().find("<!doctype")
    if i == -1: i = txt.lower().find("<html")
    if i == -1: return None
    html = txt[i:]
    if len(html) < 2500 or "</html>" not in html.lower():
        return None
    # страж языка: не-RU гео + кириллица = брак
    if ctx['geocode'] not in ("ru",) and len(re.findall(r"[А-Яа-яЁё]", html)) > 5:
        return None
    return mutate(html, ctx['domain'])

def build_multisite(brand, keyword, geo, domain, plan, content, images=None):
    """Возвращает {slug: html} для всех страниц. None по странице — пропускаем (caller решает)."""
    if not KEY:
        return None
    from core.agent_copywriter import GEO_LANG
    fl = GEO_FLAVOR.get(geo, {})
    images = images or {}
    ctx = {
        "brand": brand, "keyword": keyword, "geo": geo.upper(), "geocode": geo,
        "lang": GEO_LANG.get(geo, "English"),
        "cur": fl.get("cur", "$"), "maxbonus": fl.get("bonus", "5,000"),
        "pays": ", ".join(fl.get("pay", ["UPI"])[:4]), "hot": ", ".join(fl.get("hot", ["Aviator"])[:4]),
        "hero": images.get("hero", ""), "games": images.get("games", {}),
        "pays_logos": images.get("pays", {}), "casinos": images.get("casinos", []),
        "domain": domain,
    }
    out = {}
    for page in PAGES:
        try:
            html = _build_page(page, ctx)
        except Exception:
            html = None
        if html:
            out[page["slug"]] = html
    return out or None
