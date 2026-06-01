"""Авто-предложения для не-сеошника: софт сам предлагает бренд, домен, гео, ключи.
Опирается на нашу базу знаний (гео, горячие игры, платежи, ниши)."""

# гео с потенциалом (гембл-SEO приоритеты из созвонов: Tier-3 дешёвый трафик + высокий гембл-спрос)
GEOS = [
    {"code":"in","name":"Индия","flag":"IN","sport":"cricket","hot":["Aviator","Teen Patti","Andar Bahar"],"why":"огромный объём, дешёвый трафик, крикет+краш"},
    {"code":"bd","name":"Бангладеш","flag":"BD","sport":"cricket","hot":["Aviator","Crazy Time"],"why":"растущий рынок, bKash/Nagad, слабые конкуренты"},
    {"code":"br","name":"Бразилия","flag":"BR","sport":"football","hot":["Aviator","Fortune Tiger","Spaceman"],"why":"Pix, Fortune Tiger-мания, футбол"},
    {"code":"ng","name":"Нигерия","flag":"NG","sport":"football","hot":["Aviator","Spin","Slots"],"why":"Африка-Tier3, дешёвый трафик"},
    {"code":"pk","name":"Пакистан","flag":"PK","sport":"cricket","hot":["Aviator","Crash"],"why":"крикет, низкая конкуренция в выдаче"},
    {"code":"ke","name":"Кения","flag":"KE","sport":"football","hot":["Aviator","Spin"],"why":"M-Pesa, мобильный гембл"},
    {"code":"ph","name":"Филиппины","flag":"PH","sport":"basketball","hot":["Color Game","Slots"],"why":"GCash, азартный рынок SEA"},
    {"code":"uk","name":"Великобритания","flag":"UK","sport":"football","hot":["Book of Dead","Starburst"],"why":"Tier-1 высокий EPC (сложнее, но дороже лид)"},
]

# шаблоны брендов (нейтральные, не копируют реальные — свой бренд под сеть)
BRAND_STEMS = ["Aviator","Crash","Lucky","Royal","Mega","Turbo","Gold","Spin","Jet","Bet","Fortune","Star","Vegas","Win","Rocket","Boom","Diamond","Blaze"]
BRAND_TAILS = ["Win","Bet","Spin","Play","Casino","Club","Pro","Max","X","Gold","Jet"]

# типы сайтов с человеческим описанием
SITE_TYPES = [
    {"mode":"brand","name":"Бренд-казино","desc":"Полноценный сайт казино (14 страниц): главная, бонусы, игры, оплата, FAQ + инфо-блог. Льёт на регистрацию."},
    {"mode":"showcase","name":"Витрина-обзорник","desc":"Каталог-сравнение казино (топлист). Перехватывает запросы 'лучшие казино', льёт через сравнение."},
]

def _kw_for(geo):
    """Готовые ключи под гео — что реально ищут (краш-игры, казино, бонусы)."""
    g = next((x for x in GEOS if x["code"]==geo), GEOS[0])
    name_en = {"in":"india","bd":"bangladesh","br":"brasil","ng":"nigeria","pk":"pakistan","ke":"kenya","ph":"philippines","uk":"uk"}.get(geo,geo)
    hot = g["hot"][0].lower()
    return [
        {"kw":f"online casino {name_en}","intent":"коммерческий — высокий объём","type":"general"},
        {"kw":f"{hot} game {name_en}","intent":"краш-игра, горячо","type":"crash"},
        {"kw":f"best casino bonus {name_en}","intent":"бонус-хантеры, высокий CR","type":"general"},
        {"kw":f"{hot} predictor {name_en}","intent":"низкая конкуренция, лёгкий топ","type":"crash"},
    ]

def suggest(geo=None, seed=0):
    """Полный набор предложений. Если geo задан — заточено под него."""
    g = next((x for x in GEOS if x["code"]==geo), None)
    # генерим идеи сайтов (бренд+домен) — детерминированно по seed
    ideas = []
    for i in range(6):
        idx = (seed + i)
        stem = BRAND_STEMS[idx % len(BRAND_STEMS)]
        tail = BRAND_TAILS[(idx*3+1) % len(BRAND_TAILS)]
        brand = f"{stem}{tail}"
        gg = g or GEOS[idx % len(GEOS)]
        slug = f"{brand.lower()}-{gg['code']}"
        ideas.append({
            "brand": brand,
            "domain": slug,
            "geo": gg["code"], "geo_name": gg["name"],
            "hot_game": gg["hot"][0],
            "reason": f"{gg['name']}: {gg['why']}. Горячая игра — {gg['hot'][0]}.",
        })
    return {
        "geos": GEOS,
        "site_types": SITE_TYPES,
        "ideas": ideas,
        "keywords": _kw_for(geo or "in"),
        "tip": "Не знаешь что выбрать — жми «Случайная идея» или возьми любую карточку: бренд, домен и гео уже подобраны под спрос.",
    }
