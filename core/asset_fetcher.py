"""Asset-fetcher: реальные лого/иконки из открытых источников (не генерация).
Платёжки -> simpleicons CDN (брендовые SVG). Игры/казино -> поиск (TODO)."""
import urllib.request
# маппинг платёжка -> simpleicons slug (реальные брендовые лого)
SI={"paytm":"paytm","gpay":"googlepay","googlepay":"googlepay","phonepe":"phonepe",
    "bitcoin":"bitcoin","btc":"bitcoin","visa":"visa","mastercard":"mastercard",
    "paypal":"paypal","pix":"pix","skrill":"skrill","neteller":"neteller"}
def payment_logo_url(name):
    slug=SI.get(name.lower().replace(" ",""))
    if slug:
        url=f"https://cdn.simpleicons.org/{slug}"
        return url
    return None  # нет лого -> fallback цветной бейдж
def has_logo(name): return name.lower().replace(" ","") in SI

import urllib.parse as _up, hashlib as _hl
def _lettermark(name, domain):
    """Чистый буквенный лого (SVG data-URI) вместо google-глобуса-заглушки."""
    label = (name or domain or "?").strip()
    letter = (label[0].upper() if label else "?")
    palette = ["#e63946", "#f4a261", "#2a9d8f", "#6a4c93", "#1d3557", "#e76f51", "#457b9d", "#bc6c25"]
    color = palette[int(_hl.sha256(label.encode()).hexdigest(), 16) % len(palette)]
    svg = (f"<svg xmlns='http://www.w3.org/2000/svg' width='128' height='128'>"
           f"<rect width='128' height='128' rx='24' fill='{color}'/>"
           f"<text x='50%' y='50%' dy='.36em' text-anchor='middle' "
           f"font-family='Arial,sans-serif' font-size='68' font-weight='700' fill='#fff'>{letter}</text></svg>")
    return "data:image/svg+xml," + _up.quote(svg)

def casino_logo(domain, name=""):
    """Реальное лого казино: Clearbit (настоящий лого) → буквенный SVG (НЕ глобус-заглушка)."""
    d = (domain or "").strip().lower().replace("https://", "").replace("http://", "").split("/")[0]
    if d:
        try:
            u = f"https://logo.clearbit.com/{d}?size=128"
            req = urllib.request.Request(u, method="HEAD", headers={"User-Agent": "Mozilla/5.0"})
            if urllib.request.urlopen(req, timeout=6).status == 200:
                return u
        except Exception:
            pass
    return _lettermark(name, d)

import csv, os
def real_casino_brands(geo=None, n=3):
    """Реальные казино-бренды из нашей доменной базы (gamble_domains_base.csv)."""
    path=os.path.join(os.path.dirname(__file__),"..","..","SEO-Scanner-Pro","data","gamble_domains_base.csv")
    out=[]
    try:
        KNOWN=["1win","1xbet","melbet","4rabet","parimatch","22bet","betano","mostbet","linebet","betwinner","stake"]
        rows=list(csv.DictReader(open(path)))
        # сначала узнаваемые бренды
        for kb in KNOWN:
            for r in rows:
                d=r.get("domain","")
                if kb in d.lower() and "." in d:
                    out.append((kb.title() if kb!="1xbet" else "1xBet", d)); break
            if len(out)>=n: break
        if len(out)<n:
            for r in rows:
                d=r.get("domain","")
                if d and "." in d and not any(d==o[1] for o in out):
                    out.append((d.split(".")[0].replace("-"," ").title(), d))
                if len(out)>=n: break
    except Exception: pass
    return out[:n] if out else [("Royal Spin","royalspin.com"),("Lucky Jet","luckyjet.io"),("Mega Win","megawin.bet")]
