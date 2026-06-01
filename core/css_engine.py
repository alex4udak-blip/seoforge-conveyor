"""CSS-движок — превращает дизайн-систему агента в ПРОФЕССИОНАЛЬНЫЙ mobile-first CSS.

Не программистский примитив (голая колонка). Современный CSS: mobile-first (375px база),
плавные анимации, тени, градиенты, sticky, responsive grid. Шрифты подключаются с Google Fonts.
"""
import re

# карта анимаций → реальный CSS (keyframes + класс)
ANIM_CSS = {
    "count-up": "",  # JS-driven, см. JS ниже
    "pulse-cta": "@keyframes pulse-cta{0%,100%{transform:scale(1);box-shadow:0 0 0 0 var(--acc)}50%{transform:scale(1.04);box-shadow:0 0 0 10px transparent}}.btn{animation:pulse-cta 2.4s infinite}",
    "shimmer-bonus": "@keyframes shim{to{background-position:200% 0}}.bonus,.hb{background:linear-gradient(110deg,var(--surface) 30%,var(--acc)22 50%,var(--surface) 70%);background-size:200% 100%;animation:shim 3s infinite}",
    "shimmer-gold": "@keyframes shim{to{background-position:200% 0}}.hb,.bonus{background:linear-gradient(110deg,var(--surface) 30%,var(--acc)33 50%,var(--surface) 70%);background-size:200% 100%;animation:shim 2.5s infinite}",
    "glow-hover": ".card:hover,.cc:hover{box-shadow:0 0 24px var(--acc)55;transform:translateY(-3px)}",
    "glow-pulse": "@keyframes gp{0%,100%{box-shadow:0 0 8px var(--acc)33}50%{box-shadow:0 0 22px var(--acc)88}}.hb{animation:gp 2s infinite}",
    "hover-lift": ".card:hover,.cc:hover,.gt:hover{transform:translateY(-4px);transition:.2s}",
    "scale-hover": ".cc:hover,.gt:hover{transform:scale(1.03);transition:.2s}",
    "fade-up": "@keyframes fu{from{opacity:0;transform:translateY(20px)}to{opacity:1;transform:none}}.b,.hero{animation:fu .6s ease both}",
    "slide-in": "@keyframes si{from{opacity:0;transform:translateX(-20px)}to{opacity:1;transform:none}}.b{animation:si .5s ease both}",
    "slide-reveal": "@keyframes sr{from{opacity:0;transform:translateY(24px)}to{opacity:1;transform:none}}.b{animation:sr .6s ease both}",
    "reveal-scroll": "@keyframes fu{from{opacity:0;transform:translateY(20px)}to{opacity:1;transform:none}}.b{animation:fu .6s ease both}",
    "card-reveal-stagger": ".cc{animation:fu .5s ease both}.cc:nth-child(2){animation-delay:.1s}.cc:nth-child(3){animation-delay:.2s}@keyframes fu{from{opacity:0;transform:translateY(16px)}to{opacity:1;transform:none}}",
    "flip-cards": ".cc{transition:.3s}.cc:hover{transform:rotateX(4deg) translateY(-3px)}",
    "multiplier-bounce": "@keyframes mb{0%,100%{transform:translateY(0)}50%{transform:translateY(-6px)}}.hbamt,.cr{display:inline-block;animation:mb 1.8s ease infinite}",
    "bounce-cta": "@keyframes bc{0%,100%{transform:translateY(0)}50%{transform:translateY(-5px)}}.btn{animation:bc 2s infinite}",
    "blink-live": "@keyframes bl{50%{opacity:.4}}.live-dot{animation:bl 1.2s infinite}",
    "ticker-winners": "",  # JS
    "marquee-pays": ".pays{overflow:hidden}",
    "gradient-shift": "@keyframes gs{0%,100%{background-position:0 0}50%{background-position:100% 0}}.hero{background-size:200% 200%;animation:gs 8s ease infinite}",
    "floating-particles": "",  # decorative, skip heavy
    "zoom-in": "@keyframes zi{from{opacity:0;transform:scale(.96)}to{opacity:1;transform:none}}.hero{animation:zi .7s ease both}",
}

def _fonts_link(ds):
    """Google Fonts <link> из шрифтов дизайн-системы."""
    fams = []
    for f in (ds.get("font_head", ""), ds.get("font_body", "")):
        m = re.search(r"'([^']+)'", f)
        if m: fams.append(m.group(1).replace(" ", "+"))
    fams = list(dict.fromkeys(fams))
    if not fams: return ""
    q = "&".join(f"family={f}:wght@400;600;700;800" for f in fams)
    return f'<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin><link href="https://fonts.googleapis.com/css2?{q}&display=swap" rel="stylesheet">'

def build_css(ds):
    """Полный mobile-first CSS из дизайн-системы."""
    bg, surf = ds.get("bg", "#0a0e1a"), ds.get("surface", "#141b2e")
    acc, acc2 = ds.get("accent", "#00e5a0"), ds.get("accent2", "#22d3ee")
    tx, mut = ds.get("text", "#eef2ff"), ds.get("muted", "#8b97ad")
    fh, fb = ds.get("font_head", "'Sora',sans-serif"), ds.get("font_body", "'Inter',sans-serif")
    rad = ds.get("radius", "16px")
    airy = ds.get("layout_density", "airy") == "airy"
    pad = "26px" if airy else "18px"
    # CSS-анимации: приоритет — СВОЙ css дизайнера (custom_css), иначе пресетные из карты
    cc = ds.get("custom_css", "")
    if cc and "{" in cc:
        # санитизация: убрать попытки закрыть style/инъекции, оставить чистый CSS
        cc = cc.replace("</style", "").replace("<script", "").replace("</", "")
        anims = "\n/* designer custom CSS */\n" + cc
    else:
        anims = "".join(ANIM_CSS.get(a, "") for a in ds.get("animations", []))
    return f"""
:root{{--bg:{bg};--surface:{surf};--acc:{acc};--acc2:{acc2};--tx:{tx};--mut:{mut};--rad:{rad}}}
*{{box-sizing:border-box;margin:0;padding:0}}
html{{scroll-behavior:smooth}}
body{{font-family:{fb};background:var(--bg);color:var(--tx);line-height:1.65;font-size:16px;-webkit-font-smoothing:antialiased}}
/* MOBILE-FIRST база (375px) */
.wrap{{width:100%;max-width:1100px;margin:0 auto;padding:{pad} 16px}}
h1{{font-family:{fh};font-size:28px;line-height:1.15;font-weight:800;letter-spacing:-.5px}}
h2,.h2{{font-family:{fh};font-size:22px;font-weight:700;color:var(--acc);margin:6px 0}}
h3{{font-family:{fh};font-size:18px;color:var(--acc)}}
p{{margin:10px 0;color:var(--tx)}}.lead{{font-size:17px;font-weight:600;color:var(--tx)}}
a{{color:var(--acc2)}}
/* HERO */
.hero{{background:radial-gradient(120% 140% at 50% 0%,var(--acc)22,transparent 60%),linear-gradient(180deg,var(--surface),var(--bg));padding:36px 0 30px;position:relative;overflow:hidden}}
.hero .wrap{{position:relative;z-index:2}}
.hbg{{width:100%;border-radius:var(--rad);margin-top:16px;aspect-ratio:16/7;object-fit:cover;box-shadow:0 12px 40px #00000060}}
.hb,.bonus{{display:inline-block;background:var(--surface);border:1px solid var(--acc)44;border-radius:var(--rad);padding:12px 18px;margin:14px 0;font-weight:700;color:var(--acc)}}
.hbamt{{font-size:20px;color:var(--acc)}}
/* CTA — крупная тач-цель для моб */
.btn,.cta{{display:inline-block;background:linear-gradient(135deg,var(--acc),var(--acc2));color:#06120c;padding:15px 30px;border-radius:var(--rad);font-weight:800;font-size:16px;text-decoration:none;border:none;cursor:pointer;box-shadow:0 8px 24px var(--acc)44}}
.cta.sm{{padding:9px 16px;font-size:13px;box-shadow:none}}
/* блоки */
.b{{padding:24px 0;border-bottom:1px solid #ffffff0d}}
.trust{{display:flex;flex-wrap:wrap;gap:8px;margin-top:14px}}.trust span{{background:var(--surface);border:1px solid #ffffff14;border-radius:9px;padding:6px 12px;font-size:12px;font-weight:600;color:var(--mut)}}
.winners{{margin-top:12px;color:var(--mut);font-size:14px}}.winners b{{color:var(--acc);font-size:18px}}
.licenses{{display:flex;flex-wrap:wrap;gap:8px;padding:14px 16px;max-width:1100px;margin:0 auto}}.licenses span{{font-size:11px;color:var(--mut);background:var(--surface);padding:5px 10px;border-radius:7px}}
/* PAYMENTS — реальные лого */
.pays{{display:flex;flex-wrap:wrap;gap:10px;margin-top:14px}}
.pay{{display:inline-flex;align-items:center;gap:7px;background:#fff;color:#111;border-radius:9px;padding:8px 12px;font-size:13px;font-weight:700}}
.pay img{{height:20px;display:block}}.pay.badge{{background:var(--surface);color:var(--tx);border:1px solid #ffffff18}}
/* GAMES grid — mobile 2 cols → desktop auto */
.games{{display:grid;grid-template-columns:repeat(2,1fr);gap:12px;margin-top:16px}}
.gt{{border-radius:var(--rad);overflow:hidden;background:var(--surface);box-shadow:0 6px 18px #00000040}}
.gt img{{width:100%;aspect-ratio:3/2;object-fit:cover;display:block}}.gt figcaption{{padding:10px;font-weight:700;font-size:14px}}
/* TOPLIST cards */
.toplist{{display:flex;flex-direction:column;gap:10px;margin-top:16px}}
.cc{{display:flex;align-items:center;gap:12px;background:var(--surface);border:1px solid #ffffff12;border-radius:var(--rad);padding:14px;flex-wrap:wrap;transition:.2s}}
.cc .rk{{font-weight:800;color:var(--acc);font-size:20px;min-width:24px}}
.cc .clogo{{border-radius:8px;background:#fff}}.cc .cn{{font-weight:700;flex:1;min-width:90px}}
.cc .cb{{font-size:13px;color:var(--mut);width:100%}}.cc .cr{{color:var(--acc);font-weight:700}}
/* STICKY mobile CTA */
.sticky{{position:fixed;left:12px;right:12px;bottom:12px;background:linear-gradient(135deg,var(--acc),var(--acc2));color:#06120c;text-align:center;padding:16px;border-radius:var(--rad);font-weight:800;text-decoration:none;z-index:99;box-shadow:0 8px 30px #000a}}
footer{{padding:28px 16px;text-align:center;color:var(--mut);font-size:13px;border-top:1px solid #ffffff0d}}
/* DESKTOP ≥760px */
@media(min-width:760px){{
  h1{{font-size:42px}}h2,.h2{{font-size:26px}}
  .hero{{padding:60px 0 50px}}
  .games{{grid-template-columns:repeat(auto-fill,minmax(170px,1fr))}}
  .cc .cb{{width:auto;flex:1}}
  .sticky{{left:auto;right:24px;bottom:24px;padding:14px 30px}}
}}
{anims}
"""

def anim_js(ds):
    """JS для динамических анимаций (count-up счётчики, ticker)."""
    a = ds.get("animations", [])
    js = []
    if "count-up" in a:
        js.append("""document.querySelectorAll('[data-count]').forEach(el=>{let t=+el.dataset.count,c=0,s=t/40;let i=setInterval(()=>{c+=s;if(c>=t){c=t;clearInterval(i)}el.textContent=Math.floor(c).toLocaleString()},30)});""")
    if "ticker-winners" in a:
        js.append("""const W=['Rahul won','Priya won','Amit won','Sneha won'];let wi=0;setInterval(()=>{const e=document.querySelector('.ticker');if(e){e.textContent=W[wi%W.length]+' '+(Math.floor(Math.random()*9000)+1000);wi++}},2600);""")
    return "<script>" + "".join(js) + "</script>" if js else ""
