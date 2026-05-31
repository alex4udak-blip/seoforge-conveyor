"""Site-planner: бренд+гео -> карта СТРАНИЦ сайта (URL+тип+секции) с перелинковкой.
Режимы: 'brand' (расходник 6-9 стр, модель Димы) | 'showcase' (витрина 50-65, модель hotchip)."""
from core.keyword_taxonomy import KW_TYPES, GEO_FLAVOR
def plan_site(brand, geo, mode="brand"):
    fl=GEO_FLAVOR.get(geo,{}); hot=fl.get("hot",["slots","aviator"])
    pages=[]
    # главная (toplist/обзор бренда)
    pages.append({"slug":"index","title":f"{brand} {geo.upper()} Review","kw":f"{brand} casino","type":"brand","nav":"Home"})
    # базовые брендовые страницы (модель Димы 6-9)
    for s,kw,t in [("casino",f"{brand} casino","general"),("bet",f"{brand} betting","general"),
                   ("login",f"{brand} login","brand"),("bonus",f"{brand} bonus","brand"),
                   ("app",f"{brand} app download","brand")]:
        pages.append({"slug":s,"title":f"{brand} {s.title()}","kw":kw,"type":t,"nav":s.title()})
    # горячие игры гео (slot/crash страницы — локальная тематика)
    for g in hot[:3]:
        gt = "crash" if g.lower() in ("aviator","jetx","spaceman","mines","plinko") else "slot"
        slug=g.lower().replace(" ","-")
        pages.append({"slug":slug,"title":f"{g} on {brand}","kw":g,"type":gt,"nav":g})
    if mode=="showcase":
        # витрина: + ревью конкурентов-казино + payment + toplist-хабы (до 50+)
        for c in ["casino-a","casino-b","casino-c","casino-d"]:
            pages.append({"slug":f"review/{c}","title":f"{c} Review","kw":f"{c} casino","type":"brand","nav":None})
        for p in fl.get("pay",["upi"]):
            pages.append({"slug":f"pay/{p.lower()}","title":f"{p} Casinos","kw":f"{p} casino","type":"general","nav":None})
    # перелинковка: все nav-страницы линкуются между собой (hub-and-spoke)
    nav=[p for p in pages if p.get("nav")]
    return {"brand":brand,"geo":geo,"mode":mode,"pages":pages,"nav":nav}
