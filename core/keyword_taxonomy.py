"""Таксономия ключей гембла -> интент -> секции/семантика страницы.
Генератор подбирает структуру под ТИП ключа (Алекс 30.05)."""
KW_TYPES={
 "general":{  # casino online, best casino
   "examples":["casino online","best online casino","real money casino","gambling sites"],
   "sections":["toplist","comparison","how_to_choose","payout_speed","bonuses","why_trust","faq"],
   "intent":"выбор площадки → toplist/витрина"},
 "brand":{    # 1win, melbet, parimatch
   "examples":["1win","melbet","4rabet","parimatch","22bet","betano","stake"],
   "sections":["brand_review","is_it_legit","bonuses","payout_speed","sister_sites","faq"],
   "intent":"перехват брендового трафика → review/alternative"},
 "slot":{     # Sweet Bonanza, Gates of Olympus
   "examples":["Sweet Bonanza","Gates of Olympus","Book of Dead","Big Bass Bonanza","Starburst","Sugar Rush"],
   "sections":["slot_demo","how_to_play","rtp_features","where_to_play","best_casinos_for_slot","faq"],
   "intent":"demo/free play → лить на казино с этим слотом"},
 "crash":{    # Aviator, JetX, Spaceman
   "examples":["Aviator","JetX","Spaceman","Mines","Plinko","Aviator game"],
   "sections":["how_to_play","strategy","predictor_myth","best_crash_sites","demo","faq"],
   "intent":"стратегия/как играть → лить на казино с краш-игрой. Горячо в IN/BD/BR"},
}
GEO_FLAVOR={  # локальная специфика (из созвонов)
 "in":{"sport":"cricket","pay":["UPI","Paytm"],"hot":["Aviator","Teen Patti","Andar Bahar"]},
 "bd":{"sport":"cricket","pay":["bKash","Nagad","Rocket"],"hot":["Aviator","Crazy Time"]},
 "br":{"sport":"football","pay":["Pix"],"hot":["Aviator","Fortune Tiger","Spaceman"]},
 "uk":{"sport":"football","pay":["card","PayPal"],"hot":["Book of Dead","Starburst"]},
}
def detect_type(kw):
    k=kw.lower()
    for t,d in KW_TYPES.items():
        if any(e.lower() in k or k in e.lower() for e in d["examples"]): return t
    if any(w in k for w in ["slot","bonanza","olympus","book of"]): return "slot"
    if any(w in k for w in ["aviator","crash","jetx","spaceman","mines","plinko"]): return "crash"
    if any(w in k for w in ["casino","gambl","betting","best "]): return "general"
    return "brand"
