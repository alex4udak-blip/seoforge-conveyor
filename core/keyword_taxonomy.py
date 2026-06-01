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
GEO_FLAVOR={  # локальная специфика (из созвонов) — валюта/платежи/игры/спорт под каждое гео
 "in":{"sport":"cricket","cur":"₹","cur_code":"INR","bonus":"₹30,000","pay":["UPI","Paytm","PhonePe"],"hot":["Aviator","Teen Patti","Andar Bahar"]},
 "bd":{"sport":"cricket","cur":"৳","cur_code":"BDT","bonus":"৳50,000","pay":["bKash","Nagad","Rocket"],"hot":["Aviator","Crazy Time"]},
 "br":{"sport":"football","cur":"R$","cur_code":"BRL","bonus":"R$5.000","pay":["Pix","Boleto"],"hot":["Aviator","Fortune Tiger","Spaceman"]},
 "ng":{"sport":"football","cur":"₦","cur_code":"NGN","bonus":"₦500,000","pay":["Flutterwave","Paystack","OPay","bank transfer"],"hot":["Aviator","Spin","Slots"]},
 "pk":{"sport":"cricket","cur":"₨","cur_code":"PKR","bonus":"₨100,000","pay":["JazzCash","Easypaisa","bank transfer"],"hot":["Aviator","Crash"]},
 "ke":{"sport":"football","cur":"KSh","cur_code":"KES","bonus":"KSh50,000","pay":["M-Pesa","Airtel Money"],"hot":["Aviator","Spin"]},
 "ph":{"sport":"basketball","cur":"₱","cur_code":"PHP","bonus":"₱25,000","pay":["GCash","Maya","GrabPay"],"hot":["Color Game","Slots","Jili"]},
 "uk":{"sport":"football","cur":"£","cur_code":"GBP","bonus":"£500","pay":["Visa","PayPal","Apple Pay"],"hot":["Book of Dead","Starburst"]},
}
def detect_type(kw):
    k=kw.lower()
    for t,d in KW_TYPES.items():
        if any(e.lower() in k or k in e.lower() for e in d["examples"]): return t
    if any(w in k for w in ["slot","bonanza","olympus","book of"]): return "slot"
    if any(w in k for w in ["aviator","crash","jetx","spaceman","mines","plinko"]): return "crash"
    if any(w in k for w in ["casino","gambl","betting","best "]): return "general"
    return "brand"
