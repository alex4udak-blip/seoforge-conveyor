"""АГЕНТ-ПРОМПТОВЩИК КАРТИНОК — LLM пишет УНИКАЛЬНЫЙ промпт под каждую картинку.

Поправка Алекса: "промпты к картинкам каждый раз разные должны писаться под текст, не хардкор".
Хардкод-словарь сцен = у всех сайтов похожие картинки = footprint + не привязано к контенту.
Решение: дешёвый Haiku пишет свежий vivid-промпт под бренд+игру+гео+текст, разный каждый раз (seed).
Жёсткие рамки зашиты в system: казино-эстетика, без текста/мастей/буквальной авиации.
"""
import os, json, urllib.request, hashlib

KEY = os.environ.get("ANTHROPIC_API_KEY", "")
MODEL = "claude-haiku-4-5"  # дёшево, промпт короткий

_RULES = ("Constraints baked in EVERY prompt: vivid premium CASINO/gambling aesthetic; bright sharp "
          "photorealistic; NO text, NO letters, NO numbers, NO playing-card suits or pips, NO readable "
          "card faces, NO logos, NO watermarks. CRASH games (aviator/jetx/spaceman/crash) must read as "
          "GAMBLING, NOT aviation: ABSOLUTELY NO airplanes, aircraft, jets, pilots, pilot jackets, "
          "cockpits, control panels, runways, propellers, helmets, goggles. Render ONLY casino energy: "
          "neon, gold chips/coins, dark premium backdrop, and an abstract glowing upward-streaking light "
          "trail/curve to suggest a rising multiplier. The image must instantly look like a CASINO, not "
          "an airline or aviation brand.")

def image_prompt(kind, brand="", game="", geo="", text="", seed=""):
    """LLM пишет уникальный промпт. kind: 'hero'|'game'. Fallback — детерминированный из image_bank."""
    if not KEY:
        return None
    # вариативность: подмешиваем хеш seed в инструкцию, чтоб каждый раз иначе
    h = hashlib.sha256(f"{kind}:{brand}:{game}:{seed}".encode()).hexdigest()[:8]
    subj = (f"the HERO banner of an online casino brand '{brand}' ({geo}) themed around '{game or 'casino'}'"
            if kind == "hero" else
            f"a thumbnail for the casino game '{game}' on brand '{brand}' ({geo})")
    ctx = f"\nPage copy for context (match its mood, do NOT put any of this text in the image): {text[:300]}" if text else ""
    sys = (f"You write ONE image-generation prompt (1-2 sentences, concrete visual nouns + lighting + mood). "
           f"{_RULES} Make this prompt DISTINCT from typical casino stock — vary the composition, palette, "
           f"camera angle and props (variation token {h}). Output ONLY the prompt text, nothing else.")
    user = f"Write a unique image prompt for {subj}.{ctx}"
    try:
        body = json.dumps({"model": MODEL, "max_tokens": 200, "system": sys,
                           "messages": [{"role": "user", "content": user}]}).encode()
        req = urllib.request.Request("https://api.anthropic.com/v1/messages", data=body,
            headers={"x-api-key": KEY, "anthropic-version": "2023-06-01", "content-type": "application/json"})
        r = json.loads(urllib.request.urlopen(req, timeout=40).read())
        p = r["content"][0]["text"].strip().strip('"')
        # подстраховка: добавим жёсткие негативы на случай если модель забыла
        return p + " — no text, no letters, no card suits, no real aircraft, no watermark"
    except Exception:
        return None
