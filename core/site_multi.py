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

def _build_page(page, ctx):
    """Sonnet пишет ОДНУ страницу с общей навигацией + своей темой."""
    # nav: даём слаг + англ.подсказку темы, label Sonnet пишет на языке гео (анти-хардкор/анти-EN-течь)
    nav_links = " | ".join(f'{p["slug"]}.html (topic: {p["nav"]})' for p in PAGES)
    prompt = f"""You are a world-class web designer+developer building ONE page of a multi-page online casino site.

BRAND: {ctx['brand']} | MARKET: {ctx['geo']} | LANGUAGE: write ABSOLUTELY ALL visible text in {ctx['lang']} — this includes the menu/nav labels, every button (CTA), badges, section titles, table headers, footer, alt text. NOT a single English word unless {ctx['lang']} is English. Never Russian unless that is {ctx['lang']}.
CURRENCY: {ctx['cur']} | MAX BONUS: {ctx['maxbonus']} | PAYMENTS: {ctx['pays']} | POPULAR GAMES: {ctx['hot']}

THIS PAGE topic = {page['role']}

NAVIGATION (MUST appear in the sticky header on EVERY page; links are relative .html files; WRITE EACH MENU LABEL IN {ctx['lang']}, translating the topic): {nav_links}
Mark the current page ({page['nav']} topic) as active in the menu.

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
- STICKY BOTTOM CTA BAR: a position:fixed bar pinned to the bottom of the viewport that STAYS visible while
  scrolling (does NOT scroll away), containing a short bonus claim button (e.g. localized "Claim Bonus") as
  <a href="/go/">. Add bottom padding to the body so the fixed bar never covers the footer content. On mobile
  it must look like a native app bottom CTA, full-width, high-contrast.
- Footer with: © {ctx['brand']} · 18+ · Play Responsibly · {ctx['geo']} + the nav links repeated.
- Rich but HARMONIOUS palette (primary + complementary accent, NO clashing teal-on-orange). NO emoji — inline SVG/CSS only.
- MOBILE-FIRST (great at 390px AND desktop), body font-size>=15px line-height>=1.6, own CSS @keyframes micro-animations.
- Real content for THIS page's topic (use the data above), good typography, sections that alternate background.
- CONTENT DEPTH (SEO weight): write SUBSTANTIAL real copy — home/toplist ~1000-1500 words, other pages ~600-900 words of genuine useful text (not filler). Cover the topic thoroughly (this is how you outrank thin competitors).
- CURRENT YEAR IS 2026. Any year reference = 2026 (never 2024/2025). Fresh dates signal freshness to Google/AI.
- HUMAN TONE (anti AI-detection): write like a real local expert. BAN these AI-tells: "in conclusion", "moreover", "furthermore", "it's worth noting", "dive into", "when it comes to", "unlock", "elevate", "navigating the". Vary sentence length, be concrete and specific, no generic fluff.
- AI-SEARCH OPTIMIZATION (this is our edge — gets cited by ChatGPT/Perplexity/Google AI, 4.4x conversion):
  * Start the main content with a "Quick Answer" / TL;DR box: a self-contained 40-60 word direct answer to the page's core question (inverted pyramid — answer first, evidence after). Each major H2 also opens with a 1-2 sentence direct answer.
  * Include a FAQ section (4-6 real Q&A pairs) near the bottom — concrete questions a {ctx['geo']} player asks.
  * Add a JSON-LD <script type="application/ld+json"> in <head> with @graph: Organization + WebSite + WebPage + BreadcrumbList + (FAQPage matching the visible FAQ). Use https://{ctx['domain']} URLs, author "Editorial Team" (Person), datePublished/dateModified in 2026.
  * State the brand entity consistently (name, what it is, geo) so AI engines build a clear entity.
- LAYOUT DISCIPLINE: stack sections vertically in a logical reading order (header → hero → main content sections → footer). Every section is full-width with its inner content in ONE centered container (max-width ~1140px, consistent horizontal padding). NO overlapping blocks, NO floating/misaligned elements, NO orphaned half-width boxes — grids must have equal-height aligned cards. Consistent vertical rhythm (uniform section padding). It must look deliberately laid out, not scattered.
- TEXT-LEGIBILITY OVER IMAGES (critical, recurring bug): hero text must NEVER sit directly on raw image pixels. Put ALL hero text+CTA inside a centered content box that has its OWN semi-opaque dark backdrop (e.g. background:rgba(10,12,20,.55); padding:32px; border-radius:16px; backdrop-filter:blur(2px)) OR use a strong bottom gradient scrim. White text must stay clearly readable over the busy background. Same rule anywhere text overlays an image.
- RANK BADGES / NO OVERLAP (critical, recurring bug): in the toplist, the rank number (1/2/3) must be positioned so it NEVER overlaps the casino name — either inline BEFORE the name with a flex gap, or absolutely positioned in the card's top-left corner while the card content has enough padding-top to clear it. No element may overlap text anywhere.
- IMAGE CARDS: each game/casino image is a fixed-aspect block (e.g. height:170px; width:100%; object-fit:cover; border-radius on top corners). The game/casino NAME and button go in a separate area BELOW the image — never text on top of the image. Images never distort or overflow their card.

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
    # ГЕО-СТРАЖ: чужая валюта/платёжки/гео-слова (напр. ₹/India на BR) = брак
    try:
        from core.geo_check import check as _geocheck
        gc = _geocheck(html, ctx['geocode'])
        if not gc["ok"]:
            return None  # caller получит неполный набор → перегенерит/fallback
    except Exception:
        pass
    # ЧИСТКА: скрытые AI-символы (палево на детект) + актуальный год (LLM пишет 2024)
    try:
        from core.content_clean import clean
        html, _rep = clean(html)
    except Exception:
        pass
    # AI-выдача: гарант JSON-LD schema если Sonnet не вставил
    try:
        from core.ai_seo import ensure_schema
        html = ensure_schema(html, ctx['brand'], ctx['domain'], ctx['geocode'], page['slug'])
    except Exception:
        pass
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
        "pays": ", ".join(fl.get("pay", ["Visa","Mastercard"])[:4]), "hot": ", ".join(fl.get("hot", ["Slots","Roulette"])[:4]),
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
