"""Генерация контента страниц через Claude (haiku). Маркетинг-хуки + SEO-структура + гео-флейвор.
Инфо-страницы (guide/strategy/how-to/responsible) получают информационный, экспертный тон — для seo_structure."""
import os, json, urllib.request
from core.keyword_taxonomy import GEO_FLAVOR

KEY = os.environ.get("ANTHROPIC_API_KEY", "")
MODEL = "claude-haiku-4-5"

# инфо-слой = информационный интент (поднимает seo_structure + ловит top-of-funnel трафик)
INFO_SLUGS = {"guides", "strategy", "how-to-play", "responsible-gaming", "news"}

def gen_page_content(brand, geo, slug, title):
    flavor = GEO_FLAVOR.get(geo, GEO_FLAVOR.get("in", {}))
    hot = ", ".join(flavor.get("games", [])[:4])
    pays = ", ".join(flavor.get("pays", [])[:4])
    sport = flavor.get("sport", "cricket")
    is_info = slug in INFO_SLUGS
    if is_info:
        intent = (f"This is an INFORMATIONAL guide page (intent: educate, rank for how-to/strategy queries). "
                  f"Expert, helpful tone — NOT a sales page. Deep, useful, structured. Mention {brand} naturally once or twice, not pushy.")
        struct = '{{"h1":"...","intro":"130-167 words, informational, answers the query directly (passage-ready for AI search)","sections":[{{"h2":"...","p":"90-130 words, concrete steps/tips"}} x4],"faq":[{{"q":"...","a":"40-60 words"}} x4],"cta":"soft CTA"}}'
    else:
        intent = "This is a COMMERCIAL affiliate page. Punchy marketing: bonus, local payments, mobile, urgency."
        struct = '{{"h1":"...","intro":"120-160 words with marketing hooks + main keyword","sections":[{{"h2":"...","p":"80-120 words"}} x3],"faq":[{{"q":"...","a":"40-60 words"}} x4],"cta":"urgent CTA line"}}'
    prompt = f"""Write SEO content for a {brand} gambling page. GEO: {geo.upper()}.
Page: {title} (type: {slug}). Local hot games: {hot}. Payments: {pays}. Top sport: {sport}.
{intent}
Return STRICT JSON:
{struct}
Sound native to {geo.upper()}."""
    return _call(prompt, brand, geo, slug, title)

def _call(prompt, brand="Casino", geo="in", slug="index", title="Home"):
    try:
        req = urllib.request.Request(
            "https://api.anthropic.com/v1/messages",
            data=json.dumps({"model": MODEL, "max_tokens": 1600,
                "messages":[{"role":"user","content":prompt}]}).encode(),
            headers={"x-api-key": KEY, "anthropic-version":"2023-06-01","content-type":"application/json"})
        r = json.loads(urllib.request.urlopen(req, timeout=60).read())
        txt = r["content"][0]["text"]
        s = txt.find("{"); e = txt.rfind("}")+1
        return json.loads(txt[s:e])
    except Exception as e:
        print("content_gen fallback:", str(e)[:120])
        return _fallback(brand, geo, title)

def _fallback(brand, geo, title):
    """Шаблонный контент если Anthropic недоступен — сайт всё равно собирается (24/7 устойчивость)."""
    g = geo.upper()
    return {
        "h1": title,
        "intro": (f"{brand} is a leading online casino and betting platform for players in {g}. "
                  f"Enjoy a generous welcome bonus, fast local payments, and a huge library of slots, "
                  f"crash games and live casino — all optimised for mobile. Sign up in minutes and claim "
                  f"your bonus today. {brand} brings trusted, licensed gaming with 24/7 support to {g}."),
        "sections": [
            {"h2": f"Why Choose {brand} in {g}", "p": f"{brand} offers a licensed, secure platform with instant deposits via local payment methods, lightning-fast payouts, and round-the-clock customer support tailored for {g} players."},
            {"h2": "Games & Bonuses", "p": f"From popular slots and Aviator-style crash games to live dealer tables, {brand} delivers it all. New players get a big welcome bonus plus regular reloads and free spins."},
            {"h2": "Mobile & Payments", "p": f"Play anywhere on the {brand} mobile site — no download needed. Deposit and withdraw using fast, familiar local methods with low minimums and quick processing."},
        ],
        "faq": [
            {"q": f"Is {brand} legal in {g}?", "a": f"{brand} operates under an international gaming licence and accepts players from {g}. Always check your local regulations."},
            {"q": "How do I claim the bonus?", "a": "Register a new account, make your first deposit, and the welcome bonus is credited automatically. Terms apply."},
            {"q": "How fast are withdrawals?", "a": "Most withdrawals are processed within hours using local payment methods, depending on your chosen option."},
            {"q": "Can I play on mobile?", "a": f"Yes — {brand} works on any smartphone via the browser, no app download required."},
        ],
        "cta": f"Join {brand} now and claim your welcome bonus!",
    }
