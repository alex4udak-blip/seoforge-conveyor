"""План сайта: какие страницы генерим под каждый режим (brand/showcase/slot/crash).
Инфо-слой (guides/strategy/how-to/responsible/news) = информационные страницы для seo_structure + top-funnel трафик."""

# коммерческие страницы бренда
BRAND_COMMERCIAL = [
    ("index", "home"),
    ("review", "{brand} Review"),
    ("bonus", "{brand} Bonus & Promo Code"),
    ("app", "{brand} App Download"),
    ("login", "{brand} Login & Registration"),
    ("games", "{brand} Games & Slots"),
    ("payments", "{brand} Payments"),
    ("faq", "{brand} FAQ"),
    ("about", "About {brand}"),
]

# инфо-слой: информационный интент (hub-and-spoke, ловит how-to/strategy выдачу + AI-выдачу)
INFO_LAYER = [
    ("guides", "{brand} Casino Guide for Beginners"),
    ("strategy", "Winning Strategy & Tips for {brand}"),
    ("how-to-play", "How to Play & Win at {brand}"),
    ("responsible-gaming", "Responsible Gaming at {brand}"),
    ("news", "{brand} News & Latest Promotions"),
]

BRAND_PAGES = BRAND_COMMERCIAL + INFO_LAYER

def pages_for(mode, brand):
    if mode == "brand":
        return [(slug, title.format(brand=brand)) for slug, title in BRAND_PAGES]
    # showcase/slot/crash: hub + дочерние (пока hub)
    return [("index", "home")]
