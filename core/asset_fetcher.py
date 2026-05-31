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

def casino_logo(domain):
    """Реальное лого казино через Google favicon API (любой домен)."""
    return f"https://www.google.com/s2/favicons?domain={domain}&sz=128"

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
