"""АГЕНТ-ДИЗАЙНЕР (Sonnet) — проектирует ПОЛНУЮ дизайн-систему каждого сайта.

Корень проблемы v1/agent_builder: дизайн писал программист (я) inline в Python → говно
(голая колонка, чёрный фон, нет mobile, нет анимаций). Решение: дизайн проектирует
LLM-агент с современным вкусом. Каждый сайт = своя дизайн-система → footprint в ноль + проф.вид.

Выход: dict с дизайн-токенами для верстальщика:
  palette, fonts, layout_style, hero_style, animations[], css_vars
Sonnet (claude-sonnet) — сильнее в дизайне чем haiku. Без ключа — курируемый набор проф-пресетов.
"""
import os, json, hashlib, urllib.request

KEY = os.environ.get("ANTHROPIC_API_KEY", "")
MODEL = "claude-sonnet-4-5"  # дизайн требует сильную модель

def _h(seed, k): return int(hashlib.sha256(f"{seed}:{k}".encode()).hexdigest(), 16)

# курируемые ПРОФЕССИОНАЛЬНЫЕ пресеты (не 5 голых палитр — полноценные дизайн-направления)
PRESETS = [
    {"name": "neon-dark", "bg": "#0a0e1a", "surface": "#141b2e", "accent": "#00e5a0", "accent2": "#22d3ee",
     "text": "#eef2ff", "muted": "#8b97ad", "font_head": "'Sora',sans-serif", "font_body": "'Inter',sans-serif",
     "radius": "16px", "vibe": "modern crypto-casino, neon glow, dark premium"},
    {"name": "royal-gold", "bg": "#120d08", "surface": "#1f1810", "accent": "#f5b73d", "accent2": "#e8854a",
     "text": "#fff8ec", "muted": "#b09a7a", "font_head": "'Playfair Display',serif", "font_body": "'Inter',sans-serif",
     "radius": "10px", "vibe": "luxury gold casino, elegant, high-roller"},
    {"name": "vibrant-purple", "bg": "#100a1f", "surface": "#1c1535", "accent": "#a78bfa", "accent2": "#f472b6",
     "text": "#f5f0ff", "muted": "#9a8bb5", "font_head": "'Poppins',sans-serif", "font_body": "'DM Sans',sans-serif",
     "radius": "20px", "vibe": "playful vibrant slots, gradient, energetic"},
    {"name": "sport-green", "bg": "#081410", "surface": "#10241c", "accent": "#3ddc84", "accent2": "#4ade80",
     "text": "#ecfdf3", "muted": "#7da896", "font_head": "'Montserrat',sans-serif", "font_body": "'Inter',sans-serif",
     "radius": "12px", "vibe": "sportsbook, fresh green, dynamic cricket/football"},
    {"name": "fire-red", "bg": "#150808", "surface": "#241010", "accent": "#ff5a5f", "accent2": "#ffb648",
     "text": "#fff0f0", "muted": "#b08585", "font_head": "'Oswald',sans-serif", "font_body": "'Inter',sans-serif",
     "radius": "8px", "vibe": "aggressive crash-game, hot red, urgency"},
    {"name": "ocean-blue", "bg": "#06101f", "surface": "#0e1d33", "accent": "#38bdf8", "accent2": "#818cf8",
     "text": "#eef6ff", "muted": "#7e93ad", "font_head": "'Rubik',sans-serif", "font_body": "'Inter',sans-serif",
     "radius": "14px", "vibe": "trustworthy clean, blue, professional review site"},
]

ANIM_SETS = [
    ["count-up", "fade-up", "pulse-cta", "shimmer-bonus"],
    ["slide-in", "glow-pulse", "ticker-winners", "hover-lift"],
    ["reveal-scroll", "bounce-cta", "flip-cards", "gradient-shift"],
    ["zoom-in", "blink-live", "marquee-pays", "scale-hover"],
]

def design_system(brand, geo, niche="casino", recon=None, seed=None):
    """Проектирует дизайн-систему сайта. С ключом — Sonnet под нишу/гео; без — проф-пресет по хешу."""
    seed = seed or brand
    if not KEY:
        return _preset(brand, geo, niche, seed)
    comp = ""
    if recon and recon.get("results"):
        comp = f"Competitors look generic WordPress. Make it look MORE professional and modern."
    prompt = f"""You are a senior web designer for a gambling brand "{brand}" ({niche}, geo {geo.upper()}).
{comp}
Design a UNIQUE modern design system (mobile-first, like top 2026 casino sites). Return STRICT JSON:
{{"name":"theme-name","bg":"#hex dark","surface":"#hex","accent":"#hex bright","accent2":"#hex",
"text":"#hex light","muted":"#hex","font_head":"'Font',sans-serif","font_body":"'Font',sans-serif",
"radius":"Npx","vibe":"short style description",
"animations":[pick 4-5 ONLY from this list: count-up,pulse-cta,shimmer-bonus,shimmer-gold,glow-hover,glow-pulse,hover-lift,scale-hover,fade-up,slide-in,slide-reveal,reveal-scroll,card-reveal-stagger,flip-cards,multiplier-bounce,bounce-cta,blink-live,ticker-winners,gradient-shift,zoom-in],
"hero_style":"one of: split-image|centered-bold|gradient-overlay|card-stack",
"layout_density":"airy|compact"}}
Pick fonts that fit the vibe. Colors must be tasteful and professional, NOT default black+white."""
    try:
        body = json.dumps({"model": MODEL, "max_tokens": 1200,
                           "messages": [{"role": "user", "content": prompt}]}).encode()
        req = urllib.request.Request("https://api.anthropic.com/v1/messages", data=body,
            headers={"x-api-key": KEY, "anthropic-version": "2023-06-01", "content-type": "application/json"})
        r = json.loads(urllib.request.urlopen(req, timeout=60).read())
        txt = r["content"][0]["text"]
        import re
        txt = re.sub(r"^```(?:json)?\s*|\s*```$", "", txt.strip())
        s = txt.find("{"); e = txt.rfind("}") + 1
        ds = json.loads(txt[s:e]); ds["source"] = "sonnet"
        # фильтр: только известные анимации (Sonnet может придумать свои) + гарантия базовых
        from core.css_engine import ANIM_CSS
        valid = [a for a in ds.get("animations", []) if a in ANIM_CSS]
        if len(valid) < 3:
            valid = list(dict.fromkeys(valid + ANIM_SETS[_h(seed, "anim") % len(ANIM_SETS)]))
        ds["animations"] = valid
        return ds
    except Exception as ex:
        p = _preset(brand, geo, niche, seed); p["design_error"] = str(ex)[:80]
        return p

def _preset(brand, geo, niche, seed):
    p = dict(PRESETS[_h(seed, "preset") % len(PRESETS)])
    p["animations"] = ANIM_SETS[_h(seed, "anim") % len(ANIM_SETS)]
    p["hero_style"] = ["split-image", "centered-bold", "gradient-overlay", "card-stack"][_h(seed, "hero") % 4]
    p["layout_density"] = "airy" if _h(seed, "dens") % 2 else "compact"
    p["source"] = "preset"
    return p
