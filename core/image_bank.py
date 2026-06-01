"""БАНК изображений: Runware (УНИКАЛЬНАЯ генерация под бренд) → fallback курируемый Unsplash.

Приоритет: если есть RUNWARE_API_KEY — генерим уникальный казино-визуал под бренд+тему
(решает footprint — у каждого сайта своя картинка). Иначе — проверенные Unsplash-фото (не сток-рулетка).
"""
import hashlib, os

# проверенные фото казино/гембла (Unsplash photo-id, реальные качественные фото)
HERO = [
    "1596838132731-3301c3fd4317",  # casino interior
    "1606167668584-78701c57f13d",  # casino chips
    "1605870445919-838d190e8e1b",  # roulette
    "1518709268805-4e9042af9f23",  # neon casino
    "1551892374-ecf8754cf8b0",     # slot lights
]
SLOTS = ["1518895949257-7621c3c786d7", "1551892374-ecf8754cf8b0", "1593696140826-c58b021acf8b"]
CARDS = ["1511193311914-0346f16efe90", "1542132968-958b339d6c7e"]  # poker/cards
CHIPS = ["1606167668584-78701c57f13d", "1605870445919-838d190e8e1b"]

# тема игры → подходящая категория фото
GAME_CAT = {
    "aviator": SLOTS, "jetx": SLOTS, "spaceman": SLOTS, "crash": SLOTS,
    "teen patti": CARDS, "andar bahar": CARDS, "poker": CARDS, "blackjack": CARDS,
    "crazy time": CHIPS, "roulette": CHIPS, "live": CHIPS,
    "fortune tiger": SLOTS, "slots": SLOTS, "book of dead": SLOTS, "starburst": SLOTS,
}

def _pick(pool, domain, key):
    i = int(hashlib.sha256(f"{domain}:{key}".encode()).hexdigest(), 16)
    return pool[i % len(pool)]

def _url(photo_id, w, h):
    return f"https://images.unsplash.com/photo-{photo_id}?w={w}&h={h}&fit=crop&q=80"

_RW_CACHE = {}
def _runware(prompt, w, h, key):
    """Генерация уникальной картинки Runware. Кэш по prompt чтоб не дёргать дважды."""
    if prompt in _RW_CACHE:
        return _RW_CACHE[prompt]
    try:
        import sys
        sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        os.environ.setdefault("RUNWARE_API_KEY", key)
        from core.image_agent import gen_image
        url, _ = gen_image(prompt, w, h)
        if url:
            _RW_CACHE[prompt] = url
        return url
    except Exception:
        return None

def hero_img(domain, w=1000, h=440, brand="", vibe="casino"):
    key = os.environ.get("RUNWARE_API_KEY", "")
    if key:
        prompt = f"{vibe} online casino scene, slot machines roulette chips, cinematic premium lighting, dark vibrant background, photorealistic, no text, no letters, no words, no watermark"
        u = _runware(prompt, ((w+63)//64)*64, ((h+63)//64)*64, key)
        if u: return u
    return _url(_pick(HERO, domain, "hero"), w, h)

def game_img(game, domain, w=400, h=260, key=None):
    key = key or os.environ.get("RUNWARE_API_KEY", "")
    if key:
        prompt = f"{game} casino game screen, vibrant exciting, mobile, no text, no watermark"
        u = _runware(prompt, 512, 384, key)
        if u: return u
    pool = GAME_CAT.get(game.lower(), SLOTS)
    return _url(_pick(pool, domain, f"game_{game}"), w, h)
