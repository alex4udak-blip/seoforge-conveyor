"""ГЕО-ЧЕКЕР КОНСИСТЕНТНОСТИ — ловит чужое гео на сайте (валюта/платёжки/игры/язык).

Корень претензии Алекса: "бразильский ленд, а там India и рупии — почему vision/чекеры не ловят?".
vision смотрел только язык. Этот детерминированный чекер сверяет ВИДИМЫЙ текст с ожидаемым гео:
чужой символ валюты, чужие платёжки, чужие гео-маркеры → CRITICAL. Гоняется до выдачи.
"""
import re
from core.keyword_taxonomy import GEO_FLAVOR

# маркеры ЧУЖОГО гео: символ валюты + специфичные платёжки/слова. Если они на сайте другого гео = брак.
GEO_MARKERS = {
    "in": {"cur": "₹", "pay": ["UPI", "Paytm", "PhonePe"], "words": ["India", "Indian", "rupee"]},
    "bd": {"cur": "৳", "pay": ["bKash", "Nagad", "Rocket"], "words": ["Bangladesh", "Bangladeshi", "taka"]},
    "br": {"cur": "R$", "pay": ["Pix", "Boleto"], "words": ["Brasil", "brasileiro", "brasileira"]},
    "ng": {"cur": "₦", "pay": ["Flutterwave", "Paystack", "OPay"], "words": ["Nigeria", "Nigerian", "naira"]},
    "pk": {"cur": "₨", "pay": ["JazzCash", "Easypaisa"], "words": ["Pakistan", "Pakistani"]},
    "ke": {"cur": "KSh", "pay": ["M-Pesa", "Airtel Money"], "words": ["Kenya", "Kenyan", "shilling"]},
    "ph": {"cur": "₱", "pay": ["GCash", "Maya", "GrabPay"], "words": ["Philippines", "Filipino", "peso"]},
    "uk": {"cur": "£", "pay": [], "words": ["United Kingdom", "British"]},
}

def check(html, geo):
    """Возвращает {ok: bool, issues: [..]}. issues непуст = на сайте чужое гео."""
    issues = []
    geo = (geo or "").lower()
    own = GEO_MARKERS.get(geo, {})
    own_cur = own.get("cur", "")
    text = html
    for other_geo, m in GEO_MARKERS.items():
        if other_geo == geo:
            continue
        # чужой символ валюты (если не совпадает с нашим — напр. ₹ на BR)
        if m["cur"] and m["cur"] != own_cur and m["cur"] in text:
            cnt = text.count(m["cur"])
            issues.append(f"foreign currency '{m['cur']}' ({other_geo}) x{cnt} — expected '{own_cur}' for {geo.upper()}")
        # чужие платёжки
        for p in m["pay"]:
            if p not in (own.get("pay") or []) and re.search(rf"\b{re.escape(p)}\b", text):
                issues.append(f"foreign payment '{p}' ({other_geo}) on a {geo.upper()} site")
        # чужие гео-слова
        for w in m["words"]:
            if w not in (own.get("words") or []) and re.search(rf"\b{re.escape(w)}\b", text, re.I):
                issues.append(f"foreign geo word '{w}' ({other_geo}) on a {geo.upper()} site")
    # ok=False ТОЛЬКО при чужом гео (issues выше). Отсутствие своей валюты — мягкое предупреждение.
    warn = []
    if own_cur and own_cur not in text:
        warn.append(f"own currency '{own_cur}' not present (soft)")
    return {"ok": not issues, "issues": issues[:12], "warn": warn}
